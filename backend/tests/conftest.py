from datetime import date

import pytest


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
