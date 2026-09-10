from datetime import datetime, timezone

from sqlalchemy import DateTime, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class DataHoraUtc(TypeDecorator):
    """Data e hora que entram e saem sempre em UTC com fuso.

    O PostgreSQL guarda o fuso e o SQLite descarta. Sem este tipo o mesmo
    campo saía com fuso num banco e sem fuso no outro, e um cliente que
    lesse o valor do SQLite como hora local erraria por três horas.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError("A data e hora precisa ter fuso horário.")

        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value.astimezone(timezone.utc)


def _enable_sqlite_foreign_keys(
    dbapi_connection,
    _connection_record,
) -> None:
    cursor = dbapi_connection.cursor()

    try:
        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )
    finally:
        cursor.close()


def create_engine_from_url(database_url: str) -> Engine:
    connect_args = (
        {"check_same_thread": False}
        if database_url.startswith("sqlite")
        else {}
    )

    engine = create_engine(
        database_url,
        connect_args=connect_args,
    )

    if database_url.startswith("sqlite"):
        event.listen(
            engine,
            "connect",
            _enable_sqlite_foreign_keys,
        )

    return engine


def create_session_factory(engine: Engine):
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
