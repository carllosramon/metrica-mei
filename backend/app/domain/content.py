from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class Content:
    id: int | None
    usuario_id: int
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    criado_em: datetime
