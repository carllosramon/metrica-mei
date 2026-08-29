from datetime import datetime, timezone

import pytest

from app.domain.user import User
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.repositories.user_repository import UserPersistenceConflictError


def test_sqlalchemy_repository_persists_and_reads_user(session_factory):
    with session_factory() as session:
        repository = SQLAlchemyUserRepository(session)

        created = repository.create(
            User(
                id=None,
                nome="Carlos",
                email="carlos@email.com",
                senha_hash="hash",
                criado_em=datetime.now(timezone.utc),
            )
        )

        loaded = repository.get_by_email(
            "carlos@email.com"
        )

    assert created.id is not None
    assert loaded is not None
    assert loaded.id == created.id
    assert loaded.nome == "Carlos"
    assert loaded.email == "carlos@email.com"


def test_sqlalchemy_repository_translates_duplicate_email_and_rolls_back(
    session_factory,
):
    with session_factory() as session:
        repository = SQLAlchemyUserRepository(session)

        repository.create(
            User(
                id=None,
                nome="Carlos",
                email="carlos@email.com",
                senha_hash="hash-1",
                criado_em=datetime.now(timezone.utc),
            )
        )

        with pytest.raises(UserPersistenceConflictError):
            repository.create(
                User(
                    id=None,
                    nome="Outro Carlos",
                    email="carlos@email.com",
                    senha_hash="hash-2",
                    criado_em=datetime.now(timezone.utc),
                )
            )

        created_after_conflict = repository.create(
            User(
                id=None,
                nome="Maria",
                email="maria@email.com",
                senha_hash="hash-3",
                criado_em=datetime.now(timezone.utc),
            )
        )

        loaded_after_conflict = repository.get_by_email(
            "maria@email.com"
        )

    assert created_after_conflict.id is not None
    assert loaded_after_conflict is not None
    assert (
        loaded_after_conflict.id
        == created_after_conflict.id
    )
