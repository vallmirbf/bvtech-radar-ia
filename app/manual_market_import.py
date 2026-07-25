import csv
from pathlib import Path
from sqlalchemy import select

from .db import init_db, SessionLocal, Offer
from .market import MarketSnapshot
from .scoring import evaluate

def apply_csv(path: str) -> None:
    init_db()
    with open(path, newline="", encoding="utf-8") as f, SessionLocal() as db:
        for row in csv.DictReader(f):
            offer_id = int(row["offer_id"])
            offer = db.scalar(select(Offer).where(Offer.id == offer_id))
            if not offer:
                continue
            market = MarketSnapshot(
                sustainable_price=float(row["market_price"]),
                competitors=int(row["competitors"]) if row.get("competitors") else None,
                source=row.get("source", "manual"),
                confidence=float(row.get("confidence", 1)),
            )
            result = evaluate(offer.buy_price, market)
            offer.market_price = market.sustainable_price
            offer.competitors = market.competitors
            offer.discount_pct = result.discount_pct
            offer.net_profit = result.net_profit
            offer.roi_pct = result.roi_pct
            offer.score = result.score
            offer.approved = result.approved
            offer.reason = result.reason
        db.commit()

if __name__ == "__main__":
    import sys
    apply_csv(sys.argv[1])
