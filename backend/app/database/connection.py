from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


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
