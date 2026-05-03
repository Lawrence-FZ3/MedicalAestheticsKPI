import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, is_authenticated

st.set_page_config(page_title="Cash Flow | Zentox", page_icon="💸", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("💸 Cash Flow Statement")

col1, col2, col3 = st.columns(3)
with col1:
    start = st.date_input("Start Date", value=date.today().replace(day=1))
with col2:
    end = st.date_input("End Date", value=date.today())
with col3:
    st.markdown(" ")
    run = st.button("📊 Generate Cash Flow", use_container_width=True)

if run:
    with st.spinner("Computing cash flow..."):
        try:
            data = get("/financials/cash-flow", params={"start_date": str(start), "end_date": str(end)})
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()

    ops = data.get("operating_activities", {})
    inflows = ops.get("cash_inflows", 0)
    outflows = ops.get("cash_outflows", 0)
    net = ops.get("net_operating_cash_flow", 0)

    c1, c2, c3 = st.columns(3)
    c1.metric("💚 Cash Inflows", f"${inflows:,.2f}")
    c2.metric("🔴 Cash Outflows", f"${outflows:,.2f}")
    c3.metric("📊 Net Cash Flow", f"${net:,.2f}", delta_color="normal" if net >= 0 else "inverse")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Inflows by Source")
        inflow_detail = ops.get("inflow_detail", {})
        if inflow_detail:
            df = pd.DataFrame(list(inflow_detail.items()), columns=["Source", "Amount"])
            fig = px.bar(df, x="Source", y="Amount", color="Source", color_discrete_sequence=["#48CAE4", "#90BE6D", "#6C63FF"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Outflows by Category")
        outflow_detail = ops.get("outflow_detail", {})
        if outflow_detail:
            df2 = pd.DataFrame(list(outflow_detail.items()), columns=["Category", "Amount"])
            fig2 = px.bar(df2, x="Category", y="Amount", color="Category")
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            fig2.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Cash Flow Summary")
    summary = [
        {"Section": "Operating Activities", "Item": "Cash Inflows (Revenue Collected)", "Amount": f"${inflows:,.2f}"},
        {"Section": "Operating Activities", "Item": "Cash Outflows (Expenses Paid)", "Amount": f"(${outflows:,.2f})"},
        {"Section": "Operating Activities", "Item": "**Net Operating Cash Flow**", "Amount": f"${net:,.2f}"},
        {"Section": "Net Change", "Item": "**Net Change in Cash**", "Amount": f"${data.get('net_change_in_cash', 0):,.2f}"},
    ]
    st.dataframe(pd.DataFrame(summary), use_container_width=True, hide_index=True)
