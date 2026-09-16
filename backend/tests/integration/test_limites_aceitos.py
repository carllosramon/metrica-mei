"""Os valores que ficam exatamente na borda do que é aceito.

A suíte tinha bastante teste do que é recusado, e quase nenhum do que
passa raspando. Só com os dois lados é que a borda fica presa: sem o
lado aceito, trocar `<=` por `<` em qualquer um desses limites não
quebra teste nenhum, e o usuário perde um caractere sem explicação.
"""

from datetime import date

import pytest


LIMITE_DO_INTEIRO = 2_147_483_647


def register(client, **campos):
    corpo = {
        "nome": "Carlos",
        "email": "carlos@email.com",
        "senha": "minhasenha",
    }
    corpo.update(campos)

    return client.post("/auth/register", json=corpo)


def authenticated_headers(client):
    assert register(client).status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "carlos@email.com",
            "senha": "minhasenha",
        },
    )
    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


@pytest.mark.parametrize(
    "tamanho",
    [2, 100],
)
def test_register_accepts_name_at_the_boundary(
    client,
    tamanho,
):
    resposta = register(client, nome="a" * tamanho)

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "a" * tamanho


@pytest.mark.parametrize(
    "tamanho",
    [8, 128],
)
def test_register_accepts_password_at_the_boundary(
    client,
    tamanho,
):
    assert (
        register(client, senha="a" * tamanho).status_code
        == 201
    )


@pytest.mark.parametrize(
    "campo,tamanho",
    [
        ("titulo", 200),
        ("plataforma", 50),
        ("tipo", 50),
        ("url_publicacao", 500),
    ],
)
def test_create_content_accepts_text_at_the_boundary(
    client,
    campo,
    tamanho,
):
    headers = authenticated_headers(client)

    corpo = {
        "titulo": "Post",
        "plataforma": "Instagram",
        "tipo": "Reels",
        "data_publicacao": date.today().isoformat(),
    }

    if campo == "url_publicacao":
        prefixo = "https://exemplo.com/"
        valor = prefixo + "a" * (tamanho - len(prefixo))
    else:
        valor = "a" * tamanho

    corpo[campo] = valor

    resposta = client.post(
        "/conteudos",
        headers=headers,
        json=corpo,
    )

    assert resposta.status_code == 201
    assert resposta.json()[campo] == valor


def test_create_metric_accepts_the_integer_ceiling(
    client,
):
    headers = authenticated_headers(client)

    conteudo = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Post",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": date.today().isoformat(),
        },
    ).json()

    # O teto é o maior INTEGER do PostgreSQL. Um a mais é recusado, e
    # isso já era testado; o próprio teto precisa passar, senão a regra
    # estaria cobrando um valor a menos do que anuncia.
    resposta = client.post(
        f"/conteudos/{conteudo['id']}/metricas",
        headers=headers,
        json={
            "visualizacoes": LIMITE_DO_INTEIRO,
            "curtidas": 0,
            "comentarios": 0,
            "compartilhamentos": 0,
            "alcance": 1,
            "data_referencia": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 201
    assert (
        resposta.json()["visualizacoes"]
        == LIMITE_DO_INTEIRO
    )


@pytest.mark.parametrize(
    "valor",
    ["100", 1.0, True],
)
def test_create_metric_rejects_numbers_that_are_not_integers(
    client,
    valor,
):
    headers = authenticated_headers(client)

    conteudo = client.post(
        "/conteudos",
        headers=headers,
        json={
            "titulo": "Post",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": date.today().isoformat(),
        },
    ).json()

    # Os três seriam convertidos para inteiro por um int comum do
    # Pydantic, e a medição gravaria um número que o usuário não
    # digitou. O StrictInt existe para isso, e sem estes casos trocá-lo
    # por int não quebra nada.
    resposta = client.post(
        f"/conteudos/{conteudo['id']}/metricas",
        headers=headers,
        json={
            "visualizacoes": valor,
            "curtidas": 0,
            "comentarios": 0,
            "compartilhamentos": 0,
            "alcance": 1,
            "data_referencia": date.today().isoformat(),
        },
    )

    assert resposta.status_code == 422
