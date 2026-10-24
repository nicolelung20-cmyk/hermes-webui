"""Fail-closed spending request helper. Does not itself authorize payments."""
from decimal import Decimal, InvalidOperation
import math
import time


def validate_amount(amount):
    """Validate a positive USD amount with at most two decimal places."""
    if isinstance(amount, bool):
        raise ValueError("Amount must be a monetary value")
    if isinstance(amount, float) and not math.isfinite(amount):
        raise ValueError("Amount must be finite and positive")
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Amount must be a valid monetary value") from None
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be finite and positive")
    if value.as_tuple().exponent < -2:
        raise ValueError("USD amounts cannot exceed two decimal places")
    return value


def request_and_execute_spend(
    coordinator, agent_id, category, amount, desc, *, timeout_seconds=60,
    poll_interval=0.5,
):
    """Submit a spend request and execute only after explicit approval/readiness.

    The coordinator MUST atomically revalidate approval, limits, request binding,
    and idempotency inside execute_spend immediately before committing.
    A timeout while waiting is reported as pending; it never triggers execution.
    Exceptions from the coordinator intentionally propagate (fail closed).
    """
    value = validate_amount(amount)
    if (isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds) or timeout_seconds < 0):
        raise ValueError("timeout_seconds must be finite and non-negative")
    if (isinstance(poll_interval, bool)
            or not isinstance(poll_interval, (int, float))
            or not math.isfinite(poll_interval) or poll_interval <= 0):
        raise ValueError("poll_interval must be finite and positive")

    exec_id, status = coordinator.submit_spend_request(
        agent_id, category, value, desc
    )
    if status != "APPROVED":
        return exec_id, status

    deadline = time.monotonic() + timeout_seconds
    while True:
        ready, _detail = coordinator.check_execution_ready(exec_id)
        if ready:
            # Coordinator is the final authority and must make this atomic/idempotent.
            return exec_id, coordinator.execute_spend(exec_id)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return exec_id, "PENDING_TIMEOUT — no execution attempted"
        time.sleep(min(poll_interval, remaining))
