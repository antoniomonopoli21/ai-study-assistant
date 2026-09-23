import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings

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