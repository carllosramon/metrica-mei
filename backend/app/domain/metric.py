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
#
# Herda os campos em vez de repeti-los. Copiados à mão, uma coluna nova em
# Metric precisava ser lembrada aqui e no serviço que monta este objeto, e
# esquecer qualquer um dos dois sumia com o campo da resposta sem erro.
@dataclass(slots=True)
class MetricWithEngagement(Metric):
    engajamento: float | None
