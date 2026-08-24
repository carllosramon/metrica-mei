from datetime import date, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
)


class MetricCreateRequest(BaseModel):
    visualizacoes: StrictInt
    curtidas: StrictInt
    comentarios: StrictInt
    compartilhamentos: StrictInt
    alcance: StrictInt
    data_referencia: date


class MetricResponse(BaseModel):
    id: int
    visualizacoes: int
    curtidas: int
    comentarios: int
    compartilhamentos: int
    alcance: int
    data_referencia: date
    criado_em: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class MetricUpdateRequest(BaseModel):
    visualizacoes: StrictInt | None = None
    curtidas: StrictInt | None = None
    comentarios: StrictInt | None = None
    compartilhamentos: StrictInt | None = None
    alcance: StrictInt | None = None
    data_referencia: date | None = None
