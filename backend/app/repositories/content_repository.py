from typing import Protocol

from app.domain.content import Content


class ContentRepository(Protocol):
    def create(self, content: Content) -> Content:
        ...

    def list_by_user(self, user_id: int) -> list[Content]:
        ...

    def get_by_id_and_user(
        self,
        content_id: int,
        user_id: int,
    ) -> Content | None:
        ...

    def update(self, content: Content) -> Content:
        ...

    def delete(self, content: Content) -> None:
        ...
