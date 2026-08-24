from datetime import date, datetime, timezone

from app.domain.metric import Metric
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
    MetricRepository,
)


class MetricContentNotFoundError(Exception):
    pass


class InvalidMetricError(Exception):
    pass


class DuplicateMetricError(Exception):
    pass


class MetricService:
    def __init__(
        self,
        content_repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._content_repository = content_repository
        self._metric_repository = metric_repository

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
        content = self._content_repository.get_by_id_and_user(
            content_id,
            user_id,
        )

        if content is None:
            raise MetricContentNotFoundError("Conteúdo não encontrado.")

        if (
            type(visualizacoes) is not int
            or type(curtidas) is not int
            or type(comentarios) is not int
            or type(compartilhamentos) is not int
            or type(alcance) is not int
            or visualizacoes < 0
            or curtidas < 0
            or comentarios < 0
            or compartilhamentos < 0
            or alcance < 0
        ):
            raise InvalidMetricError(
                "As métricas devem ser inteiras e maiores ou iguais a zero."
            )

        if type(data_referencia) is not date:
            raise InvalidMetricError(
                "A data de referência deve ser uma data válida."
            )

        if data_referencia < content.data_publicacao:
            raise InvalidMetricError(
                "A data de referência não pode ser anterior à publicação."
            )

        if data_referencia > date.today():
            raise InvalidMetricError(
                "A data de referência não pode estar no futuro."
            )

        existing = (
            self._metric_repository
            .get_by_content_and_reference_date(
                content_id,
                data_referencia,
            )
        )

        if existing is not None:
            raise DuplicateMetricError(
                "Já existe uma métrica para este conteúdo nesta data."
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
            return self._metric_repository.create(metric)
        except MetricPersistenceConflictError as exc:
            raise DuplicateMetricError(
                "Já existe uma métrica para este conteúdo nesta data."
            ) from exc
