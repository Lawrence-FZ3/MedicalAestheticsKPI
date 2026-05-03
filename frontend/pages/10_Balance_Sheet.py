import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, is_authenticated

st.set_page_config(page_title="Balance Sheet | Zentox", page_icon="⚖️", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("⚖️ Balance Sheet")

with st.spinner("Loading balance sheet..."):
    try:
        data = get("/financials/balance-sheet")
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

st.caption(f"As of {data.get('as_of', 'today')}")
st.markdown("---")

assets = data.get("assets", {})
liabilities = data.get("liabilities", {})
equity = data.get("equity", {})

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🟢 Assets")
    ca = assets.get("current_assets", {})
    rows = []
    for k, v in ca.items():
        rows.append({"Asset": k.replace("_", " ").title(), "Value": f"${float(v):,.2f}"})
    rows.append({"Asset": "**TOTAL ASSETS**", "Value": f"${assets.get('total_assets', 0):,.2f}"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("🔴 Liabilities")
    rows_l = []
    cl = liabilities.get("current_liabilities", {})
    for k, v in cl.items():
        rows_l.append({"Liability": k.replace("_", " ").title(), "Value": f"${float(v):,.2f}"})
    rows_l.append({"Liability": "**TOTAL LIABILITIES**", "Value": f"${liabilities.get('total_liabilities', 0):,.2f}"})
    st.dataframe(pd.DataFrame(rows_l), use_container_width=True, hide_index=True)

with col_right:
    st.subheader("🔵 Equity")
    rows_e = [
        {"Equity": "Retained Earnings", "Value": f"${equity.get('retained_earnings', 0):,.2f}"},
        {"Equity": "**TOTAL EQUITY**", "Value": f"${equity.get('total_equity', 0):,.2f}"},
    ]
    st.dataframe(pd.DataFrame(rows_e), use_container_width=True, hide_index=True)

    st.subheader("Balance Check")
    total_assets_val = assets.get("total_assets", 0)
    total_le = data.get("total_liabilities_and_equity", 0)
    balanced = abs(total_assets_val - total_le) < 0.01
    st.metric("Total Assets", f"${total_assets_val:,.2f}")
    st.metric("Total Liabilities + Equity", f"${total_le:,.2f}")
    if balanced:
        st.success("✅ Balance sheet is balanced")
    else:
        st.warning("⚠️ Balance sheet discrepancy — check your entries")

st.markdown("---")
st.info("💡 The balance sheet updates in real-time from your Appointments (revenue) and Expenses data. Connect more data sources via the Integrations page for higher accuracy.")
