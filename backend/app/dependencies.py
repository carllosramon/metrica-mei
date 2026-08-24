from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database.connection import (
    create_engine_from_url,
    create_session_factory,
)
from app.domain.user import User
from app.repositories.sqlalchemy_content_repository import SQLAlchemyContentRepository
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.repositories.sqlalchemy_metric_repository import (
    SQLAlchemyMetricRepository,
)
from app.security.jwt import TokenService
from app.security.password import PasswordService
from app.services.auth_service import AuthService, UnauthenticatedError
from app.services.content_service import ContentService
from app.services.metric_service import MetricService


security = HTTPBearer(
    auto_error=False,
)


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
    settings: Settings = Depends(get_settings),
):
    if not settings.jwt_secret:
        raise RuntimeError(
            "JWT_SECRET não configurado."
        )

    return AuthService(
        repository,
        PasswordService(),
        TokenService(
            settings.jwt_secret,
            settings.jwt_algorithm,
            settings.jwt_expires_minutes,
        ),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    service: AuthService = Depends(get_auth_service),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    try:
        return service.get_current_user(
            credentials.credentials
        )

    except UnauthenticatedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc



def get_content_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyContentRepository(session)


def get_content_service(
    repository=Depends(get_content_repository),
):
    return ContentService(repository)

def get_metric_repository(
    session: Session = Depends(get_db_session),
):
    return SQLAlchemyMetricRepository(session)


def get_metric_service(
    content_repository=Depends(
        get_content_repository
    ),
    metric_repository=Depends(
        get_metric_repository
    ),
):
    return MetricService(
        content_repository,
        metric_repository,
    )
