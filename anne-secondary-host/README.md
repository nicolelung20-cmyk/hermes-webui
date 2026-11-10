# ANNE Secondary Host

A small self-hosted standby API for ANNE. It is isolated from the existing Hermes WebUI runtime and does not modify existing services, data, credentials, or production configuration.

## Design and safeguards

- ANNE remains the single orchestrator; this is not an agent swarm.
- FastAPI provides authenticated status, task intake, and audit endpoints.
- SQLite stores queued task metadata and audit events.
- Optional MYLM and Hermes URLs are used only for health probes.
- Task intake is disabled by default. There is no shell execution, arbitrary tool execution, or autonomous worker.
- Docker publishes only to host loopback (127.0.0.1:8788). Use Tailscale Serve for private tailnet access; never enable Funnel.
- No paid API, cloud host, external database, or model provider is required.
- No secrets are committed. Configure a unique ANNE_HOST_TOKEN of at least 32 characters.

## Run

1. Copy .env.example to .env.
2. Set ANNE_HOST_TOKEN to a long random secret.
3. Keep ANNE_ALLOW_TASK_SUBMISSION=false.
4. Run docker compose up --build -d.
5. Check http://127.0.0.1:8788/health.

Authenticated API access fails closed when the token is missing or shorter than 32 characters.

## Endpoints

- GET /health: minimal liveness response.
- GET /v1/status: authenticated config and upstream reachability summary.
- POST /v1/tasks: optional authenticated task intake; stores pending metadata only.
- GET /v1/tasks: list queued task metadata.
- GET /v1/audit: recent audit events.

Queued tasks are inert records. They are never executed or forwarded by this host.

## Private access

After local verification, expose the service only to your tailnet using Tailscale Serve on the host. Do not use Funnel or a public reverse proxy. Keep the container port bound to loopback.

## Verification

Install requirements.txt and run pytest -q. The Mac Desktop Commander bridge was offline when this branch was created, so live MYLM/Hermes integration and failover remain pending.
