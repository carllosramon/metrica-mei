def register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )

    assert response.status_code == 201


def test_login_returns_access_token(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]


def test_login_returns_401_for_invalid_credentials(client):
    register_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "carlos@email.com",
            "senha": "senhaerrada",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-mail ou senha inválidos."
    }