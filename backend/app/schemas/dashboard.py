from datetime import date

from pydantic import BaseModel, ConfigDict


class DashboardContentResponse(BaseModel):
    conteudo_id: int
    titulo: str
    plataforma: str
    alcance: int
    engajamento: float | None
    data_referencia: date

    model_config = ConfigDict(
        from_attributes=True,
    )


class DashboardPlatformResponse(BaseModel):
    plataforma: str
    total_conteudos: int
    total_visualizacoes: int
    total_curtidas: int
    total_comentarios: int
    total_compartilhamentos: int
    total_alcance: int
    engajamento: float | None

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
    desempenho_por_plataforma: list[DashboardPlatformResponse]
    maiores_alcances: list[DashboardContentResponse]

    model_config = ConfigDict(
        from_attributes=True,
    )
