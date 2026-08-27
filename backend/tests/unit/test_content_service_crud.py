from datetime import date, timedelta

import pytest

from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.services.content_service import (
    ContentNotFoundError,
    InvalidContentError,
    ContentService,
)


def make_service():
    repository = InMemoryContentRepository()
    service = ContentService(repository)
    return service, repository


def test_list_returns_only_user_contents_ordered_by_date_and_id_desc():
    service, _ = make_service()

    older = service.create(
        user_id=1,
        titulo="Conteúdo antigo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today() - timedelta(days=2),
    )

    service.create(
        user_id=2,
        titulo="Conteúdo de outro usuário",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today() - timedelta(days=1),
    )

    same_date_first = service.create(
        user_id=1,
        titulo="Primeiro do mesmo dia",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today() - timedelta(days=1),
    )

    same_date_second = service.create(
        user_id=1,
        titulo="Segundo do mesmo dia",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today() - timedelta(days=1),
    )

    contents = service.list(user_id=1)

    assert [content.id for content in contents] == [
        same_date_second.id,
        same_date_first.id,
        older.id,
    ]


def test_get_returns_content_owned_by_user():
    service, _ = make_service()

    created = service.create(
        user_id=7,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
    )

    content = service.get(
        content_id=created.id,
        user_id=7,
    )

    assert content == created


def test_get_raises_content_not_found_for_missing_content():
    service, _ = make_service()

    with pytest.raises(ContentNotFoundError):
        service.get(
            content_id=999,
            user_id=1,
        )


def test_get_raises_content_not_found_for_content_owned_by_another_user():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Conteúdo privado",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
    )

    with pytest.raises(ContentNotFoundError):
        service.get(
            content_id=created.id,
            user_id=2,
        )


def test_update_changes_only_provided_title():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Título antigo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today() - timedelta(days=1),
    )

    updated = service.update(
        content_id=created.id,
        user_id=1,
        titulo="  Título novo  ",
    )

    assert updated.id == created.id
    assert updated.usuario_id == created.usuario_id
    assert updated.titulo == "Título novo"
    assert updated.plataforma == created.plataforma
    assert updated.tipo == created.tipo
    assert updated.data_publicacao == created.data_publicacao
    assert updated.criado_em == created.criado_em
    assert service.get(
        content_id=created.id,
        user_id=1,
    ) == updated


def test_update_changes_only_provided_platform():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    updated = service.update(
        content_id=created.id,
        user_id=1,
        plataforma="  TikTok  ",
    )

    assert updated.id == created.id
    assert updated.usuario_id == created.usuario_id
    assert updated.titulo == created.titulo
    assert updated.plataforma == "TikTok"
    assert updated.tipo == created.tipo
    assert updated.data_publicacao == created.data_publicacao
    assert updated.criado_em == created.criado_em


def test_update_changes_only_provided_type():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    updated = service.update(
        content_id=created.id,
        user_id=1,
        tipo="  Reels  ",
    )

    assert updated.id == created.id
    assert updated.usuario_id == created.usuario_id
    assert updated.titulo == created.titulo
    assert updated.plataforma == created.plataforma
    assert updated.tipo == "Reels"
    assert updated.data_publicacao == created.data_publicacao
    assert updated.criado_em == created.criado_em


def test_update_changes_only_provided_publication_date():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today() - timedelta(days=5),
    )

    new_date = date.today() - timedelta(days=1)

    updated = service.update(
        content_id=created.id,
        user_id=1,
        data_publicacao=new_date,
    )

    assert updated.id == created.id
    assert updated.usuario_id == created.usuario_id
    assert updated.titulo == created.titulo
    assert updated.plataforma == created.plataforma
    assert updated.tipo == created.tipo
    assert updated.data_publicacao == new_date
    assert updated.criado_em == created.criado_em


def test_update_rejects_empty_changes():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    with pytest.raises(InvalidContentError):
        service.update(
            content_id=created.id,
            user_id=1,
        )


def test_update_rejects_explicit_null_field():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    with pytest.raises(InvalidContentError):
        service.update(
            content_id=created.id,
            user_id=1,
            titulo=None,
            plataforma="TikTok",
        )


def test_update_rejects_null_publication_date():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    with pytest.raises(InvalidContentError):
        service.update(
            content_id=created.id,
            user_id=1,
            data_publicacao=None,
        )


def test_delete_removes_content_owned_by_user():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Conteúdo para excluir",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    service.delete(
        content_id=created.id,
        user_id=1,
    )

    with pytest.raises(ContentNotFoundError):
        service.get(
            content_id=created.id,
            user_id=1,
        )


def test_delete_raises_content_not_found_for_missing_content():
    service, _ = make_service()

    with pytest.raises(ContentNotFoundError):
        service.delete(
            content_id=999,
            user_id=1,
        )


def test_delete_raises_content_not_found_for_content_owned_by_another_user():
    service, _ = make_service()

    created = service.create(
        user_id=1,
        titulo="Conteúdo privado",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=date.today(),
    )

    with pytest.raises(ContentNotFoundError):
        service.delete(
            content_id=created.id,
            user_id=2,
        )

    assert service.get(
        content_id=created.id,
        user_id=1,
    ) == created
