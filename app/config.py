from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    test_database_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int

    openai_api_key: str
    openai_model: str = "gpt-6-luna"

    model_config = SettingsConfigDict(
        env_file=".env"
    )


settings = Settings()