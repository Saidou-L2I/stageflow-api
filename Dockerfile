# --- Etape de build : installation des dependances ---
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Etape finale : image d'execution minimale ---
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 stageflow \
    && useradd --uid 1000 --gid stageflow --shell /bin/bash --create-home stageflow

WORKDIR /app

COPY --from=builder /root/.local /home/stageflow/.local
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

RUN chown -R stageflow:stageflow /app

ENV PATH=/home/stageflow/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER stageflow

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
