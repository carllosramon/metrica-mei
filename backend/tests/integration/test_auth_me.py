from app.security.jwt import TokenService


TEST_SECRET = "test-secret-key-with-at-least-32-bytes"


def register_and_login(client):
    register_response = client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_me_returns_authenticated_user(client):
    token = register_and_login(client)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["email"] == "carlos@email.com"
    assert body["nome"] == "Carlos"
    assert body["id"] is not None
    assert "senha" not in body
    assert "senha_hash" not in body


def test_me_returns_401_without_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }


def test_me_returns_401_for_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer token-invalido"
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }


def test_me_returns_401_for_expired_token(client):
    register_response = client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )

    assert register_response.status_code == 201

    user_id = register_response.json()["id"]

    expired_token = TokenService(
        TEST_SECRET,
        "HS256",
        -1,
    ).create_access_token(user_id)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}"
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }