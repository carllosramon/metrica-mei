"""O criado_em sai com fuso em qualquer banco.

O PostgreSQL guarda o fuso e o SQLite descarta. Sem tratamento, o mesmo
campo saía com fuso num banco e sem fuso no outro.
"""

from datetime import datetime, timezone


def _sessao(client):
    client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "senha-forte-123",
        },
    )

    resposta = client.post(
        "/auth/login",
        json={"email": "carlos@email.com", "senha": "senha-forte-123"},
    )

    return {"Authorization": f"Bearer {resposta.json()['access_token']}"}


def _com_fuso_utc(texto: str) -> bool:
    instante = datetime.fromisoformat(texto)

    return (
        instante.tzinfo is not None
        and instante.utcoffset() == timezone.utc.utcoffset(None)
    )


def test_criado_em_do_usuario_tem_fuso(client):
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Carlos",
            "email": "carlos@email.com",
            "senha": "senha-forte-123",
        },
    )

    assert resposta.status_code == 201
    assert _com_fuso_utc(resposta.json()["criado_em"])


def test_criado_em_do_conteudo_e_da_metrica_tem_fuso(client):
    cabecalhos = _sessao(client)

    conteudo = client.post(
        "/conteudos",
        headers=cabecalhos,
        json={
            "titulo": "Reels",
            "plataforma": "Instagram",
            "tipo": "Reels",
            "data_publicacao": "2026-08-21",
        },
    )

    assert conteudo.status_code == 201
    assert _com_fuso_utc(conteudo.json()["criado_em"])

    metrica = client.post(
        f"/conteudos/{conteudo.json()['id']}/metricas",
        headers=cabecalhos,
        json={
            "visualizacoes": 100,
            "curtidas": 10,
            "comentarios": 1,
            "compartilhamentos": 1,
            "alcance": 80,
            "data_referencia": "2026-08-22",
        },
    )

    assert metrica.status_code == 201
    assert _com_fuso_utc(metrica.json()["criado_em"])
