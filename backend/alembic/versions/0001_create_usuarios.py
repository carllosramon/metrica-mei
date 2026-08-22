from alembic import op
import sqlalchemy as sa


revision = "0001_create_usuarios"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usuarios",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "nome",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=False,
        ),
        sa.Column(
            "senha_hash",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "email",
            name="uq_usuarios_email",
        ),
    )


def downgrade():
    op.drop_table("usuarios")