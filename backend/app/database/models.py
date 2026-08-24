from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class UserModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
    )

    senha_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ContentModel(Base):
    __tablename__ = "conteudos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )

    titulo: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    plataforma: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    data_publicacao: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

class MetricModel(Base):
    __tablename__ = "metricas"

    __table_args__ = (
        UniqueConstraint(
            "conteudo_id",
            "data_referencia",
            name="uq_metricas_conteudo_data_referencia",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    conteudo_id: Mapped[int] = mapped_column(
        ForeignKey(
            "conteudos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    visualizacoes: Mapped[int] = mapped_column(
        nullable=False,
    )

    curtidas: Mapped[int] = mapped_column(
        nullable=False,
    )

    comentarios: Mapped[int] = mapped_column(
        nullable=False,
    )

    compartilhamentos: Mapped[int] = mapped_column(
        nullable=False,
    )

    alcance: Mapped[int] = mapped_column(
        nullable=False,
    )

    data_referencia: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
