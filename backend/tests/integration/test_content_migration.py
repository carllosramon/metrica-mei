from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


def test_alembic_upgrade_head_creates_content_table(
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

        table_names = inspector.get_table_names()

        assert "usuarios" in table_names
        assert "conteudos" in table_names

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "conteudos"
            )
        }

        assert columns == {
            "id",
            "usuario_id",
            "titulo",
            "plataforma",
            "tipo",
            "data_publicacao",
            "criado_em",
            "url_publicacao",
        }

        foreign_keys = inspector.get_foreign_keys(
            "conteudos"
        )

        assert len(foreign_keys) == 1
        assert foreign_keys[0]["referred_table"] == "usuarios"
        assert foreign_keys[0]["constrained_columns"] == [
            "usuario_id"
        ]
        assert foreign_keys[0]["referred_columns"] == [
            "id"
        ]

        indexes = inspector.get_indexes(
            "conteudos"
        )

        indexed_columns = {
            tuple(index["column_names"])
            for index in indexes
        }

        assert ("usuario_id",) in indexed_columns
    finally:
        get_settings.cache_clear()
