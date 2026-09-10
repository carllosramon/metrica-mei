"""Os dublês em memória respondem como os repositórios do SQLAlchemy.

Os testes de serviço rodam sobre os dublês. Onde eles são mais permissivos
que a produção, o teste aprova uma semântica que a aplicação não tem, e o
defeito só aparece com o banco de verdade. Estes casos fixam as quatro
divergências que existiam.
"""

from dataclasses import replace
from datetime import date, datetime, timezone

import pytest

from app.domain.content import Content
from app.domain.metric import Metric
from app.domain.user import User
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.repositories.in_memory_user_repository import (
    InMemoryUserRepository,
)
from app.repositories.user_repository import (
    UserPersistenceConflictError,
)


def conteudo_de(repositorio, usuario_id=1):
    return repositorio.create(
        Content(
            id=None,
            usuario_id=usuario_id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )


def metrica_de(repositorio, conteudo_id):
    return repositorio.create(
        Metric(
            id=None,
            conteudo_id=conteudo_id,
            visualizacoes=100,
            curtidas=10,
            comentarios=1,
            compartilhamentos=1,
            alcance=80,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )


def test_atualizar_conteudo_nao_troca_o_dono():
    repositorio = InMemoryContentRepository()
    conteudo = conteudo_de(repositorio, usuario_id=1)

    # O repositório do SQLAlchemy filtra por id e dono, então uma
    # atualização com outro dono não encontra linha e devolve None.
    assert repositorio.update(replace(conteudo, usuario_id=2)) is None

    guardado = repositorio.get_by_id_and_user(conteudo.id, 1)

    assert guardado is not None
    assert guardado.usuario_id == 1


def test_atualizar_metrica_nao_troca_de_conteudo():
    repositorio = InMemoryMetricRepository()
    metrica = metrica_de(repositorio, conteudo_id=7)

    assert repositorio.update(replace(metrica, conteudo_id=8)) is None

    assert repositorio.get_by_id_and_content(metrica.id, 7) is not None
    assert repositorio.get_by_id_and_content(metrica.id, 8) is None


def test_excluir_conteudo_leva_as_medicoes():
    metricas = InMemoryMetricRepository()
    conteudos = InMemoryContentRepository(metric_repository=metricas)

    conteudo = conteudo_de(conteudos)
    metrica_de(metricas, conteudo.id)

    conteudos.delete(conteudo)

    # No banco a chave estrangeira apaga as medições em cascata. Sem o
    # mesmo aqui, o dublê deixava medições sem conteúdo e sem dono.
    assert metricas.list_by_content(conteudo.id) == []


def test_email_repetido_e_recusado():
    repositorio = InMemoryUserRepository()

    def cadastrar():
        return repositorio.create(
            User(
                id=None,
                nome="Carlos",
                email="carlos@email.com",
                senha_hash="hash",
                criado_em=datetime.now(timezone.utc),
            )
        )

    cadastrar()

    # O e-mail é único no banco. Permitindo o repetido, o dublê guardava
    # duas contas e a segunda ficava inalcançável pelo login, que busca
    # pelo e-mail e encontra sempre a primeira.
    with pytest.raises(UserPersistenceConflictError):
        cadastrar()
