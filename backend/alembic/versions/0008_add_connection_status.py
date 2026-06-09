"""add_connection_status

Revision ID: 0008_add_connection_status
Revises: 0007_add_telegram_link
Create Date: 2026-06-05

"""
from alembic import op
import sqlalchemy as sa

revision = "0008_add_connection_status"
down_revision = "0007_add_telegram_link"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Создаем ENUM тип для статусов подключения
    conn_status_enum = sa.Enum('ACTIVE', 'STANDBY', 'REVOKED', name='connectionstatus')
    conn_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Добавляем колонку status со значением по умолчанию 'ACTIVE'
    op.add_column(
        'user_connections',
        sa.Column('status', conn_status_enum, nullable=False, server_default='ACTIVE')
    )

    # 3. Мигрируем старые данные: если is_active == false, ставим REVOKED, иначе ACTIVE
    op.execute(
        sa.text("""
            UPDATE user_connections 
            SET status = 'REVOKED' 
            WHERE is_active = false
        """)
    )

    # 4. Удаляем старую колонку is_active
    op.drop_column('user_connections', 'is_active')

    # 5. Добавляем индекс на status для быстрых выборок пула
    op.create_index('ix_user_connections_status', 'user_connections', ['status'])


def downgrade():
    # 1. Возвращаем is_active
    op.add_column(
        'user_connections',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )

    # 2. Мигрируем данные обратно: ACTIVE/STANDBY -> true, REVOKED -> false
    op.execute(
        sa.text("""
            UPDATE user_connections 
            SET is_active = false 
            WHERE status = 'REVOKED'
        """)
    )

    # 3. Удаляем колонку status и индекс
    op.drop_index('ix_user_connections_status', table_name='user_connections')
    op.drop_column('user_connections', 'status')

    # 4. Удаляем ENUM тип
    conn_status_enum = sa.Enum('ACTIVE', 'STANDBY', 'REVOKED', name='connectionstatus')
    conn_status_enum.drop(op.get_bind(), checkfirst=True)