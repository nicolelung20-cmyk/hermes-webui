FROM nousresearch/hermes-agent:latest
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/hermes/.venv/bin:/opt/hermes-agent/.venv/bin:$PATH"
ENV API_SERVER_ENABLED=true
ENV API_SERVER_HOST=0.0.0.0
ENV HERMES_DASHBOARD=0
ENV HERMES_WEBUI_HOST=0.0.0.0
CMD ["sh","-lc","export API_SERVER_PORT="${PORT:-8642}"; export HERMES_WEBUI_PORT="${PORT:-8787}"; exec /opt/hermes/.venv/bin/hermes gateway run"]
