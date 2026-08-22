from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class User:
    id: int | None
    nome: str
    email: str
    senha_hash: str
    criado_em: datetime