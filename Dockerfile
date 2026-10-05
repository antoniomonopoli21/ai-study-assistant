FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN groupadd \
        --system \
        --gid 10001 \
        appuser \
    && useradd \
        --system \
        --uid 10001 \
        --gid appuser \
        --create-home \
        --home-dir /home/appuser \
        appuser


FROM base AS migrate

COPY requirements-migrate.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements-migrate.txt

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .
COPY --chown=appuser:appuser model_manifest.json ./model_manifest.json

USER appuser

CMD ["alembic", "upgrade", "head"]


FROM base AS api

ENV HF_HOME=/home/appuser/.cache/huggingface

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        torch==2.14.0 \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt

RUN mkdir -p /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser /home/appuser

COPY --chown=appuser:appuser model_manifest.json ./model_manifest.json

USER appuser

RUN python -c "\
import json; \
from pathlib import Path; \
from huggingface_hub import snapshot_download; \
manifest = json.loads( \
    Path('/app/model_manifest.json').read_text() \
); \
ignored_files = [ \
    'onnx/*', \
    'openvino/*', \
    'pytorch_model.bin', \
]; \
snapshot_download( \
    repo_id=manifest['embedding']['model'], \
    revision=manifest['embedding']['revision'], \
    ignore_patterns=ignored_files \
); \
snapshot_download( \
    repo_id=manifest['reranker']['model'], \
    revision=manifest['reranker']['revision'], \
    ignore_patterns=ignored_files \
)"

ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY --chown=appuser:appuser app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]