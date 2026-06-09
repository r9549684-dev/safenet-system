from datetime import datetime
from sqlalchemy import Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class NodeMetrics(Base):
    __tablename__ = "service_node_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int] = mapped_column(Integer, ForeignKey("servers.id"), index=True)
    
    rtt_avg: Mapped[float] = mapped_column(Float, default=999.0)
    jitter: Mapped[float] = mapped_column(Float, default=100.0)
    loss_pct: Mapped[float] = mapped_column(Float, default=50.0)
    throughput_kbps: Mapped[float] = mapped_column(Float, default=10.0)
    life_hours: Mapped[float] = mapped_column(Float, default=1.0)
    
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Server (optional but useful)
    # server = relationship("Server", back_populates="metrics")
