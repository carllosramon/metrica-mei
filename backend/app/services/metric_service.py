from dataclasses import replace
from datetime import date, datetime, timezone

from app.domain.metric import Metric
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
    MetricRepository,
)


_METRIC_VALUE_FIELDS = (
    "visualizacoes",
    "curtidas",
    "comentarios",
    "compartilhamentos",
    "alcance",
)

_IMMUTABLE_FIELDS = (
    "id",
    "conteudo_id",
    "criado_em",
)


class MetricContentNotFoundError(Exception):
    pass


class InvalidMetricError(Exception):
    pass


class DuplicateMetricError(Exception):
    pass


class MetricNotFoundError(Exception):
    pass


class MetricService:
    def __init__(
        self,
        content_repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._content_repository = content_repository
        self._metric_repository = metric_repository

    def _get_owned_content(
        self,
        content_id: int,
        user_id: int,
    ):
        content = self._content_repository.get_by_id_and_user(
            content_id,
            user_id,
        )

        if content is None:
            raise MetricContentNotFoundError(
                "Conteúdo não encontrado."
            )

        return content

    @staticmethod
    def _validate_metric_values(
        values: dict[str, object],
    ) -> None:
        for field in _METRIC_VALUE_FIELDS:
            if field not in values:
                continue

            value = values[field]

            if (
                type(value) is not int
                or value < 0
            ):
                raise InvalidMetricError(
                    "As métricas devem ser inteiras "
                    "e maiores ou iguais a zero."
                )

    @staticmethod
    def _validate_reference_date(
        data_referencia: date,
        data_publicacao: date,
    ) -> None:
        if type(data_referencia) is not date:
            raise InvalidMetricError(
                "A data de referência deve ser uma data válida."
            )

        if data_referencia < data_publicacao:
            raise InvalidMetricError(
                "A data de referência não pode ser "
                "anterior à publicação."
            )

        if data_referencia > date.today():
            raise InvalidMetricError(
                "A data de referência não pode estar no futuro."
            )

    def _ensure_unique_reference_date(
        self,
        content_id: int,
        data_referencia: date,
        metric_id: int | None = None,
    ) -> None:
        existing = (
            self._metric_repository
            .get_by_content_and_reference_date(
                content_id,
                data_referencia,
            )
        )

        if (
            existing is not None
            and existing.id != metric_id
        ):
            raise DuplicateMetricError(
                "Já existe uma métrica para este "
                "conteúdo nesta data."
            )

    def create(
        self,
        user_id: int,
        content_id: int,
        visualizacoes: int,
        curtidas: int,
        comentarios: int,
        compartilhamentos: int,
        alcance: int,
        data_referencia: date,
    ) -> Metric:
        content = self._get_owned_content(
            content_id,
            user_id,
        )

        metric_values = {
            "visualizacoes": visualizacoes,
            "curtidas": curtidas,
            "comentarios": comentarios,
            "compartilhamentos": compartilhamentos,
            "alcance": alcance,
        }

        self._validate_metric_values(
            metric_values
        )

        self._validate_reference_date(
            data_referencia,
            content.data_publicacao,
        )

        self._ensure_unique_reference_date(
            content_id,
            data_referencia,
        )

        metric = Metric(
            id=None,
            conteudo_id=content_id,
            visualizacoes=visualizacoes,
            curtidas=curtidas,
            comentarios=comentarios,
            compartilhamentos=compartilhamentos,
            alcance=alcance,
            data_referencia=data_referencia,
            criado_em=datetime.now(timezone.utc),
        )

        try:
            return self._metric_repository.create(
                metric
            )
        except MetricPersistenceConflictError as exc:
            raise DuplicateMetricError(
                "Já existe uma métrica para este "
                "conteúdo nesta data."
            ) from exc

    def list(
        self,
        user_id: int,
        content_id: int,
    ) -> list[Metric]:
        self._get_owned_content(
            content_id,
            user_id,
        )

        return self._metric_repository.list_by_content(
            content_id
        )

    def get(
        self,
        user_id: int,
        content_id: int,
        metric_id: int,
    ) -> Metric:
        self._get_owned_content(
            content_id,
            user_id,
        )

        metric = self._metric_repository.get_by_id_and_content(
            metric_id,
            content_id,
        )

        if metric is None:
            raise MetricNotFoundError(
                "Métrica não encontrada."
            )

        return metric

    def update(
        self,
        user_id: int,
        content_id: int,
        metric_id: int,
        **changes,
    ) -> Metric:
        metric = self.get(
            user_id=user_id,
            content_id=content_id,
            metric_id=metric_id,
        )

        if not changes:
            raise InvalidMetricError(
                "Informe pelo menos um campo para atualizar."
            )

        if any(
            value is None
            for value in changes.values()
        ):
            raise InvalidMetricError(
                "Os campos informados não podem ser nulos."
            )

        for field in _IMMUTABLE_FIELDS:
            if field in changes:
                raise InvalidMetricError(
                    f"O campo {field} não pode ser alterado."
                )

        self._validate_metric_values(
            changes
        )

        if "data_referencia" in changes:
            content = self._get_owned_content(
                content_id,
                user_id,
            )

            new_reference_date = changes[
                "data_referencia"
            ]

            self._validate_reference_date(
                new_reference_date,
                content.data_publicacao,
            )

            self._ensure_unique_reference_date(
                content_id,
                new_reference_date,
                metric.id,
            )

        updated = replace(
            metric,
            **changes,
        )

        try:
            return self._metric_repository.update(
                updated
            )
        except MetricPersistenceConflictError as exc:
            raise DuplicateMetricError(
                "Já existe uma métrica para este "
                "conteúdo nesta data."
            ) from exc

    def delete(
        self,
        user_id: int,
        content_id: int,
        metric_id: int,
    ) -> None:
        metric = self.get(
            user_id=user_id,
            content_id=content_id,
            metric_id=metric_id,
        )

        self._metric_repository.delete(
            metric
        )
