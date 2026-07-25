import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.db import init_db, SessionLocal, Offer

st.set_page_config(page_title="BV-TECH Radar IA", layout="wide")
init_db()

st.title("BV-TECH Radar IA")
st.caption("Ofertas capturadas, validadas e classificadas pelo Índice de Oportunidade BV-TECH.")

with SessionLocal() as db:
    rows = db.execute(select(Offer).order_by(Offer.created_at.desc()).limit(1000)).scalars().all()

data = [{
    "Data": x.created_at,
    "Status": "COMPRAR" if x.approved else "PENDENTE/IGNORAR",
    "Produto": x.title,
    "Compra": x.buy_price,
    "Mercado": x.market_price,
    "Desconto %": x.discount_pct,
    "Lucro líquido": x.net_profit,
    "ROI %": x.roi_pct,
    "IOB": x.score,
    "Concorrentes": x.competitors,
    "Motivo": x.reason,
    "Fonte": x.source,
    "Link": x.url,
} for x in rows]

df = pd.DataFrame(data)

if df.empty:
    st.info("Nenhuma oferta capturada ainda.")
else:
    approved = int((df["Status"] == "COMPRAR").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Ofertas analisadas", len(df))
    c2.metric("Aprovadas", approved)
    c3.metric("Taxa de aprovação", f"{approved / len(df) * 100:.1f}%")
    st.dataframe(df, use_container_width=True, hide_index=True)
