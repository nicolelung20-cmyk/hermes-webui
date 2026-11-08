"""Behavioral tests for ANNE's zero-spend model eligibility policy."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_policy(payload, mode="LOCAL"):
    script = r"""
const policy = require(process.argv[1]);
const input = JSON.parse(process.argv[2]);
const routes = policy.buildRoutes(input.providers);
const selected = policy.selectRoute(routes, input.mode, input.activeProvider);
process.stdout.write(JSON.stringify({
  routes: routes.map(({providerId, modelId, eligible, reason}) => ({providerId, modelId, eligible, reason})),
  selected: selected && {providerId: selected.providerId, modelId: selected.modelId}
}));
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "static" / "anne-policy.js"),
         json.dumps({"providers": payload, "mode": mode, "activeProvider": None})],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def test_local_private_self_hosted_models_are_zero_spend_eligible():
    result = run_policy([{
        "id": "ollama", "display_name": "Ollama", "is_self_hosted": True,
        "base_url": "http://127.0.0.1:11434",
        "models": [{"id": "qwen3:4b", "label": "Qwen 3 4B"}],
    }])
    assert result["routes"][0]["eligible"] is True
    assert result["selected"] == {"providerId": "ollama", "modelId": "qwen3:4b"}


def test_self_hosted_provider_on_public_host_is_blocked():
    result = run_policy([{
        "id": "custom-cloud", "display_name": "Custom", "is_self_hosted": True,
        "base_url": "https://models.example.com/v1",
        "models": [{"id": "model-a", "label": "Model A"}],
    }])
    assert result["routes"][0]["eligible"] is False
    assert result["selected"] is None


def test_hosted_provider_with_free_sounding_model_name_is_blocked():
    result = run_policy([{
        "id": "openrouter", "display_name": "OpenRouter", "is_self_hosted": False,
        "base_url": "https://openrouter.ai/api/v1",
        "models": [{"id": "free-model", "label": "Free model"}],
    }])
    assert result["routes"][0]["eligible"] is False
    assert result["selected"] is None


def test_auto_prefers_active_provider_only_when_it_is_verified_local():
    providers = [
        {"id": "ollama", "display_name": "Ollama", "is_self_hosted": True,
         "base_url": "http://localhost:11434",
         "models": [{"id": "qwen3:4b", "label": "Qwen 3 4B"}]},
        {"id": "lmstudio", "display_name": "LM Studio", "is_self_hosted": True,
         "base_url": "http://192.168.1.20:1234/v1",
         "models": [{"id": "local-fast", "label": "Local Fast"}]},
    ]
    script = r"""
const p = require(process.argv[1]);
const providers = JSON.parse(process.argv[2]);
const routes = p.buildRoutes(providers);
const selected = p.selectRoute(routes, "AUTO", "lmstudio");
process.stdout.write(JSON.stringify(selected && {providerId:selected.providerId,modelId:selected.modelId}));
"""
    result = subprocess.run(
        ["node", "-e", script, str(ROOT / "static" / "anne-policy.js"), json.dumps(providers)],
        check=True, capture_output=True, text=True,
    )
    assert json.loads(result.stdout) == {"providerId": "lmstudio", "modelId": "local-fast"}


def test_auto_fails_closed_when_no_cost_verified_route_exists():
    result = run_policy([{
        "id": "anthropic", "display_name": "Anthropic", "is_self_hosted": False,
        "base_url": "https://api.anthropic.com",
        "models": [{"id": "claude", "label": "Claude"}],
    }], mode="AUTO")
    assert result["selected"] is None
