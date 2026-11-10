import importlib


def make_client(monkeypatch, tmp_path):
    monkeypatch.setenv("ANNE_HOST_TOKEN", "t" * 48)
    monkeypatch.setenv("ANNE_DB_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("ANNE_ALLOW_TASK_SUBMISSION", "false")
    import host
    importlib.reload(host)
    from fastapi.testclient import TestClient
    return TestClient(host.app), host


def test_health_is_minimal(monkeypatch, tmp_path):
    client, _ = make_client(monkeypatch, tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "token" not in response.text.lower()


def test_status_requires_auth(monkeypatch, tmp_path):
    client, _ = make_client(monkeypatch, tmp_path)
    assert client.get("/v1/status").status_code == 401
    response = client.get(
        "/v1/status",
        headers={"Authorization": "Bearer " + "t" * 48},
    )
    assert response.status_code == 200
    assert response.json()["task_execution_enabled"] is False


def test_task_intake_disabled_by_default(monkeypatch, tmp_path):
    client, _ = make_client(monkeypatch, tmp_path)
    response = client.post(
        "/v1/tasks",
        headers={"Authorization": "Bearer " + "t" * 48},
        json={"title": "safe test", "approval_reference": "TEST-APPROVAL"},
    )
    assert response.status_code == 403


def test_external_upstream_probe_is_blocked(monkeypatch, tmp_path):
    _, host = make_client(monkeypatch, tmp_path)
    assert host.probe("https://example.com/health") == "blocked_non_private_url"
