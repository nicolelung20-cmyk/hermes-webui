import json
import tempfile
import threading
import unittest
from pathlib import Path

from durable_spend_ledger import Principal, SpendLedger


REQUESTER = Principal("requester", frozenset({"spend:request", "spend:read"}))
REVIEWER = Principal("reviewer", frozenset({"spend:approve", "spend:revoke"}))
EXECUTOR = Principal("worker", frozenset({"spend:execute"}))
AUDITOR = Principal("auditor", frozenset({"spend:reconcile", "spend:audit", "spend:read"}))
UNPRIVILEGED = Principal("stranger", frozenset())


class DurableSpendLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "spend.sqlite3")
        self.ledger = SpendLedger(self.db, max_per_transaction="25", max_cumulative="30")

    def tearDown(self):
        self.temp.cleanup()

    def submit(self, amount="10"):
        return self.ledger.submit(REQUESTER, "agent-1", "test", amount, "test request")

    def test_state_and_audit_survive_reopen(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        reopened = SpendLedger(self.db, max_per_transaction="25", max_cumulative="30")
        row = reopened.get(AUDITOR, rid)
        self.assertEqual(row["state"], "APPROVED")
        actions = [x["action"] for x in reopened.audit(AUDITOR, rid)]
        self.assertEqual(actions, ["SUBMITTED", "APPROVED"])

    def test_unauthorized_and_self_approval_rejected(self):
        rid = self.submit()
        with self.assertRaises(PermissionError):
            self.ledger.approve(UNPRIVILEGED, rid)
        with self.assertRaises(PermissionError):
            self.ledger.approve(Principal("requester", frozenset({"spend:approve"})), rid)
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "PENDING")

    def test_revocation_blocks_execution(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        self.ledger.revoke(REVIEWER, rid)
        calls = []
        with self.assertRaises(ValueError):
            self.ledger.execute(EXECUTOR, rid, lambda payload, key: calls.append(key) or {"provider_ref": "p1"})
        self.assertEqual(calls, [])
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "REVOKED")

    def test_duplicate_execution_is_idempotent(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        calls = []
        def executor(payload, key):
            calls.append(key)
            return {"provider_ref": "provider-1", "status": "accepted"}
        first = self.ledger.execute(EXECUTOR, rid, executor)
        second = self.ledger.execute(EXECUTOR, rid, executor)
        self.assertEqual(first, second)
        self.assertEqual(calls, [rid])

    def test_external_side_effect_then_timeout_becomes_unknown_and_is_not_retried(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        side_effects = []
        def ambiguous_executor(payload, key):
            side_effects.append(key)  # stand-in for provider accepted payment
            raise TimeoutError("response lost after provider accepted")
        with self.assertRaises(TimeoutError):
            self.ledger.execute(EXECUTOR, rid, ambiguous_executor)
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "UNKNOWN")
        with self.assertRaises(ValueError):
            self.ledger.execute(EXECUTOR, rid, ambiguous_executor)
        self.assertEqual(side_effects, [rid])
        self.ledger.reconcile(AUDITOR, rid, outcome="EXECUTED", provider_ref="provider-accepted-1")
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "EXECUTED")

    def test_reconciliation_requires_provider_reference_for_success(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        with self.assertRaises(TimeoutError):
            self.ledger.execute(EXECUTOR, rid, lambda payload, key: (_ for _ in ()).throw(TimeoutError()))
        with self.assertRaises(ValueError):
            self.ledger.reconcile(AUDITOR, rid, outcome="EXECUTED")
        self.ledger.reconcile(AUDITOR, rid, outcome="NOT_EXECUTED", details="provider confirms no operation")
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "FAILED")

    def test_cumulative_limit_reserves_pending_requests_atomically(self):
        barrier = threading.Barrier(2)
        outcomes = []
        def worker():
            barrier.wait()
            try:
                outcomes.append(("ok", self.ledger.submit(REQUESTER, "a", "test", "20", "parallel")))
            except ValueError:
                outcomes.append(("rejected", None))
        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads: t.start()
        for t in threads: t.join()
        self.assertEqual(sum(x[0] == "ok" for x in outcomes), 1)
        self.assertEqual(sum(x[0] == "rejected" for x in outcomes), 1)

    def test_execution_permission_is_required(self):
        rid = self.submit()
        self.ledger.approve(REVIEWER, rid)
        with self.assertRaises(PermissionError):
            self.ledger.execute(UNPRIVILEGED, rid, lambda payload, key: {"provider_ref": "x"})
        self.assertEqual(self.ledger.get(AUDITOR, rid)["state"], "APPROVED")

    def test_audit_requires_permission(self):
        rid = self.submit()
        with self.assertRaises(PermissionError):
            self.ledger.audit(UNPRIVILEGED, rid)

    def test_uncertain_state_reserves_limit(self):
        rid = self.submit("20")
        self.ledger.approve(REVIEWER, rid)
        with self.assertRaises(TimeoutError):
            self.ledger.execute(EXECUTOR, rid, lambda payload, key: (_ for _ in ()).throw(TimeoutError()))
        with self.assertRaises(ValueError):
            self.ledger.submit(REQUESTER, "agent-2", "test", "15", "would exceed reserved limit")


if __name__ == "__main__":
    unittest.main(verbosity=2)
