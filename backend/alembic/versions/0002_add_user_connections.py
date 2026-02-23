"""add_user_connections

Revision ID: 0002_add_user_connections
Revises: 0001_init
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_user_connections"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_connections",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "server_id",
            sa.Integer(),
            sa.ForeignKey("servers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("peer_private_key", sa.Text(), nullable=False),
        sa.Column("peer_public_key", sa.String(length=64), nullable=False),
        sa.Column("allocated_ip", sa.String(length=15), nullable=False, index=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=False), nullable=True),
    )


def downgrade():
    op.drop_table("user_connections")
