from app.routers.ask import llm_service

from app.routers import ask as ask_router

def test_ask_returns_answer_and_sources(
    client,
    auth_headers,
    monkeypatch
):
    monkeypatch.setattr(
    ask_router.settings,
    "rag_max_distance",
    2.0
)
    client.post(
        "/notes/",
        headers=auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Improper integrals",
            "content": (
                "An improper integral converges when the limit "
                "that defines it exists and is finite."
            ),
            "priority": 3
        }
    )

    captured = {}

    def fake_generate(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Mocked RAG answer"

    monkeypatch.setattr(
        llm_service,
        "generate",
        fake_generate
    )

    response = client.post(
        "/ask/",
        headers=auth_headers,
        json={
            "question": "When does an improper integral converge?",
            "limit": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "Mocked RAG answer"
    assert len(data["sources"]) >= 1

    assert "integral" in data["sources"][0]["content"].lower()

    assert "improper integral" in captured["prompt"].lower()
    assert "When does an improper integral converge?" in captured["prompt"]


def test_ask_requires_authentication(client):
    response = client.post(
        "/ask/",
        json={
            "question": "When does an improper integral converge?",
            "limit": 3
        }
    )

    assert response.status_code == 401






def test_ask_does_not_use_another_users_notes(
    client,
    monkeypatch
):
    monkeypatch.setattr(
        ask_router.settings,
        "rag_max_distance",
        2.0
    )
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

    secret_content = (
        "ZEBRA_SECRET theorem says the special value is 12345."
    )

    client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "subject": "Private",
            "title": "Secret note",
            "content": secret_content,
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

    client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "subject": "Public",
            "title": "User B note",
            "content": (
                "A theorem is a mathematical statement "
                "that can be proved from assumptions."
            ),
            "priority": 1
        }
    )


    captured = {}

    def fake_generate(prompt: str) -> str:
        captured["prompt"] = prompt
        return "Mocked answer"

    monkeypatch.setattr(
        llm_service,
        "generate",
        fake_generate
    )

    response = client.post(
        "/ask/",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "question": "What is the ZEBRA_SECRET theorem?",
            "limit": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        "ZEBRA_SECRET" not in source["content"]
        for source in data["sources"]
    )

    context = (
        captured["prompt"]
        .split("Context:", 1)[1]
        .split("Question:", 1)[0]
    )

    assert "ZEBRA_SECRET" not in context
    assert "12345" not in context
    assert "mathematical statement" in context





def test_ask_does_not_call_llm_without_relevant_context(
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
        return []

    def fail_if_called(prompt: str):
        raise AssertionError(
            "LLM should not be called without relevant context"
        )

    monkeypatch.setattr(
        ask_router,
        "search_similar_chunks",
        fake_search_similar_chunks
    )

    monkeypatch.setattr(
        ask_router.llm_service,
        "generate",
        fail_if_called
    )

    response = client.post(
        "/ask/",
        headers=auth_headers,
        json={
            "question": "How does photosynthesis work?",
            "limit": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["sources"] == []
    assert data["answer"] == (
        "I don't have enough information in your notes "
        "to answer that question."
    )