from dataclasses import replace
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

from app.domain.content import Content
from app.repositories.content_repository import ContentRepository
from app.repositories.metric_repository import MetricRepository
from app.services.business_clock import business_today


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
        texto: object,
        tamanho_maximo: int,
    ) -> str:
        if not isinstance(texto, str):
            raise InvalidContentError

        normalized = texto.strip()

        if not 1 <= len(normalized) <= tamanho_maximo:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _normalize_url(
        endereco: object,
    ) -> str | None:
        # None é aceito de propósito: é assim que o PATCH remove a URL
        # de um conteúdo que já a tinha.
        if endereco is None:
            return None

        if not isinstance(endereco, str):
            raise InvalidContentError

        normalized = endereco.strip()

        # A validação fica no serviço, e não em HttpUrl do Pydantic, para
        # manter a regra de negócio fora da camada de contrato. Conferir só
        # o prefixo deixava passar "https://" sem endereço e recusava
        # "HTTPS://", que é esquema válido, o esquema não distingue caixa.
        try:
            partes = urlsplit(normalized)
        except ValueError as exc:
            # Endereço com colchete de IPv6 aberto e não fechado faz o
            # urlsplit estourar. Sem isto a API respondia 500 a uma URL
            # que o usuário só digitou errado.
            raise InvalidContentError(
                "A URL informada não é um endereço válido."
            ) from exc

        if partes.scheme.lower() not in ("http", "https"):
            raise InvalidContentError

        if not partes.netloc:
            raise InvalidContentError

        if len(normalized) > 500:
            raise InvalidContentError

        return normalized

    @staticmethod
    def _validate_publication_date(
        dia: object,
    ) -> date:
        if not isinstance(dia, date) or isinstance(dia, datetime):
            raise InvalidContentError

        if dia > business_today():
            raise InvalidContentError

        return dia

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

    def _recusar_data_depois_das_medicoes(
        self,
        content_id: int,
        data_publicacao: date,
    ) -> None:
        # Empurrar a publicação para depois de uma medição existente
        # deixaria o histórico com desempenho medido antes de o conteúdo
        # ter sido publicado.
        metricas = self._metric_repository.list_by_content(
            content_id
        )

        for metrica in metricas:
            if metrica.data_referencia < data_publicacao:
                raise InvalidContentError

    def _alteracoes_normalizadas(
        self,
        content_id: int,
        titulo: object,
        plataforma: object,
        tipo: object,
        data_publicacao: object,
        url_publicacao: object,
    ) -> dict[str, object]:
        # Só os campos informados entram. Os ausentes ficam de fora para
        # que o replace preserve o valor que já estava gravado.
        alteracoes: dict[str, object] = {}

        if titulo is not _UNSET:
            alteracoes["titulo"] = self._normalize_text(titulo, 200)

        if plataforma is not _UNSET:
            alteracoes["plataforma"] = self._normalize_text(
                plataforma,
                50,
            )

        if tipo is not _UNSET:
            alteracoes["tipo"] = self._normalize_text(tipo, 50)

        if data_publicacao is not _UNSET:
            nova_data = self._validate_publication_date(
                data_publicacao
            )

            self._recusar_data_depois_das_medicoes(
                content_id,
                nova_data,
            )

            alteracoes["data_publicacao"] = nova_data

        if url_publicacao is not _UNSET:
            alteracoes["url_publicacao"] = self._normalize_url(
                url_publicacao
            )

        return alteracoes

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
        informados = (
            titulo,
            plataforma,
            tipo,
            data_publicacao,
            url_publicacao,
        )

        if all(campo is _UNSET for campo in informados):
            raise InvalidContentError

        content = self.get(
            content_id=content_id,
            user_id=user_id,
        )

        alteracoes = self._alteracoes_normalizadas(
            content_id,
            titulo,
            plataforma,
            tipo,
            data_publicacao,
            url_publicacao,
        )

        persistido = self._repository.update(
            replace(content, **alteracoes)
        )

        # O conteúdo pode ter sido excluído entre a leitura acima e
        # esta gravação. Devolver os valores enviados diria ao
        # usuário que a edição valeu, e ela não valeu.
        if persistido is None:
            raise ContentNotFoundError

        return persistido

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