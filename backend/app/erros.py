from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    UnauthenticatedError,
)
from app.services.content_service import (
    ContentNotFoundError,
    InvalidContentError,
)
from app.services.metric_service import (
    DuplicateMetricError,
    InvalidMetricError,
    MetricContentNotFoundError,
    MetricNotFoundError,
)

_PEDE_AUTENTICACAO = {"WWW-Authenticate": "Bearer"}

# Cada erro de domínio tem uma resposta HTTP, e uma só. O mapa vive aqui
# porque a tradução era feita à mão em cada endpoint, vinte e sete vezes
# para nove mapeamentos, e um endpoint novo que esquecesse o try devolvia
# 500 no lugar do erro certo.
_RESPOSTAS = (
    (
        ContentNotFoundError,
        status.HTTP_404_NOT_FOUND,
        "Conteúdo não encontrado.",
        None,
    ),
    (
        MetricContentNotFoundError,
        status.HTTP_404_NOT_FOUND,
        "Conteúdo não encontrado.",
        None,
    ),
    (
        MetricNotFoundError,
        status.HTTP_404_NOT_FOUND,
        "Métrica não encontrada.",
        None,
    ),
    (
        InvalidContentError,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Dados do conteúdo inválidos.",
        None,
    ),
    (
        InvalidMetricError,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Dados da métrica inválidos.",
        None,
    ),
    (
        DuplicateMetricError,
        status.HTTP_409_CONFLICT,
        "Já existe uma métrica para este conteúdo nesta data.",
        None,
    ),
    (
        EmailAlreadyRegisteredError,
        status.HTTP_409_CONFLICT,
        "E-mail já cadastrado.",
        None,
    ),
    (
        InvalidCredentialsError,
        status.HTTP_401_UNAUTHORIZED,
        "E-mail ou senha inválidos.",
        _PEDE_AUTENTICACAO,
    ),
    (
        UnauthenticatedError,
        status.HTTP_401_UNAUTHORIZED,
        "Não autenticado.",
        _PEDE_AUTENTICACAO,
    ),
)


def _tradutor(
    codigo: int,
    detalhe: str,
    cabecalhos: dict[str, str] | None,
):
    async def traduzir(
        _request: Request,
        _excecao: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=codigo,
            content={"detail": detalhe},
            headers=cabecalhos,
        )

    return traduzir


def registrar_erros(app: FastAPI) -> None:
    for excecao, codigo, detalhe, cabecalhos in _RESPOSTAS:
        app.add_exception_handler(
            excecao,
            _tradutor(codigo, detalhe, cabecalhos),
        )
