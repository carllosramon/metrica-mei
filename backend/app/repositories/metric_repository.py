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
    ) -> Metric:
        ...

    def delete(
        self,
        metric: Metric,
    ) -> None:
        ...
