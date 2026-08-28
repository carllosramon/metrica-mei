from datetime import datetime, timezone

from app.domain.user import User
from app.repositories.user_repository import (
    UserPersistenceConflictError,
    UserRepository,
)
from app.security.jwt import TokenService
from app.security.password import PasswordService


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidRegistrationError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UnauthenticatedError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        password_service: PasswordService,
        token_service: TokenService,
    ):
        self._repository = repository
        self._password_service = password_service
        self._token_service = token_service

    def register(
        self,
        nome: str,
        email: str,
        senha: str,
    ) -> User:
        # O e-mail é comparado sem diferenciar maiúsculas, então precisa
        # ser normalizado antes da busca de duplicata e antes de gravar:
        # senão Joao@ e joao@ criariam duas contas.
        normalized_name = nome.strip()
        normalized_email = email.strip().lower()

        if not 2 <= len(normalized_name) <= 100:
            raise InvalidRegistrationError

        if not 8 <= len(senha) <= 128:
            raise InvalidRegistrationError

        if self._repository.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegisteredError

        user = User(
            id=None,
            nome=normalized_name,
            email=normalized_email,
            senha_hash=self._password_service.hash(senha),
            criado_em=datetime.now(timezone.utc),
        )

        try:
            return self._repository.create(user)
        except UserPersistenceConflictError as exc:
            raise EmailAlreadyRegisteredError from exc

    def login(
        self,
        email: str,
        senha: str,
    ) -> str:
        normalized_email = email.strip().lower()

        user = self._repository.get_by_email(
            normalized_email
        )

        if user is None:
            raise InvalidCredentialsError

        if not self._password_service.verify(
            senha,
            user.senha_hash,
        ):
            raise InvalidCredentialsError

        if user.id is None:
            raise InvalidCredentialsError

        return self._token_service.create_access_token(
            user.id
        )

    def get_current_user(
        self,
        token: str,
    ) -> User:
        user_id = self._token_service.decode_subject(
            token
        )

        if user_id is None:
            raise UnauthenticatedError

        user = self._repository.get_by_id(
            user_id
        )

        if user is None:
            raise UnauthenticatedError

        return user