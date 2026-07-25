from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    website: Mapped[str] = mapped_column(Text, default="")
    supplier_type: Mapped[str] = mapped_column(String(40), default="telegram")
    requires_login: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    collector_key: Mapped[str] = mapped_column(String(80), default="telegram")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    offers: Mapped[list[SupplierOffer]] = relationship(back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(Text, index=True)
    normalized_key: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    brand: Mapped[str] = mapped_column(String(100), default="")
    model: Mapped[str] = mapped_column(String(160), default="")
    ean: Mapped[str] = mapped_column(String(32), default="", index=True)
    sku: Mapped[str] = mapped_column(String(100), default="", index=True)
    category: Mapped[str] = mapped_column(String(100), default="")
    condition: Mapped[str] = mapped_column(String(30), default="novo")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    offers: Mapped[list[SupplierOffer]] = relationship(back_populates="product")
    market_snapshots: Mapped[list[MarketSnapshot]] = relationship(back_populates="product")


class SupplierOffer(Base):
    __tablename__ = "supplier_offers"
    __table_args__ = (
        UniqueConstraint("supplier_id", "external_id", name="uq_supplier_external_offer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(180), index=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float] = mapped_column(Float)
    freight: Mapped[float] = mapped_column(Float, default=0)
    coupon: Mapped[float] = mapped_column(Float, default=0)
    cashback: Mapped[float] = mapped_column(Float, default=0)
    stock_status: Mapped[str] = mapped_column(String(30), default="desconhecido")
    source_kind: Mapped[str] = mapped_column(String(30), default="external")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    supplier: Mapped[Supplier] = relationship(back_populates="offers")
    product: Mapped[Product] = relationship(back_populates="offers")
    analyses: Mapped[list[ViabilityAnalysis]] = relationship(back_populates="supplier_offer")

    @property
    def effective_cost(self) -> float:
        return max(0.0, self.price + self.freight - self.coupon - self.cashback)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    marketplace: Mapped[str] = mapped_column(String(40), default="mercado_livre")
    minimum_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    median_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    sustainable_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    competitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sold_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_competitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    official_store_competitors: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, default="")
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    product: Mapped[Product] = relationship(back_populates="market_snapshots")
    analyses: Mapped[list[ViabilityAnalysis]] = relationship(back_populates="market_snapshot")


class ViabilityAnalysis(Base):
    __tablename__ = "viability_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_offer_id: Mapped[int] = mapped_column(ForeignKey("supplier_offers.id"), index=True)
    market_snapshot_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_snapshots.id"), nullable=True, index=True
    )
    expected_sale_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    marketplace_fee: Mapped[float] = mapped_column(Float, default=0)
    taxes: Mapped[float] = mapped_column(Float, default=0)
    outbound_freight: Mapped[float] = mapped_column(Float, default=0)
    advertising_cost: Mapped[float] = mapped_column(Float, default=0)
    packaging_cost: Mapped[float] = mapped_column(Float, default=0)
    net_profit: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_buy_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0)
    decision: Mapped[str] = mapped_column(String(30), default="monitorar")
    reason: Mapped[str] = mapped_column(Text, default="")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    supplier_offer: Mapped[SupplierOffer] = relationship(back_populates="analyses")
    market_snapshot: Mapped[MarketSnapshot | None] = relationship(back_populates="analyses")


# Modelo legado mantido para preservar o dashboard e os dados já coletados.
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
