from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


_BUSINESS_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def business_today(
    instant: datetime | None = None,
) -> date:
    current = (
        instant
        if instant is not None
        else datetime.now(timezone.utc)
    )

    if current.tzinfo is None:
        raise ValueError(
            "O instante precisa conter informação de fuso horário."
        )

    return current.astimezone(
        _BUSINESS_TIMEZONE
    ).date()