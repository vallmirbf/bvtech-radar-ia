from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.config import settings
from app.db import init_db, SessionLocal, Offer


st.set_page_config(
    page_title="BV-TECH Radar IA",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 14px 16px;
            border-radius: 14px;
        }
        .status-ok {
            display:inline-block; padding:5px 10px; border-radius:999px;
            background:#123c2a; color:#65e6a5; font-weight:700; font-size:.82rem;
        }
        .status-warn {
            display:inline-block; padding:5px 10px; border-radius:999px;
            background:#4a3510; color:#ffd36a; font-weight:700; font-size:.82rem;
        }
        .hero {
            border: 1px solid rgba(255,255,255,.08);
            background: linear-gradient(135deg, rgba(45,92,255,.18), rgba(0,201,167,.08));
            border-radius: 18px; padding: 22px 24px; margin-bottom: 18px;
        }
        .hero h1 {margin:0; font-size:2.1rem;}
        .hero p {margin:.45rem 0 0 0; color:#aeb7c4;}
        .decision-buy {color:#5ce39a; font-weight:800;}
        .decision-ignore {color:#ffbd5c; font-weight:800;}
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()


def brl(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%".replace(".", ",")


@st.cache_data(ttl=15)
def load_offers() -> pd.DataFrame:
    with SessionLocal() as db:
        rows = db.execute(
            select(Offer).order_by(Offer.created_at.desc()).limit(5000)
        ).scalars().all()

    data = []
    for x in rows:
        data.append(
            {
                "id": x.id,
                "Data": x.created_at,
                "Status": "COMPRAR" if x.approved else "IGNORAR/MONITORAR",
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
            }
        )
    return pd.DataFrame(data)


df = load_offers()

st.markdown(
    """
    <div class="hero">
      <h1>📡 BV-TECH Radar IA</h1>
      <p>Central de inteligência para filtrar ofertas, estimar margem e priorizar compras para revenda.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("⚙️ Controle da V1")
    st.caption("Filtros e regras atuais")

    if st.button("🔄 Atualizar agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    status_options = ["COMPRAR", "IGNORAR/MONITORAR"]
    selected_status = st.multiselect("Status", status_options, default=status_options)

    source_options = sorted(df["Fonte"].dropna().unique().tolist()) if not df.empty else []
    selected_sources = st.multiselect("Fontes / grupos", source_options, default=source_options)

    search_text = st.text_input("Buscar produto", placeholder="Ex.: Ryzen, iPhone, SSD")

    min_price = float(settings.min_buy_price)
    max_price = float(settings.max_buy_price)
    price_range = st.slider(
        "Faixa de compra",
        min_value=0.0,
        max_value=max(10000.0, max_price),
        value=(min_price, max_price),
        step=50.0,
        format="R$ %.0f",
    )

    st.divider()
    st.subheader("Regras vigentes")
    st.write(f"Ticket: **{brl(settings.min_buy_price)} a {brl(settings.max_buy_price)}**")
    st.write(f"ROI mínimo: **{pct(settings.min_roi_pct)}**")
    st.write(f"Lucro mínimo: **{brl(settings.min_net_profit)}**")
    st.write(f"Desconto mínimo: **{pct(settings.min_discount_pct)}**")

filtered = df.copy()
if not filtered.empty:
    filtered = filtered[filtered["Status"].isin(selected_status)]
    if selected_sources:
        filtered = filtered[filtered["Fonte"].isin(selected_sources)]
    filtered = filtered[
        filtered["Compra"].between(price_range[0], price_range[1], inclusive="both")
    ]
    if search_text.strip():
        filtered = filtered[
            filtered["Produto"].str.contains(search_text.strip(), case=False, na=False)
        ]

if df.empty:
    st.info("Nenhuma oferta capturada ainda. O coletor está aguardando novas mensagens do Telegram.")
    st.stop()

approved_total = int((df["Status"] == "COMPRAR").sum())
approval_rate = approved_total / len(df) * 100
potential_profit = float(df.loc[df["Status"] == "COMPRAR", "Lucro líquido"].fillna(0).sum())
capital_required = float(df.loc[df["Status"] == "COMPRAR", "Compra"].fillna(0).sum())
latest_at = pd.to_datetime(df["Data"].max())
is_recent = latest_at >= datetime.now() - timedelta(hours=24)

health_col, updated_col = st.columns([1, 3])
with health_col:
    badge = "status-ok" if is_recent else "status-warn"
    label = "COLETOR ATIVO" if is_recent else "SEM NOVAS OFERTAS"
    st.markdown(f'<span class="{badge}">{label}</span>', unsafe_allow_html=True)
with updated_col:
    st.caption(f"Última oferta capturada: {latest_at.strftime('%d/%m/%Y %H:%M:%S')}")

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Ofertas analisadas", f"{len(df):,}".replace(",", "."))
m2.metric("Aprovadas", approved_total)
m3.metric("Taxa de aprovação", pct(approval_rate))
m4.metric("Lucro potencial", brl(potential_profit))
m5.metric("Capital necessário", brl(capital_required))

st.write("")

tab_opportunities, tab_analysis, tab_simulator, tab_rules = st.tabs(
    ["🎯 Oportunidades", "📊 Análises", "🧮 Simulador", "🛠️ Diagnóstico"]
)

with tab_opportunities:
    buy_df = filtered[filtered["Status"] == "COMPRAR"].copy()
    if buy_df.empty:
        st.warning("Nenhuma oportunidade aprovada com os filtros atuais.")
    else:
        buy_df = buy_df.sort_values(["IOB", "ROI %", "Lucro líquido"], ascending=False)
        for _, row in buy_df.head(10).iterrows():
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([3, 1.2, 1.2, 1.2, 1])
                c1.markdown(f"### {row['Produto']}")
                c1.caption(f"Fonte: {row['Fonte']} · {row['Motivo']}")
                c2.metric("Compra", brl(row["Compra"]))
                c3.metric("Venda", brl(row["Mercado"]))
                c4.metric("Lucro", brl(row["Lucro líquido"]))
                c5.metric("IOB", f"{row['IOB']:.0f}/100")
                if row.get("Link"):
                    st.link_button("Abrir oferta", row["Link"])

    st.subheader("Todas as ofertas filtradas")
    display_df = filtered.copy()
    display_df["Data"] = pd.to_datetime(display_df["Data"]).dt.strftime("%d/%m/%Y %H:%M")
    display_df["Compra"] = display_df["Compra"].apply(brl)
    display_df["Mercado"] = display_df["Mercado"].apply(brl)
    display_df["Lucro líquido"] = display_df["Lucro líquido"].apply(brl)
    display_df["Desconto %"] = display_df["Desconto %"].apply(pct)
    display_df["ROI %"] = display_df["ROI %"].apply(pct)
    visible_columns = [
        "Data", "Status", "Produto", "Compra", "Mercado", "Lucro líquido",
        "ROI %", "IOB", "Concorrentes", "Fonte", "Motivo", "Link"
    ]
    st.dataframe(
        display_df[visible_columns],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Link": st.column_config.LinkColumn("Oferta", display_text="Abrir"),
            "Produto": st.column_config.TextColumn("Produto", width="large"),
            "Motivo": st.column_config.TextColumn("Motivo", width="large"),
        },
    )

with tab_analysis:
    left, right = st.columns(2)
    with left:
        st.subheader("Ofertas por fonte")
        source_counts = df.groupby("Fonte").size().sort_values(ascending=False).head(15)
        st.bar_chart(source_counts)
    with right:
        st.subheader("Decisões do radar")
        decision_counts = df.groupby("Status").size()
        st.bar_chart(decision_counts)

    chart_df = df.dropna(subset=["Compra"]).copy()
    if not chart_df.empty:
        st.subheader("Distribuição dos preços capturados")
        bins = pd.cut(chart_df["Compra"], bins=[0, 500, 1000, 2000, 3000, 5000, 10000, float("inf")])
        histogram = bins.value_counts().sort_index()
        histogram.index = histogram.index.astype(str)
        st.bar_chart(histogram)

    st.subheader("Principais motivos de rejeição")
    reasons = (
        df[df["Status"] != "COMPRAR"]["Motivo"]
        .fillna("Sem motivo informado")
        .value_counts()
        .head(10)
    )
    st.dataframe(reasons.rename("Quantidade"), use_container_width=True)

with tab_simulator:
    st.subheader("Simulador rápido de revenda no Mercado Livre")
    st.caption("Use para validar manualmente uma oferta antes de comprar.")

    c1, c2, c3 = st.columns(3)
    buy_price = c1.number_input("Preço de compra", min_value=0.0, value=2500.0, step=10.0)
    sale_price = c2.number_input("Preço de venda", min_value=0.0, value=3300.0, step=10.0)
    inbound_freight = c3.number_input("Frete da compra", min_value=0.0, value=0.0, step=5.0)

    c4, c5, c6 = st.columns(3)
    ml_fee = c4.number_input("Tarifa ML (%)", min_value=0.0, max_value=30.0, value=float(settings.ml_fee_pct), step=0.5)
    tax = c5.number_input("Impostos (%)", min_value=0.0, max_value=30.0, value=float(settings.tax_pct), step=0.5)
    ads = c6.number_input("Publicidade (%)", min_value=0.0, max_value=30.0, value=float(settings.ads_pct), step=0.5)

    costs = (
        buy_price
        + inbound_freight
        + float(settings.packaging_cost)
        + float(settings.default_freight_cost)
        + sale_price * (ml_fee + tax + ads) / 100
    )
    net_profit = sale_price - costs
    roi = net_profit / buy_price * 100 if buy_price else 0
    max_buy = sale_price - (
        inbound_freight
        + float(settings.packaging_cost)
        + float(settings.default_freight_cost)
        + sale_price * (ml_fee + tax + ads) / 100
        + float(settings.min_net_profit)
    )

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Lucro líquido", brl(net_profit))
    r2.metric("ROI", pct(roi))
    r3.metric("Preço máximo de compra", brl(max_buy))
    r4.metric("Decisão", "COMPRAR" if net_profit >= settings.min_net_profit and roi >= settings.min_roi_pct else "IGNORAR")

    if net_profit >= settings.min_net_profit and roi >= settings.min_roi_pct:
        st.success("A operação atende às regras mínimas atuais da BV-TECH.")
    else:
        st.error("A operação não atende às regras mínimas de lucro e ROI.")

with tab_rules:
    st.subheader("Diagnóstico da V1")
    d1, d2, d3 = st.columns(3)
    d1.success("Dashboard online")
    d2.success("Banco SQLite conectado")
    d3.success("Coletor registrando mensagens" if is_recent else "Coletor sem novas mensagens")

    st.write("**Banco de dados:**", settings.database_url)
    st.write("**Limite de concorrentes:**", settings.max_competitors)
    st.write("**Custo padrão de embalagem:**", brl(settings.packaging_cost))
    st.write("**Frete padrão de venda:**", brl(settings.default_freight_cost))
    st.info("As regras ainda são carregadas do arquivo .env. A edição direta pelo painel será a próxima melhoria da V1.")
