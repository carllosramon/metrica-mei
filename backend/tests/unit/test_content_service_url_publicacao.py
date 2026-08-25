from datetime import date

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
    return ContentService(repository)


def create_content(
    service,
    url_publicacao=None,
):
    return service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
        url_publicacao=url_publicacao,
    )


def test_create_stores_publication_url():
    service = make_service()

    content = create_content(
        service,
        "https://instagram.com/p/abc123",
    )

    assert content.url_publicacao == "https://instagram.com/p/abc123"


def test_create_without_url_keeps_field_empty():
    service = make_service()

    content = service.create(
        user_id=1,
        titulo="Meu conteúdo",
        plataforma="Instagram",
        tipo="Reels",
        data_publicacao=date.today(),
    )

    assert content.url_publicacao is None


def test_create_strips_surrounding_spaces_from_url():
    service = make_service()

    content = create_content(
        service,
        "   https://tiktok.com/@perfil/video/1   ",
    )

    assert content.url_publicacao == "https://tiktok.com/@perfil/video/1"


def test_create_rejects_url_without_http_scheme():
    service = make_service()

    with pytest.raises(InvalidContentError):
        create_content(
            service,
            "instagram.com/p/abc123",
        )


def test_create_rejects_url_longer_than_limit():
    service = make_service()

    long_url = "https://instagram.com/p/" + "a" * 500

    with pytest.raises(InvalidContentError):
        create_content(
            service,
            long_url,
        )


def test_update_sets_publication_url():
    service = make_service()

    content = create_content(service)

    updated = service.update(
        content_id=content.id,
        user_id=1,
        url_publicacao="https://instagram.com/p/abc123",
    )

    assert updated.url_publicacao == "https://instagram.com/p/abc123"


def test_update_changes_existing_publication_url():
    service = make_service()

    content = create_content(
        service,
        "https://instagram.com/p/antigo",
    )

    updated = service.update(
        content_id=content.id,
        user_id=1,
        url_publicacao="https://instagram.com/p/novo",
    )

    assert updated.url_publicacao == "https://instagram.com/p/novo"


def test_update_clears_publication_url_with_explicit_none():
    service = make_service()

    content = create_content(
        service,
        "https://instagram.com/p/abc123",
    )

    updated = service.update(
        content_id=content.id,
        user_id=1,
        url_publicacao=None,
    )

    assert updated.url_publicacao is None


def test_update_keeps_url_when_field_is_not_informed():
    service = make_service()

    content = create_content(
        service,
        "https://instagram.com/p/abc123",
    )

    updated = service.update(
        content_id=content.id,
        user_id=1,
        titulo="Outro título",
    )

    assert updated.url_publicacao == "https://instagram.com/p/abc123"


def test_update_rejects_url_without_http_scheme():
    service = make_service()

    content = create_content(service)

    with pytest.raises(InvalidContentError):
        service.update(
            content_id=content.id,
            user_id=1,
            url_publicacao="instagram.com/p/abc123",
        )
