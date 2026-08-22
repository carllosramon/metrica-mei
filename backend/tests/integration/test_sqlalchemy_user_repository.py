from datetime import datetime, timezone

from app.database import models  # noqa: F401
from app.database.connection import (
    Base,
    create_engine_from_url,
    create_session_factory,
)
from app.domain.user import User
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


def test_sqlalchemy_repository_persists_and_reads_user(tmp_path):
    database_path = tmp_path / "repository.db"

    engine = create_engine_from_url(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)

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