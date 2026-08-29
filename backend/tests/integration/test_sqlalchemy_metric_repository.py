from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import importlib
import importlib.util

import pytest

from app.database.models import (
    ContentModel,
    UserModel,
)
from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


def get_repository_class():
    module_name = (
        "app.repositories.sqlalchemy_metric_repository"
    )

    spec = importlib.util.find_spec(module_name)

    assert spec is not None

    module = importlib.import_module(module_name)

    repository_class = getattr(
        module,
        "SQLAlchemyMetricRepository",
        None,
    )

    assert repository_class is not None

    return repository_class


def test_sqlalchemy_metric_repository_persists_and_reads_metric(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Meu conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=1000,
                curtidas=120,
                comentarios=15,
                compartilhamentos=8,
                alcance=800,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        loaded = repository.get_by_id_and_content(
            created.id,
            content.id,
        )

    assert created.id is not None
    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.conteudo_id == content.id
    assert loaded.visualizacoes == 1000
    assert loaded.curtidas == 120
    assert loaded.comentarios == 15
    assert loaded.compartilhamentos == 8
    assert loaded.alcance == 800
    assert loaded.data_referencia == date.today()

def test_sqlalchemy_metric_repository_lists_content_metrics_in_expected_order(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo principal",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        other_content = ContentModel(
            usuario_id=owner.id,
            titulo="Outro conteúdo",
            plataforma="TikTok",
            tipo="Vídeo",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        session.add_all([
            content,
            other_content,
        ])
        session.commit()
        session.refresh(content)
        session.refresh(other_content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        older = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=date.today() - timedelta(days=2),
                criado_em=datetime.now(timezone.utc),
            )
        )

        newer = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=200,
                curtidas=20,
                comentarios=2,
                compartilhamentos=2,
                alcance=160,
                data_referencia=date.today() - timedelta(days=1),
                criado_em=datetime.now(timezone.utc),
            )
        )

        repository.create(
            Metric(
                id=None,
                conteudo_id=other_content.id,
                visualizacoes=999,
                curtidas=99,
                comentarios=9,
                compartilhamentos=9,
                alcance=900,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        metrics = repository.list_by_content(
            content.id
        )

    assert [metric.id for metric in metrics] == [
        newer.id,
        older.id,
    ]

def test_sqlalchemy_metric_repository_gets_metric_by_content_and_reference_date(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo principal",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        other_content = ContentModel(
            usuario_id=owner.id,
            titulo="Outro conteúdo",
            plataforma="TikTok",
            tipo="Vídeo",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        session.add_all([
            content,
            other_content,
        ])
        session.commit()
        session.refresh(content)
        session.refresh(other_content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        reference_date = (
            date.today() - timedelta(days=1)
        )

        expected = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=300,
                curtidas=30,
                comentarios=3,
                compartilhamentos=2,
                alcance=250,
                data_referencia=reference_date,
                criado_em=datetime.now(timezone.utc),
            )
        )

        repository.create(
            Metric(
                id=None,
                conteudo_id=other_content.id,
                visualizacoes=999,
                curtidas=99,
                comentarios=9,
                compartilhamentos=9,
                alcance=900,
                data_referencia=reference_date,
                criado_em=datetime.now(timezone.utc),
            )
        )

        loaded = (
            repository
            .get_by_content_and_reference_date(
                content.id,
                reference_date,
            )
        )

    assert loaded is not None
    assert loaded.id == expected.id
    assert loaded.conteudo_id == content.id
    assert loaded.data_referencia == reference_date

def test_sqlalchemy_metric_repository_persists_update(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=date.today() - timedelta(days=2),
                criado_em=datetime.now(timezone.utc),
            )
        )

        changed = replace(
            created,
            visualizacoes=500,
            curtidas=50,
            comentarios=7,
            compartilhamentos=4,
            alcance=400,
            data_referencia=date.today() - timedelta(days=1),
        )

        updated = repository.update(changed)

        loaded = repository.get_by_id_and_content(
            created.id,
            content.id,
        )

    assert updated.id == created.id
    assert updated.visualizacoes == 500
    assert updated.curtidas == 50
    assert updated.comentarios == 7
    assert updated.compartilhamentos == 4
    assert updated.alcance == 400
    assert (
        updated.data_referencia
        == date.today() - timedelta(days=1)
    )

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.visualizacoes == 500
    assert loaded.curtidas == 50
    assert loaded.comentarios == 7
    assert loaded.compartilhamentos == 4
    assert loaded.alcance == 400
    assert (
        loaded.data_referencia
        == date.today() - timedelta(days=1)
    )

def test_sqlalchemy_metric_repository_deletes_metric(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        repository.delete(created)

        loaded = repository.get_by_id_and_content(
            created.id,
            content.id,
        )

    assert loaded is None

def test_sqlalchemy_metric_repository_translates_create_unique_conflict(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        first = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        with pytest.raises(
            MetricPersistenceConflictError
        ):
            repository.create(
                Metric(
                    id=None,
                    conteudo_id=content.id,
                    visualizacoes=200,
                    curtidas=20,
                    comentarios=2,
                    compartilhamentos=2,
                    alcance=160,
                    data_referencia=date.today(),
                    criado_em=datetime.now(timezone.utc),
                )
            )

        loaded = repository.get_by_id_and_content(
            first.id,
            content.id,
        )

    assert loaded is not None
    assert loaded.id == first.id

def test_sqlalchemy_metric_repository_translates_create_unique_conflict(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        first = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        with pytest.raises(
            MetricPersistenceConflictError
        ):
            repository.create(
                Metric(
                    id=None,
                    conteudo_id=content.id,
                    visualizacoes=200,
                    curtidas=20,
                    comentarios=2,
                    compartilhamentos=2,
                    alcance=160,
                    data_referencia=date.today(),
                    criado_em=datetime.now(timezone.utc),
                )
            )

        loaded = repository.get_by_id_and_content(
            first.id,
            content.id,
        )

    assert loaded is not None
    assert loaded.id == first.id

def test_sqlalchemy_metric_repository_translates_update_unique_conflict(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add(owner)
        session.commit()
        session.refresh(owner)

        content = ContentModel(
            usuario_id=owner.id,
            titulo="Conteúdo",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() - timedelta(days=5),
            criado_em=datetime.now(timezone.utc),
        )

        session.add(content)
        session.commit()
        session.refresh(content)

        repository_class = get_repository_class()
        repository = repository_class(session)

        first_date = date.today() - timedelta(days=2)
        second_date = date.today() - timedelta(days=1)

        first = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=100,
                curtidas=10,
                comentarios=1,
                compartilhamentos=1,
                alcance=80,
                data_referencia=first_date,
                criado_em=datetime.now(timezone.utc),
            )
        )

        second = repository.create(
            Metric(
                id=None,
                conteudo_id=content.id,
                visualizacoes=200,
                curtidas=20,
                comentarios=2,
                compartilhamentos=2,
                alcance=160,
                data_referencia=second_date,
                criado_em=datetime.now(timezone.utc),
            )
        )

        conflicting = replace(
            second,
            data_referencia=first_date,
        )

        with pytest.raises(
            MetricPersistenceConflictError
        ):
            repository.update(conflicting)

        loaded_first = repository.get_by_id_and_content(
            first.id,
            content.id,
        )

        loaded_second = repository.get_by_id_and_content(
            second.id,
            content.id,
        )

    assert loaded_first is not None
    assert loaded_second is not None
    assert loaded_first.data_referencia == first_date
    assert loaded_second.data_referencia == second_date
