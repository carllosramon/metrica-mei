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


def test_create_metric_for_owned_content():
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

    assert created.id == 1
    assert created.conteudo_id == content.id
    assert created.visualizacoes == 100
    assert created.curtidas == 10
    assert created.comentarios == 2
    assert created.compartilhamentos == 3
    assert created.alcance == 80
    assert created.data_referencia == date.today()
    assert created.criado_em.tzinfo is not None

def test_create_rejects_missing_content():
    service = MetricService(
        content_repository=InMemoryContentRepository(),
        metric_repository=InMemoryMetricRepository(),
    )

    with pytest.raises(Exception) as exc_info:
        service.create(
            user_id=1,
            content_id=999,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "MetricContentNotFoundError"
    )
    assert str(exc_info.value) == "Conteúdo não encontrado."

def test_create_rejects_negative_visualizacoes():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=-1,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_negative_curtidas():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=-1,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_negative_comentarios():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=-1,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_negative_compartilhamentos():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=-1,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_negative_alcance():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=-1,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_boolean_visualizacoes():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=True,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_boolean_curtidas():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=True,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_boolean_comentarios():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=True,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_boolean_compartilhamentos():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=True,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_boolean_alcance():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=True,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_reference_date_before_publication():
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

    publication_date = date.today()

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

    with pytest.raises(Exception) as exc_info:
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=(
                publication_date - timedelta(days=1)
            ),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_future_reference_date():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=(
                date.today() + timedelta(days=1)
            ),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

def test_create_rejects_duplicate_reference_date():
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

    service.create(
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=200,
            curtidas=20,
            comentarios=4,
            compartilhamentos=6,
            alcance=160,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )

def test_create_rejects_datetime_as_reference_date():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=datetime.now(timezone.utc),
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )

@pytest.mark.parametrize(
    "field_name",
    [
        "visualizacoes",
        "curtidas",
        "comentarios",
        "compartilhamentos",
        "alcance",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        1.5,
        "10",
        None,
    ],
)
def test_create_rejects_non_integer_metric_values(
    field_name,
    invalid_value,
):
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

    values = {
        "visualizacoes": 100,
        "curtidas": 10,
        "comentarios": 2,
        "compartilhamentos": 3,
        "alcance": 80,
    }

    values[field_name] = invalid_value

    with pytest.raises(Exception) as exc_info:
        service.create(
            user_id=1,
            content_id=content.id,
            data_referencia=date.today(),
            **values,
        )

    assert (
        exc_info.type.__name__
        == "InvalidMetricError"
    )


def test_create_accepts_zero_for_all_metric_values():
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
        visualizacoes=0,
        curtidas=0,
        comentarios=0,
        compartilhamentos=0,
        alcance=0,
        data_referencia=date.today(),
    )

    assert created.visualizacoes == 0
    assert created.curtidas == 0
    assert created.comentarios == 0
    assert created.compartilhamentos == 0
    assert created.alcance == 0

def test_create_checks_duplicate_before_persisting():
    class GuardedMetricRepository(
        InMemoryMetricRepository
    ):
        def __init__(self):
            super().__init__()
            self.block_create = False

        def create(self, metric):
            if self.block_create:
                raise AssertionError(
                    "create não deveria ser chamado"
                )

            return super().create(metric)

    content_repository = InMemoryContentRepository()
    metric_repository = GuardedMetricRepository()

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

    service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
    )

    metric_repository.block_create = True

    with pytest.raises(Exception) as exc_info:
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=200,
            curtidas=20,
            comentarios=4,
            compartilhamentos=6,
            alcance=160,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )

def test_create_checks_content_ownership_before_metric_validation():
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
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=-1,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "MetricContentNotFoundError"
    )
    assert str(exc_info.value) == "Conteúdo não encontrado."

def test_create_translates_persistence_conflict():
    class ConflictingMetricRepository(
        InMemoryMetricRepository
    ):
        def get_by_content_and_reference_date(
            self,
            content_id,
            data_referencia,
        ):
            return None

        def create(self, metric):
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

    with pytest.raises(Exception) as exc_info:
        service.create(
            user_id=1,
            content_id=content.id,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
        )

    assert (
        exc_info.type.__name__
        == "DuplicateMetricError"
    )
    assert str(exc_info.value) == (
        "Já existe uma métrica para este conteúdo nesta data."
    )
