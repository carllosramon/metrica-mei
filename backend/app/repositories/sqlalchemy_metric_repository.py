from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import MetricModel
from app.domain.metric import Metric
from app.repositories.metric_repository import (
    MetricPersistenceConflictError,
)


class SQLAlchemyMetricRepository:
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: MetricModel) -> Metric:
        return Metric(
            id=model.id,
            conteudo_id=model.conteudo_id,
            visualizacoes=model.visualizacoes,
            curtidas=model.curtidas,
            comentarios=model.comentarios,
            compartilhamentos=model.compartilhamentos,
            alcance=model.alcance,
            data_referencia=model.data_referencia,
            criado_em=model.criado_em,
        )

    def create(
        self,
        metric: Metric,
    ) -> Metric:
        model = MetricModel(
            conteudo_id=metric.conteudo_id,
            visualizacoes=metric.visualizacoes,
            curtidas=metric.curtidas,
            comentarios=metric.comentarios,
            compartilhamentos=metric.compartilhamentos,
            alcance=metric.alcance,
            data_referencia=metric.data_referencia,
            criado_em=metric.criado_em,
        )

        self._session.add(model)

        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise MetricPersistenceConflictError(
                "Conflito ao persistir a métrica."
            ) from exc

        self._session.refresh(model)

        return self._to_domain(model)
    def get_by_id_and_content(
        self,
        metric_id: int,
        content_id: int,
    ) -> Metric | None:
        statement = select(MetricModel).where(
            MetricModel.id == metric_id,
            MetricModel.conteudo_id == content_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)
    def list_by_content(
        self,
        content_id: int,
    ) -> list[Metric]:
        statement = (
            select(MetricModel)
            .where(
                MetricModel.conteudo_id == content_id
            )
            .order_by(
                MetricModel.data_referencia.desc(),
                MetricModel.id.desc(),
            )
        )

        models = self._session.scalars(
            statement
        ).all()

        return [
            self._to_domain(model)
            for model in models
        ]
    def get_by_content_and_reference_date(
        self,
        content_id: int,
        data_referencia: date,
    ) -> Metric | None:
        statement = select(MetricModel).where(
            MetricModel.conteudo_id == content_id,
            MetricModel.data_referencia == data_referencia,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)
    def update(
        self,
        metric: Metric,
    ) -> Metric | None:
        statement = select(MetricModel).where(
            MetricModel.id == metric.id,
            MetricModel.conteudo_id == metric.conteudo_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        model.visualizacoes = metric.visualizacoes
        model.curtidas = metric.curtidas
        model.comentarios = metric.comentarios
        model.compartilhamentos = metric.compartilhamentos
        model.alcance = metric.alcance
        model.data_referencia = metric.data_referencia

        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise MetricPersistenceConflictError(
                "Conflito ao persistir a métrica."
            ) from exc

        self._session.refresh(model)

        return self._to_domain(model)
    def delete(
        self,
        metric: Metric,
    ) -> None:
        statement = select(MetricModel).where(
            MetricModel.id == metric.id,
            MetricModel.conteudo_id == metric.conteudo_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return

        self._session.delete(model)
        self._session.commit()
