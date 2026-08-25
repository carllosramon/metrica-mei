from datetime import date


def authenticated_headers(client):
    register = client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )
    assert register.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )
    assert login.status_code == 200

    token = login.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_content(client, headers):
    response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Post",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": date.today().isoformat(),
        },
    )

    assert response.status_code == 201

    return response.json()


def create_metric(
    client,
    headers,
    content_id,
    *,
    alcance=1450,
):
    response = client.post(
        f"/conteudos/{content_id}/metricas",
        headers=headers,
        json={
            "visualizacoes": 2000,
            "curtidas": 110,
            "comentarios": 14,
            "compartilhamentos": 22,
            "alcance": alcance,
            "data_referencia": date.today().isoformat(),
        },
    )

    assert response.status_code == 201

    return response.json()


def test_create_metric_returns_engagement(client):
    headers = authenticated_headers(client)
    content = create_content(client, headers)

    body = create_metric(
        client,
        headers,
        content["id"],
    )

    assert body["engajamento"] == 10.07


def test_get_metric_returns_engagement(client):
    headers = authenticated_headers(client)
    content = create_content(client, headers)

    created = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.get(
        (f"/conteudos/{content['id']}" f"/metricas/{created['id']}"),
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["engajamento"] == 10.07


def test_list_metrics_returns_engagement(client):
    headers = authenticated_headers(client)
    content = create_content(client, headers)

    create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.get(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["engajamento"] == 10.07


def test_metric_with_zero_reach_returns_null_engagement(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(client, headers)

    body = create_metric(
        client,
        headers,
        content["id"],
        alcance=0,
    )

    assert body["engajamento"] is None


def test_patch_metric_recalculates_engagement(client):
    headers = authenticated_headers(client)
    content = create_content(client, headers)

    created = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (f"/conteudos/{content['id']}" f"/metricas/{created['id']}"),
        headers=headers,
        json={
            "alcance": 1000,
        },
    )

    assert response.status_code == 200
    assert response.json()["engajamento"] == 14.6
