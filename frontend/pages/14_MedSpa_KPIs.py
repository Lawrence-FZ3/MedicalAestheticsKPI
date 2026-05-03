import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, is_authenticated
from frontend.utils.charts import kpi_gauge

st.set_page_config(page_title="MedSpa KPIs | Zentox", page_icon="🏥", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("🏥 MedSpa KPI Center")
st.caption("Industry benchmarks and performance metrics specific to medical aesthetics.")

with st.spinner("Computing MedSpa KPIs..."):
    try:
        kpis = get("/financials/medspa-kpis")
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()

rev = kpis.get("revenue", {})
appts = kpis.get("appointments", {})
prof = kpis.get("profitability", {})
exp = kpis.get("expenses", {})
benchmarks = kpis.get("benchmarks", {})

# --- Revenue banner ---
st.markdown("### 💰 Revenue")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"${rev.get('total', 0):,.2f}")
c2.metric("Revenue / Appointment", f"${rev.get('per_appointment', 0):,.2f}", help="Industry target: $200-500+")
c3.metric("Total Appointments", appts.get("total", 0))
c4.metric("Completed", appts.get("completed", 0))

# --- Profitability gauges ---
st.markdown("---")
st.markdown("### 📊 Profitability Benchmarks")
st.caption("Green zone = healthy MedSpa performance")

g1, g2, g3, g4 = st.columns(4)
with g1:
    fig = kpi_gauge(prof.get("profit_margin_pct", 0), "Net Profit Margin", max_val=40, suffix="%")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Target: {benchmarks.get('ideal_profit_margin', '15-25%')}")

with g2:
    fig2 = kpi_gauge(prof.get("payroll_ratio_pct", 0), "Payroll Ratio", max_val=70, suffix="%")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption(f"Target: {benchmarks.get('ideal_payroll_ratio', '35-45%')}")

with g3:
    fig3 = kpi_gauge(appts.get("no_show_rate_pct", 0), "No-Show Rate", max_val=30, suffix="%")
    st.plotly_chart(fig3, use_container_width=True)
    st.caption(f"Target: {benchmarks.get('ideal_no_show_rate', '< 10%')}")

with g4:
    fig4 = kpi_gauge(prof.get("overhead_ratio_pct", 0), "Overhead Ratio", max_val=100, suffix="%")
    st.plotly_chart(fig4, use_container_width=True)
    st.caption(f"Target: {benchmarks.get('ideal_overhead_ratio', '< 70%')}")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🏆 Top Services by Revenue")
    top_services = rev.get("top_services", {})
    if top_services:
        df = pd.DataFrame(list(top_services.items()), columns=["Service", "Revenue"])
        df = df.sort_values("Revenue", ascending=True)
        fig = px.bar(df, x="Revenue", y="Service", orientation="h",
                     color="Revenue", color_continuous_scale="Teal",
                     text="Revenue")
        fig.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No service revenue data yet.")

with col_right:
    st.subheader("👩‍⚕️ Revenue by Provider")
    by_provider = rev.get("by_provider", {})
    if by_provider:
        df2 = pd.DataFrame(list(by_provider.items()), columns=["Provider", "Revenue"])
        df2 = df2.sort_values("Revenue", ascending=False)
        fig2 = px.bar(df2, x="Provider", y="Revenue", color="Provider",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           showlegend=False, margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No provider revenue data yet.")

st.markdown("---")
st.subheader("📋 Full KPI Summary")
summary_rows = [
    {"KPI": "Total Revenue", "Value": f"${rev.get('total', 0):,.2f}", "Benchmark": "Track month-over-month growth"},
    {"KPI": "Revenue per Appointment", "Value": f"${rev.get('per_appointment', 0):,.2f}", "Benchmark": "$200–$500+ for MedSpas"},
    {"KPI": "No-Show Rate", "Value": f"{appts.get('no_show_rate_pct', 0):.1f}%", "Benchmark": "< 10%"},
    {"KPI": "Profit Margin", "Value": f"{prof.get('profit_margin_pct', 0):.1f}%", "Benchmark": "15–25%"},
    {"KPI": "Payroll Ratio", "Value": f"{prof.get('payroll_ratio_pct', 0):.1f}%", "Benchmark": "35–45%"},
    {"KPI": "Marketing ROI", "Value": f"{prof.get('marketing_roi', 0):.2f}x", "Benchmark": "> 3x"},
    {"KPI": "Overhead Ratio", "Value": f"{prof.get('overhead_ratio_pct', 0):.1f}%", "Benchmark": "< 70%"},
    {"KPI": "Total Payroll", "Value": f"${exp.get('payroll', 0):,.2f}", "Benchmark": "Largest cost center"},
    {"KPI": "Marketing Spend", "Value": f"${exp.get('marketing', 0):,.2f}", "Benchmark": "8–15% of revenue"},
]
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)
