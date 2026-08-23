from typing import Protocol

from app.domain.content import Content


class ContentRepository(Protocol):
    def create(
        self,
        content: Content,
    ) -> Content: ...

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None: ...
