from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import importlib
import importlib.util

from app.database.models import UserModel
from app.domain.content import Content


def get_repository_class():
    module_name = (
        "app.repositories.sqlalchemy_content_repository"
    )

    spec = importlib.util.find_spec(module_name)

    assert spec is not None

    module = importlib.import_module(module_name)

    repository_class = getattr(
        module,
        "SQLAlchemyContentRepository",
        None,
    )

    assert repository_class is not None

    return repository_class


def test_sqlalchemy_content_repository_persists_and_reads_content(
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

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Meu conteúdo",
                plataforma="Instagram",
                tipo="Reels",
                data_publicacao=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        loaded = repository.get_by_id_and_user(
            created.id,
            owner.id,
        )

    assert created.id is not None
    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.usuario_id == owner.id
    assert loaded.titulo == "Meu conteúdo"
    assert loaded.plataforma == "Instagram"
    assert loaded.tipo == "Reels"
    assert loaded.data_publicacao == date.today()


def test_sqlalchemy_content_repository_lists_only_user_contents_in_expected_order(
    session_factory,
):
    with session_factory() as session:
        owner = UserModel(
            nome="Carlos",
            email="carlos@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        other_owner = UserModel(
            nome="Outro",
            email="outro@email.com",
            senha_hash="hash",
            criado_em=datetime.now(timezone.utc),
        )

        session.add_all([
            owner,
            other_owner,
        ])
        session.commit()
        session.refresh(owner)
        session.refresh(other_owner)

        repository_class = get_repository_class()
        repository = repository_class(session)

        older = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Conteúdo antigo",
                plataforma="Instagram",
                tipo="Carrossel",
                data_publicacao=date.today() - timedelta(days=2),
                criado_em=datetime.now(timezone.utc),
            )
        )

        repository.create(
            Content(
                id=None,
                usuario_id=other_owner.id,
                titulo="Conteúdo de outro usuário",
                plataforma="Instagram",
                tipo="Reels",
                data_publicacao=date.today() - timedelta(days=1),
                criado_em=datetime.now(timezone.utc),
            )
        )

        same_date_first = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Primeiro do mesmo dia",
                plataforma="Instagram",
                tipo="Reels",
                data_publicacao=date.today() - timedelta(days=1),
                criado_em=datetime.now(timezone.utc),
            )
        )

        same_date_second = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Segundo do mesmo dia",
                plataforma="Instagram",
                tipo="Reels",
                data_publicacao=date.today() - timedelta(days=1),
                criado_em=datetime.now(timezone.utc),
            )
        )

        contents = repository.list_by_user(owner.id)

    assert [content.id for content in contents] == [
        same_date_second.id,
        same_date_first.id,
        older.id,
    ]


def test_sqlalchemy_content_repository_persists_update(
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

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Título antigo",
                plataforma="Instagram",
                tipo="Carrossel",
                data_publicacao=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        changed = replace(
            created,
            titulo="Título novo",
            plataforma="TikTok",
        )

        updated = repository.update(changed)

        loaded = repository.get_by_id_and_user(
            created.id,
            owner.id,
        )

    assert updated.titulo == "Título novo"
    assert updated.plataforma == "TikTok"

    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.titulo == "Título novo"
    assert loaded.plataforma == "TikTok"
    assert loaded.tipo == created.tipo
    assert loaded.data_publicacao == created.data_publicacao


def test_sqlalchemy_content_repository_deletes_content(
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

        repository_class = get_repository_class()
        repository = repository_class(session)

        created = repository.create(
            Content(
                id=None,
                usuario_id=owner.id,
                titulo="Conteúdo para excluir",
                plataforma="Instagram",
                tipo="Reels",
                data_publicacao=date.today(),
                criado_em=datetime.now(timezone.utc),
            )
        )

        repository.delete(created)

        loaded = repository.get_by_id_and_user(
            created.id,
            owner.id,
        )

    assert loaded is None
