from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ContentCreateRequest(BaseModel):
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    url_publicacao: str | None = None


class ContentResponse(BaseModel):
    id: int
    titulo: str
    plataforma: str
    tipo: str
    data_publicacao: date
    criado_em: datetime
    url_publicacao: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ContentUpdateRequest(BaseModel):
    titulo: str | None = None
    plataforma: str | None = None
    tipo: str | None = None
    data_publicacao: date | None = None
    url_publicacao: str | None = None
