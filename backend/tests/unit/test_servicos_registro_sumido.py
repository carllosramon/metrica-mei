"""O serviço lê, decide, e só então manda gravar.

Entre a leitura e a gravação outra requisição pode excluir o registro.
Estes testes fixam o que o usuário recebe nessa corrida: um aviso de que o
registro não existe mais, e não um "salvo" para algo que não foi gravado.
"""

from datetime import date, datetime, timezone

import pytest

from app.domain.content import Content
from app.domain.metric import Metric
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)
from app.services.content_service import (
    ContentNotFoundError,
    ContentService,
)
from app.services.metric_service import (
    DuplicateMetricError,
    MetricContentNotFoundError,
    MetricNotFoundError,
    MetricService,
)


class ConteudosQueSomemAntesDaGravacao(InMemoryContentRepository):
    """Reproduz a corrida: o registro desaparece na janela exata."""

    def update(self, content):
        self._contents.pop(content.id, None)

        return super().update(content)


class MetricasQueSomemAntesDaGravacao(InMemoryMetricRepository):
    def update(self, metric):
        self._metrics.pop(metric.id, None)

        return super().update(metric)


def conteudo_de(repositorio, user_id=1):
    return repositorio.create(
        Content(
            id=None,
            usuario_id=user_id,
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


def test_repositorio_de_conteudo_em_memoria_nao_recria_o_que_sumiu():
    repositorio = InMemoryContentRepository()
    conteudo = conteudo_de(repositorio)

    repositorio.delete(conteudo)

    assert repositorio.update(conteudo) is None
    assert repositorio.get_by_id_and_user(conteudo.id, 1) is None


def test_repositorio_de_metrica_em_memoria_nao_recria_o_que_sumiu():
    conteudos = InMemoryContentRepository()
    conteudo = conteudo_de(conteudos)

    repositorio = InMemoryMetricRepository()
    metrica = metrica_de(repositorio, conteudo.id)

    repositorio.delete(metrica)

    assert repositorio.update(metrica) is None
    assert (
        repositorio.get_by_id_and_content(metrica.id, conteudo.id) is None
    )


def test_editar_conteudo_que_sumiu_avisa_em_vez_de_fingir_que_salvou():
    repositorio = ConteudosQueSomemAntesDaGravacao()
    conteudo = conteudo_de(repositorio)

    servico = ContentService(repositorio, InMemoryMetricRepository())

    with pytest.raises(ContentNotFoundError):
        servico.update(
            content_id=conteudo.id,
            user_id=1,
            titulo="Título novo",
        )


def test_corrigir_metrica_que_sumiu_avisa_em_vez_de_fingir_que_salvou():
    conteudos = InMemoryContentRepository()
    conteudo = conteudo_de(conteudos)

    metricas = MetricasQueSomemAntesDaGravacao()
    metrica = metrica_de(metricas, conteudo.id)

    servico = MetricService(
        content_repository=conteudos,
        metric_repository=metricas,
    )

    with pytest.raises(MetricNotFoundError):
        servico.update(
            user_id=1,
            content_id=conteudo.id,
            metric_id=metrica.id,
            alcance=999,
        )


class MetricasQueConflitamAoGravar(InMemoryMetricRepository):
    """O banco recusa a gravação, sem dizer qual constraint falhou."""

    def create(self, metric):
        raise MetricPersistenceConflictError("Conflito ao persistir.")


class ConteudosQueSomemDepoisDaChecagem(InMemoryContentRepository):
    """O conteúdo existe na checagem de posse e some logo em seguida."""

    def get_by_id_and_user(self, content_id, user_id):
        content = super().get_by_id_and_user(content_id, user_id)

        self._contents.pop(content_id, None)

        return content


def nova_medicao(servico, conteudo_id):
    return servico.create(
        user_id=1,
        content_id=conteudo_id,
        visualizacoes=100,
        curtidas=10,
        comentarios=1,
        compartilhamentos=1,
        alcance=80,
        data_referencia=date.today(),
    )


def test_conflito_com_conteudo_sumido_avisa_nao_encontrado():
    conteudos = ConteudosQueSomemDepoisDaChecagem()
    conteudo = conteudo_de(conteudos)

    servico = MetricService(
        content_repository=conteudos,
        metric_repository=MetricasQueConflitamAoGravar(),
    )

    # A gravação falhou na chave estrangeira, não na data repetida. Dizer
    # "medição duplicada" mandaria o usuário editar uma medição de um
    # conteúdo que já não existe.
    with pytest.raises(MetricContentNotFoundError):
        nova_medicao(servico, conteudo.id)


def test_conflito_com_conteudo_presente_e_medicao_duplicada():
    conteudos = InMemoryContentRepository()
    conteudo = conteudo_de(conteudos)

    servico = MetricService(
        content_repository=conteudos,
        metric_repository=MetricasQueConflitamAoGravar(),
    )

    with pytest.raises(DuplicateMetricError):
        nova_medicao(servico, conteudo.id)
