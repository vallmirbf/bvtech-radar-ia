import re
from dataclasses import dataclass

PRICE_PATTERNS = [
    r"R\$\s*([\d\.]+,\d{2})",
    r"R\$\s*([\d\.]+)",
]
URL_PATTERN = re.compile(r"https?://\S+", re.I)

@dataclass
class ParsedOffer:
    title: str
    buy_price: float
    url: str

def parse_brl(value: str) -> float:
    value = value.replace(".", "").replace(",", ".")
    return float(value)

def parse_offer(text: str) -> ParsedOffer | None:
    text = (text or "").strip()
    if not text:
        return None

    price = None
    for pattern in PRICE_PATTERNS:
        match = re.search(pattern, text, re.I)
        if match:
            price = parse_brl(match.group(1))
            break

    if price is None:
        return None

    url_match = URL_PATTERN.search(text)
    url = url_match.group(0).rstrip(").,]") if url_match else ""
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "Oferta")
    return ParsedOffer(title=first_line[:500], buy_price=price, url=url)
