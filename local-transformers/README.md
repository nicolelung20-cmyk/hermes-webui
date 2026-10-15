# Optional local Transformers runtime

This is an isolated, opt-in inference service. It does **not** alter the Hermes WebUI
or its existing provider configuration. It exposes a small OpenAI-compatible subset
for chat completions so a compatible Hermes provider can target a local model.

## Security and compatibility

- Binds to `127.0.0.1` by default; do not expose it to a LAN or the public internet.
- Requires a bearer token for API routes. Generate one locally; never commit it.
- `/health` is intentionally unauthenticated and returns only status/model metadata.
- `trust_remote_code=False`; use only models whose architecture is supported natively.
- Supports text-only `/v1/chat/completions`, non-streaming responses, and `/v1/models`.
  It is not a complete OpenAI API implementation (no tools/function calling, streaming,
  multimodal inputs, or usage accounting).
- Model weights are downloaded from Hugging Face on first run unless already cached.
  Inference can run locally after the model is available; model license and hardware
  requirements still apply. No promise of unlimited speed or unlimited context.
- No database writes, Supabase access, trading, or money movement are included.

## Run on a Mac

Use a dedicated virtual environment. PyTorch/MPS support and available model sizes vary
by macOS, Python version, and hardware.

```bash
cd local-transformers
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
export TRANSFORMERS_API_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export TRANSFORMERS_MODEL="Qwen/Qwen2.5-1.5B-Instruct"
uvicorn server:app --host 127.0.0.1 --port 8788
```

Keep the generated token in the same shell or a private secret manager. Do not paste it
into GitHub, chat logs, browser JavaScript, or a public config file.

## Smoke test (second terminal)

Set `TRANSFORMERS_API_KEY` to the same value in the client shell:

```bash
curl -fsS http://127.0.0.1:8788/health
curl -fsS http://127.0.0.1:8788/v1/models \
  -H "Authorization: Bearer $TRANSFORMERS_API_KEY"
curl -fsS http://127.0.0.1:8788/v1/chat/completions \
  -H "Authorization: Bearer $TRANSFORMERS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Reply with exactly: LOCAL_OK"}],"max_tokens":24,"temperature":0}'
```

Expected: health reports `ok`, the model list includes the configured model, and chat
returns a completion. The first model load can take time and use substantial disk/RAM.

## Connect Hermes

In the Hermes provider/model settings, select an OpenAI-compatible/custom endpoint and
configure base URL `http://127.0.0.1:8788/v1`, API key as the locally generated
`TRANSFORMERS_API_KEY`, and model ID exactly as `TRANSFORMERS_MODEL`. Use Hermes' own
documented provider configuration path; do not put secrets in the web UI's static files.
If Hermes and the runtime run on different machines or in separate containers,
`127.0.0.1` refers to each process's own network namespace, so configure a private
authenticated network path only after reviewing firewall and access controls.

## Integration gates

1. Install and run the smoke tests on the target Mac.
2. Verify Hermes accepts this endpoint and its request/response subset.
3. Measure first-token latency, sustained throughput, memory pressure, and context length.
4. Keep the current provider as a fallback until local results pass real tasks.
5. Do not change Supabase policies, production deployment, or any live trading setting
   as part of this optional runtime.
