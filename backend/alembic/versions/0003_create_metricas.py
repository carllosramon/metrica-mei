from alembic import op
import sqlalchemy as sa


revision = "0003_create_metricas"
down_revision = "0002_create_conteudos"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "metricas",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "conteudo_id",
            sa.Integer(),
            sa.ForeignKey(
                "conteudos.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "visualizacoes",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "curtidas",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "comentarios",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "compartilhamentos",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "alcance",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_referencia",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "conteudo_id",
            "data_referencia",
            name="uq_metricas_conteudo_data_referencia",
        ),
    )


def downgrade():
    op.drop_table("metricas")
