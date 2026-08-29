import os
from datetime import date

import pytest

from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)


@pytest.fixture(autouse=True)
def align_business_day_with_test_calendar(monkeypatch):
    """Mantém testes comuns independentes do fuso horário do runner.

    Os testes existentes constroem datas relativas a date.today(). Durante
    esses testes, as regras de conteúdo e métrica precisam enxergar o mesmo
    dia. O comportamento real de America/Sao_Paulo continua verificado
    separadamente em test_business_clock.py.
    """
    monkeypatch.setattr(
        "app.services.content_service.business_today",
        lambda: date.today(),
    )
    monkeypatch.setattr(
        "app.services.metric_service.business_today",
        lambda: date.today(),
    )


@pytest.fixture
def database_url(tmp_path) -> str:
    """Endereço do banco que os testes de integração devem usar.

    Sem TEST_DATABASE_URL, cada teste ganha o próprio arquivo SQLite, que é
    o comportamento de sempre. Com ela, a suíte inteira roda contra o banco
    apontado — é assim que a integração contínua exercita as consultas da
    aplicação no PostgreSQL, onde diferenças de dialeto aparecem.
    """
    configurado = os.environ.get("TEST_DATABASE_URL")

    if configurado:
        return configurado

    return f"sqlite:///{tmp_path / 'teste.db'}"


@pytest.fixture
def test_engine(database_url):
    engine = create_engine_from_url(database_url)

    # Num banco compartilhado o schema sobrevive ao teste anterior, então
    # precisa ser derrubado antes de recriado. No arquivo SQLite, que nasce
    # vazio a cada teste, o drop_all não encontra nada para remover.
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def session_factory(test_engine):
    return create_session_factory(test_engine)
