from datetime import date, timedelta


def authenticated_headers(
    client,
    *,
    name="Carlos",
    email="carlos@email.com",
):
    register = client.post(
        "/auth/register",
        json={
            "nome": name,
            "email": email,
            "senha": "minhasenha",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": email,
            "senha": "minhasenha",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_content(
    client,
    headers,
    *,
    publication_date=None,
    title="Post",
):
    response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": title,
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": (
                publication_date
                or date.today().isoformat()
            ),
        },
    )
    assert response.status_code == 201
    return response.json()


def metric_payload(
    *,
    reference_date=None,
):
    return {
        "visualizacoes": 100,
        "curtidas": 10,
        "comentarios": 2,
        "compartilhamentos": 3,
        "alcance": 80,
        "data_referencia": (
            reference_date
            or date.today().isoformat()
        ),
    }


def test_create_metric_returns_201_and_public_dto(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["id"] is not None
    assert body["alcance"] == 80
    assert "criado_em" in body
    assert "conteudo_id" not in body
    assert "usuario_id" not in body


def test_list_metrics_returns_empty_list(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_metrics_orders_reference_date_desc(
    client,
):
    headers = authenticated_headers(client)
    publication = (
        date.today() - timedelta(days=3)
    )

    content = create_content(
        client,
        headers,
        publication_date=publication.isoformat(),
    )

    for reference in [
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=1),
    ]:
        response = client.post(
            f"/conteudos/{content['id']}/metricas",
            headers=headers,
            json=metric_payload(
                reference_date=reference.isoformat()
            ),
        )

        assert response.status_code == 201

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
    )

    body = response.json()

    assert response.status_code == 200
    assert body[0]["data_referencia"] == (
        date.today()
        - timedelta(days=1)
    ).isoformat()

    assert body[1]["data_referencia"] == (
        date.today()
        - timedelta(days=2)
    ).isoformat()


def test_get_metric_returns_owned_metric(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    created = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    ).json()

    response = client.get(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{created['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == (
        created["id"]
    )


def test_metric_routes_require_token(
    client,
):
    response = client.get(
        "/conteudos/1/metricas"
    )

    assert response.status_code == 401


def test_metric_routes_reject_invalid_token(
    client,
):
    response = client.get(
        "/conteudos/1/metricas",
        headers={
            "Authorization": "Bearer invalid"
        },
    )

    assert response.status_code == 401


def test_metric_routes_hide_foreign_content(
    client,
):
    owner_headers = authenticated_headers(
        client,
        email="owner@email.com",
    )

    content = create_content(
        client,
        owner_headers,
    )

    other_headers = authenticated_headers(
        client,
        name="Outro",
        email="other@email.com",
    )

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conteúdo não encontrado."
    }
