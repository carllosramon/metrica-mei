import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_db_session
from app.main import app

SEGREDO_DE_TESTE = "test-secret-key-with-at-least-32-bytes"


@pytest.fixture
def client(database_url, session_factory, monkeypatch):
    def override_db_session():
        with session_factory() as session:
            yield session

    def override_settings():
        return Settings(
            database_url=database_url,
            jwt_secret=SEGREDO_DE_TESTE,
            jwt_algorithm="HS256",
            jwt_expires_minutes=30,
        )

    app.dependency_overrides[get_db_session] = (
        override_db_session
    )

    app.dependency_overrides[get_settings] = (
        override_settings
    )

    # A subida da aplicação lê o ambiente direto, sem passar pelas
    # substituições acima, e recusa subir sem o segredo.
    monkeypatch.setenv("JWT_SECRET", SEGREDO_DE_TESTE)
    get_settings.cache_clear()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    get_settings.cache_clear()
