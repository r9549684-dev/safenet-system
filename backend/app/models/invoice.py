from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, Numeric, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), index=True)

    provider: Mapped[str] = mapped_column(String(32))
    provider_invoice_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)

    asset: Mapped[str] = mapped_column(String(16))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6))

    status: Mapped[str] = mapped_column(String(32), index=True)  # pending/paid/expired/failed

    payload: Mapped[str] = mapped_column(String(255))
    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)