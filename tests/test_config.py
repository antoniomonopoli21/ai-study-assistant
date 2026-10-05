import pytest

from pydantic import ValidationError

from app.config import Settings


def make_settings(
    jwt_secret_key: str,
    jwt_algorithm: str = "HS256",
):
    return Settings(
        database_url=(
            "postgresql+psycopg://localhost/test"
        ),
        test_database_url=None,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=30,
        openai_api_key="test-openai-key",
    )


def test_rejects_short_jwt_secret():
    with pytest.raises(ValidationError):
        make_settings(
            jwt_secret_key="too-short"
        )


def test_accepts_strong_jwt_secret():
    settings = make_settings(
        jwt_secret_key="a" * 32
    )

    assert len(
        settings.jwt_secret_key
    ) == 32


def test_rejects_unsupported_jwt_algorithm():
    with pytest.raises(ValidationError):
        make_settings(
            jwt_secret_key="a" * 32,
            jwt_algorithm="HS512",
        )


def test_validation_error_hides_invalid_jwt_secret():
    invalid_secret = "do-not-log-me"

    with pytest.raises(ValidationError) as exc_info:
        make_settings(
            jwt_secret_key=invalid_secret
        )

    error_message = str(
        exc_info.value
    )

    assert invalid_secret not in error_message