import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, patch, is_authenticated

st.set_page_config(page_title="Patients | Zentox CRM", page_icon="👥", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("👥 Patient Management")

# --- Filters ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search = st.text_input("🔍 Search by name", placeholder="Start typing...")
with col2:
    status_filter = st.selectbox("Status", ["All", "Active", "Inactive", "Lead", "VIP"])
with col3:
    st.markdown(" ")
    show_form = st.button("➕ Add Patient", use_container_width=True)

# --- Fetch patients ---
with st.spinner("Loading patients..."):
    try:
        params = {}
        if status_filter != "All":
            params["status"] = status_filter
        patients = get("/patients/", params=params)
    except Exception as e:
        st.error(f"Failed to load patients: {e}")
        patients = []

# --- Filter by search ---
if search:
    patients = [p for p in patients if search.lower() in p.get("Full Name", "").lower()]

# --- Add patient form ---
if show_form:
    st.session_state["show_patient_form"] = not st.session_state.get("show_patient_form", False)

if st.session_state.get("show_patient_form"):
    with st.expander("New Patient", expanded=True):
        with st.form("new_patient"):
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Name *")
            email = c2.text_input("Email")
            phone = c1.text_input("Phone")
            dob = c2.date_input("Date of Birth", value=None)
            gender = c1.selectbox("Gender", ["", "Female", "Male", "Non-binary", "Prefer not to say"])
            lead_source = c2.selectbox("Lead Source", ["AestheticsPro", "GetWeave", "Referral", "Walk-in", "Social Media", "Website", "Google Ads", "Other"])
            status = c1.selectbox("Status", ["Active", "Lead", "VIP", "Inactive"])
            address = st.text_area("Address")
            notes = st.text_area("Notes (do not include clinical notes here)")
            submitted = st.form_submit_button("Save Patient")
            if submitted and full_name:
                payload = {
                    "full_name": full_name,
                    "email": email or None,
                    "phone": phone or None,
                    "date_of_birth": str(dob) if dob else None,
                    "gender": gender or None,
                    "lead_source": lead_source,
                    "status": status,
                    "address": address or None,
                    "notes": notes or None,
                }
                try:
                    post("/patients/", payload)
                    st.success(f"Patient '{full_name}' created!")
                    st.session_state["show_patient_form"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# --- Patient table ---
st.markdown(f"**{len(patients)} patients found**")

if patients:
    display_cols = ["Full Name", "Email", "Phone", "Status", "Lead Source", "Visit Count", "Total Spend", "Last Visit Date"]
    rows = []
    for p in patients:
        rows.append({col: p.get(col, "") for col in display_cols})
    df = pd.DataFrame(rows)
    if "Total Spend" in df.columns:
        df["Total Spend"] = df["Total Spend"].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Patient detail expander ---
    with st.expander("View / Edit Patient Details"):
        patient_names = [p.get("Full Name", f"ID:{p['id']}") for p in patients]
        selected_name = st.selectbox("Select Patient", patient_names)
        selected = next((p for p in patients if p.get("Full Name") == selected_name), None)
        if selected:
            st.json({k: v for k, v in selected.items() if k not in ("id",) and v})
            with st.form("edit_patient"):
                new_status = st.selectbox("Update Status", ["Active", "Inactive", "Lead", "VIP"], index=["Active", "Inactive", "Lead", "VIP"].index(selected.get("Status", "Active")) if selected.get("Status") in ["Active", "Inactive", "Lead", "VIP"] else 0)
                new_notes = st.text_area("Notes", value=selected.get("Notes", ""))
                if st.form_submit_button("Save Changes"):
                    try:
                        patch(f"/patients/{selected['id']}", {"status": new_status, "notes": new_notes or None})
                        st.success("Patient updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
else:
    st.info("No patients found. Sync from AestheticsPro/GetWeave or add manually.")
