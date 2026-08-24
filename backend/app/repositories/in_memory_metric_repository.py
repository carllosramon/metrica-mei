from dataclasses import replace
from datetime import date

from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


class InMemoryMetricRepository:
    def __init__(self):
        self._metrics: dict[int, Metric] = {}
        self._next_id = 1

    def create(self, metric: Metric) -> Metric:
        if self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        ) is not None:
            raise MetricPersistenceConflictError

        stored = replace(
            metric,
            id=self._next_id,
        )

        self._metrics[self._next_id] = stored
        self._next_id += 1

        return stored

    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]:
        metrics = [
            metric
            for metric in self._metrics.values()
            if metric.conteudo_id == content_id
        ]

        return sorted(
            metrics,
            key=lambda metric: (
                metric.data_referencia,
                metric.id or 0,
            ),
            reverse=True,
        )

    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None:
        metric = self._metrics.get(metric_id)

        if metric is None:
            return None

        if metric.conteudo_id != content_id:
            return None

        return metric

    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None:
        for metric in self._metrics.values():
            if (
                metric.conteudo_id == content_id
                and metric.data_referencia
                == data_referencia
            ):
                return metric

        return None
    def update(
        self,
        metric: Metric,
    ) -> Metric:
        existing = self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        )

        if (
            existing is not None
            and existing.id != metric.id
        ):
            raise MetricPersistenceConflictError

        if metric.id is not None:
            self._metrics[metric.id] = metric

        return metric
    def update(
        self,
        metric: Metric,
    ) -> Metric:
        existing = self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        )

        if (
            existing is not None
            and existing.id != metric.id
        ):
            raise MetricPersistenceConflictError

        if metric.id is not None:
            self._metrics[metric.id] = metric

        return metric
    def delete(
        self,
        metric: Metric,
    ) -> None:
        if metric.id is not None:
            self._metrics.pop(
                metric.id,
                None,
            )
