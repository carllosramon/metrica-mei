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
