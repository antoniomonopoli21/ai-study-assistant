def test_create_note(client, auth_headers):
    response = client.post(
        "/notes",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Analysis 1",
            "content" : "Study improper integrals",
            "priority": 2
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "Analysis 1"
    assert data["content"] == "Study improper integrals"
    assert data["priority"] == 2
    assert "id" in data
    assert "created_at" in data



def test_get_notes(client, auth_headers):
    client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Physics",
            "content": "Study waves",
            "priority": 1
        }
    )

    response = client.get("/notes/", headers = auth_headers,)

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Physics"


def test_get_note_not_found(client, auth_headers):
    response = client.get("/notes/999", headers = auth_headers,)

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found"
    }


def test_update_note(client, auth_headers):
    create_response = client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Old title",
            "content": "Old content",
            "priority": 1
        }
    )

    note_id = create_response.json()["id"]

    response = client.put(
        f"/notes/{note_id}",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "New title",
            "content": "New content",
            "priority": 3
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == note_id
    assert data["title"] == "New title"
    assert data["content"] == "New content"
    assert data["priority"] == 3


def test_delete_note(client, auth_headers):
    create_response = client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Delete me",
            "content": "Temporary note",
            "priority": 1
        }
    )

    note_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/notes/{note_id}",
        headers=auth_headers)

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Note deleted successfully"
    }

    get_response = client.get(
        f"/notes/{note_id}",
        headers = auth_headers
    )

    assert get_response.status_code == 404
    
    


def test_create_note_with_invalid_priority(client, auth_headers):
    response = client.post(
            "/notes/",
            headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Physics",
            "content": "Study waves",
            "priority": 10
        }
    )

    assert response.status_code == 422

def test_create_note_with_empty_title(client, auth_headers):
    response = client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "",
            "content": "Study waves",
            "priority": 2
        }
    )

    assert response.status_code == 422

def test_create_note_with_blank_title(client, auth_headers):
    response = client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "     ",
            "content": "Study waves",
            "priority": 2
        }
    )

    assert response.status_code == 422


def test_create_note_with_blank_subject(client, auth_headers):
    response = client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "     ",
            "title": "Improper integrals",
            "content": "Study convergence criteria",
            "priority": 2
        }
    )

    assert response.status_code == 422



def test_filter_notes_by_subject(client, auth_headers):
    client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Analysis 1",
            "title": "Improper integrals",
            "content": "Study convergence criteria",
            "priority": 2
        }
    )

    client.post(
        "/notes/",
        headers = auth_headers,
        json={
            "subject": "Physics",
            "title": "Electromagnetic waves",
            "content": "Review Maxwell equations",
            "priority": 3
        }
    )

    response = client.get(
        "/notes/",
        headers = auth_headers,
        params={"subject": "Analysis 1"}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["subject"] == "Analysis 1"



def test_user_cannot_access_another_users_note(client):
    # User 1
    client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    login1 = client.post(
        "/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    token1 = login1.json()["access_token"]

    create_response = client.post(
        "/notes/",
        headers={
            "Authorization": f"Bearer {token1}"
        },
        json={
            "subject": "Analysis 1",
            "title": "Integrals",
            "content": "Private note",
            "priority": 2
        }
    )

    note_id = create_response.json()["id"]

    # User 2
    client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    login2 = client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    token2 = login2.json()["access_token"]

    response = client.get(
        f"/notes/{note_id}",
        headers={
            "Authorization": f"Bearer {token2}"
        }
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_note(client):
    # User 1
    client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    login1 = client.post(
        "/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    token1 = login1.json()["access_token"]

    create_response = client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "subject": "Analysis 1",
            "title": "Private note",
            "content": "User 1 content",
            "priority": 2
        }
    )

    note_id = create_response.json()["id"]

    # User 2
    client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    login2 = client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    token2 = login2.json()["access_token"]

    response = client.put(
        f"/notes/{note_id}",
        headers={"Authorization": f"Bearer {token2}"},
        json={
            "subject": "Physics",
            "title": "Hacked",
            "content": "Modified by user 2",
            "priority": 5
        }
    )

    assert response.status_code == 404
    owner_response = client.get(
        f"/notes/{note_id}",
        headers={"Authorization": f"Bearer {token1}"}
)

    assert owner_response.status_code == 200

    data = owner_response.json()

    assert data["title"] == "Private note"
    assert data["content"] == "User 1 content"
    assert data["subject"] == "Analysis 1"
    assert data["priority"] == 2


def test_user_cannot_delete_another_users_note(client):
    # User 1
    client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    login1 = client.post(
        "/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    token1 = login1.json()["access_token"]

    create_response = client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "subject": "Analysis 1",
            "title": "Private note",
            "content": "User 1 content",
            "priority": 2
        }
    )

    note_id = create_response.json()["id"]

    # User 2
    client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    login2 = client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    token2 = login2.json()["access_token"]

    response = client.delete(
        f"/notes/{note_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 404

    owner_response = client.get(
        f"/notes/{note_id}",
    headers={"Authorization": f"Bearer {token1}"}
)

    assert owner_response.status_code == 200


def test_user_cannot_see_another_users_notes_in_collection(client):
    # User 1
    client.post(
        "/auth/register",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    login1 = client.post(
        "/auth/login",
        json={
            "email": "user1@example.com",
            "password": "password123"
        }
    )

    token1 = login1.json()["access_token"]

    client.post(
        "/notes/",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "subject": "Analysis 1",
            "title": "User 1 private note",
            "content": "Secret",
            "priority": 2
        }
    )

    # User 2
    client.post(
        "/auth/register",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    login2 = client.post(
        "/auth/login",
        json={
            "email": "user2@example.com",
            "password": "password123"
        }
    )

    token2 = login2.json()["access_token"]

    response = client.get(
        "/notes/",
        headers={"Authorization": f"Bearer {token2}"}
    )

    assert response.status_code == 200
    assert response.json() == []