from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.content import Content
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)
from app.services.metric_service import MetricService


def test_list_returns_owned_content_metrics_in_descending_order():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    publication_date = (
        date.today() - timedelta(days=2)
    )

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=publication_date,
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    older = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=publication_date,
    )

    newer = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=200,
        curtidas=20,
        comentarios=4,
        compartilhamentos=6,
        alcance=160,
        data_referencia=(
            publication_date + timedelta(days=1)
        ),
    )

    result = service.list(
        user_id=1,
        content_id=content.id,
    )

    assert [metric.id for metric in result] == [
        newer.id,
        older.id,
    ]

def test_get_returns_metric_from_owned_content():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    loaded = service.get(
        user_id=1,
        content_id=content.id,
        metric_id=created.id,
    )

    assert loaded == created

def test_get_rejects_missing_metric():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    with pytest.raises(Exception) as exc_info:
        service.get(
            user_id=1,
            content_id=content.id,
            metric_id=999,
        )

    assert (
        exc_info.type.__name__
        == "MetricNotFoundError"
    )
    assert str(exc_info.value) == (
        "Métrica não encontrada."
    )

def test_update_changes_metric_from_owned_content():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    updated = service.update(
        user_id=1,
        content_id=content.id,
        metric_id=created.id,
        alcance=999,
    )

    assert updated.id == created.id
    assert updated.conteudo_id == created.conteudo_id
    assert updated.alcance == 999
    assert updated.visualizacoes == created.visualizacoes
    assert updated.curtidas == created.curtidas
    assert updated.comentarios == created.comentarios
    assert updated.compartilhamentos == created.compartilhamentos
    assert updated.data_referencia == created.data_referencia
    assert updated.criado_em == created.criado_em

def test_update_rejects_empty_changes():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_explicit_none():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            alcance=None,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_negative_metric_value():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            alcance=-1,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_negative_visualizacoes():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            visualizacoes=-1,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_negative_curtidas():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            curtidas=-1,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_negative_comentarios():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            comentarios=-1,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_negative_compartilhamentos():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            compartilhamentos=-1,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_reference_date_before_publication():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    publication_date = (
        date.today() - timedelta(days=1)
    )

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=publication_date,
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            data_referencia=(
                publication_date - timedelta(days=1)
            ),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_future_reference_date():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    publication_date = (
        date.today() - timedelta(days=1)
    )

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=publication_date,
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            data_referencia=(
                date.today() + timedelta(days=1)
            ),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_datetime_as_reference_date():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            data_referencia=datetime.now(timezone.utc),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_duplicate_reference_date():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    publication_date = (
        date.today() - timedelta(days=2)
    )

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=publication_date,
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    first = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=(
            publication_date + timedelta(days=1)
        ),
    )

    second = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=200,
        curtidas=20,
        comentarios=4,
        compartilhamentos=6,
        alcance=160,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=second.id,
            data_referencia=first.data_referencia,
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )

def test_update_checks_duplicate_before_persisting():
    class GuardedMetricRepository(
        InMemoryMetricRepository
    ):
        def __init__(self):
            super().__init__()
            self.block_update = False

        def update(self, metric):
            if self.block_update:
                raise AssertionError(
                    "update não deveria ser chamado"
                )

            return super().update(metric)

    content_repository = InMemoryContentRepository()
    metric_repository = GuardedMetricRepository()

    publication_date = (
        date.today() - timedelta(days=2)
    )

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=publication_date,
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    first = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=(
            publication_date + timedelta(days=1)
        ),
    )

    second = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=200,
        curtidas=20,
        comentarios=4,
        compartilhamentos=6,
        alcance=160,
        data_referencia=date.today(),
    )

    metric_repository.block_update = True

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=second.id,
            data_referencia=first.data_referencia,
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )

def test_update_rejects_immutable_id():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            id=999,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_immutable_conteudo_id():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            conteudo_id=999,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_update_rejects_immutable_criado_em():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            criado_em=(
                datetime.now(timezone.utc)
                + timedelta(days=1)
            ),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_delete_removes_metric_from_owned_content():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    result = service.delete(
        user_id=1,
        content_id=content.id,
        metric_id=created.id,
    )

    assert result is None

    with pytest.raises(Exception) as exc_info:
        service.get(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
        )

    assert (
        exc_info.type.__name__
        == "MetricNotFoundError"
    )

def test_list_rejects_content_from_another_user():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=2,
            titulo="Conteúdo de outro usuário",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    with pytest.raises(Exception) as exc_info:
        service.list(
            user_id=1,
            content_id=content.id,
        )

    assert (
        exc_info.type.__name__
        == "MetricContentNotFoundError"
    )
    assert str(exc_info.value) == (
        "Conteúdo não encontrado."
    )


def test_get_rejects_metric_from_another_content():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    first_content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Primeiro conteúdo",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    second_content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Segundo conteúdo",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=first_content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.get(
            user_id=1,
            content_id=second_content.id,
            metric_id=created.id,
        )

    assert (
        exc_info.type.__name__
        == "MetricNotFoundError"
    )
    assert str(exc_info.value) == (
        "Métrica não encontrada."
    )


def test_update_translates_persistence_conflict():
    class ConflictingMetricRepository(
        InMemoryMetricRepository
    ):
        def update(self, metric):
            raise MetricPersistenceConflictError

    content_repository = InMemoryContentRepository()
    metric_repository = ConflictingMetricRepository()

    content = content_repository.create(
        Content(
            id=None,
            usuario_id=1,
            titulo="Post sobre métricas",
            plataforma="Instagram",
            tipo="Carrossel",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    service = MetricService(
        content_repository=content_repository,
        metric_repository=metric_repository,
    )

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    with pytest.raises(Exception) as exc_info:
        service.update(
            user_id=1,
            content_id=content.id,
            metric_id=created.id,
            alcance=81,
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )
