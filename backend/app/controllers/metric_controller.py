from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
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
from app.services.metric_service import (
    DuplicateMetricError,
    InvalidMetricError,
    MetricContentNotFoundError,
    MetricNotFoundError,
    MetricService,
)


router = APIRouter(
    tags=["metricas"],
)


def _raise_content_not_found(exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Conteúdo não encontrado.",
    ) from exc


def _raise_metric_not_found(exc):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Métrica não encontrada.",
    ) from exc


def _raise_invalid_metric(exc):
    raise HTTPException(
        status_code=(
            status.HTTP_422_UNPROCESSABLE_CONTENT
        ),
        detail="Dados da métrica inválidos.",
    ) from exc


def _raise_duplicate_metric(exc):
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            "Já existe uma métrica para este "
            "conteúdo nesta data."
        ),
    ) from exc


@router.post(
    "/conteudos/{content_id}/metricas",
    response_model=MetricResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_metric(
    content_id: int,
    payload: MetricCreateRequest,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
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

    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)

    except DuplicateMetricError as exc:
        _raise_duplicate_metric(exc)

    except InvalidMetricError as exc:
        _raise_invalid_metric(exc)


@router.get(
    "/conteudos/{content_id}/metricas",
    response_model=list[MetricResponse],
)
def list_metrics(
    content_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        return service.list(
            user_id=current_user.id,
            content_id=content_id,
        )

    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)


@router.get(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
)
def get_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        return service.get(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
        )

    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)

    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)

@router.patch(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    response_model=MetricResponse,
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

    try:
        return service.update(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
            **changes,
        )

    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)

    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)

    except DuplicateMetricError as exc:
        _raise_duplicate_metric(exc)

    except InvalidMetricError as exc:
        _raise_invalid_metric(exc)

@router.delete(
    (
        "/conteudos/{content_id}/metricas/"
        "{metric_id}"
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_metric(
    content_id: int,
    metric_id: int,
    current_user=Depends(get_current_user),
    service: MetricService = Depends(
        get_metric_service
    ),
):
    try:
        service.delete(
            user_id=current_user.id,
            content_id=content_id,
            metric_id=metric_id,
        )

    except MetricContentNotFoundError as exc:
        _raise_content_not_found(exc)

    except MetricNotFoundError as exc:
        _raise_metric_not_found(exc)
