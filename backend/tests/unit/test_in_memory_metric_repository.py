from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.metric import Metric
from app.repositories.in_memory_metric_repository import (
    InMemoryMetricRepository,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


def test_create_assigns_id_and_get_reads_same_metric():
    repository = InMemoryMetricRepository()

    metric = Metric(
        id=None,
        conteudo_id=1,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
        criado_em=datetime.now(timezone.utc),
    )

    created = repository.create(metric)

    loaded = repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    )

    assert created.id == 1
    assert loaded == created

def test_list_by_content_filters_and_orders_descending():
    repository = InMemoryMetricRepository()

    older = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=(
                date.today() - timedelta(days=2)
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )

    newer = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=200,
            curtidas=20,
            comentarios=4,
            compartilhamentos=6,
            alcance=160,
            data_referencia=(
                date.today() - timedelta(days=1)
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )

    repository.create(
        Metric(
            id=None,
            conteudo_id=2,
            visualizacoes=300,
            curtidas=30,
            comentarios=6,
            compartilhamentos=9,
            alcance=240,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    result = repository.list_by_content(1)

    assert [metric.id for metric in result] == [
        newer.id,
        older.id,
    ]

def test_get_by_content_and_reference_date_finds_snapshot():
    repository = InMemoryMetricRepository()

    created = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    loaded = repository.get_by_content_and_reference_date(
        created.conteudo_id,
        created.data_referencia,
    )

    assert loaded == created

def test_duplicate_content_and_date_raises_persistence_conflict():
    repository = InMemoryMetricRepository()

    first = Metric(
        id=None,
        conteudo_id=1,
        visualizacoes=100,
        curtidas=10,
        comentarios=2,
        compartilhamentos=3,
        alcance=80,
        data_referencia=date.today(),
        criado_em=datetime.now(timezone.utc),
    )

    duplicate = Metric(
        id=None,
        conteudo_id=1,
        visualizacoes=200,
        curtidas=20,
        comentarios=4,
        compartilhamentos=6,
        alcance=160,
        data_referencia=date.today(),
        criado_em=datetime.now(timezone.utc),
    )

    repository.create(first)

    with pytest.raises(
        MetricPersistenceConflictError
    ):
        repository.create(duplicate)

def test_update_replaces_existing_metric():
    repository = InMemoryMetricRepository()

    created = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    updated = repository.update(
        replace(
            created,
            alcance=999,
        )
    )

    loaded = repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    )

    assert updated.id == created.id
    assert updated.alcance == 999
    assert loaded is not None
    assert loaded.alcance == 999

def test_update_rejects_date_collision():
    repository = InMemoryMetricRepository()

    first = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=(
                date.today() - timedelta(days=1)
            ),
            criado_em=datetime.now(timezone.utc),
        )
    )

    second = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=200,
            curtidas=20,
            comentarios=4,
            compartilhamentos=6,
            alcance=160,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    with pytest.raises(
        MetricPersistenceConflictError
    ):
        repository.update(
            replace(
                second,
                data_referencia=(
                    first.data_referencia
                ),
            )
        )

def test_delete_removes_metric():
    repository = InMemoryMetricRepository()

    created = repository.create(
        Metric(
            id=None,
            conteudo_id=1,
            visualizacoes=100,
            curtidas=10,
            comentarios=2,
            compartilhamentos=3,
            alcance=80,
            data_referencia=date.today(),
            criado_em=datetime.now(timezone.utc),
        )
    )

    repository.delete(created)

    loaded = repository.get_by_id_and_content(
        created.id,
        created.conteudo_id,
    )

    assert loaded is None
