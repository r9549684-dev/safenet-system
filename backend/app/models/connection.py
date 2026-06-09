import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ConnectionStatus(str, enum.Enum):
    """Статус подключения для поддержки пула конфигов (Seamless Failover)."""
    ACTIVE = "ACTIVE"
    STANDBY = "STANDBY"
    REVOKED = "REVOKED"


class UserConnection(Base):
    """
    Хранит WireGuard-подключения пользователей для поддержки пула конфигов (Seamless Failover).
    Пользователь может иметь до 3 активных/резервных записей на сервер (1 ACTIVE, до 2 STANDBY).
    Заблокированные конфиги переводятся в статус REVOKED.
    """
    __tablename__ = "user_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Ссылки
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    server_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("servers.id", ondelete="CASCADE"), index=True, nullable=False
    )

    # WireGuard-ключи (private key хранится в plaintext для MVP;
    # в проде — шифровать через KMS/Vault)
    peer_private_key: Mapped[str] = mapped_column(Text, nullable=False)
    peer_public_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Выделенный IP в пуле (например "10.8.0.5")
    allocated_ip: Mapped[str] = mapped_column(String(15), nullable=False, index=True)

    # Статус подключения для пула (ACTIVE, STANDBY, REVOKED)
    status: Mapped[ConnectionStatus] = mapped_column(
        SQLEnum(ConnectionStatus), 
        default=ConnectionStatus.ACTIVE, 
        nullable=False, 
        index=True
    )

    # Временны́е метки
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
