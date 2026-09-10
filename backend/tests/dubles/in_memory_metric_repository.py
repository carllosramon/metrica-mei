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
            key=self._ordem,
            reverse=True,
        )

    @staticmethod
    def _ordem(metric: Metric) -> tuple:
        return (metric.data_referencia, metric.id or 0)

    def latest_by_contents(
        self,
        content_ids: list[int],
    ) -> dict[int, Metric]:
        procurados = set(content_ids)

        mais_recentes: dict[int, Metric] = {}

        for metric in self._metrics.values():
            if metric.conteudo_id not in procurados:
                continue

            atual = mais_recentes.get(metric.conteudo_id)

            if atual is None or self._ordem(metric) > self._ordem(atual):
                mais_recentes[metric.conteudo_id] = metric

        return mais_recentes

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

    def apagar_do_conteudo(self, content_id: int) -> None:
        # Emula o cascade do banco, acionado pelo dublê de conteúdo quando
        # o conteúdo é excluído.
        for metric_id in list(self._metrics):
            if self._metrics[metric_id].conteudo_id == content_id:
                del self._metrics[metric_id]

    def update(
        self,
        metric: Metric,
    ) -> Metric | None:
        # Métrica excluída não volta por uma atualização: sem esta
        # verificação, gravar abaixo a recriaria. E a métrica não troca de
        # conteúdo por uma atualização, porque o repositório do SQLAlchemy
        # filtra por id e conteúdo.
        guardada = self._metrics.get(metric.id)

        if guardada is None:
            return None

        if guardada.conteudo_id != metric.conteudo_id:
            return None

        existing = self.get_by_content_and_reference_date(
            metric.conteudo_id,
            metric.data_referencia,
        )

        if (
            existing is not None
            and existing.id != metric.id
        ):
            raise MetricPersistenceConflictError

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
