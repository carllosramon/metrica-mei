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

def create_metric(
    client,
    headers,
    content_id,
    *,
    reference_date=None,
):
    response = client.post(
        f"/conteudos/{content_id}/metricas",
        headers=headers,
        json=metric_payload(
            reference_date=reference_date
        ),
    )

    assert response.status_code == 201

    return response.json()


def test_patch_metric_updates_one_field(
    client,
):
    headers = authenticated_headers(client)

    content = create_content(
        client,
        headers,
    )

    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={
            "alcance": 999,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["alcance"] == 999
    assert (
        body["visualizacoes"]
        == metric["visualizacoes"]
    )

def test_delete_metric_returns_204(
    client,
):
    headers = authenticated_headers(client)

    content = create_content(
        client,
        headers,
    )

    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.delete(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 204
    assert response.content == b""

def test_patch_metric_accepts_zero(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={"alcance": 0},
    )

    assert response.status_code == 200
    assert response.json()["alcance"] == 0


def test_patch_metric_rejects_empty_payload(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_patch_metric_rejects_explicit_null(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )
    metric = create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
        json={"alcance": None},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_negative_value(
    client,
):
    headers = authenticated_headers(client)
    content = create_content(
        client,
        headers,
    )

    payload = metric_payload()
    payload["alcance"] = -1

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=payload,
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_reference_date_before_publication(
    client,
):
    headers = authenticated_headers(client)

    publication = (
        date.today() - timedelta(days=1)
    )

    content = create_content(
        client,
        headers,
        publication_date=publication.isoformat(),
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(
            reference_date=(
                publication - timedelta(days=1)
            ).isoformat()
        ),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_future_reference_date(
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
        json=metric_payload(
            reference_date=(
                date.today() + timedelta(days=1)
            ).isoformat()
        ),
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Dados da métrica inválidos."
    }


def test_create_metric_rejects_duplicate_date(
    client,
):
    headers = authenticated_headers(client)

    content = create_content(
        client,
        headers,
    )

    create_metric(
        client,
        headers,
        content["id"],
    )

    response = client.post(
        f"/conteudos/{content['id']}/metricas",
        headers=headers,
        json=metric_payload(),
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Já existe uma métrica para este "
            "conteúdo nesta data."
        )
    }


def test_patch_metric_rejects_date_collision(
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

    first_date = (
        date.today() - timedelta(days=1)
    )

    first = create_metric(
        client,
        headers,
        content["id"],
        reference_date=first_date.isoformat(),
    )

    second = create_metric(
        client,
        headers,
        content["id"],
        reference_date=date.today().isoformat(),
    )

    response = client.patch(
        (
            f"/conteudos/{content['id']}"
            f"/metricas/{second['id']}"
        ),
        headers=headers,
        json={
            "data_referencia": (
                first["data_referencia"]
            )
        },
    )

    assert response.status_code == 409


def test_metric_id_from_other_content_is_hidden(
    client,
):
    headers = authenticated_headers(client)

    first_content = create_content(
        client,
        headers,
        title="A",
    )

    second_content = create_content(
        client,
        headers,
        title="B",
    )

    metric = create_metric(
        client,
        headers,
        second_content["id"],
    )

    response = client.get(
        (
            f"/conteudos/{first_content['id']}"
            f"/metricas/{metric['id']}"
        ),
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Métrica não encontrada."
    }


def test_delete_missing_metric_returns_404(
    client,
):
    headers = authenticated_headers(client)

    content = create_content(
        client,
        headers,
    )

    response = client.delete(
        (
            f"/conteudos/{content['id']}"
            "/metricas/999"
        ),
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Métrica não encontrada."
    }
