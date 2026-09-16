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


class ContentListItemResponse(ContentResponse):
    # Só a lista traz o campo. Na resposta de um conteúdo isolado ele
    # seria sempre nulo, e nulo ali significaria "nunca medido" para um
    # conteúdo que pode ter histórico inteiro.
    ultima_medicao: date | None


class ContentUpdateRequest(BaseModel):
    titulo: str | None = None
    plataforma: str | None = None
    tipo: str | None = None
    data_publicacao: date | None = None
    url_publicacao: str | None = None
