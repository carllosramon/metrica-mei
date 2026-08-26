from datetime import date


def authenticated_headers(
    client,
    *,
    nome="Carlos",
    email="carlos@email.com",
):
    register = client.post(
        "/auth/register",
        json={
            "nome": nome,
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

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_content(
    client,
    headers,
    *,
    titulo="Post",
):
    response = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": titulo,
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
    visualizacoes=1000,
    curtidas=110,
    comentarios=14,
    compartilhamentos=22,
    alcance=1450,
):
    response = client.post(
        f"/conteudos/{content_id}/metricas",
        headers=headers,
        json={
            "visualizacoes": visualizacoes,
            "curtidas": curtidas,
            "comentarios": comentarios,
            "compartilhamentos": compartilhamentos,
            "alcance": alcance,
            "data_referencia": date.today().isoformat(),
        },
    )

    assert response.status_code == 201

    return response.json()


def test_dashboard_returns_consolidated_numbers(client):
    headers = authenticated_headers(client)

    primeiro = create_content(
        client,
        headers,
        titulo="Reels sobre preço",
    )
    segundo = create_content(
        client,
        headers,
        titulo="Carrossel de dicas",
    )

    create_metric(
        client,
        headers,
        primeiro["id"],
        visualizacoes=3200,
        curtidas=110,
        comentarios=14,
        compartilhamentos=22,
        alcance=1450,
    )
    create_metric(
        client,
        headers,
        segundo["id"],
        visualizacoes=800,
        curtidas=20,
        comentarios=4,
        compartilhamentos=1,
        alcance=550,
    )

    response = client.get(
        "/painel",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_conteudos"] == 2
    assert body["conteudos_com_metricas"] == 2
    assert body["total_visualizacoes"] == 4000
    assert body["total_curtidas"] == 130
    assert body["total_comentarios"] == 18
    assert body["total_compartilhamentos"] == 23
    assert body["total_alcance"] == 2000
    assert body["engajamento_geral"] == 8.55

    assert [item["titulo"] for item in body["maiores_alcances"]] == [
        "Reels sobre preço",
        "Carrossel de dicas",
    ]

    assert body["maiores_alcances"][0]["alcance"] == 1450
    assert body["maiores_alcances"][0]["engajamento"] == 10.07
    assert body["maiores_alcances"][0]["conteudo_id"] == primeiro["id"]

    plataformas = body["desempenho_por_plataforma"]

    assert len(plataformas) == 1
    assert plataformas[0]["plataforma"] == "Instagram"
    assert plataformas[0]["total_conteudos"] == 2
    assert plataformas[0]["total_alcance"] == 2000
    assert plataformas[0]["engajamento"] == 8.55


def test_dashboard_is_empty_for_new_user(client):
    headers = authenticated_headers(client)

    response = client.get(
        "/painel",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_conteudos"] == 0
    assert body["conteudos_com_metricas"] == 0
    assert body["total_visualizacoes"] == 0
    assert body["engajamento_geral"] is None
    assert body["maiores_alcances"] == []


def test_dashboard_only_sees_own_contents(client):
    dono = authenticated_headers(client)
    outro = authenticated_headers(
        client,
        nome="Outro",
        email="outro@email.com",
    )

    conteudo = create_content(
        client,
        dono,
        titulo="Conteúdo do dono",
    )
    create_metric(
        client,
        dono,
        conteudo["id"],
    )

    response = client.get(
        "/painel",
        headers=outro,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_conteudos"] == 0
    assert body["total_visualizacoes"] == 0
    assert body["maiores_alcances"] == []


def test_dashboard_returns_401_without_token(client):
    response = client.get("/painel")

    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}
    assert response.headers["www-authenticate"] == "Bearer"


def test_dashboard_returns_401_for_invalid_token(client):
    response = client.get(
        "/painel",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Não autenticado."}
