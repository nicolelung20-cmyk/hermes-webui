"""Request output independent of agent/tool stdout capture."""

import os
import threading


# Import before agent code. Own the descriptor so replacing or closing Python's
# sys.stdout cannot capture access/error records intended for the service log.
try:
    _STREAM = os.fdopen(
        os.dup(1), "w", encoding="utf-8", errors="backslashreplace", buffering=1,
    )
except OSError:
    _STREAM = None
_LOCK = threading.Lock()
# Protect the runtime from proxy/polling storms overwhelming the platform log
# pipe. Keep enough request visibility for diagnostics while bounding output.
_WINDOW_STARTED = 0.0
_WINDOW_COUNT = 0
_DROPPED_COUNT = 0
_MAX_PER_SECOND = max(20, int(os.environ.get("HERMES_WEBUI_MAX_LOGS_PER_SECOND", "100")))


def emit_request_log(message: str) -> None:
    """Emit bounded request logs so observability cannot destabilize the service."""
    global _WINDOW_STARTED, _WINDOW_COUNT, _DROPPED_COUNT
    try:
        if _STREAM is None:
            return
        import time
        now = time.monotonic()
        with _LOCK:
            if now - _WINDOW_STARTED >= 1.0:
                if _DROPPED_COUNT:
                    _STREAM.write(f"[webui] dropped {_DROPPED_COUNT} excess request logs\\n")
                _WINDOW_STARTED = now
                _WINDOW_COUNT = 0
                _DROPPED_COUNT = 0
            if _WINDOW_COUNT >= _MAX_PER_SECOND:
                _DROPPED_COUNT += 1
                return
            _WINDOW_COUNT += 1
            _STREAM.write(message + "\\n")
            _STREAM.flush()
    except Exception:
        pass
