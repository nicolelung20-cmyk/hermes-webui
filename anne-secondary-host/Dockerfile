FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY host.py .
RUN useradd --create-home --uid 10001 anne && mkdir -p /data && chown -R anne:anne /app /data
USER 10001:10001
EXPOSE 8788
CMD ["uvicorn", "host:app", "--host", "0.0.0.0", "--port", "8788"]
