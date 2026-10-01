from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    test_database_url: str | None = Field(
        default=None,
        min_length=1,
    )

    jwt_secret_key: str
    jwt_algorithm: str
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

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()


