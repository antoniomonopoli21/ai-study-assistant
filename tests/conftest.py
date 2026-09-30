import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import make_url

from app.main import app
from app.database import Base, get_db
from app.config import settings

import hashlib
import math
import re

from app.services.embeddings import embedding_service
from app.services.reranker import reranker_service

test_engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit = False
)

def override_get_db():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def ensure_safe_test_database():
    test_url = make_url(settings.test_database_url)
    dev_url = make_url(settings.database_url)

    if test_url == dev_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must not point to the development database"
        )

    if test_url.database is None or "test" not in test_url.database.lower():
        raise RuntimeError(
            "Refusing to run tests: database name must clearly be a test database"
        )


ensure_safe_test_database()


@pytest.fixture(autouse=True)
def fake_embedding_model(monkeypatch):
    dimension = 384

    def make_embedding(text: str) -> list[float]:
        vector = [0.0] * dimension

        words = re.findall(
            r"\w+",
            text.lower()
        )

        for word in words:
            digest = hashlib.sha256(
                word.encode()
            ).digest()

            index = int.from_bytes(
                digest[:4],
                "big"
            ) % dimension

            vector[index] += 1.0

        norm = math.sqrt(
            sum(value * value for value in vector)
        )

        if norm == 0:
            return vector

        return [
            value / norm
            for value in vector
        ]

    def fake_embed_query(text: str) -> list[float]:
        return make_embedding(text)


    def fake_embed_passages(
        texts: list[str]
    ) -> list[list[float]]:
        return [
            make_embedding(text)
            for text in texts
        ]

    monkeypatch.setattr(
        embedding_service,
        "embed_query",
        fake_embed_query
    )



    monkeypatch.setattr(
        embedding_service,
        "embed_passages",
        fake_embed_passages
    )


@pytest.fixture(autouse=True)
def fake_reranker_model(monkeypatch):
    def fake_rerank(
        query,
        candidates,
    ):
        return [
            (
                chunk,
                distance,
                10.0,
            )
            for chunk, distance in candidates
        ]

    monkeypatch.setattr(
        reranker_service,
        "rerank",
        fake_rerank,
    )