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