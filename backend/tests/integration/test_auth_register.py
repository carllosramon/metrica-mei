def test_register_returns_201_and_public_user(client):
    response = client.post(
        "/auth/register",
        json={
            "nome": "Carlos Ramon",
            "email": "CARLOS@EMAIL.COM",
            "senha": "minhasenha",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "carlos@email.com"
    assert body["nome"] == "Carlos Ramon"
    assert body["id"] is not None
    assert "criado_em" in body
    assert "senha" not in body
    assert "senha_hash" not in body


def test_register_returns_409_for_duplicate_email(client):
    payload = {
        "nome": "Carlos",
        "email": "carlos@email.com",
        "senha": "minhasenha",
    }

    first_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/auth/register",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "E-mail já cadastrado."
    }


def test_register_returns_422_for_invalid_payload(client):
    response = client.post(
        "/auth/register",
        json={
            "nome": "C",
            "email": "email-invalido",
            "senha": "123",
        },
    )

    assert response.status_code == 422