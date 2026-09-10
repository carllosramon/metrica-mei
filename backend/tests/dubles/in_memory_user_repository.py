from dataclasses import replace

from app.domain.user import User
from app.repositories.user_repository import (
    UserPersistenceConflictError,
)


class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1

    def get_by_email(self, email: str) -> User | None:
        return next(
            (user for user in self._users.values() if user.email == email),
            None,
        )

    def get_by_id(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def create(self, user: User) -> User:
        # O e-mail é único no banco, e o dublê precisa recusar o repetido
        # do mesmo jeito. Permitindo, ele guardava duas contas com o mesmo
        # e-mail e a segunda ficava inalcançável pelo login.
        if self.get_by_email(user.email) is not None:
            raise UserPersistenceConflictError

        stored_user = replace(user, id=self._next_id)

        self._users[self._next_id] = stored_user
        self._next_id += 1

        return stored_user