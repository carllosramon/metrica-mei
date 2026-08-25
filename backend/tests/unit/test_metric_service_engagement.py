from datetime import date, datetime, timedelta, timezone

from app.domain.content import Content
from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.services.metric_service import MetricService


def build_service_with_content(publication_date):
    content_repository = InMemoryContentRepository()
    metric_repository = InMemoryMetricRepository()

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

    return service, content


def test_create_returns_metric_with_engagement():
    service, content = build_service_with_content(date.today())

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=2000,
        curtidas=110,
        comentarios=14,
        compartilhamentos=22,
        alcance=1450,
        data_referencia=date.today(),
    )

    assert created.engajamento == 10.07


def test_get_returns_metric_with_engagement():
    service, content = build_service_with_content(date.today())

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=500,
        curtidas=20,
        comentarios=5,
        compartilhamentos=5,
        alcance=300,
        data_referencia=date.today(),
    )

    found = service.get(
        user_id=1,
        content_id=content.id,
        metric_id=created.id,
    )

    assert found.engajamento == 10.0


def test_list_calculates_engagement_per_metric_keeping_order():
    publication_date = date.today() - timedelta(days=1)

    service, content = build_service_with_content(publication_date)

    service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=100,
        curtidas=5,
        comentarios=3,
        compartilhamentos=2,
        alcance=200,
        data_referencia=publication_date,
    )

    service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=400,
        curtidas=30,
        comentarios=10,
        compartilhamentos=10,
        alcance=250,
        data_referencia=date.today(),
    )

    metrics = service.list(
        user_id=1,
        content_id=content.id,
    )

    assert [metric.data_referencia for metric in metrics] == [
        date.today(),
        publication_date,
    ]

    assert metrics[0].engajamento == 20.0
    assert metrics[1].engajamento == 5.0


def test_update_recalculates_engagement():
    service, content = build_service_with_content(date.today())

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=500,
        curtidas=20,
        comentarios=5,
        compartilhamentos=5,
        alcance=300,
        data_referencia=date.today(),
    )

    assert created.engajamento == 10.0

    updated = service.update(
        user_id=1,
        content_id=content.id,
        metric_id=created.id,
        curtidas=140,
        alcance=1000,
    )

    assert updated.curtidas == 140
    assert updated.alcance == 1000
    assert updated.engajamento == 15.0


def test_engagement_is_none_when_reach_is_zero():
    service, content = build_service_with_content(date.today())

    created = service.create(
        user_id=1,
        content_id=content.id,
        visualizacoes=0,
        curtidas=10,
        comentarios=2,
        compartilhamentos=1,
        alcance=0,
        data_referencia=date.today(),
    )

    assert created.engajamento is None
