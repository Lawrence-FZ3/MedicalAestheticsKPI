import streamlit as st
import pandas as pd
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated
from frontend.utils.charts import revenue_trend

st.set_page_config(page_title="Financials | Zentox CRM", page_icon="💰", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("💰 Financial Reports")

tab1, tab2, tab3 = st.tabs(["📈 KPI Snapshots", "📋 QuickBooks Revenue", "💾 Create Snapshot"])

with tab1:
    period = st.selectbox("Period", ["Monthly", "Weekly", "Daily", "Quarterly", "Annual"])
    try:
        snapshots = get("/kpi/snapshots", params={"period": period})
    except Exception as e:
        st.error(f"Error: {e}")
        snapshots = []

    if snapshots:
        df = pd.DataFrame(snapshots)
        show_cols = ["Snapshot Date", "Total Revenue", "New Patients", "Total Appointments",
                     "Completed Appointments", "No-Show Rate", "Avg Revenue Per Patient",
                     "New Leads", "Leads Converted", "Conversion Rate", "Data Source"]
        df = df[[c for c in show_cols if c in df.columns]]
        for col in ["Total Revenue", "Avg Revenue Per Patient"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"${float(x):,.2f}" if x else "-")
        for col in ["No-Show Rate", "Conversion Rate"]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: f"{float(x):.1f}%" if x else "-")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Chart
        try:
            chart_df = pd.DataFrame(snapshots)
            if "Snapshot Date" in chart_df.columns and "Total Revenue" in chart_df.columns:
                chart_df = chart_df.dropna(subset=["Total Revenue"])
                chart_df = chart_df.sort_values("Snapshot Date")
                fig = revenue_trend(chart_df, "Snapshot Date", "Total Revenue")
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass
    else:
        st.info(f"No {period.lower()} KPI snapshots yet. Create one in the **Create Snapshot** tab.")

with tab2:
    st.subheader("QuickBooks Online Revenue Summary")
    if st.button("🔄 Sync from QuickBooks"):
        try:
            result = get("/integrations/sync/quickbooks/revenue")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Invoiced", f"${result.get('total_invoiced', 0):,.2f}")
            c2.metric("Total Paid", f"${result.get('total_paid', 0):,.2f}")
            c3.metric("Outstanding", f"${result.get('outstanding', 0):,.2f}")
            c4.metric("Invoice Count", result.get("invoice_count", 0))
        except Exception as e:
            st.error(f"QuickBooks sync failed: {e}. Make sure QBO credentials are configured in .env")

    st.info("Configure `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REFRESH_TOKEN`, and `QBO_REALM_ID` in your `.env` file to enable QuickBooks sync.")

with tab3:
    st.subheader("Create KPI Snapshot")
    with st.form("new_snapshot"):
        c1, c2 = st.columns(2)
        period_s = c1.selectbox("Period", ["Monthly", "Weekly", "Daily", "Quarterly", "Annual"])
        snap_date = c2.date_input("Snapshot Date", value=date.today())
        total_rev = c1.number_input("Total Revenue ($)", min_value=0.0, step=100.0)
        new_patients = c2.number_input("New Patients", min_value=0, step=1)
        total_appts = c1.number_input("Total Appointments", min_value=0, step=1)
        completed_appts = c2.number_input("Completed Appointments", min_value=0, step=1)
        no_show_rate = c1.number_input("No-Show Rate (%)", min_value=0.0, max_value=100.0, step=0.1)
        avg_rev = c2.number_input("Avg Revenue / Patient ($)", min_value=0.0, step=10.0)
        new_leads = c1.number_input("New Leads", min_value=0, step=1)
        converted = c2.number_input("Leads Converted", min_value=0, step=1)
        conv_rate = c1.number_input("Conversion Rate (%)", min_value=0.0, max_value=100.0, step=0.1)
        data_source = c2.selectbox("Data Source", ["Mixed", "AestheticsPro", "QuickBooks", "Manual"])
        notes = st.text_area("Notes")
        if st.form_submit_button("Save Snapshot"):
            payload = {
                "period": period_s,
                "snapshot_date": str(snap_date),
                "total_revenue": total_rev or None,
                "new_patients": int(new_patients) or None,
                "total_appointments": int(total_appts) or None,
                "completed_appointments": int(completed_appts) or None,
                "no_show_rate": no_show_rate or None,
                "avg_revenue_per_patient": avg_rev or None,
                "new_leads": int(new_leads) or None,
                "leads_converted": int(converted) or None,
                "conversion_rate": conv_rate or None,
                "data_source": data_source,
                "notes": notes or None,
            }
            try:
                post("/kpi/snapshots", payload)
                st.success("KPI Snapshot saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
