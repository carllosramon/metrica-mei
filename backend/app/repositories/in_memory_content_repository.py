from dataclasses import replace

from app.domain.content import Content


class InMemoryContentRepository:
    def __init__(self):
        self._contents: dict[int, Content] = {}
        self._next_id = 1

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

    def update(self, content: Content) -> Content:
        self._contents[content.id] = content
        return content

    def delete(self, content: Content) -> None:
        if content.id is not None:
            self._contents.pop(content.id, None)
