import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, is_authenticated
from frontend.utils.charts import revenue_trend, appointment_status_donut, kpi_gauge, pipeline_funnel

st.set_page_config(page_title="Dashboard | Zentox CRM", page_icon="📊", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("📊 Live KPI Dashboard")
st.caption("Real-time data from AestheticsPro, GetWeave & QuickBooks")

# --- Fetch live KPIs ---
with st.spinner("Loading KPIs..."):
    try:
        kpis = get("/kpi/live")
        appt_stats = get("/appointments/stats/summary")
    except Exception as e:
        st.error(f"Could not load data: {e}")
        st.stop()

# --- Top metric row ---
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("💰 Total Revenue", f"${kpis['total_revenue']:,.2f}")
col2.metric("👥 Active Patients", f"{kpis['total_active_patients']:,}")
col3.metric("📅 Appointments", f"{kpis['total_appointments']:,}")
col4.metric("🎯 Conversion Rate", f"{kpis['conversion_rate']}%")
col5.metric("❌ No-Show Rate", f"{kpis['no_show_rate']}%")

st.markdown("---")

# --- Charts row ---
col_left, col_mid, col_right = st.columns([2, 1.5, 1.5])

with col_left:
    st.subheader("Revenue Trend")
    try:
        snapshots = get("/kpi/snapshots", params={"period": "Monthly"})
        if snapshots:
            df = pd.DataFrame(snapshots)
            if "Snapshot Date" in df.columns and "Total Revenue" in df.columns:
                df = df.sort_values("Snapshot Date")
                fig = revenue_trend(df, "Snapshot Date", "Total Revenue")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly snapshots yet. Sync data or create a KPI snapshot.")
        else:
            st.info("No KPI snapshots yet.")
    except Exception:
        st.info("Revenue trend requires KPI snapshots.")

with col_mid:
    st.subheader("Appointment Status")
    by_status = appt_stats.get("by_status", {})
    if by_status:
        fig = appointment_status_donut(by_status)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No appointment data yet.")

with col_right:
    st.subheader("Pipeline")
    try:
        board = get("/pipeline/board")
        stage_counts = {stage: len(leads) for stage, leads in board.items()}
        if any(stage_counts.values()):
            fig = pipeline_funnel(stage_counts)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No pipeline data yet.")
    except Exception:
        st.info("No pipeline data.")

st.markdown("---")

# --- Secondary metrics ---
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.subheader("Avg Revenue / Patient")
    fig = kpi_gauge(kpis["avg_revenue_per_patient"], "Avg Revenue", max_val=1000, suffix="$")
    st.plotly_chart(fig, use_container_width=True)
with col_b:
    st.subheader("Lead Conversion")
    fig = kpi_gauge(kpis["conversion_rate"], "Conversion", max_val=100, suffix="%")
    st.plotly_chart(fig, use_container_width=True)
with col_c:
    st.subheader("No-Show Rate")
    fig = kpi_gauge(kpis["no_show_rate"], "No-Shows", max_val=50, suffix="%")
    st.plotly_chart(fig, use_container_width=True)

st.caption(f"Data as of {kpis.get('as_of', 'N/A')}")
