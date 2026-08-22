from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.connection import (
    create_engine_from_url,
    create_session_factory,
)
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.security.password import PasswordService
from app.services.auth_service import AuthService


@lru_cache
def get_engine():
    return create_engine_from_url(
        get_settings().database_url
    )


@lru_cache
def get_session_factory():
    return create_session_factory(
        get_engine()
    )


def get_db_session():
    with get_session_factory()() as session:
        yield session


def get_user_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyUserRepository(session)


def get_auth_service(
    repository=Depends(get_user_repository),
):
    return AuthService(
        repository,
        PasswordService(),
    )