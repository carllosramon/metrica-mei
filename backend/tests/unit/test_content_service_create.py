from datetime import date, datetime, timedelta

import pytest

from app.repositories.in_memory_content_repository import (
    InMemoryContentRepository,
)
from app.services.content_service import (
    ContentService,
    InvalidContentError,
)


def make_service():
    repository = InMemoryContentRepository()
    service = ContentService(repository)

    return service, repository


def test_create_normalizes_text_and_assigns_user():
    service, repository = make_service()

    content = service.create(
        user_id=7,
        titulo="  Meu conteúdo  ",
        plataforma="  Instagram  ",
        tipo="  Reels  ",
        data_publicacao=date.today(),
    )

    assert content.id == 1
    assert content.usuario_id == 7
    assert content.titulo == "Meu conteúdo"
    assert content.plataforma == "Instagram"
    assert content.tipo == "Reels"
    assert content.data_publicacao == date.today()
    assert repository.get_by_id_and_user(
        1,
        7,
    ) == content


def test_create_rejects_empty_title_after_normalization():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="   ",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
        )


def test_create_rejects_title_longer_than_200_characters():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="A" * 201,
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today(),
        )


def test_create_rejects_empty_platform_after_normalization():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo válido",
            plataforma="   ",
            tipo="Reels",
            data_publicacao=date.today(),
        )


def test_create_rejects_platform_longer_than_50_characters():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo válido",
            plataforma="A" * 51,
            tipo="Reels",
            data_publicacao=date.today(),
        )


def test_create_rejects_empty_type_after_normalization():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo válido",
            plataforma="Instagram",
            tipo="   ",
            data_publicacao=date.today(),
        )


def test_create_rejects_type_longer_than_50_characters():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo válido",
            plataforma="Instagram",
            tipo="A" * 51,
            data_publicacao=date.today(),
        )


def test_create_rejects_future_publication_date():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo futuro",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=date.today() + timedelta(days=1),
        )


def test_create_accepts_past_publication_date():
    service, _ = make_service()

    past_date = date.today() - timedelta(days=30)

    content = service.create(
        user_id=1,
        titulo="Conteúdo antigo",
        plataforma="Instagram",
        tipo="Carrossel",
        data_publicacao=past_date,
    )

    assert content.data_publicacao == past_date


def test_create_rejects_datetime_as_publication_date():
    service, _ = make_service()

    with pytest.raises(InvalidContentError):
        service.create(
            user_id=1,
            titulo="Conteúdo válido",
            plataforma="Instagram",
            tipo="Reels",
            data_publicacao=datetime.now(),
        )
