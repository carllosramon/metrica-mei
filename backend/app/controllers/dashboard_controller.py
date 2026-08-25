from fastapi import APIRouter, Depends

from app.dependencies import (
    get_current_user,
    get_dashboard_service,
)
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(
    tags=["painel"],
)


@router.get(
    "/painel",
    response_model=DashboardResponse,
)
def get_dashboard(
    current_user=Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    # Conta sem conteúdo devolve painel zerado, não 404: ausência de dado é
    # a primeira tela de todo usuário novo, e não uma falha da requisição.
    return service.get(
        user_id=current_user.id,
    )
