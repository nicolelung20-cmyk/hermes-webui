from __future__ import annotations

import hmac
import ipaddress
import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

APP_NAME = "anne-secondary-host"
DB_PATH = os.getenv("ANNE_DB_PATH", "/data/anne-host.sqlite3")
TOKEN = os.getenv("ANNE_HOST_TOKEN", "")
ALLOW_TASK_SUBMISSION = os.getenv("ANNE_ALLOW_TASK_SUBMISSION", "false").lower() == "true"
MYLM_HEALTH_URL = os.getenv("MYLM_HEALTH_URL", "").strip()
HERMES_HEALTH_URL = os.getenv("HERMES_HEALTH_URL", "").strip()

app = FastAPI(title="ANNE Secondary Host", version="0.1.0", docs_url=None, redoc_url=None)


@contextmanager
def db() -> Any:
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=5)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at REAL NOT NULL,
                event TEXT NOT NULL,
                detail_json TEXT NOT NULL
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                title TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL
            )"""
        )
        connection.commit()
        yield connection
    finally:
        connection.close()


def audit(event: str, detail: dict[str, Any] | None = None) -> None:
    with db() as connection:
        connection.execute(
            "INSERT INTO audit_events(created_at, event, detail_json) VALUES (?, ?, ?)",
            (time.time(), event, json.dumps(detail or {}, separators=(",", ":"))),
        )
        connection.commit()


def require_auth(authorization: str | None = Header(default=None)) -> None:
    if len(TOKEN) < 32:
        raise HTTPException(status_code=503, detail="Host authentication is not configured")
    expected = "Bearer " + TOKEN
    if authorization is None or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")


class TaskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_reference: str | None = Field(default=None, max_length=120)


def private_url_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False
        host = parsed.hostname.lower()
        if host == "localhost" or host.endswith(".local") or host.endswith(".ts.net"):
            return True
        address = ipaddress.ip_address(host)
        return (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address in ipaddress.ip_network("100.64.0.0/10")
        )
    except ValueError:
        return False


def probe(url: str) -> str:
    if not url:
        return "not_configured"
    if not private_url_allowed(url):
        return "blocked_non_private_url"
    try:
        with urlopen(url, timeout=2) as response:
            return "reachable" if 200 <= response.status < 300 else "unhealthy"
    except (URLError, TimeoutError, OSError):
        return "unreachable"


@app.on_event("startup")
def initialize() -> None:
    with db():
        pass


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.get("/v1/status", dependencies=[Depends(require_auth)])
def status_summary() -> dict[str, Any]:
    return {
        "service": APP_NAME,
        "version": "0.1.0",
        "task_submission_enabled": ALLOW_TASK_SUBMISSION,
        "task_execution_enabled": False,
        "shell_execution_enabled": False,
        "mylm": probe(MYLM_HEALTH_URL),
        "hermes": probe(HERMES_HEALTH_URL),
        "database": "sqlite",
    }


@app.post("/v1/tasks", status_code=202, dependencies=[Depends(require_auth)])
def submit_task(task: TaskRequest) -> dict[str, str]:
    if not ALLOW_TASK_SUBMISSION:
        raise HTTPException(status_code=403, detail="Task intake is disabled by configuration")
    if not task.approval_reference:
        raise HTTPException(status_code=400, detail="An approval_reference is required")
    task_id = str(uuid.uuid4())
    with db() as connection:
        connection.execute(
            "INSERT INTO tasks(id, created_at, title, payload_json, status) VALUES (?, ?, ?, ?, ?)",
            (task_id, time.time(), task.title, json.dumps(task.payload), "pending"),
        )
        connection.commit()
    audit("task_queued", {"task_id": task_id, "approval_reference": task.approval_reference})
    return {"id": task_id, "status": "pending", "execution": "disabled"}


@app.get("/v1/tasks", dependencies=[Depends(require_auth)])
def list_tasks(limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    bounded_limit = max(1, min(limit, 100))
    with db() as connection:
        rows = connection.execute(
            "SELECT id, created_at, title, status FROM tasks ORDER BY created_at DESC LIMIT ?",
            (bounded_limit,),
        ).fetchall()
    return {"tasks": [dict(row) for row in rows]}


@app.get("/v1/audit", dependencies=[Depends(require_auth)])
def list_audit(limit: int = 50) -> dict[str, list[dict[str, Any]]]:
    bounded_limit = max(1, min(limit, 100))
    with db() as connection:
        rows = connection.execute(
            "SELECT id, created_at, event, detail_json FROM audit_events ORDER BY id DESC LIMIT ?",
            (bounded_limit,),
        ).fetchall()
    return {
        "events": [
            {
                "id": row["id"],
                "created_at": row["created_at"],
                "event": row["event"],
                "detail": json.loads(row["detail_json"]),
            }
            for row in rows
        ]
    }
