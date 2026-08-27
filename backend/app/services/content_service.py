from dataclasses import replace
from datetime import date, datetime, timezone

from app.domain.content import Content
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import MetricRepository


_UNSET = object()


class InvalidContentError(Exception):
    pass


class ContentNotFoundError(Exception):
    pass


class ContentService:
    def __init__(
        self,
        repository: ContentRepository,
        metric_repository: MetricRepository,
    ):
        self._repository = repository
        self._metric_repository = metric_repository

    @staticmethod
    def _normalize_text(
        value: object,
        max_length: int,
    ) -> str:
        if not isinstance(value, str):
            raise InvalidContentError

        normalized = value.strip()

        if not 1 <= len(normalized) <= max_length:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _normalize_url(
        value: object,
    ) -> str | None:
        # None é aceito de propósito: é assim que o PATCH remove a URL
        # de um conteúdo que já a tinha.
        if value is None:
            return None

        if not isinstance(value, str):
            raise InvalidContentError

        normalized = value.strip()

        # A validação fica no serviço, e não em HttpUrl do Pydantic, para
        # manter a regra de negócio fora da camada de contrato.
        if not normalized.startswith(("http://", "https://")):
            raise InvalidContentError

        if len(normalized) > 500:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _validate_publication_date(
        value: object,
    ) -> date:
        if not isinstance(value, date) or isinstance(value, datetime):
            raise InvalidContentError

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
        url_publicacao: str | None = None,
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
            url_publicacao=self._normalize_url(
                url_publicacao
            ),
        )

        return self._repository.create(content)

    def list(
        self,
        user_id: int,
    ) -> list[Content]:
        return self._repository.list_by_user(user_id)

    def get(
        self,
        content_id: int,
        user_id: int,
    ) -> Content:
        content = self._repository.get_by_id_and_user(
            content_id,
            user_id,
        )

        if content is None:
            raise ContentNotFoundError

        return content

    def update(
        self,
        content_id: int,
        user_id: int,
        titulo: object = _UNSET,
        plataforma: object = _UNSET,
        tipo: object = _UNSET,
        data_publicacao: object = _UNSET,
        url_publicacao: object = _UNSET,
    ) -> Content:
        if (
            titulo is _UNSET
            and plataforma is _UNSET
            and tipo is _UNSET
            and data_publicacao is _UNSET
            and url_publicacao is _UNSET
        ):
            raise InvalidContentError

        content = self.get(
            content_id=content_id,
            user_id=user_id,
        )

        normalized_publication_date = (
            self._validate_publication_date(data_publicacao)
            if data_publicacao is not _UNSET
            else content.data_publicacao
        )

        if data_publicacao is not _UNSET:
            metrics = self._metric_repository.list_by_content(
                content_id
            )

            if any(
                metric.data_referencia < normalized_publication_date
                for metric in metrics
            ):
                raise InvalidContentError

        updated_content = replace(
            content,
            titulo=(
                self._normalize_text(titulo, 200)
                if titulo is not _UNSET
                else content.titulo
            ),
            plataforma=(
                self._normalize_text(plataforma, 50)
                if plataforma is not _UNSET
                else content.plataforma
            ),
            tipo=(
                self._normalize_text(tipo, 50)
                if tipo is not _UNSET
                else content.tipo
            ),
            data_publicacao=normalized_publication_date,
            url_publicacao=(
                self._normalize_url(url_publicacao)
                if url_publicacao is not _UNSET
                else content.url_publicacao
            ),
        )

        return self._repository.update(updated_content)

    def delete(
        self,
        content_id: int,
        user_id: int,
    ) -> None:
        content = self.get(
            content_id=content_id,
            user_id=user_id,
        )

        self._repository.delete(content)