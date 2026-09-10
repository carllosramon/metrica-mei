from dataclasses import replace

from app.domain.content import Content


class InMemoryContentRepository:
    def __init__(self, metric_repository=None):
        self._contents: dict[int, Content] = {}
        self._next_id = 1

        # O banco apaga as medições do conteúdo por cascade. Recebendo o
        # repositório de métricas, o dublê faz o mesmo, e um teste de
        # serviço deixa de ver medições órfãs que a produção não deixa.
        self._metric_repository = metric_repository

    def create(self, content: Content) -> Content:
        stored_content = replace(
            content,
            id=self._next_id,
        )

        self._contents[self._next_id] = stored_content
        self._next_id += 1

        return stored_content

    def list_by_user(
        self,
        user_id: int,
    ) -> list[Content]:
        contents = [
            content
            for content in self._contents.values()
            if content.usuario_id == user_id
        ]

        return sorted(
            contents,
            key=lambda content: (
                content.data_publicacao,
                content.id or 0,
            ),
            reverse=True,
        )

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None:
        content = self._contents.get(content_id)

        if content is None:
            return None

        if content.usuario_id != user_id:
            return None

        return content

    def update(self, content: Content) -> Content | None:
        # Conteúdo excluído não volta por uma atualização: sem esta
        # verificação, gravar abaixo o recriaria. E o dono não muda por
        # uma atualização, porque o repositório do SQLAlchemy filtra por
        # id e dono, e um dublê mais permissivo validaria uma semântica
        # que a produção não tem.
        guardado = self._contents.get(content.id)

        if guardado is None:
            return None

        if guardado.usuario_id != content.usuario_id:
            return None

        self._contents[content.id] = content

        return content

    def delete(self, content: Content) -> None:
        if content.id is None:
            return

        self._contents.pop(content.id, None)

        if self._metric_repository is not None:
            self._metric_repository.apagar_do_conteudo(content.id)
