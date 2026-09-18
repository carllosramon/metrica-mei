from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.content_controller import router as content_router
from app.controllers.dashboard_controller import (
    router as dashboard_router,
)
from app.controllers.metric_controller import (
    router as metric_router,
)
from app.controllers.respostas import prazo_do_token
from app.erros import registrar_erros
from app.security.jwt import PRAZO_MINIMO_EM_MINUTOS, TokenService


_DESCRICAO = f"""
API do MetricaMEI, que centraliza o registro e a análise de desempenho de
conteúdos digitais publicados em redes sociais por microempreendedores.

## Autenticação

Todas as rotas exigem um token, exceto o cadastro, o login e o `/health`.
Obtenha o token em `POST /auth/login` e envie-o no cabeçalho:

```
Authorization: Bearer <token>
```

O token expira em {prazo_do_token()} e não há renovação automática.

## Convenção de erros

Toda falha devolve um corpo com o campo `detail`. Nas validações de schema o
`detail` é uma lista com um item por campo; nas regras de negócio é um texto.

Recursos de outro usuário respondem `404`, e não `403`: informar que o registro
existe mas pertence a outra conta revelaria dados alheios.
"""

_GRUPOS = [
    {
        "name": "autenticacao",
        "description": (
            "Cadastro de conta, obtenção do token e identificação do "
            "usuário autenticado."
        ),
    },
    {
        "name": "conteudos",
        "description": (
            "Publicações digitais do usuário. Cada conteúdo pertence a "
            "uma conta e é a âncora das medições."
        ),
    },
    {
        "name": "metricas",
        "description": (
            "Medições de desempenho de um conteúdo. Cada registro é um "
            "retrato acumulado numa data, e não o incremento do dia."
        ),
    },
    {
        "name": "painel",
        "description": (
            "Indicadores consolidados da conta, derivados da medição "
            "mais recente de cada conteúdo."
        ),
    },
]


def verificar_configuracao(settings: Settings) -> None:
    # Sem um segredo à altura a API subia, respondia no /health e só
    # falhava no primeiro login, longe de quem estava olhando a subida.
    # Construir o serviço de token aqui faz a exigência dele valer já na
    # subida, com a mesma mensagem.
    TokenService(
        settings.jwt_secret,
        settings.jwt_algorithm,
        settings.jwt_expires_minutes,
    )

    # O prazo é conferido aqui, e não dentro do TokenService, porque um
    # prazo no passado é forma legítima de forjar token vencido em teste.
    # O que não pode é a aplicação subir assim: com zero, o login devolve
    # 200 e a requisição seguinte devolve 401, e a falha aparece ao
    # usuário como sessão que não começa.
    if settings.jwt_expires_minutes < PRAZO_MINIMO_EM_MINUTOS:
        raise ValueError(
            "JWT_EXPIRES_MINUTES precisa ser de ao menos "
            f"{PRAZO_MINIMO_EM_MINUTOS} minuto."
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    verificar_configuracao(get_settings())

    yield


app = FastAPI(
    title="MetricaMEI API",
    version="0.11.0",
    description=_DESCRICAO,
    openapi_tags=_GRUPOS,
    lifespan=lifespan,
)

# O frontend roda em outra porta durante o desenvolvimento, então o
# navegador trata cada requisição como origem cruzada e a bloqueia
# sem esta liberação explícita.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins(),
    allow_methods=[
        "GET",
        "POST",
        "PATCH",
        "DELETE",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)

app.include_router(auth_router)
app.include_router(content_router)
app.include_router(metric_router)
app.include_router(dashboard_router)

# Os erros de domínio viram resposta HTTP num lugar só, e não em cada
# endpoint.
registrar_erros(app)


@app.get(
    "/health",
    tags=["painel"],
    summary="Verificar se a API está no ar",
    description=(
        "Responde sem consultar o banco nem exigir autenticação. Serve "
        "para o processo que sobe a aplicação saber quando ela está "
        "pronta para receber requisições."
    ),
)
def health_check():
    return {"status": "ok"}
