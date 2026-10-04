FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/home/appuser/.cache/huggingface

ARG EMBEDDING_MODEL=intfloat/multilingual-e5-small
ARG EMBEDDING_MODEL_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3
ARG RERANKER_MODEL=cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
ARG RERANKER_MODEL_REVISION=1427fd652930e4ba29e8149678df786c240d8825

ENV EMBEDDING_MODEL=${EMBEDDING_MODEL}
ENV EMBEDDING_MODEL_REVISION=${EMBEDDING_MODEL_REVISION}
ENV RERANKER_MODEL=${RERANKER_MODEL}
ENV RERANKER_MODEL_REVISION=${RERANKER_MODEL_REVISION}

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install \
        torch==2.14.0 \
        --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install -r requirements.txt

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
        appuser \
    && mkdir -p /home/appuser/.cache/huggingface \
    && chown -R appuser:appuser /home/appuser

USER appuser

RUN python -c "\
from huggingface_hub import snapshot_download; \
import os; \
snapshot_download( \
    repo_id=os.environ['EMBEDDING_MODEL'], \
    revision=os.environ['EMBEDDING_MODEL_REVISION'] \
); \
snapshot_download( \
    repo_id=os.environ['RERANKER_MODEL'], \
    revision=os.environ['RERANKER_MODEL_REVISION'] \
)"

ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]