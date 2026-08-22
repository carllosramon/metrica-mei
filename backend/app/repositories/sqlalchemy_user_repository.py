from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import UserModel
from app.domain.user import User


class SQLAlchemyUserRepository:
    def __init__(self, session: Session):
        self._session = session

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            nome=model.nome,
            email=model.email,
            senha_hash=model.senha_hash,
            criado_em=model.criado_em,
        )

    def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(
            UserModel.email == email
        )

        model = self._session.scalar(statement)

        if model is None:
            return None

        return self._to_domain(model)

    def get_by_id(self, user_id: int) -> User | None:
        model = self._session.get(
            UserModel,
            user_id,
        )

        if model is None:
            return None

        return self._to_domain(model)

    def create(self, user: User) -> User:
        model = UserModel(
            nome=user.nome,
            email=user.email,
            senha_hash=user.senha_hash,
            criado_em=user.criado_em,
        )

        self._session.add(model)
        self._session.commit()
        self._session.refresh(model)

        return self._to_domain(model)