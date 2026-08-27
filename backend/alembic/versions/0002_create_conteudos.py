from alembic import op
import sqlalchemy as sa


revision = "0002_create_conteudos"
down_revision = "0001_create_usuarios"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "conteudos",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=False,
        ),
        sa.Column(
            "titulo",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "plataforma",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "data_publicacao",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_conteudos_usuario_id",
        "conteudos",
        ["usuario_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_conteudos_usuario_id",
        table_name="conteudos",
    )

    op.drop_table("conteudos")
