"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.String(), nullable=False, unique=True, index=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("referral_code", sa.String(length=16), nullable=True, unique=True),
        sa.Column("referred_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_premium", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("premium_until", sa.DateTime(timezone=False), nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=2), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.UniqueConstraint("country", name="uq_profiles_country"),
    )

    op.create_table(
        "servers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("country", sa.String(length=2), nullable=False, index=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False, server_default=sa.text("51820")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_invoice_id", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("asset", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, index=True),
        sa.Column("payload", sa.String(length=255), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=False), nullable=True),
    )

def downgrade():
    op.drop_table("invoices")
    op.drop_table("servers")
    op.drop_table("profiles")
    op.drop_table("users")