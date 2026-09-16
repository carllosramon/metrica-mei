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
    url_publicacao: str | None = None


# Modelo de leitura da lista. Repete os campos do conteúdo porque a tela
# precisa deles ao lado da data da última medição, que não é atributo do
# conteúdo e sim derivada das medições dele.
@dataclass(slots=True)
class ContentListItem:
    id: int
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    criado_em: datetime
    url_publicacao: str | None
    # None é "nunca medido", e é a informação que a rotina periódica
    # precisa: sem ela a lista não responde o que falta anotar.
    ultima_medicao: date | None
