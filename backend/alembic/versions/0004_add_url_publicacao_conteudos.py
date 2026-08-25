from alembic import op
import sqlalchemy as sa

revision = "0004_add_url_publicacao_conteudos"
down_revision = "0003_create_metricas"
branch_labels = None
depends_on = None


def upgrade():
    # Nullable porque a coluna nasce em uma tabela que já tem registros e
    # a especificação não exige a URL para publicar um conteúdo.
    op.add_column(
        "conteudos",
        sa.Column(
            "url_publicacao",
            sa.String(length=500),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "conteudos",
        "url_publicacao",
    )
