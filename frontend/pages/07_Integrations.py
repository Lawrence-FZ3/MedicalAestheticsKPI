import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import post, get, is_authenticated

st.set_page_config(page_title="Integrations | Zentox CRM", page_icon="🔌", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("🔌 Integrations & Data Sync")
st.caption("Pull patient and appointment data from connected platforms or upload Excel reports.")

# --- AestheticsPro ---
with st.expander("🏥 AestheticsPro", expanded=True):
    st.markdown("Syncs **patients** and **appointments** from your AestheticsPro practice management system.")
    days = st.slider("Days back to sync appointments", 7, 365, 30, key="ap_days")
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("🔄 Sync AestheticsPro", use_container_width=True):
            with st.spinner("Syncing..."):
                try:
                    result = post(f"/integrations/sync/aestheticspro?days_back={days}")
                    st.success(f"Sync complete! Patients: {result.get('patients', {})} | Appointments: {result.get('appointments', {})}")
                except Exception as e:
                    st.error(f"Sync failed: {e}")
    with col1:
        st.info("Configure `AESTHETICSPRO_API_URL` and `AESTHETICSPRO_API_KEY` in your `.env` file.")

st.markdown("---")

# --- GetWeave ---
with st.expander("📞 GetWeave"):
    st.markdown("Syncs **contacts** and **appointments** from GetWeave (patient communication platform).")
    days_gw = st.slider("Days back to sync appointments", 7, 365, 30, key="gw_days")
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("🔄 Sync GetWeave", use_container_width=True):
            with st.spinner("Syncing..."):
                try:
                    result = post(f"/integrations/sync/getweave?days_back={days_gw}")
                    st.success(f"Sync complete! Contacts: {result.get('contacts', {})} | Appointments: {result.get('appointments', {})}")
                except Exception as e:
                    st.error(f"Sync failed: {e}")
    with col1:
        st.info("Configure `GETWEAVE_API_KEY` and `GETWEAVE_LOCATION_ID` in your `.env` file.")

st.markdown("---")

# --- QuickBooks ---
with st.expander("📊 QuickBooks Online"):
    st.markdown("Pulls **revenue summary** and P&L data from QuickBooks Online.")
    col1, col2 = st.columns([2, 1])
    with col2:
        if st.button("🔄 Fetch QBO Revenue", use_container_width=True):
            with st.spinner("Connecting to QuickBooks..."):
                try:
                    result = get("/integrations/sync/quickbooks/revenue")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Invoiced", f"${result.get('total_invoiced', 0):,.2f}")
                    c2.metric("Total Paid", f"${result.get('total_paid', 0):,.2f}")
                    c3.metric("Outstanding", f"${result.get('outstanding', 0):,.2f}")
                except Exception as e:
                    st.error(f"Failed: {e}")
    with col1:
        st.info("Configure `QBO_CLIENT_ID`, `QBO_CLIENT_SECRET`, `QBO_REFRESH_TOKEN`, and `QBO_REALM_ID` in `.env`.")

st.markdown("---")

# --- Excel Upload ---
with st.expander("📁 Excel / CSV Upload"):
    st.markdown("Upload exported reports from **AestheticsPro**, **QuickBooks**, or any source.")

    upload_type = st.selectbox("Report Type", ["Patients", "Appointments", "Financial"])
    uploaded = st.file_uploader("Upload .xlsx file", type=["xlsx", "xls"])

    if uploaded and st.button("📤 Upload & Import"):
        with st.spinner("Processing..."):
            try:
                endpoint_map = {
                    "Patients": "/integrations/upload/patients",
                    "Appointments": "/integrations/upload/appointments",
                    "Financial": "/integrations/upload/financial",
                }
                endpoint = endpoint_map[upload_type]
                files = {"file": (uploaded.name, uploaded.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                result = post(endpoint, files=files)
                st.success(f"Import complete! {result}")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    st.info("Excel files should have column headers in row 1. See the column mapping in the docs.")

st.markdown("---")
st.subheader("📋 Sync Status")
st.info("All sync events are recorded in the **Audit Log** table in Airtable for HIPAA compliance.")
