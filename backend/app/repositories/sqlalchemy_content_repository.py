from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import ContentModel
from app.domain.content import Content


class SQLAlchemyContentRepository:
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: ContentModel) -> Content:
        return Content(
            id=model.id,
            usuario_id=model.usuario_id,
            titulo=model.titulo,
            plataforma=model.plataforma,
            tipo=model.tipo,
            data_publicacao=model.data_publicacao,
            criado_em=model.criado_em,
        )

    def create(self, content: Content) -> Content:
        model = ContentModel(
            usuario_id=content.usuario_id,
            titulo=content.titulo,
            plataforma=content.plataforma,
            tipo=content.tipo,
            data_publicacao=content.data_publicacao,
            criado_em=content.criado_em,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None:
        statement = select(ContentModel).where(
            ContentModel.id == content_id,
            ContentModel.usuario_id == user_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Content]:
        statement = (
            select(ContentModel)
            .where(
                ContentModel.usuario_id == user_id
            )
            .order_by(
                ContentModel.data_publicacao.desc(),
                ContentModel.id.desc(),
            )
        )

        models = self._session.scalars(statement).all()

        return [
            self._to_domain(model)
            for model in models
        ]

    def update(
        self,
        content: Content,
    ) -> Content:
        statement = select(ContentModel).where(
            ContentModel.id == content.id,
            ContentModel.usuario_id == content.usuario_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return content

        model.titulo = content.titulo
        model.plataforma = content.plataforma
        model.tipo = content.tipo
        model.data_publicacao = content.data_publicacao

        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)

    def delete(
        self,
        content: Content,
    ) -> None:
        statement = select(ContentModel).where(
            ContentModel.id == content.id,
            ContentModel.usuario_id == content.usuario_id,
        )

        model = self._session.scalar(statement)

        if model is None:
            return

        self._session.delete(model)
        self._session.commit()
