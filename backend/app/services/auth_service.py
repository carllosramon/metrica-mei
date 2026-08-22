from datetime import datetime, timezone

from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.security.password import PasswordService


class EmailAlreadyRegisteredError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        password_service: PasswordService,
    ):
        self._repository = repository
        self._password_service = password_service

    def register(
        self,
        nome: str,
        email: str,
        senha: str,
    ) -> User:
        normalized_name = nome.strip()
        normalized_email = email.strip().lower()

        if self._repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            id=None,
            nome=normalized_name,
            email=normalized_email,
            senha_hash=self._password_service.hash(senha),
            criado_em=datetime.now(timezone.utc),
        )

        return self._repository.create(user)