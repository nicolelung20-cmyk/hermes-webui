"""Tests for the opt-in xAI Grok Responses API adapter."""
import json
from unittest.mock import Mock

import pytest

from api import xai_grok


def test_disabled_by_default_does_not_make_request(monkeypatch):
    monkeypatch.delenv("ANNE_XAI_ENABLED", raising=False)
    monkeypatch.setenv("XAI_API_KEY", "test-secret")
    urlopen = Mock(side_effect=AssertionError("network must not be called"))
    monkeypatch.setattr(xai_grok.urllib.request, "urlopen", urlopen)

    with pytest.raises(xai_grok.XAIAdapterError, match="disabled"):
        xai_grok.create_response("hello")

    urlopen.assert_not_called()


def test_missing_key_does_not_make_request(monkeypatch):
    monkeypatch.setenv("ANNE_XAI_ENABLED", "1")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    urlopen = Mock(side_effect=AssertionError("network must not be called"))
    monkeypatch.setattr(xai_grok.urllib.request, "urlopen", urlopen)

    with pytest.raises(xai_grok.XAIAdapterError, match="not configured"):
        xai_grok.create_response("hello")

    urlopen.assert_not_called()


def test_sends_responses_request_with_server_side_key(monkeypatch):
    monkeypatch.setenv("ANNE_XAI_ENABLED", "true")
    monkeypatch.setenv("XAI_API_KEY", "test-secret")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"id":"resp_test","output":[]}'

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["auth"] = request.get_header("Authorization")
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(xai_grok.urllib.request, "urlopen", fake_urlopen)

    result = xai_grok.create_response("hello", timeout=45)

    assert result["id"] == "resp_test"
    assert captured["url"] == "https://api.x.ai/v1/responses"
    assert captured["auth"] == "Bearer test-secret"
    assert captured["payload"] == {
        "model": "grok-4.7",
        "input": "hello",
        "store": False,
    }
    assert captured["timeout"] == 45


def test_http_error_is_sanitized(monkeypatch):
    import urllib.error

    monkeypatch.setenv("ANNE_XAI_ENABLED", "1")
    monkeypatch.setenv("XAI_API_KEY", "do-not-leak-this")
    monkeypatch.setattr(
        xai_grok.urllib.request,
        "urlopen",
        Mock(side_effect=urllib.error.HTTPError(
            "https://api.x.ai/v1/responses", 401, "unauthorized", {}, None
        )),
    )

    with pytest.raises(xai_grok.XAIAdapterError) as error:
        xai_grok.create_response("hello")

    assert "do-not-leak-this" not in str(error.value)
    assert "401" in str(error.value)


def test_invalid_timeout_rejected_before_network(monkeypatch):
    monkeypatch.setenv("ANNE_XAI_ENABLED", "1")
    monkeypatch.setenv("XAI_API_KEY", "test-secret")
    urlopen = Mock(side_effect=AssertionError("network must not be called"))
    monkeypatch.setattr(xai_grok.urllib.request, "urlopen", urlopen)

    with pytest.raises(ValueError):
        xai_grok.create_response("hello", timeout=0)

    urlopen.assert_not_called()
