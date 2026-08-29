import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_db_session
from app.main import app


@pytest.fixture
def client(database_url, session_factory):
    def override_db_session():
        with session_factory() as session:
            yield session

    def override_settings():
        return Settings(
            database_url=database_url,
            jwt_secret="test-secret-key-with-at-least-32-bytes",
            jwt_algorithm="HS256",
            jwt_expires_minutes=30,
        )

    app.dependency_overrides[get_db_session] = (
        override_db_session
    )

    app.dependency_overrides[get_settings] = (
        override_settings
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
