import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)
from app.dependencies import get_db_session
from app.main import app


@pytest.fixture
def client(tmp_path):
    database_path = tmp_path / "api.db"

    engine = create_engine_from_url(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(engine)

    session_factory = create_session_factory(
        engine
    )

    def override_db_session():
        with session_factory() as session:
            yield session

    def override_settings():
        return Settings(
            database_url=f"sqlite:///{database_path}",
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
