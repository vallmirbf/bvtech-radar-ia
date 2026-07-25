import asyncio
from telethon import TelegramClient, events
from sqlalchemy.exc import IntegrityError

from .config import settings
from .db import init_db, SessionLocal, Offer
from .parser import parse_offer
from .market import find_market_snapshot
from .scoring import evaluate

def format_alert(offer: Offer) -> str:
    return (
        "🟢 BV-TECH RADAR — COMPRAR\n\n"
        f"Produto: {offer.title}\n"
        f"Compra: R$ {offer.buy_price:,.2f}\n"
        f"Mercado sustentável: R$ {offer.market_price:,.2f}\n"
        f"Desconto: {offer.discount_pct:.1f}%\n"
        f"Lucro líquido estimado: R$ {offer.net_profit:,.2f}\n"
        f"ROI: {offer.roi_pct:.1f}%\n"
        f"IOB: {offer.score:.1f}/100\n"
        f"Link: {offer.url}"
    ).replace(",", "X").replace(".", ",").replace("X", ".")

async def main() -> None:
    init_db()
    if not settings.telegram_api_id or not settings.telegram_api_hash:
        raise RuntimeError("Configure TELEGRAM_API_ID e TELEGRAM_API_HASH.")

    client = TelegramClient(
        settings.telegram_session,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    )
    await client.start(phone=settings.telegram_phone or None)

    chats = list(settings.telegram_source_chats) or None

    @client.on(events.NewMessage(chats=chats))
    async def on_message(event):
        parsed = parse_offer(event.raw_text)
        if not parsed:
            return

        source = getattr(event.chat, "title", None) or str(event.chat_id)
        message_key = f"{event.chat_id}:{event.id}"
        market = find_market_snapshot(parsed.title, parsed.url)
        result = evaluate(parsed.buy_price, market)

        with SessionLocal() as db:
            offer = Offer(
                source=source,
                source_message_id=message_key,
                title=parsed.title,
                url=parsed.url,
                buy_price=parsed.buy_price,
                market_price=market.sustainable_price,
                competitors=market.competitors,
                discount_pct=result.discount_pct,
                net_profit=result.net_profit,
                roi_pct=result.roi_pct,
                score=result.score,
                approved=result.approved,
                reason=result.reason,
            )
            db.add(offer)
            try:
                db.commit()
                db.refresh(offer)
            except IntegrityError:
                db.rollback()
                return

        if result.approved and settings.telegram_alert_chat:
            await client.send_message(settings.telegram_alert_chat, format_alert(offer))

    print("BV-TECH Radar IA ativo.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
