FROM nousresearch/hermes-agent:latest
ENV PYTHONUNBUFFERED=1
ENV API_SERVER_ENABLED=true
ENV API_SERVER_HOST=0.0.0.0
ENV HERMES_DASHBOARD=0
CMD ["sh","-lc","export API_SERVER_PORT=\"${PORT:-8642}\"; exec python -m hermes_cli.main gateway run"]
