from dataclasses import replace

from app.domain.content import Content


class InMemoryContentRepository:
    def __init__(self):
        self._contents: dict[int, Content] = {}
        self._next_id = 1

    def create(
        self,
        content: Content,
    ) -> Content:
        stored_content = replace(
            content,
            id=self._next_id,
        )

        self._contents[self._next_id] = stored_content
        self._next_id += 1

        return stored_content

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
