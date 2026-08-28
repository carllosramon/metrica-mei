from datetime import date, datetime, timezone

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