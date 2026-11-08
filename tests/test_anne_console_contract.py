from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "static" / "anne-console.html"
SCRIPT = ROOT / "static" / "anne-console.js"
POLICY = ROOT / "static" / "anne-policy.js"


def test_anne_console_uses_authenticated_hermes_endpoints():
    html = HTML.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    assert "/static/anne-policy.js" in html
    assert "/static/anne-console.js" in html
    assert 'credentials: "same-origin"' in script
    assert '"/api/auth/status"' in script
    assert '"/api/health/agent"' in script
    assert '"/api/providers"' in script
    assert '"/api/session/new"' in script


def test_model_session_uses_native_authenticated_hermes_routing():
    script = SCRIPT.read_text(encoding="utf-8")
    assert "model_provider: route.providerId" in script
    assert "worktree: false" in script
    assert "if (!route || route.eligible !== true) return;" in script
    assert "X-Hermes-CSRF-Token" in script


def test_console_exposes_all_four_operating_modes():
    html = HTML.read_text(encoding="utf-8")
    assert 'value="FAST"' in html
    assert 'value="REASON"' in html
    assert 'value="LOCAL"' in html
    assert 'value="AUTO"' in html


def test_browser_bundle_contains_no_provider_or_supabase_secrets():
    source = HTML.read_text(encoding="utf-8") + SCRIPT.read_text(encoding="utf-8") + POLICY.read_text(encoding="utf-8")
    assert "XAI_API_KEY" not in source
    assert "SUPABASE_SERVICE_ROLE_KEY" not in source
    assert "SUPABASE_SERVICE_KEY" not in source
    assert "localStorage" not in source
