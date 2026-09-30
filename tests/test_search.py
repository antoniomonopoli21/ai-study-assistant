from app.routers import search as search_router
from app.services.embeddings import EmbeddingServiceError


def test_search_requires_authentication(client):
    response = client.get(
        "/search/",
        params={
            "q": "integral"
        }
    )

    assert response.status_code == 401


def test_semantic_search(client, auth_headers):
    client.post(
        "/notes/",
        headers=auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Improper integrals",
            "content": (
                "An improper integral converges when the limit "
                "that defines the integral exists and is finite."
            ),
            "priority": 3
        }
    )

    client.post(
        "/notes/",
        headers=auth_headers,
        json={
            "subject": "Physics",
            "title": "Newton",
            "content": (
                "Newton's second law states that force equals "
                "mass multiplied by acceleration."
            ),
            "priority": 2
        }
    )

    response = client.get(
        "/search/",
        headers=auth_headers,
        params={
            "q": "When does an improper integral converge?",
            "limit": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert "integral" in data[0]["content"].lower()


def test_search_does_not_return_another_users_notes(client):
    # User A
    client.post(
        "/auth/register",
        json={
            "email": "usera@example.com",
            "password": "password123"
        }
    )

    login_a = client.post(
        "/auth/login",
        json={
            "email": "usera@example.com",
            "password": "password123"
        }
    )

    token_a = login_a.json()["access_token"]

    client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "subject": "Private",
            "title": "Secret",
            "content": "ZEBRA_SECRET unique confidential content",
            "priority": 1
        }
    )

    # User B
    client.post(
        "/auth/register",
        json={
            "email": "userb@example.com",
            "password": "password123"
        }
    )

    login_b = client.post(
        "/auth/login",
        json={
            "email": "userb@example.com",
            "password": "password123"
        }
    )

    token_b = login_b.json()["access_token"]

    response = client.get(
        "/search/",
        headers={"Authorization": f"Bearer {token_b}"},
        params={
            "q": "ZEBRA_SECRET",
            "limit": 3
        }
    )

    assert response.status_code == 200

    assert all(
        "ZEBRA_SECRET" not in result["content"]
        for result in response.json()
    )


def test_search_returns_503_when_embedding_fails(
    client,
    auth_headers,
    monkeypatch
):
    def fake_search_similar_chunks(
        db,
        user_id,
        query,
        limit
    ):
        raise EmbeddingServiceError(
            "simulated embedding failure"
        )

    monkeypatch.setattr(
        search_router,
        "search_similar_chunks",
        fake_search_similar_chunks
    )

    response = client.get(
        "/search/",
        headers=auth_headers,
        params={
            "q": "improper integral",
            "limit": 3
        }
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "Embedding service temporarily unavailable"
    }