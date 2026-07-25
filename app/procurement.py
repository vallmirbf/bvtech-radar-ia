from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import MarketSnapshot, Product, Supplier, SupplierOffer, ViabilityAnalysis


def normalize_product_key(title: str) -> str:
    text = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"https?://\S+", " ", text.lower())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    tokens = [token for token in text.split() if len(token) > 1]
    return " ".join(tokens[:40])[:300] or "produto-sem-identificacao"


def get_or_create_supplier(
    db: Session,
    name: str,
    *,
    supplier_type: str = "telegram",
    collector_key: str = "telegram",
) -> Supplier:
    supplier = db.scalar(select(Supplier).where(Supplier.name == name))
    if supplier:
        return supplier

    supplier = Supplier(
        name=name,
        supplier_type=supplier_type,
        collector_key=collector_key,
        priority=3,
    )
    db.add(supplier)
    db.flush()
    return supplier


def get_or_create_product(db: Session, title: str) -> Product:
    normalized_key = normalize_product_key(title)
    product = db.scalar(select(Product).where(Product.normalized_key == normalized_key))
    if product:
        return product

    product = Product(canonical_name=title.strip(), normalized_key=normalized_key)
    db.add(product)
    db.flush()
    return product


def save_procurement_analysis(
    db: Session,
    *,
    supplier_name: str,
    external_id: str,
    title: str,
    url: str,
    buy_price: float,
    market_price: float | None,
    competitors: int | None,
    net_profit: float | None,
    roi_pct: float | None,
    score: float,
    approved: bool,
    reason: str,
    source_kind: str = "external",
) -> SupplierOffer | None:
    supplier = get_or_create_supplier(db, supplier_name)
    product = get_or_create_product(db, title)

    offer = SupplierOffer(
        supplier_id=supplier.id,
        product_id=product.id,
        external_id=external_id,
        title=title,
        url=url,
        price=buy_price,
        source_kind=source_kind,
    )
    db.add(offer)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return None

    snapshot = MarketSnapshot(
        product_id=product.id,
        sustainable_price=market_price,
        competitors=competitors,
    )
    db.add(snapshot)
    db.flush()

    analysis = ViabilityAnalysis(
        supplier_offer_id=offer.id,
        market_snapshot_id=snapshot.id,
        expected_sale_price=market_price,
        net_profit=net_profit,
        roi_pct=roi_pct,
        score=score,
        decision="comprar" if approved else "monitorar",
        reason=reason,
    )
    db.add(analysis)
    return offer
