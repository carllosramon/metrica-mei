from fastapi import APIRouter, Depends

from app.controllers.respostas import SEM_SESSAO
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
    summary="Consultar o painel de análise",
    description=(
        "Devolve os indicadores consolidados da conta em uma única "
        "requisição: totais gerais, desempenho por plataforma e ranking dos "
        "conteúdos de maior alcance."
        "\n\n"
        "Como as medições são acumuladas, **cada conteúdo entra nos totais "
        "apenas pela sua medição mais recente**. Somar todo o histórico "
        "contaria repetidamente o mesmo desempenho."
        "\n\n"
        "O `engajamento_geral` é calculado sobre os totais, e não como média "
        "dos índices individuais, para que conteúdos de alcance minúsculo "
        "não dominem o indicador da conta. Quando o alcance total é zero, "
        "vem `null`: o índice não é calculável, o que é diferente de "
        "engajamento zero."
        "\n\n"
        "Conta sem conteúdos recebe `200` com o painel zerado. Ausência de "
        "dado é o estado inicial de toda conta, não um erro."
    ),
    responses=SEM_SESSAO,
)
def get_dashboard(
    current_user=Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
):
    return service.get(
        user_id=current_user.id,
    )
