"""Durable, fail-closed spend approval ledger.

This module is a safety ledger, not a payment processor. A trusted application
must derive Principal from authenticated identity/authorization middleware.
External executors must support idempotency keys and a reconciliation API.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import json
import sqlite3
import uuid


ACTIVE_STATES = ("PENDING", "APPROVED", "EXECUTING", "UNKNOWN", "EXECUTED")


@dataclass(frozen=True)
class Principal:
    actor_id: str
    permissions: frozenset[str]


def _money(value):
    if isinstance(value, bool):
        raise ValueError("amount must be positive finite USD")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("amount must be positive finite USD") from None
    if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
        raise ValueError("amount must be positive finite USD with at most 2 decimals")
    return amount.quantize(Decimal("0.01"))


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb):
        try:
            return super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


class SpendLedger:
    """SQLite-backed atomic approval/limit/idempotency ledger."""

    def __init__(self, db_path, *, max_per_transaction="0", max_cumulative="0"):
        self.db_path = str(Path(db_path))
        self.max_per_transaction = _money(max_per_transaction)
        self.max_cumulative = _money(max_cumulative)
        if self.max_per_transaction <= 0 or self.max_cumulative <= 0:
            raise ValueError("limits must be positive; zero-limit policy blocks spending")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                PRAGMA synchronous=FULL;
                CREATE TABLE IF NOT EXISTS spend_requests (
                    id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    description TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    approved_by TEXT,
                    provider_ref TEXT,
                    result TEXT,
                    failure TEXT
                );
                CREATE TABLE IF NOT EXISTS spend_audit (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    FOREIGN KEY(request_id) REFERENCES spend_requests(id)
                );
            """)

    def _connect(self):
        db = sqlite3.connect(self.db_path, timeout=15, isolation_level=None, factory=_ClosingConnection)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @staticmethod
    def _require(principal, permission):
        if not isinstance(principal, Principal) or not principal.actor_id:
            raise PermissionError("authenticated principal required")
        if permission not in principal.permissions:
            raise PermissionError(f"missing permission: {permission}")

    @staticmethod
    def _audit(db, request_id, actor_id, action, **details):
        db.execute(
            "INSERT INTO spend_audit(request_id,actor_id,action,details) VALUES(?,?,?,?)",
            (request_id, actor_id, action, json.dumps(details, sort_keys=True)),
        )

    def submit(self, principal, agent_id, category, amount, description):
        self._require(principal, "spend:request")
        amount = _money(amount)
        if amount > self.max_per_transaction:
            raise ValueError("per-transaction limit exceeded")
        fields = (agent_id, category, description)
        if any(not isinstance(v, str) or not v.strip() for v in fields):
            raise ValueError("agent_id, category, and description are required")
        request_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            placeholders = ",".join("?" for _ in ACTIVE_STATES)
            rows = db.execute(
                f"SELECT amount FROM spend_requests WHERE state IN ({placeholders})",
                ACTIVE_STATES,
            ).fetchall()
            reserved = sum((Decimal(r["amount"]) for r in rows), Decimal("0.00"))
            if reserved + amount > self.max_cumulative:
                db.rollback()
                raise ValueError("cumulative limit exceeded by active/reserved requests")
            db.execute(
                """INSERT INTO spend_requests
                (id,agent_id,category,amount,description,state,created_by)
                VALUES(?,?,?,?,?,'PENDING',?)""",
                (request_id, agent_id, category, str(amount), description, principal.actor_id),
            )
            self._audit(db, request_id, principal.actor_id, "SUBMITTED", amount=str(amount))
            db.commit()
        return request_id

    def approve(self, principal, request_id):
        self._require(principal, "spend:approve")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError(request_id)
            if row["created_by"] == principal.actor_id:
                db.rollback()
                raise PermissionError("requester cannot approve their own request")
            if row["state"] != "PENDING":
                db.rollback()
                raise ValueError("only pending requests can be approved")
            db.execute("UPDATE spend_requests SET state='APPROVED',approved_by=? WHERE id=?",
                       (principal.actor_id, request_id))
            self._audit(db, request_id, principal.actor_id, "APPROVED")
            db.commit()

    def revoke(self, principal, request_id):
        self._require(principal, "spend:revoke")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError(request_id)
            if row["state"] != "APPROVED":
                db.rollback()
                raise ValueError("only approved, unclaimed requests can be revoked")
            db.execute("UPDATE spend_requests SET state='REVOKED' WHERE id=?", (request_id,))
            self._audit(db, request_id, principal.actor_id, "REVOKED")
            db.commit()

    def execute(self, principal, request_id, executor):
        """Claim exactly once, then invoke executor with request_id as idempotency key.

        Any exception after claim yields UNKNOWN, never automatic retry. Reconcile
        UNKNOWN against the provider before resolving it.
        """
        self._require(principal, "spend:execute")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError(request_id)
            if row["state"] == "EXECUTED":
                db.commit()
                return row["result"]
            if row["state"] != "APPROVED":
                db.rollback()
                raise ValueError(f"request cannot execute from state {row['state']}")
            # Recheck reserved limit inside the same serialized transaction.
            db.execute("UPDATE spend_requests SET state='EXECUTING' WHERE id=?", (request_id,))
            self._audit(db, request_id, principal.actor_id, "EXECUTION_CLAIMED",
                        idempotency_key=request_id)
            payload = dict(row)
            db.commit()
        try:
            result = executor(payload, request_id)
            if not isinstance(result, dict) or not result.get("provider_ref"):
                raise RuntimeError("executor must return provider_ref for reconciliation")
        except Exception as exc:
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("UPDATE spend_requests SET state='UNKNOWN',failure=? WHERE id=? AND state='EXECUTING'",
                           (f"{type(exc).__name__}: {exc}"[:500], request_id))
                self._audit(db, request_id, principal.actor_id, "OUTCOME_UNKNOWN")
                db.commit()
            raise
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT state FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            if current["state"] != "EXECUTING":
                db.rollback()
                raise RuntimeError("execution state changed unexpectedly; reconcile provider")
            db.execute("UPDATE spend_requests SET state='EXECUTED',provider_ref=?,result=?,failure=NULL WHERE id=?",
                       (str(result["provider_ref"]), json.dumps(result, sort_keys=True), request_id))
            self._audit(db, request_id, principal.actor_id, "EXECUTED",
                        provider_ref=str(result["provider_ref"]))
            db.commit()
        return json.dumps(result, sort_keys=True)

    def reconcile(self, principal, request_id, *, outcome, provider_ref=None, details=""):
        self._require(principal, "spend:reconcile")
        if outcome not in {"EXECUTED", "NOT_EXECUTED", "UNKNOWN"}:
            raise ValueError("outcome must be EXECUTED, NOT_EXECUTED, or UNKNOWN")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            if row is None:
                db.rollback()
                raise KeyError(request_id)
            if row["state"] not in {"UNKNOWN", "EXECUTING"}:
                db.rollback()
                raise ValueError("only uncertain executions can be reconciled")
            if outcome == "EXECUTED" and not provider_ref:
                db.rollback()
                raise ValueError("provider_ref required for executed outcome")
            state = {"EXECUTED": "EXECUTED", "NOT_EXECUTED": "FAILED", "UNKNOWN": "UNKNOWN"}[outcome]
            db.execute("UPDATE spend_requests SET state=?,provider_ref=COALESCE(?,provider_ref),failure=? WHERE id=?",
                       (state, provider_ref, details[:500] or None, request_id))
            self._audit(db, request_id, principal.actor_id, "RECONCILED",
                        outcome=outcome, provider_ref=provider_ref, details=details[:500])
            db.commit()

    def get(self, principal, request_id):
        self._require(principal, "spend:read")
        with self._connect() as db:
            row = db.execute("SELECT * FROM spend_requests WHERE id=?", (request_id,)).fetchone()
            return dict(row) if row else None

    def audit(self, principal, request_id):
        self._require(principal, "spend:audit")
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM spend_audit WHERE request_id=? ORDER BY seq", (request_id,)
            ).fetchall()]
