from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "static" / "anne-console.html"
SCRIPT = ROOT / "static" / "anne-console.js"


def test_anne_console_uses_authenticated_hermes_endpoints():
    html = HTML.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    assert "/static/anne-console.js" in html
    assert 'credentials: "same-origin"' in script
    assert '"/api/auth/status"' in script
    assert '"/api/health/agent"' in script
    assert '"/api/providers"' in script
    assert '"/api/session/new"' in script


def test_grok_route_is_native_session_scoped_and_fail_closed():
    script = SCRIPT.read_text(encoding="utf-8")
    assert 'providerId !== "x-ai" && providerId !== "xai-oauth"' in script
    assert 'model_provider: route.provider' in script
    assert 'worktree: false' in script
    assert "if (!route || !route.hasKey) return;" in script
    assert 'X-Hermes-CSRF-Token' in script


def test_browser_bundle_contains_no_provider_or_supabase_secrets():
    source = HTML.read_text(encoding="utf-8") + SCRIPT.read_text(encoding="utf-8")
    assert "XAI_API_KEY" not in source
    assert "SUPABASE_SERVICE_ROLE_KEY" not in source
    assert "SUPABASE_SERVICE_KEY" not in source
