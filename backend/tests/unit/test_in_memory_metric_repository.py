from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)
from tests.dubles.in_memory_metric_repository import (
    InMemoryMetricRepository,
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


def test_latest_by_contents_picks_the_most_recent_of_each():
    repository = InMemoryMetricRepository()

    hoje = date.today()

    def criar(conteudo_id, data_referencia, alcance):
        return repository.create(
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

    criar(1, hoje - timedelta(days=2), 100)
    criar(1, hoje, 300)
    criar(1, hoje - timedelta(days=1), 200)
    criar(2, hoje - timedelta(days=5), 50)

    mais_recentes = repository.latest_by_contents([1, 2, 3])

    # A ordem de inserção não é a ordem das datas: o que decide é a data
    # de referência, como no repositório do SQLAlchemy.
    assert mais_recentes[1].alcance == 300
    assert mais_recentes[2].alcance == 50

    # Conteúdo sem medição não aparece no resultado.
    assert set(mais_recentes) == {1, 2}


def test_latest_by_contents_with_no_ids_returns_empty():
    repository = InMemoryMetricRepository()

    assert repository.latest_by_contents([]) == {}
