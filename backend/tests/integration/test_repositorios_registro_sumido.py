"""O registro pode sumir entre a leitura do serviço e a gravação.

Outra requisição pode excluí-lo no intervalo. Estes testes fixam o que os
repositórios fazem nessa corrida, que até então divergia entre a
implementação do SQLAlchemy e a em memória sem ninguém perceber.
"""

from dataclasses import replace
from datetime import date, datetime, timezone

from app.database.models import UserModel
from app.domain.content import Content
from app.domain.metric import Metric
from app.repositories.sqlalchemy_content_repository import (
    SQLAlchemyContentRepository,
)
from app.repositories.sqlalchemy_metric_repository import (
    SQLAlchemyMetricRepository,
)


def criar_dono(session):
    dono = UserModel(
        nome="Carlos",
        email="carlos@email.com",
        senha_hash="hash",
        criado_em=datetime.now(timezone.utc),
    )

    session.add(dono)
    session.commit()
    session.refresh(dono)

    return dono


def criar_conteudo(repositorio, usuario_id):
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


def criar_metrica(repositorio, conteudo_id):
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


def test_atualizar_conteudo_sumido_avisa_e_nao_recria(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)
        repositorio = SQLAlchemyContentRepository(session)

        conteudo = criar_conteudo(repositorio, dono.id)

        repositorio.delete(conteudo)

        resultado = repositorio.update(
            replace(conteudo, titulo="Título novo")
        )

        assert resultado is None

        # O que sumiu continua sumido: a gravação não pode ressuscitá-lo.
        assert (
            repositorio.get_by_id_and_user(conteudo.id, dono.id) is None
        )


def test_excluir_conteudo_ja_sumido_nao_faz_nada(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)
        repositorio = SQLAlchemyContentRepository(session)

        conteudo = criar_conteudo(repositorio, dono.id)

        repositorio.delete(conteudo)

        # Apagar o que já sumiu alcançou o objetivo: é operação repetível.
        repositorio.delete(conteudo)

        assert (
            repositorio.get_by_id_and_user(conteudo.id, dono.id) is None
        )


def test_atualizar_metrica_sumida_avisa_e_nao_recria(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)

        conteudos = SQLAlchemyContentRepository(session)
        conteudo = criar_conteudo(conteudos, dono.id)

        repositorio = SQLAlchemyMetricRepository(session)
        metrica = criar_metrica(repositorio, conteudo.id)

        repositorio.delete(metrica)

        resultado = repositorio.update(replace(metrica, alcance=999))

        assert resultado is None

        assert (
            repositorio.get_by_id_and_content(metrica.id, conteudo.id)
            is None
        )


def test_excluir_metrica_ja_sumida_nao_faz_nada(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)

        conteudos = SQLAlchemyContentRepository(session)
        conteudo = criar_conteudo(conteudos, dono.id)

        repositorio = SQLAlchemyMetricRepository(session)
        metrica = criar_metrica(repositorio, conteudo.id)

        repositorio.delete(metrica)
        repositorio.delete(metrica)

        assert (
            repositorio.get_by_id_and_content(metrica.id, conteudo.id)
            is None
        )
