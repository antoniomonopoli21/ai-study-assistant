from app.database_config import DatabaseSettings


def test_database_settings_do_not_require_app_secrets():
    settings = DatabaseSettings(
        _env_file=None,
        postgres_host="db",
        postgres_port=5432,
        postgres_user="app_user",
        postgres_password="test-password",
        postgres_db="ai_study_assistant",
    )

    assert settings.postgres_host == "db"
    assert settings.postgres_port == 5432
    assert settings.postgres_user == "app_user"
    assert settings.postgres_db == "ai_study_assistant"