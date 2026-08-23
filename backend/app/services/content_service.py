from datetime import date, datetime, timezone

from app.domain.content import Content
from app.repositories.content_repository import ContentRepository


class InvalidContentError(Exception):
    pass


class ContentService:
    def __init__(
        self,
        repository: ContentRepository,
    ):
        self._repository = repository

    @staticmethod
    def _normalize_text(
        value: str,
        max_length: int,
    ) -> str:
        normalized = value.strip()

        if not 1 <= len(normalized) <= max_length:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _validate_publication_date(
        value: date,
    ) -> date:
        if value > date.today():
            raise InvalidContentError

        return value

    def create(
        self,
        user_id: int,
        titulo: str,
        plataforma: str,
        tipo: str,
        data_publicacao: date,
    ) -> Content:
        content = Content(
            id=None,
            usuario_id=user_id,
            titulo=self._normalize_text(
                titulo,
                200,
            ),
            plataforma=self._normalize_text(
                plataforma,
                50,
            ),
            tipo=self._normalize_text(
                tipo,
                50,
            ),
            data_publicacao=self._validate_publication_date(
                data_publicacao
            ),
            criado_em=datetime.now(timezone.utc),
        )

        return self._repository.create(content)
