import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, is_authenticated

st.set_page_config(page_title="Income Statement | Zentox", page_icon="📑", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("📑 Income Statement (P&L)")

col1, col2, col3 = st.columns(3)
with col1:
    start = st.date_input("Start Date", value=date.today().replace(day=1))
with col2:
    end = st.date_input("End Date", value=date.today())
with col3:
    st.markdown(" ")
    run = st.button("📊 Generate P&L", use_container_width=True)

if run or "pnl_data" in st.session_state:
    with st.spinner("Computing P&L..."):
        try:
            data = get("/financials/income-statement", params={"start_date": str(start), "end_date": str(end)})
            st.session_state["pnl_data"] = data
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    data = st.session_state.get("pnl_data", {})

    # --- Summary metrics ---
    rev = data.get("revenue", {}).get("total", 0)
    cogs = data.get("cost_of_goods_sold", 0)
    gp = data.get("gross_profit", 0)
    gm = data.get("gross_margin_pct", 0)
    opex = data.get("operating_expenses", {}).get("total", 0)
    net = data.get("operating_income", 0)
    nm = data.get("net_margin_pct", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Revenue", f"${rev:,.2f}")
    c2.metric("🏷️ COGS", f"${cogs:,.2f}")
    c3.metric("📈 Gross Profit", f"${gp:,.2f}", f"{gm}% margin")
    c4.metric("💸 OpEx", f"${opex:,.2f}")
    c5.metric("✅ Net Income", f"${net:,.2f}", f"{nm}% margin", delta_color="normal" if net >= 0 else "inverse")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Revenue by Service")
        by_service = data.get("revenue", {}).get("by_service", {})
        if by_service:
            df_svc = pd.DataFrame(list(by_service.items()), columns=["Service", "Revenue"])
            df_svc = df_svc.sort_values("Revenue", ascending=False)
            fig = px.bar(df_svc, x="Revenue", y="Service", orientation="h", color="Revenue", color_continuous_scale="Blues")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No revenue data for this period.")

    with col_right:
        st.subheader("Expenses by Category")
        by_cat = data.get("operating_expenses", {}).get("by_category", {})
        if by_cat:
            df_exp = pd.DataFrame(list(by_cat.items()), columns=["Category", "Amount"])
            fig2 = px.pie(df_exp, values="Amount", names="Category", color_discrete_sequence=px.colors.qualitative.Set3)
            fig2.update_layout(margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for this period.")

    # --- Full P&L Table ---
    st.markdown("---")
    st.subheader("Full P&L Detail")
    pnl_rows = [
        {"Line Item": "**REVENUE**", "Amount": ""},
        *[{"Line Item": f"  {svc}", "Amount": f"${amt:,.2f}"} for svc, amt in data.get("revenue", {}).get("by_service", {}).items()],
        {"Line Item": "**Total Revenue**", "Amount": f"${rev:,.2f}"},
        {"Line Item": "---", "Amount": ""},
        {"Line Item": "Cost of Goods Sold (Supplies)", "Amount": f"(${cogs:,.2f})"},
        {"Line Item": "**Gross Profit**", "Amount": f"${gp:,.2f}  ({gm}%)"},
        {"Line Item": "---", "Amount": ""},
        {"Line Item": "**OPERATING EXPENSES**", "Amount": ""},
        *[{"Line Item": f"  {cat}", "Amount": f"(${amt:,.2f})"} for cat, amt in data.get("operating_expenses", {}).get("by_category", {}).items()],
        {"Line Item": "**Total Operating Expenses**", "Amount": f"(${opex:,.2f})"},
        {"Line Item": "---", "Amount": ""},
        {"Line Item": "**NET INCOME**", "Amount": f"${net:,.2f}  ({nm}%)"},
    ]
    df_pnl = pd.DataFrame(pnl_rows)
    st.dataframe(df_pnl, use_container_width=True, hide_index=True)
