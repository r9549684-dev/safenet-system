"""add promocodes

Revision ID: 0004_add_promocodes
Revises: 0003_add_affiliate_system
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_add_promocodes"
down_revision = "0003_add_affiliate_system"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "promo_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("duration_months", sa.Integer(), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_promo_codes_code", "promo_codes", ["code"], unique=True)

    op.create_table(
        "promo_code_redemptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("promo_code_id", sa.Integer(), sa.ForeignKey("promo_codes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("granted_months", sa.Integer(), nullable=False),
        sa.UniqueConstraint("promo_code_id", "user_id", name="uq_promocode_user_redemption"),
    )
    op.create_index("ix_promocode_redemptions_code_id", "promo_code_redemptions", ["promo_code_id"])
    op.create_index("ix_promocode_redemptions_user_id", "promo_code_redemptions", ["user_id"])


def downgrade():
    op.drop_index("ix_promocode_redemptions_user_id", table_name="promo_code_redemptions")
    op.drop_index("ix_promocode_redemptions_code_id", table_name="promo_code_redemptions")
    op.drop_table("promo_code_redemptions")
    op.drop_index("ix_promo_codes_code", table_name="promo_codes")
    op.drop_table("promo_codes")

