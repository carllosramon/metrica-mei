import pytest
from fastapi.testclient import TestClient


def test_health_endpoint_returns_ok():
    try:
        from app.main import app
    except ModuleNotFoundError:
        pytest.fail("O módulo app.main ainda não existe.")

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}