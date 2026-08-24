from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


def test_alembic_upgrade_head_creates_metric_table(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "metric_migration.db"
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

        assert "metricas" in table_names

        columns = {
            column["name"]
            for column in inspector.get_columns(
                "metricas"
            )
        }

        assert columns == {
            "id",
            "conteudo_id",
            "visualizacoes",
            "curtidas",
            "comentarios",
            "compartilhamentos",
            "alcance",
            "data_referencia",
            "criado_em",
        }
    finally:
        get_settings.cache_clear()

def test_metric_migration_creates_content_foreign_key_with_cascade(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "metric_fk_migration.db"
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

        foreign_keys = inspector.get_foreign_keys(
            "metricas"
        )

        assert len(foreign_keys) == 1
        assert (
            foreign_keys[0]["referred_table"]
            == "conteudos"
        )
        assert foreign_keys[0]["constrained_columns"] == [
            "conteudo_id"
        ]
        assert foreign_keys[0]["referred_columns"] == [
            "id"
        ]
        assert (
            foreign_keys[0]["options"].get("ondelete")
            == "CASCADE"
        )
    finally:
        get_settings.cache_clear()

def test_metric_migration_creates_unique_content_reference_date(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "metric_unique_migration.db"
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

        unique_constraints = (
            inspector.get_unique_constraints(
                "metricas"
            )
        )

        matching = [
            constraint
            for constraint in unique_constraints
            if set(constraint["column_names"])
            == {
                "conteudo_id",
                "data_referencia",
            }
        ]

        assert len(matching) == 1
        assert (
            matching[0]["name"]
            == "uq_metricas_conteudo_data_referencia"
        )
    finally:
        get_settings.cache_clear()
