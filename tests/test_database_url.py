from sqlalchemy.engine import make_url

from app.database_url import (
    create_postgres_url,
)


def test_postgres_url_handles_special_characters():
    password = "p@ss:w/or%d#strange"

    url = create_postgres_url(
        username="app_user",
        password=password,
        host="db",
        port=5432,
        database="ai_study_assistant",
    )

    assert url.username == "app_user"
    assert url.password == password
    assert url.host == "db"
    assert url.port == 5432

    rendered = url.render_as_string(
        hide_password=False
    )

    parsed = make_url(
        rendered
    )

    assert parsed.username == "app_user"
    assert parsed.password == password
    assert parsed.host == "db"
    assert parsed.port == 5432
    assert (
        parsed.database
        == "ai_study_assistant"
    )