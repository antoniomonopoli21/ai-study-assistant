from sqlalchemy.engine import URL, make_url

from app.config import settings


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
        "POSTGRES_HOST": settings.postgres_host,
        "POSTGRES_PORT": settings.postgres_port,
        "POSTGRES_USER": settings.postgres_user,
        "POSTGRES_PASSWORD": settings.postgres_password,
        "POSTGRES_DB": settings.postgres_db,
    }

    if settings.postgres_host is not None:
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
            username=settings.postgres_user,
            password=settings.postgres_password,
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
        )

    if settings.database_url is not None:
        return make_url(
            settings.database_url
        )

    raise RuntimeError(
        "Database configuration is missing. "
        "Set DATABASE_URL or all POSTGRES_* settings."
    )