from dataclasses import dataclass

@dataclass
class MarketSnapshot:
    sustainable_price: float | None
    competitors: int | None
    source: str
    confidence: float
    note: str = ""

def find_market_snapshot(title: str, url: str = "") -> MarketSnapshot:
    # Ponto de extensão.
    # Nunca estimar silenciosamente: enquanto não houver adaptador de mercado,
    # a oferta fica pendente em vez de ser aprovada com informação inventada.
    return MarketSnapshot(
        sustainable_price=None,
        competitors=None,
        source="pending",
        confidence=0.0,
        note="Preço de mercado ainda não validado por uma fonte externa."
    )
