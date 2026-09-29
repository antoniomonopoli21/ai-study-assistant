from app.routers.ask import llm_service


def test_ask_returns_answer_and_sources(
    client,
    auth_headers,
    monkeypatch
):
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