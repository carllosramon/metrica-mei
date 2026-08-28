import pytest

from app.repositories.in_memory_user_repository import InMemoryUserRepository
from app.repositories.user_repository import UserPersistenceConflictError
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidRegistrationError,
)


TEST_SECRET = "test-secret-key-with-at-least-32-bytes"


def make_service():
    repository = InMemoryUserRepository()
    password_service = PasswordService()

    service = AuthService(
        repository,
        password_service,
        TokenService(
            TEST_SECRET,
            "HS256",
            30,
        ),
    )

    return service, repository, password_service


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
    assert password_service.verify(
        "minhasenha",
        user.senha_hash,
    )
    assert repository.get_by_email(
        "carlos@email.com"
    ) == user


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


@pytest.mark.parametrize(
    "nome",
    [
        "",
        "A",
        " A ",
        "A" * 101,
    ],
)
def test_register_rejects_invalid_name(nome):
    service, _, _ = make_service()

    with pytest.raises(InvalidRegistrationError):
        service.register(
            nome,
            "carlos@email.com",
            "minhasenha",
        )


@pytest.mark.parametrize(
    "senha",
    [
        "",
        "1234567",
        "A" * 129,
    ],
)
def test_register_rejects_invalid_password(senha):
    service, _, _ = make_service()

    with pytest.raises(InvalidRegistrationError):
        service.register(
            "Carlos",
            "carlos@email.com",
            senha,
        )


def test_register_translates_persistence_email_conflict():
    class ConflictingUserRepository(InMemoryUserRepository):
        def get_by_email(self, email):
            return None

        def create(self, user):
            raise UserPersistenceConflictError

    service = AuthService(
        ConflictingUserRepository(),
        PasswordService(),
        TokenService(
            TEST_SECRET,
            "HS256",
            30,
        ),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(
            "Carlos",
            "carlos@email.com",
            "minhasenha",
        )
