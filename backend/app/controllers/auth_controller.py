from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

from app.services.auth_service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        return service.register(
            payload.nome,
            str(payload.email),
            payload.senha,
        )

    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail já cadastrado.",
        ) from exc

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    try:
        token = service.login(
            str(payload.email),
            payload.senha,
        )

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        ) from exc

    return TokenResponse(
        access_token=token,
    )