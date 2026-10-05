from sqlalchemy.engine import URL, make_url

from app.database_config import database_settings


def create_postgres_url(
    *,
    username: str,
    password: str,
    host: str,
    port: int,
    database: str,
) -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )


def get_database_url() -> URL:
    postgres_components = {
        "POSTGRES_HOST": database_settings.postgres_host,
        "POSTGRES_PORT": database_settings.postgres_port,
        "POSTGRES_USER": database_settings.postgres_user,
        "POSTGRES_PASSWORD": database_settings.postgres_password,
        "POSTGRES_DB": database_settings.postgres_db,
    }

    if database_settings.postgres_host is not None:
        missing = [
            name
            for name, value in postgres_components.items()
            if value is None
        ]

        if missing:
            raise RuntimeError(
                "Incomplete PostgreSQL configuration. "
                "Missing: "
                + ", ".join(missing)
            )

        return create_postgres_url(
            username=database_settings.postgres_user,
            password=database_settings.postgres_password,
            host=database_settings.postgres_host,
            port=database_settings.postgres_port,
            database=database_settings.postgres_db,
        )

    if database_settings.database_url is not None:
        return make_url(
            database_settings.database_url
        )

    raise RuntimeError(
        "Database configuration is missing. "
        "Set DATABASE_URL or all POSTGRES_* settings."
    )