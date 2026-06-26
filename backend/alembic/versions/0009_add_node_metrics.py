"""add node_metrics

Revision ID: 0009_add_node_metrics
Revises: 0008_add_connection_status
Create Date: 2026-06-26

SafeNet ANO: Node metrics for Scout/ANO ranking.
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_add_node_metrics"
down_revision = "0008_add_connection_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_node_metrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("server_id", sa.Integer(), sa.ForeignKey("servers.id"), nullable=False, index=True),
        sa.Column("rtt_avg", sa.Float(), nullable=False, server_default="999.0"),
        sa.Column("jitter", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("loss_pct", sa.Float(), nullable=False, server_default="50.0"),
        sa.Column("throughput_kbps", sa.Float(), nullable=False, server_default="10.0"),
        sa.Column("life_hours", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("service_node_metrics")
