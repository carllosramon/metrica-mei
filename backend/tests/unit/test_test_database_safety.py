import pytest


def test_database_url_rejects_postgresql_without_test_name(
    monkeypatch,
    request,
):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        (
            "postgresql+psycopg://usuario:senha@localhost:5432/"
            "metricamei"
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="banco explicitamente de teste",
    ):
        request.getfixturevalue("database_url")


def test_database_url_rejects_development_sqlite_file(
    monkeypatch,
    request,
):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "sqlite:///./data/metrica_mei.db",
    )

    with pytest.raises(
        RuntimeError,
        match="banco explicitamente de teste",
    ):
        request.getfixturevalue("database_url")


def test_database_url_accepts_explicit_postgresql_test_database(
    monkeypatch,
    request,
):
    database_url = (
        "postgresql+psycopg://usuario:senha@localhost:5432/"
        "metricamei_test"
    )

    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        database_url,
    )

    assert (
        request.getfixturevalue("database_url")
        == database_url
    )


def test_database_url_accepts_explicit_sqlite_test_database(
    monkeypatch,
    request,
):
    database_url = "sqlite:///./data/metricamei_test.db"

    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        database_url,
    )

    assert (
        request.getfixturevalue("database_url")
        == database_url
    )
