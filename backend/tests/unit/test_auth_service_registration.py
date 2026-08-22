import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.security.password import PasswordService
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError
from app.security.jwt import TokenService


def make_service():
    repository = InMemoryUserRepository()
    password_service = PasswordService()
    return (
    AuthService(
        repository,
        password_service,
        TokenService(
            "test-secret-key-with-at-least-32-bytes",
            "HS256",
            30,
        ),
    ),
    repository,
    password_service,
)


def test_register_normalizes_user_and_hashes_password():
    service, repository, password_service = make_service()

    user = service.register(
        "  Carlos Ramon  ",
        "  CARLOS@EMAIL.COM  ",
        "minhasenha",
    )

    assert user.id == 1
    assert user.nome == "Carlos Ramon"
    assert user.email == "carlos@email.com"
    assert user.senha_hash != "minhasenha"
    assert password_service.verify("minhasenha", user.senha_hash)
    assert repository.get_by_email("carlos@email.com") == user


def test_register_rejects_duplicate_email_case_insensitively():
    service, _, _ = make_service()

    service.register(
        "Carlos",
        "carlos@email.com",
        "minhasenha",
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(
            "Outro",
            "CARLOS@email.com",
            "outrasenha",
        )
