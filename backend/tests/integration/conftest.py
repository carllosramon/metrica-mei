import pytest
from fastapi.testclient import TestClient

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

    app.dependency_overrides[get_db_session] = (
        override_db_session
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()