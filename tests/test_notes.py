def test_create_note(client):
    response = client.post(
        "/notes",
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



def test_get_notes(client):
    client.post(
        "/notes/",
        json={
            "subject": "Analysis 1",
            "title": "Physics",
            "content": "Study waves",
            "priority": 1
        }
    )

    response = client.get("/notes/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["title"] == "Physics"


def test_get_note_not_found(client):
    response = client.get("/notes/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Note not found"
    }


def test_update_note(client):
    create_response = client.post(
        "/notes/",
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


def test_delete_note(client):
    create_response = client.post(
        "/notes/",
        json={
            "subject": "Analysis 1",
            "title": "Delete me",
            "content": "Temporary note",
            "priority": 1
        }
    )

    note_id = create_response.json()["id"]

    delete_response = client.delete(f"/notes/{note_id}")

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "message": "Note deleted successfully"
    }

    get_response = client.get(f"/notes/{note_id}")

    assert get_response.status_code == 404


def test_create_note_with_invalid_priority(client):
    response = client.post(
            "/notes/",
        json={
            "subject": "Analysis 1",
            "title": "Physics",
            "content": "Study waves",
            "priority": 10
        }
    )

    assert response.status_code == 422

def test_create_note_with_empty_title(client):
    response = client.post(
        "/notes/",
        json={
            "subject": "Analysis 1",
            "title": "",
            "content": "Study waves",
            "priority": 2
        }
    )

    assert response.status_code == 422

def test_create_note_with_blank_title(client):
    response = client.post(
        "/notes/",
        json={
            "subject": "Analysis 1",
            "title": "     ",
            "content": "Study waves",
            "priority": 2
        }
    )

    assert response.status_code == 422


def test_create_note_with_blank_subject(client):
    response = client.post(
        "/notes/",
        json={
            "subject": "     ",
            "title": "Improper integrals",
            "content": "Study convergence criteria",
            "priority": 2
        }
    )

    assert response.status_code == 422