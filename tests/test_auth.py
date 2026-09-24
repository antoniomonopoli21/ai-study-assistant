import jwt
from app.config import settings



def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data

def test_login_user(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_get_current_user(client):
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

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        }
    )

    assert response.status_code == 401


def test_token_without_exp_is_rejected(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    token = jwt.encode(
        {"sub": "1"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 401



def test_token_without_sub_is_rejected(client):
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    token = jwt.encode(
        {
            "exp": 4102444800
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 401


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123"
        }
    )

    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "abc"
        }
    )

    assert response.status_code == 422


def test_email_is_normalized(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "  User@Example.COM  ",
            "password": "password123"
        }
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"


def test_login_with_normalized_email(client):
    client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123"
        }
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "  USER@EXAMPLE.COM ",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_duplicate_email(client):
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }

    first_response = client.post(
        "/auth/register",
        json=user_data
    )

    second_response = client.post(
        "/auth/register",
        json=user_data
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Email already registered"
    }

def test_register_duplicate_email_is_case_insensitive(client):
    first_response = client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123"
        }
    )

    second_response = client.post(
        "/auth/register",
        json={
            "email": "USER@EXAMPLE.COM",
            "password": "password123"
        }
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

