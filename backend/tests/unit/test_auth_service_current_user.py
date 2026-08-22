import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, UnauthenticatedError


TEST_SECRET = "test-secret-key-with-at-least-32-bytes"


def make_service():
    repository = InMemoryUserRepository()
    tokens = TokenService(
        TEST_SECRET,
        "HS256",
        30,
    )

    service = AuthService(
        repository,
        PasswordService(),
        tokens,
    )

    return service, repository, tokens


def test_get_current_user_returns_token_subject_user():
    service, _, tokens = make_service()

    user = service.register(
        "Carlos",
        "carlos@email.com",
        "minhasenha",
    )

    token = tokens.create_access_token(user.id)

    current_user = service.get_current_user(token)

    assert current_user == user


def test_get_current_user_rejects_invalid_token():
    service, _, _ = make_service()

    with pytest.raises(UnauthenticatedError):
        service.get_current_user(
            "token-invalido"
        )


def test_get_current_user_rejects_token_for_missing_user():
    service, _, tokens = make_service()

    token = tokens.create_access_token(999)

    with pytest.raises(UnauthenticatedError):
        service.get_current_user(token)