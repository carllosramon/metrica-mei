from dataclasses import dataclass
from datetime import date


# Modelos de leitura: o painel é inteiramente derivado dos conteúdos e das
# métricas já persistidos, e nada aqui é gravado no banco.
@dataclass(slots=True)
class DashboardContent:
    conteudo_id: int
    titulo: str
    plataforma: str
    engajamento: float
    data_referencia: date


@dataclass(slots=True)
class Dashboard:
    total_conteudos: int
    conteudos_com_metricas: int
    total_visualizacoes: int
    total_curtidas: int
    total_comentarios: int
    total_compartilhamentos: int
    total_alcance: int
    engajamento_geral: float | None
    melhores_conteudos: list[DashboardContent]
