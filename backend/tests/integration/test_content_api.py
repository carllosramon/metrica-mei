import pytest

from app.services.content_service import InvalidContentError

def authenticated_headers(client):
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

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_create_content_returns_201_and_public_content(
    client,
):
    response = client.post(
        "/conteudos",
        headers=authenticated_headers(client),
        json={
            "titulo": "  Meu conteúdo  ",
            "plataforma": "  Instagram  ",
            "tipo": "  Reels  ",
            "data_publicacao": "2026-08-20",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["titulo"] == "Meu conteúdo"
    assert body["plataforma"] == "Instagram"
    assert body["tipo"] == "Reels"
    assert body["data_publicacao"] == "2026-08-20"
    assert "criado_em" in body
    assert "usuario_id" not in body


def test_list_contents_returns_authenticated_user_contents(
    client,
):
    headers = authenticated_headers(client)

    first_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Conteúdo antigo",
            "plataforma": "Instagram",
            "tipo": "Carrossel",
            "data_publicacao": "2026-08-18",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Conteúdo recente",
            "plataforma": "TikTok",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert second_response.status_code == 201

    response = client.get(
        "/conteudos",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["titulo"] == "Conteúdo recente"
    assert body[0]["data_publicacao"] == "2026-08-20"

    assert body[1]["titulo"] == "Conteúdo antigo"
    assert body[1]["data_publicacao"] == "2026-08-18"

    assert "usuario_id" not in body[0]
    assert "usuario_id" not in body[1]


def test_get_content_returns_owned_content(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Meu conteúdo",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    response = client.get(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created["id"]
    assert body["titulo"] == "Meu conteúdo"
    assert body["plataforma"] == "Instagram"
    assert body["tipo"] == "Reels"
    assert body["data_publicacao"] == "2026-08-20"
    assert "usuario_id" not in body


def test_get_content_returns_404_for_missing_content(
    client,
):
    headers = authenticated_headers(client)

    response = client.get(
        "/conteudos/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_update_content_changes_only_provided_fields(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Título antigo",
            "plataforma": "Instagram",
            "tipo": "Carrossel",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "titulo": "Título novo",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == created["id"]
    assert body["titulo"] == "Título novo"
    assert body["plataforma"] == "Instagram"
    assert body["tipo"] == "Carrossel"
    assert body["data_publicacao"] == "2026-08-20"
    assert "usuario_id" not in body


def test_update_content_accepts_other_editable_fields(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Meu conteúdo",
            "plataforma": "Instagram",
            "tipo": "Carrossel",
            "data_publicacao": "2026-08-18",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "plataforma": "TikTok",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["titulo"] == "Meu conteúdo"
    assert body["plataforma"] == "TikTok"
    assert body["tipo"] == "Reels"
    assert body["data_publicacao"] == "2026-08-20"



def test_update_content_returns_422_for_empty_payload(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Meu conteúdo",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    try:
        response = client.patch(
            f"/conteudos/{created['id']}",
            headers=headers,
            json={},
        )
    except InvalidContentError:
        pytest.fail(
            "InvalidContentError escapou do Controller."
        )

    assert response.status_code == 422


def test_update_content_returns_422_for_explicit_null(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Meu conteúdo",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    response = client.patch(
        f"/conteudos/{created['id']}",
        headers=headers,
        json={
            "titulo": None,
        },
    )

    assert response.status_code == 422


def test_update_content_returns_404_for_missing_content(
    client,
):
    headers = authenticated_headers(client)

    response = client.patch(
        "/conteudos/999999",
        headers=headers,
        json={
            "titulo": "Novo título",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_delete_content_returns_204_and_removes_content(
    client,
):
    headers = authenticated_headers(client)

    create_response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Conteúdo para excluir",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    created = create_response.json()

    response = client.delete(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    get_response = client.get(
        f"/conteudos/{created['id']}",
        headers=headers,
    )

    assert get_response.status_code == 404
    assert get_response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_delete_content_returns_404_for_missing_content(
    client,
):
    headers = authenticated_headers(client)

    response = client.delete(
        "/conteudos/999999",
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def authenticated_headers_for(
    client,
    nome,
    email,
):
    register_response = client.post(
        "/auth/register",
        json={
            "nome": nome,
            "email": email,
            "senha": "minhasenha",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": "minhasenha",
        },
    )

    assert login_response.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login_response.json()['access_token']}"
        )
    }


def test_get_content_returns_404_for_another_users_content(
    client,
):
    owner_headers = authenticated_headers_for(
        client,
        "Carlos",
        "carlos@email.com",
    )

    other_headers = authenticated_headers_for(
        client,
        "Outro",
        "outro@email.com",
    )

    create_response = client.post(
        "/conteudos",
        headers=owner_headers,
        json={
            "titulo": "Conteúdo privado",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    content_id = create_response.json()["id"]

    response = client.get(
        f"/conteudos/{content_id}",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }


def test_update_content_returns_404_for_another_users_content(
    client,
):
    owner_headers = authenticated_headers_for(
        client,
        "Carlos",
        "carlos@email.com",
    )

    other_headers = authenticated_headers_for(
        client,
        "Outro",
        "outro@email.com",
    )

    create_response = client.post(
        "/conteudos",
        headers=owner_headers,
        json={
            "titulo": "Título original",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    content_id = create_response.json()["id"]

    response = client.patch(
        f"/conteudos/{content_id}",
        headers=other_headers,
        json={
            "titulo": "Tentativa de alteração",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }

    owner_response = client.get(
        f"/conteudos/{content_id}",
        headers=owner_headers,
    )

    assert owner_response.status_code == 200
    assert (
        owner_response.json()["titulo"]
        == "Título original"
    )


def test_delete_content_returns_404_for_another_users_content(
    client,
):
    owner_headers = authenticated_headers_for(
        client,
        "Carlos",
        "carlos@email.com",
    )

    other_headers = authenticated_headers_for(
        client,
        "Outro",
        "outro@email.com",
    )

    create_response = client.post(
        "/conteudos",
        headers=owner_headers,
        json={
            "titulo": "Conteúdo privado",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-20",
        },
    )

    assert create_response.status_code == 201

    content_id = create_response.json()["id"]

    response = client.delete(
        f"/conteudos/{content_id}",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }

    owner_response = client.get(
        f"/conteudos/{content_id}",
        headers=owner_headers,
    )

    assert owner_response.status_code == 200


def test_create_content_returns_422_for_future_publication_date(
    client,
):
    headers = authenticated_headers(client)

    try:
        response = client.post(
            "/conteudos",
            headers=headers,
            json={
                "titulo": "Conteúdo futuro",
                "plataforma": "Instagram",
                "tipo": "Reels",
                "data_publicacao": "2999-01-01",
            },
        )
    except InvalidContentError:
        pytest.fail(
            "InvalidContentError escapou do Controller no POST."
        )

    assert response.status_code == 422


def test_list_contents_returns_401_without_token(
    client,
):
    response = client.get(
        "/conteudos",
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_list_contents_returns_401_for_invalid_token(
    client,
):
    response = client.get(
        "/conteudos",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Não autenticado."
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )
