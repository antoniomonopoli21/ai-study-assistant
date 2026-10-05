import pytest

from fastapi.testclient import TestClient

from app.main import app


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_returns_ready(
    client
):
    response = client.get(
        "/readiness"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ready",
        "components": {
            "database": "ready",
            "embedding_model": "ready",
            "reranker_model": "ready",
        },
    }

def test_readiness_returns_503_when_model_is_not_ready(
    client,
    monkeypatch,
):
    from app.main import embedding_service

    monkeypatch.setattr(
        embedding_service,
        "is_ready",
        lambda: False,
    )

    response = client.get(
        "/readiness"
    )

    assert response.status_code == 503

    data = response.json()

    assert data["status"] == "not_ready"

    assert (
        data["components"]["embedding_model"]
        == "not_ready"
    )

    assert (
        data["components"]["database"]
        == "ready"
    )

def test_startup_fails_when_embedding_model_cannot_load(
    monkeypatch,
):
    from app.main import embedding_service

    def fail_load_model():
        raise RuntimeError(
            "synthetic embedding startup failure"
        )

    monkeypatch.setattr(
        embedding_service,
        "load_model",
        fail_load_model,
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic embedding startup failure",
    ):
        with TestClient(app):
            pass


def test_startup_fails_when_reranker_model_cannot_load(
    monkeypatch,
):
    from app.main import reranker_service

    def fail_load_model():
        raise RuntimeError(
            "synthetic reranker startup failure"
        )

    monkeypatch.setattr(
        reranker_service,
        "load_model",
        fail_load_model,
    )

    with pytest.raises(
        RuntimeError,
        match="synthetic reranker startup failure",
    ):
        with TestClient(app):
            pass