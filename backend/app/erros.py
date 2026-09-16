from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.auth_service import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRegistrationError,
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
    # Os limites de nome e senha estão também no schema, que responde
    # antes com o detalhe por campo. Sem este mapa, o dia em que a ordem
    # mudasse o usuário receberia 500 no lugar de 422.
    (
        InvalidRegistrationError,
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Dados de cadastro inválidos.",
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
        excecao: Exception,
    ) -> JSONResponse:
        # A mensagem da exceção vence o texto do mapa quando existe. O
        # serviço sabe dizer "A data de referência não pode estar no
        # futuro", e o usuário lia "Dados da métrica inválidos". Todas as
        # mensagens levantadas são literais do código, nenhuma carrega
        # texto de origem externa.
        return JSONResponse(
            status_code=codigo,
            content={"detail": str(excecao) or detalhe},
            headers=cabecalhos,
        )

    return traduzir


def registrar_erros(app: FastAPI) -> None:
    for excecao, codigo, detalhe, cabecalhos in _RESPOSTAS:
        app.add_exception_handler(
            excecao,
            _tradutor(codigo, detalhe, cabecalhos),
        )
