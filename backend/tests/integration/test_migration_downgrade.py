from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.config import get_settings


TABELAS = {"usuarios", "conteudos", "metricas"}


def tabelas_existentes(database_url):
    engine = create_engine(database_url)

    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def test_migrations_sobem_descem_e_sobem_de_novo(
    tmp_path,
    monkeypatch,
):
    """Prova que a cadeia de migrations é reversível.

    Sem este ciclo, um downgrade quebrado só apareceria no momento em que
    fosse preciso desfazer uma migration — que é o pior momento possível
    para descobrir. O downgrade do 0004 remove uma coluna, operação que o
    SQLite nem sempre suportou.
    """
    database_path = tmp_path / "ciclo.db"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv(
        "DATABASE_URL",
        database_url,
    )

    get_settings.cache_clear()

    try:
        config = Config("alembic.ini")

        command.upgrade(config, "head")

        assert TABELAS.issubset(tabelas_existentes(database_url))

        command.downgrade(config, "base")

        restantes = tabelas_existentes(database_url)

        assert TABELAS.isdisjoint(restantes)

        command.upgrade(config, "head")

        depois = tabelas_existentes(database_url)

        assert TABELAS.issubset(depois)
    finally:
        get_settings.cache_clear()


def test_downgrade_de_um_passo_remove_a_url_de_publicacao(
    tmp_path,
    monkeypatch,
):
    database_path = tmp_path / "um-passo.db"
    database_url = f"sqlite:///{database_path}"

    monkeypatch.setenv(
        "DATABASE_URL",
        database_url,
    )

    get_settings.cache_clear()

    try:
        config = Config("alembic.ini")

        command.upgrade(config, "head")

        command.downgrade(config, "-1")

        engine = create_engine(database_url)

        try:
            colunas = {
                coluna["name"]
                for coluna in inspect(engine).get_columns("conteudos")
            }
        finally:
            engine.dispose()

        # A tabela continua de pé; só a coluna do último passo sai.
        assert "url_publicacao" not in colunas
        assert "titulo" in colunas
    finally:
        get_settings.cache_clear()
