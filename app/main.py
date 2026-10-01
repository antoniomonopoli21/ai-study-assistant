import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import router as auth_router
from app.routers.notes import router as notes_router
from app.routers import ask, search
from app.services.embeddings import (
    EmbeddingServiceError,
    embedding_service,
)
from app.services.reranker import (
    RerankerServiceError,
    reranker_service,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        embedding_service.load_model()
        logger.info(
            "Embedding model loaded successfully"
        )
    except EmbeddingServiceError:
        logger.exception(
            "Embedding model failed to load"
        )

    try:
        reranker_service.load_model()
        logger.info(
            "Reranker model loaded successfully"
        )
    except RerankerServiceError:
        logger.exception(
            "Reranker model failed to load"
        )

    yield


app = FastAPI(
    lifespan=lifespan
)

app.include_router(notes_router)
app.include_router(auth_router)
app.include_router(search.router)
app.include_router(ask.router)


@app.get("/")
def root():
    return {
        "message": "AI Study Assistant API is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/readiness")
def readiness_check(
    db: Session = Depends(get_db)
):
    components = {
        "database": "not_ready",
        "embedding_model": (
            "ready"
            if embedding_service.is_ready()
            else "not_ready"
        ),
        "reranker_model": (
            "ready"
            if reranker_service.is_ready()
            else "not_ready"
        ),
    }

    try:
        db.execute(
            text("SELECT 1")
        )

        components["database"] = "ready"

    except SQLAlchemyError:
        logger.exception(
            "Database readiness check failed"
        )

        db.rollback()

    all_ready = all(
        status == "ready"
        for status in components.values()
    )

    response = {
        "status": (
            "ready"
            if all_ready
            else "not_ready"
        ),
        "components": components,
    }

    if not all_ready:
        return JSONResponse(
            status_code=503,
            content=response,
        )

    return response