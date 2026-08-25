ORIGEM_PERMITIDA = "http://localhost:5173"


def test_preflight_allows_configured_origin(client):
    response = client.options(
        "/painel",
        headers={
            "Origin": ORIGEM_PERMITIDA,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == ORIGEM_PERMITIDA
    )


def test_preflight_allows_authorization_header(client):
    response = client.options(
        "/conteudos",
        headers={
            "Origin": ORIGEM_PERMITIDA,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200

    cabecalhos_liberados = response.headers[
        "access-control-allow-headers"
    ].lower()

    assert "authorization" in cabecalhos_liberados


def test_response_includes_allow_origin_header(client):
    response = client.get(
        "/health",
        headers={
            "Origin": ORIGEM_PERMITIDA,
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == ORIGEM_PERMITIDA
    )


def test_unknown_origin_is_not_allowed(client):
    response = client.get(
        "/health",
        headers={
            "Origin": "http://site-malicioso.com",
        },
    )

    # A resposta ainda chega, mas sem o cabeçalho de liberação o navegador
    # é quem recusa a leitura pelo JavaScript da outra origem.
    assert "access-control-allow-origin" not in response.headers
