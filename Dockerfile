FROM python:3.11-slim

# Non-root user for production
RUN groupadd -r app && useradd -r -g app app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-nlp.txt ./
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org  --no-cache-dir -r requirements.txt && \
    pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org  --no-cache-dir -r requirements-nlp.txt

COPY . .
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org-e . && chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Healthcheck: liveness only (no DB)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -sf http://localhost:8000/live || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
