from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    openai_api_key: str
    openai_model: str = "gpt-6-luna"

    rag_max_distance: float = 0.25

    reranker_model: str = (
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    )
    reranker_threshold: float = 0.5
    reranker_top_k: int = 5

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()


