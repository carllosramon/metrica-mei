from fastapi import APIRouter, Depends, HTTPException, status

from app.controllers.respostas import SEM_SESSAO
from app.dependencies import get_auth_service, get_current_user
from app.domain.user import User
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
    tags=["autenticacao"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar conta",
    description=(
        "Cadastra um usuário. O nome tem entre 2 e 100 caracteres e a senha "
        "no mínimo 8. A senha é gravada apenas como hash Argon2, nunca em "
        "texto, e o e-mail é único, comparado sem diferenciar maiúsculas."
        "\n\n"
        "A resposta traz o usuário criado, e não um token: use "
        "`POST /auth/login` em seguida para abrir a sessão."
    ),
    responses={
        409: {
            "description": "E-mail já cadastrado em outra conta.",
        },
    },
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
    summary="Entrar e obter o token",
    description=(
        "Devolve um token válido por trinta minutos, a ser enviado no "
        "cabeçalho `Authorization` das demais rotas. Não há renovação "
        "automática: vencido o prazo, é preciso entrar de novo."
        "\n\n"
        "E-mail inexistente e senha errada produzem a mesma resposta. "
        "Distinguir os dois casos transformaria esta rota em um verificador "
        "de quais e-mails têm conta no sistema."
    ),
    responses={
        401: {
            "description": "E-mail ou senha inválidos.",
        },
    },
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
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    return TokenResponse(
        access_token=token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Identificar o usuário autenticado",
    description=(
        "Devolve os dados de quem porta o token. A interface usa esta rota "
        "ao abrir a aplicação para saber se o token guardado ainda vale, já "
        "que só o servidor sabe se ele expirou."
    ),
    responses=SEM_SESSAO,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user
