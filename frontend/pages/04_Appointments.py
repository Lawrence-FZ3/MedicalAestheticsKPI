import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, patch, is_authenticated
from frontend.utils.charts import appointment_status_donut

st.set_page_config(page_title="Appointments | Zentox CRM", page_icon="📅", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("📅 Appointments")

tab1, tab2, tab3 = st.tabs(["📋 List", "📊 Stats", "➕ New Appointment"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Scheduled", "Confirmed", "Completed", "No-Show", "Cancelled"])
    with col2:
        provider_filter = st.text_input("Provider", placeholder="Filter by provider")

    try:
        params = {}
        if status_filter != "All":
            params["status"] = status_filter
        if provider_filter:
            params["provider"] = provider_filter
        appointments = get("/appointments/", params=params)
    except Exception as e:
        st.error(f"Failed to load appointments: {e}")
        appointments = []

    st.markdown(f"**{len(appointments)} appointments**")
    if appointments:
        display_cols = ["Appointment Date", "Provider", "Service", "Status", "Duration (min)", "Revenue", "Source"]
        rows = [{col: a.get(col, "") for col in display_cols} for a in appointments]
        df = pd.DataFrame(rows)
        if "Revenue" in df.columns:
            df["Revenue"] = df["Revenue"].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No appointments found.")

with tab2:
    try:
        stats = get("/appointments/stats/summary")
    except Exception:
        stats = {}

    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Appointments", stats.get("total", 0))
        c2.metric("Total Revenue", f"${stats.get('total_revenue', 0):,.2f}")
        c3.metric("No-Show Rate", f"{stats.get('no_show_rate', 0)}%")
        completed = stats.get("by_status", {}).get("Completed", 0)
        c4.metric("Completed", completed)

        by_status = stats.get("by_status", {})
        if by_status:
            fig = appointment_status_donut(by_status)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No appointment stats available.")

with tab3:
    with st.form("new_appt"):
        c1, c2 = st.columns(2)
        provider = c1.text_input("Provider *")
        service = c2.text_input("Service / Treatment *")
        appt_date = c1.date_input("Date", value=date.today())
        appt_time = c2.time_input("Time")
        status = c1.selectbox("Status", ["Scheduled", "Confirmed", "Completed", "No-Show", "Cancelled"])
        duration = c2.number_input("Duration (min)", min_value=15, max_value=480, step=15, value=60)
        revenue = c1.number_input("Revenue ($)", min_value=0.0, step=10.0)
        source = c2.selectbox("Source", ["Manual", "AestheticsPro", "GetWeave"])
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Appointment")
        if submitted and provider and service:
            import datetime
            dt = datetime.datetime.combine(appt_date, appt_time)
            payload = {
                "provider": provider,
                "service": service,
                "appointment_date": dt.isoformat(),
                "status": status,
                "duration_min": int(duration),
                "revenue": float(revenue) if revenue else None,
                "source": source,
                "notes": notes or None,
            }
            try:
                post("/appointments/", payload)
                st.success("Appointment saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
