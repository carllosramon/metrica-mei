from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.controllers.auth_controller import router as auth_router
from app.controllers.content_controller import router as content_router
from app.controllers.dashboard_controller import (
    router as dashboard_router,
)
from app.controllers.metric_controller import (
    router as metric_router,
)


_DESCRICAO = """
API do MetricaMEI, que centraliza o registro e a análise de desempenho de
conteúdos digitais publicados em redes sociais por microempreendedores.

## Autenticação

Todas as rotas exigem um token, exceto o cadastro, o login e o `/health`.
Obtenha o token em `POST /auth/login` e envie-o no cabeçalho:

```
Authorization: Bearer <token>
```

O token expira em trinta minutos e não há renovação automática.

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


app = FastAPI(
    title="MetricaMEI API",
    version="0.7.0",
    description=_DESCRICAO,
    openapi_tags=_GRUPOS,
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
