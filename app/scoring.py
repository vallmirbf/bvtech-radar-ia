from dataclasses import dataclass
from .config import settings
from .market import MarketSnapshot

@dataclass
class Evaluation:
    approved: bool
    discount_pct: float | None
    net_profit: float | None
    roi_pct: float | None
    score: float
    reason: str

def evaluate(buy_price: float, market: MarketSnapshot) -> Evaluation:
    if not settings.min_buy_price <= buy_price <= settings.max_buy_price:
        return Evaluation(False, None, None, None, 0, "Fora do ticket permitido.")

    if market.sustainable_price is None:
        return Evaluation(False, None, None, None, 0, market.note)

    sale = market.sustainable_price
    discount = (sale - buy_price) / sale * 100

    variable_pct = (
        settings.ml_fee_pct + settings.tax_pct + settings.ads_pct
    ) / 100
    costs = (
        buy_price
        + sale * variable_pct
        + settings.packaging_cost
        + settings.default_freight_cost
    )
    profit = sale - costs
    roi = profit / buy_price * 100

    score = 0
    score += min(max(discount, 0), 50) * 0.8
    score += min(max(roi, 0), 40) * 0.8
    score += min(max(profit / 20, 0), 20)
    if market.competitors is not None:
        score += max(0, 10 - market.competitors / 3)
    score = round(min(score, 100), 1)

    checks = [
        (discount >= settings.min_discount_pct,
         f"desconto {discount:.1f}% < {settings.min_discount_pct:.0f}%"),
        (roi >= settings.min_roi_pct,
         f"ROI {roi:.1f}% < {settings.min_roi_pct:.0f}%"),
        (profit >= settings.min_net_profit,
         f"lucro líquido R$ {profit:.2f} < R$ {settings.min_net_profit:.2f}"),
        (
            market.competitors is None or market.competitors <= settings.max_competitors,
            f"concorrentes {market.competitors} > {settings.max_competitors}",
        ),
    ]
    failures = [msg for ok, msg in checks if not ok]
    approved = not failures
    reason = "APROVADA" if approved else "; ".join(failures)

    return Evaluation(approved, discount, profit, roi, score, reason)
