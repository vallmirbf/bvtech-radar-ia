from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import func, select

from app.db import (
    Product,
    SessionLocal,
    Supplier,
    SupplierOffer,
    ViabilityAnalysis,
    init_db,
)


st.set_page_config(page_title="Fornecedores | BV-TECH", page_icon="🏭", layout="wide")
init_db()


def brl(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(ttl=10)
def load_suppliers() -> pd.DataFrame:
    with SessionLocal() as db:
        rows = db.execute(
            select(
                Supplier.id,
                Supplier.name,
                Supplier.website,
                Supplier.supplier_type,
                Supplier.requires_login,
                Supplier.active,
                Supplier.priority,
                Supplier.collector_key,
                func.count(SupplierOffer.id).label("offers"),
            )
            .outerjoin(SupplierOffer, SupplierOffer.supplier_id == Supplier.id)
            .group_by(Supplier.id)
            .order_by(Supplier.priority.asc(), Supplier.name.asc())
        ).all()

    return pd.DataFrame(
        rows,
        columns=[
            "ID",
            "Fornecedor",
            "Site",
            "Tipo",
            "Exige login",
            "Ativo",
            "Prioridade",
            "Coletor",
            "Ofertas",
        ],
    )


@st.cache_data(ttl=10)
def load_opportunities() -> pd.DataFrame:
    with SessionLocal() as db:
        rows = db.execute(
            select(
                SupplierOffer.captured_at,
                Product.canonical_name,
                Supplier.name,
                SupplierOffer.price,
                SupplierOffer.freight,
                SupplierOffer.coupon,
                SupplierOffer.cashback,
                ViabilityAnalysis.expected_sale_price,
                ViabilityAnalysis.net_profit,
                ViabilityAnalysis.roi_pct,
                ViabilityAnalysis.score,
                ViabilityAnalysis.decision,
                SupplierOffer.url,
            )
            .join(Product, Product.id == SupplierOffer.product_id)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .outerjoin(
                ViabilityAnalysis,
                ViabilityAnalysis.supplier_offer_id == SupplierOffer.id,
            )
            .order_by(SupplierOffer.captured_at.desc())
            .limit(1000)
        ).all()

    return pd.DataFrame(
        rows,
        columns=[
            "Data",
            "Produto",
            "Fornecedor",
            "Compra",
            "Frete compra",
            "Cupom",
            "Cashback",
            "Venda ML",
            "Lucro líquido",
            "ROI %",
            "Score",
            "Decisão",
            "Link",
        ],
    )


st.title("🏭 Inteligência de fornecedores")
st.caption(
    "Fontes externas são oportunidades de compra. O Mercado Livre é usado como referência de venda e concorrência."
)

suppliers = load_suppliers()
opportunities = load_opportunities()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Fornecedores cadastrados", len(suppliers))
m2.metric("Fornecedores ativos", int(suppliers["Ativo"].sum()) if not suppliers.empty else 0)
m3.metric("Produtos normalizados", int(opportunities["Produto"].nunique()) if not opportunities.empty else 0)
m4.metric("Ofertas externas", len(opportunities))

register_tab, suppliers_tab, opportunities_tab = st.tabs(
    ["➕ Cadastrar fornecedor", "📋 Fornecedores", "🎯 Oportunidades de compra"]
)

with register_tab:
    with st.form("supplier_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nome do fornecedor *", placeholder="Ex.: Inpower")
        website = c2.text_input("Site", placeholder="https://...")

        c3, c4, c5 = st.columns(3)
        supplier_type = c3.selectbox(
            "Tipo",
            ["distribuidor", "atacadista", "varejista", "marketplace", "telegram", "catalogo"],
        )
        collector_key = c4.selectbox(
            "Forma de coleta",
            ["pendente", "site", "api", "telegram", "csv", "excel", "xml", "email"],
        )
        priority = c5.selectbox("Prioridade", [1, 2, 3, 4, 5], index=2)

        requires_login = st.checkbox("Exige login para consultar preço")
        notes = st.text_area("Observações")
        submitted = st.form_submit_button("Salvar fornecedor", use_container_width=True)

    if submitted:
        clean_name = name.strip()
        if not clean_name:
            st.error("Informe o nome do fornecedor.")
        else:
            with SessionLocal() as db:
                existing = db.scalar(select(Supplier).where(Supplier.name == clean_name))
                if existing:
                    st.warning("Esse fornecedor já está cadastrado.")
                else:
                    db.add(
                        Supplier(
                            name=clean_name,
                            website=website.strip(),
                            supplier_type=supplier_type,
                            collector_key=collector_key,
                            priority=priority,
                            requires_login=requires_login,
                            notes=notes.strip(),
                        )
                    )
                    db.commit()
                    st.cache_data.clear()
                    st.success("Fornecedor cadastrado. Agora ele pode receber um conector de coleta.")
                    st.rerun()

with suppliers_tab:
    if suppliers.empty:
        st.info("Nenhum fornecedor cadastrado.")
    else:
        edited = st.data_editor(
            suppliers,
            use_container_width=True,
            hide_index=True,
            disabled=["ID", "Fornecedor", "Ofertas"],
            column_config={
                "Site": st.column_config.LinkColumn("Site"),
                "Ativo": st.column_config.CheckboxColumn("Ativo"),
                "Exige login": st.column_config.CheckboxColumn("Exige login"),
                "Prioridade": st.column_config.NumberColumn("Prioridade", min_value=1, max_value=5),
            },
            key="supplier_editor",
        )

        if st.button("Salvar alterações", type="primary"):
            with SessionLocal() as db:
                for _, row in edited.iterrows():
                    supplier = db.get(Supplier, int(row["ID"]))
                    if supplier:
                        supplier.website = str(row["Site"] or "")
                        supplier.supplier_type = str(row["Tipo"])
                        supplier.requires_login = bool(row["Exige login"])
                        supplier.active = bool(row["Ativo"])
                        supplier.priority = int(row["Prioridade"])
                        supplier.collector_key = str(row["Coletor"])
                db.commit()
            st.cache_data.clear()
            st.success("Alterações salvas.")
            st.rerun()

with opportunities_tab:
    if opportunities.empty:
        st.info("As próximas ofertas coletadas aparecerão aqui no novo modelo de compras.")
    else:
        supplier_options = sorted(opportunities["Fornecedor"].dropna().unique().tolist())
        selected = st.multiselect("Fornecedores", supplier_options, default=supplier_options)
        search = st.text_input("Buscar produto", placeholder="Ex.: iPhone 16, SSD, notebook")

        filtered = opportunities[opportunities["Fornecedor"].isin(selected)].copy()
        if search.strip():
            filtered = filtered[
                filtered["Produto"].str.contains(search.strip(), case=False, na=False)
            ]

        for column in ["Compra", "Frete compra", "Cupom", "Cashback", "Venda ML", "Lucro líquido"]:
            filtered[column] = filtered[column].apply(brl)
        filtered["Data"] = pd.to_datetime(filtered["Data"]).dt.strftime("%d/%m/%Y %H:%M")

        st.dataframe(
            filtered,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Oferta", display_text="Abrir"),
                "Produto": st.column_config.TextColumn("Produto", width="large"),
            },
        )
