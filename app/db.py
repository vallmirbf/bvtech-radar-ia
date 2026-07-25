from datetime import datetime
from sqlalchemy import create_engine, String, Float, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from .config import settings

class Base(DeclarativeBase):
    pass

class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(100))
    source_message_id: Mapped[str] = mapped_column(String(100), unique=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, default="")
    buy_price: Mapped[float] = mapped_column(Float)
    market_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    discount_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)

def init_db() -> None:
    Base.metadata.create_all(engine)
