import math
import unittest
from decimal import Decimal
from spend_guard import validate_amount, request_and_execute_spend


class FakeCoordinator:
    def __init__(self, status="APPROVED", ready=True, execute_result="EXECUTED"):
        self.status, self.ready, self.execute_result = status, ready, execute_result
        self.executions = 0
        self.submitted = None

    def submit_spend_request(self, agent_id, category, amount, desc):
        self.submitted = (agent_id, category, amount, desc)
        return "exec-1", self.status

    def check_execution_ready(self, exec_id):
        return self.ready, "not ready"

    def execute_spend(self, exec_id):
        self.executions += 1
        return self.execute_result


class ValidateAmountTests(unittest.TestCase):
    def test_valid_values_return_decimal(self):
        self.assertEqual(validate_amount("12.30"), Decimal("12.30"))
        self.assertEqual(validate_amount(1), Decimal("1"))

    def test_rejects_bool_nonpositive_nonfinite_and_invalid(self):
        for value in (True, False, 0, -1, float("nan"), float("inf"), "nope", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_amount(value)

    def test_rejects_more_than_two_decimal_places(self):
        with self.assertRaises(ValueError):
            validate_amount("1.001")


class RequestExecutionTests(unittest.TestCase):
    def test_executes_only_when_explicitly_approved_and_ready(self):
        c = FakeCoordinator()
        self.assertEqual(
            request_and_execute_spend(c, "a", "test", "2.50", "desc"),
            ("exec-1", "EXECUTED"),
        )
        self.assertEqual(c.executions, 1)
        self.assertEqual(c.submitted[2], Decimal("2.50"))

    def test_non_approval_never_executes(self):
        for status in ("PENDING", "NOT_APPROVED", "APPROVED_WITH_WARNINGS", None):
            c = FakeCoordinator(status=status)
            result = request_and_execute_spend(c, "a", "test", 2, "desc")
            self.assertEqual(result, ("exec-1", status))
            self.assertEqual(c.executions, 0)

    def test_timeout_never_executes(self):
        c = FakeCoordinator(ready=False)
        result = request_and_execute_spend(
            c, "a", "test", 2, "desc", timeout_seconds=0
        )
        self.assertEqual(
            result, ("exec-1", "PENDING_TIMEOUT — no execution attempted")
        )
        self.assertEqual(c.executions, 0)

    def test_coordinator_errors_propagate_without_execution(self):
        class Broken(FakeCoordinator):
            def submit_spend_request(self, *args):
                raise RuntimeError("offline")
        c = Broken()
        with self.assertRaisesRegex(RuntimeError, "offline"):
            request_and_execute_spend(c, "a", "test", 2, "desc")
        self.assertEqual(c.executions, 0)

    def test_invalid_amount_is_rejected_before_submission(self):
        c = FakeCoordinator()
        with self.assertRaises(ValueError):
            request_and_execute_spend(c, "a", "test", math.nan, "desc")
        self.assertIsNone(c.submitted)


if __name__ == "__main__":
    unittest.main(verbosity=2)
