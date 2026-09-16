from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.services.business_clock import business_today


def test_business_today_uses_brazilian_calendar_day():
    instant = datetime(
        2026,
        8,
        28,
        0,
        30,
        tzinfo=timezone.utc,
    )

    assert business_today(instant) == date(
        2026,
        8,
        27,
    )


def test_business_today_without_argument_reads_the_clock():
    # Sem este teste, a chamada sem argumento nunca roda: todos os outros
    # passam o instante, e trocar datetime.now(timezone.utc) por qualquer
    # outra coisa passaria despercebido. É a forma que a aplicação usa em
    # produção, e a única que o conftest substitui nos demais testes.
    esperado = (
        datetime.now(timezone.utc)
        .astimezone(ZoneInfo("America/Sao_Paulo"))
        .date()
    )

    assert business_today() == esperado


def test_business_today_rejects_instant_without_timezone():
    # Um datetime ingênuo seria convertido como se fosse do fuso da
    # máquina, e o dia de negócio passaria a depender do servidor.
    with pytest.raises(ValueError):
        business_today(
            datetime(
                2026,
                8,
                28,
                0,
                30,
            )
        )
