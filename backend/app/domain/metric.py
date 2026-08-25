from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Metric:
    id: int | None
    conteudo_id: int
    visualizacoes: int
    curtidas: int
    comentarios: int
    compartilhamentos: int
    alcance: int
    data_referencia: date
    criado_em: datetime


# Modelo de leitura: o engajamento é derivado e nunca persistido, então
# fica fora de Metric para que o domínio não carregue dado calculado.
@dataclass(slots=True)
class MetricWithEngagement:
    id: int | None
    conteudo_id: int
    visualizacoes: int
    curtidas: int
    comentarios: int
    compartilhamentos: int
    alcance: int
    data_referencia: date
    criado_em: datetime
    engajamento: float | None
