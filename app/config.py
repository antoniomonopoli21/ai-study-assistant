from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.model_manifest import model_manifest

class Settings(BaseSettings):
    database_url: str

    test_database_url: str | None = Field(
        default=None,
        min_length=1,
    )

    jwt_secret_key: str

    jwt_algorithm: Literal["HS256"] = "HS256"

    access_token_expire_minutes: int

    openai_api_key: str
    openai_model: str = "gpt-6-luna"

    reranker_threshold: float = Field(
        default=0.5,
        allow_inf_nan=False,
    )

    reranker_candidate_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    @property
    def embedding_model(self) -> str:
        return model_manifest.embedding.model

    @property
    def embedding_model_revision(self) -> str:
        return model_manifest.embedding.revision

    @property
    def reranker_model(self) -> str:
        return model_manifest.reranker.model

    @property
    def reranker_model_revision(self) -> str:
        return model_manifest.reranker.revision

    @field_validator(
        "jwt_secret_key",
        mode="before",
    )
    @classmethod
    def validate_jwt_secret_key(
        cls,
        value: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "JWT_SECRET_KEY must be a string"
            )

        value = value.strip()

        if len(value) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must contain "
                "at least 32 characters"
            )

        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()


