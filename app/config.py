from typing import Literal

from pydantic import Field, field_validator


from pydantic_settings import BaseSettings, SettingsConfigDict


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

    embedding_model: str = Field(
        default="intfloat/multilingual-e5-small",
        min_length=1,
    )


    reranker_model: str = Field(
        default="cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        min_length=1,
    )

    reranker_threshold: float = Field(
        default=0.5,
        allow_inf_nan=False,
    )

    reranker_candidate_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

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


