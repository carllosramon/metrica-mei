from datetime import date
from typing import Protocol

from app.domain.metric import Metric


class MetricPersistenceConflictError(Exception):
    pass


class MetricRepository(Protocol):
    def create(
        self,
        metric: Metric,
    ) -> Metric:
        ...

    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]:
        """Devolve as medições do conteúdo, da mais recente para a mais
        antiga por data de referência, com desempate por identificador."""
        ...

    def latest_by_contents(
        self,
        content_ids: list[int],
    ) -> dict[int, Metric]:
        """Devolve a medição mais recente de cada conteúdo pedido.

        Mais recente é a de maior data de referência, com desempate pelo
        maior identificador. Conteúdo sem medição não aparece no
        resultado.

        O painel precisa de uma medição por conteúdo, e pedir o histórico
        de cada um custava uma consulta por conteúdo e trazia todas as
        medições da conta para descartar quase todas.
        """
        ...

    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None:
        ...

    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None:
        ...

    def update(
        self,
        metric: Metric,
    ) -> Metric | None:
        """Grava a métrica e devolve o que ficou persistido.

        Devolve None quando a métrica não existe mais: outra requisição
        pode tê-la excluído entre a leitura do serviço e esta gravação.
        """
        ...

    def delete(
        self,
        metric: Metric,
    ) -> None:
        ...
