from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


def test_alembic_upgrade_head_adds_publication_url_column(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv(
        "DATABASE_URL",
        database_url,
    )

    get_settings.cache_clear()

    try:
        config = Config("alembic.ini")

        command.upgrade(
            config,
            "head",
        )

        engine = create_engine(database_url)
        inspector = inspect(engine)

        columns = {
            column["name"]: column for column in inspector.get_columns("conteudos")
        }

        assert "url_publicacao" in columns

        url_column = columns["url_publicacao"]

        assert url_column["nullable"] is True
        assert str(url_column["type"]) == "VARCHAR(500)"
    finally:
        get_settings.cache_clear()
