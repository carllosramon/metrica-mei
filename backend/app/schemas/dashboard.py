from datetime import date

from pydantic import BaseModel, ConfigDict


class DashboardContentResponse(BaseModel):
    conteudo_id: int
    titulo: str
    plataforma: str
    engajamento: float
    data_referencia: date

    model_config = ConfigDict(
        from_attributes=True,
    )


class DashboardResponse(BaseModel):
    total_conteudos: int
    conteudos_com_metricas: int
    total_visualizacoes: int
    total_curtidas: int
    total_comentarios: int
    total_compartilhamentos: int
    total_alcance: int
    engajamento_geral: float | None
    melhores_conteudos: list[DashboardContentResponse]

    model_config = ConfigDict(
        from_attributes=True,
    )
