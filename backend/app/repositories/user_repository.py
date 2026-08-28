from typing import Protocol

from app.domain.user import User


class UserPersistenceConflictError(Exception):
    pass


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_by_id(self, user_id: int) -> User | None: ...

    def create(self, user: User) -> User: ...