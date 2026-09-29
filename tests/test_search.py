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