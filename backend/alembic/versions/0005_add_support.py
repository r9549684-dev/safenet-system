"""add support tables

Revision ID: 0005_add_support
Revises: 0004_add_promocodes
Create Date: 2026-02-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_add_support"
down_revision = "0004_add_promocodes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "support_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lang", sa.String(length=5), nullable=False, server_default="en"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("rating", sa.SmallInteger(), nullable=True),
    )
    op.create_index("ix_support_sessions_user_id", "support_sessions", ["user_id"])
    op.create_index("ix_support_sessions_resolved_at", "support_sessions", ["resolved_at"])

    op.create_table(
        "support_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("support_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),   # 'user' | 'agent'
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_support_messages_session_id", "support_messages", ["session_id"])
    op.create_index("ix_support_messages_user_id", "support_messages", ["user_id"])


def downgrade():
    op.drop_index("ix_support_messages_user_id", table_name="support_messages")
    op.drop_index("ix_support_messages_session_id", table_name="support_messages")
    op.drop_table("support_messages")
    op.drop_index("ix_support_sessions_resolved_at", table_name="support_sessions")
    op.drop_index("ix_support_sessions_user_id", table_name="support_sessions")
    op.drop_table("support_sessions")
