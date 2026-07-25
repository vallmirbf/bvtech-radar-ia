from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

def _float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default

@dataclass(frozen=True)
class Settings:
    telegram_api_id: int = int(os.getenv("TELEGRAM_API_ID", "0") or 0)
    telegram_api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    telegram_phone: str = os.getenv("TELEGRAM_PHONE", "")
    telegram_session: str = os.getenv("TELEGRAM_SESSION", "/data/bvtech")
    telegram_source_chats: tuple[str, ...] = tuple(
        x.strip() for x in os.getenv("TELEGRAM_SOURCE_CHATS", "").split(",") if x.strip()
    )
    telegram_alert_chat: str = os.getenv("TELEGRAM_ALERT_CHAT", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:////data/radar.db")

    min_buy_price: float = _float("MIN_BUY_PRICE", 500)
    max_buy_price: float = _float("MAX_BUY_PRICE", 5000)
    min_discount_pct: float = _float("MIN_DISCOUNT_PCT", 40)
    min_roi_pct: float = _float("MIN_ROI_PCT", 20)
    min_net_profit: float = _float("MIN_NET_PROFIT", 300)
    max_competitors: int = int(_float("MAX_COMPETITORS", 30))

    ml_fee_pct: float = _float("ML_FEE_PCT", 16)
    tax_pct: float = _float("TAX_PCT", 6)
    ads_pct: float = _float("ADS_PCT", 3)
    packaging_cost: float = _float("PACKAGING_COST", 15)
    default_freight_cost: float = _float("DEFAULT_FREIGHT_COST", 45)

settings = Settings()
