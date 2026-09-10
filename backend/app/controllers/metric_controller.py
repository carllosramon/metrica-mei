from fastapi import (
    APIRouter,
    Depends,
    status,
)

from app.controllers.respostas import (
    MEDICAO_DUPLICADA,
    METRICA_NAO_ENCONTRADA,
    SEM_SESSAO,
)
from app.dependencies import (
    get_current_user,
    get_metric_service,
)
from app.schemas.metric import (
    MetricCreateRequest,
    MetricResponse,
    MetricUpdateRequest,
)
from app.services.metric_service import MetricService


router = APIRouter(
    tags=["metricas"],
)


_VALORES_INVALIDOS = {
    422: {
        "description": (
            "Valores que não sejam inteiros maiores ou iguais a zero, ou "
            "data de referência anterior à publicação ou no futuro."
        ),
    },
}

_SNAPSHOT = (
    "Cada medição é um retrato **acumulado** do desempenho até a data de "
    "referência, e não o incremento do dia — é assim que as plataformas "
    "apresentam os números. O sistema não exige crescimento entre medições, "
    "porque as redes corrigem e recalculam valores."
)


@router.post(
    "/conteudos/{content_id}/metricas",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar medição",
    description=(
        _SNAPSHOT
        + "\n\n"
        "Existe no máximo uma medição por conteúdo e data de referência. A "
        "resposta traz o índice de engajamento já calculado, que nunca é "
        "aceito como entrada."
    ),
    responses={
        **SEM_SESSAO,
        **METRICA_NAO_ENCONTRADA,
        **MEDICAO_DUPLICADA,
        **_VALORES_INVALIDOS,
    },
)
def create_metric(
    content_id: int,
    payload: MetricCreateRequest,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    return service.create(
        user_id=current_user.id,
        content_id=content_id,
        visualizacoes=payload.visualizacoes,
        curtidas=payload.curtidas,
        comentarios=payload.comentarios,
        compartilhamentos=(
            payload.compartilhamentos
        ),
        alcance=payload.alcance,
        data_referencia=(
            payload.data_referencia
        ),
    )


@router.get(
    "/conteudos/{content_id}/metricas",
    response_model=list[MetricResponse],
    summary="Listar o histórico de medições",
    description=(
        "Devolve as medições do conteúdo, da mais recente para a mais "
        "antiga. Cada item traz o índice de engajamento calculado sobre os "
        "seus próprios valores."
    ),
    responses={**SEM_SESSAO, **METRICA_NAO_ENCONTRADA},
)
def list_metrics(
    content_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    return service.list(
        user_id=current_user.id,
        content_id=content_id,
    )


@router.get(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
    summary="Consultar uma medição",
    description=(
        "Devolve uma medição específica do conteúdo, com o índice de "
        "engajamento calculado."
    ),
    responses={**SEM_SESSAO, **METRICA_NAO_ENCONTRADA},
)
def get_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    return service.get(
        user_id=current_user.id,
        content_id=content_id,
        metric_id=metric_id,
    )


@router.patch(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
    summary="Corrigir uma medição",
    description=(
        "Altera somente os campos enviados e recalcula o índice de "
        "engajamento na resposta."
        "\n\n"
        "Mudar a data de referência para uma já ocupada por outra medição "
        "do mesmo conteúdo é recusado."
    ),
    responses={
        **SEM_SESSAO,
        **METRICA_NAO_ENCONTRADA,
        **MEDICAO_DUPLICADA,
        **_VALORES_INVALIDOS,
    },
)
def update_metric(
    content_id: int,
    metric_id: int,
    payload: MetricUpdateRequest,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    changes = payload.model_dump(
        exclude_unset=True,
    )

    return service.update(
        user_id=current_user.id,
        content_id=content_id,
        metric_id=metric_id,
        **changes,
    )


@router.delete(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir uma medição",
    description=(
        "Remove apenas a medição indicada. O conteúdo e as demais medições "
        "permanecem."
    ),
    responses={**SEM_SESSAO, **METRICA_NAO_ENCONTRADA},
)
def delete_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    service.delete(
        user_id=current_user.id,
        content_id=content_id,
        metric_id=metric_id,
    )
