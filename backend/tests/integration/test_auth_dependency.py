from datetime import datetime, timezone

from app import dependencies
from app.domain.user import User
from app.main import app


def test_shared_current_user_dependency_exists():
    current_user_dependency = getattr(
        dependencies,
        "get_current_user",
        None,
    )

    assert callable(current_user_dependency)


def test_me_uses_shared_current_user_dependency(client):
    fake_user = User(
        id=123,
        nome="Usuário de teste",
        email="teste@email.com",
        senha_hash="hash",
        criado_em=datetime.now(timezone.utc),
    )

    def override_current_user():
        return fake_user

    app.dependency_overrides[
        dependencies.get_current_user
    ] = override_current_user

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == 123
    assert response.json()["email"] == "teste@email.com"
