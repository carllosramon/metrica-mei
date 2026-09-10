"""A medição mais recente de cada conteúdo, numa consulta só.

O painel precisa de uma linha por conteúdo. Pedir o histórico de cada um
custava uma consulta por conteúdo e trazia todas as medições da conta para
descartar quase todas.
"""

from datetime import date, datetime, timedelta, timezone

from app.database.models import ContentModel, UserModel
from app.domain.metric import Metric
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


def criar_conteudo(session, usuario_id, titulo):
    conteudo = ContentModel(
        usuario_id=usuario_id,
        titulo=titulo,
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today() - timedelta(days=30),
        criado_em=datetime.now(timezone.utc),
    )

    session.add(conteudo)
    session.commit()
    session.refresh(conteudo)

    return conteudo


def criar_metrica(
    repositorio,
    conteudo_id,
    data_referencia,
    alcance,
):
    return repositorio.create(
        Metric(
            id=None,
            conteudo_id=conteudo_id,
            visualizacoes=alcance * 2,
            curtidas=10,
            comentarios=1,
            compartilhamentos=1,
            alcance=alcance,
            data_referencia=data_referencia,
            criado_em=datetime.now(timezone.utc),
        )
    )


def test_devolve_a_medicao_de_maior_data_de_cada_conteudo(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)

        primeiro = criar_conteudo(session, dono.id, "Reels")
        segundo = criar_conteudo(session, dono.id, "Carrossel")

        repositorio = SQLAlchemyMetricRepository(session)

        hoje = date.today()

        criar_metrica(repositorio, primeiro.id, hoje - timedelta(days=2), 100)
        criar_metrica(repositorio, primeiro.id, hoje, 300)
        criar_metrica(repositorio, primeiro.id, hoje - timedelta(days=1), 200)

        criar_metrica(repositorio, segundo.id, hoje - timedelta(days=5), 50)

        mais_recentes = repositorio.latest_by_contents([primeiro.id, segundo.id])

        # A ordem de inserção não é a ordem das datas, de propósito: o que
        # decide é a data de referência.
        assert mais_recentes[primeiro.id].alcance == 300
        assert mais_recentes[segundo.id].alcance == 50


def test_conteudo_sem_medicao_fica_fora_do_resultado(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)

        medido = criar_conteudo(session, dono.id, "Medido")
        sem_medicao = criar_conteudo(session, dono.id, "Sem medição")

        repositorio = SQLAlchemyMetricRepository(session)

        criar_metrica(repositorio, medido.id, date.today(), 100)

        mais_recentes = repositorio.latest_by_contents([medido.id, sem_medicao.id])

        assert set(mais_recentes) == {medido.id}


def test_lista_vazia_nao_consulta_o_banco(session_factory):
    with session_factory() as session:
        repositorio = SQLAlchemyMetricRepository(session)

        assert repositorio.latest_by_contents([]) == {}


def test_ignora_medicoes_de_outros_conteudos(session_factory):
    with session_factory() as session:
        dono = criar_dono(session)

        pedido = criar_conteudo(session, dono.id, "Pedido")
        alheio = criar_conteudo(session, dono.id, "Não pedido")

        repositorio = SQLAlchemyMetricRepository(session)

        criar_metrica(repositorio, pedido.id, date.today(), 100)
        criar_metrica(repositorio, alheio.id, date.today(), 9999)

        mais_recentes = repositorio.latest_by_contents([pedido.id])

        assert set(mais_recentes) == {pedido.id}
        assert mais_recentes[pedido.id].alcance == 100
