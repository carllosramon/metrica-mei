import pytest

from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, InvalidCredentialsError
from tests.dubles.in_memory_user_repository import InMemoryUserRepository


def make_service():
    repository = InMemoryUserRepository()
    service = AuthService(
        repository,
        PasswordService(),
        TokenService(
            "test-secret-key-with-at-least-32-bytes",
            "HS256",
            30,
        ),
    )

    service.register(
        "Carlos",
        "carlos@email.com",
        "minhasenha",
    )

    return service


def test_login_returns_token_for_valid_credentials():
    token = make_service().login(
        "CARLOS@EMAIL.COM",
        "minhasenha",
    )

    assert isinstance(token, str)
    assert token


def test_login_rejects_wrong_password():
    with pytest.raises(InvalidCredentialsError):
        make_service().login(
            "carlos@email.com",
            "senhaerrada",
        )


def test_login_rejects_unknown_email():
    with pytest.raises(InvalidCredentialsError):
        make_service().login(
            "ninguem@email.com",
            "minhasenha",
        )
