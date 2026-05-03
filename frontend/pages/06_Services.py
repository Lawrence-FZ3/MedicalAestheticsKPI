import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated

st.set_page_config(page_title="Services | Zentox CRM", page_icon="🩺", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("🩺 Services & Treatments")

col1, col2 = st.columns([3, 1])
with col2:
    show_all = st.checkbox("Show inactive", value=False)

try:
    services = get("/services/", params={"active_only": not show_all})
except Exception as e:
    st.error(f"Error: {e}")
    services = []

if services:
    df = pd.DataFrame([{
        "Service": s.get("Service Name", ""),
        "Category": s.get("Category", ""),
        "Price": f"${float(s.get('Price') or 0):,.2f}",
        "Duration (min)": s.get("Duration (min)", ""),
        "Active": "✅" if s.get("Active") else "❌",
    } for s in services])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No services yet. Add your treatment menu below.")

st.markdown("---")
st.subheader("Add New Service")
with st.form("new_service"):
    c1, c2 = st.columns(2)
    name = c1.text_input("Service Name *")
    category = c2.selectbox("Category", ["Injectables", "Laser", "Skincare", "Body Contouring", "Consultation", "PRP", "Other"])
    price = c1.number_input("Price ($)", min_value=0.0, step=10.0)
    duration = c2.number_input("Duration (min)", min_value=15, step=15, value=60)
    active = st.checkbox("Active", value=True)
    description = st.text_area("Description")
    if st.form_submit_button("Add Service"):
        if name:
            try:
                post("/services/", {
                    "service_name": name,
                    "category": category,
                    "price": float(price) if price else None,
                    "duration_min": int(duration),
                    "active": active,
                    "description": description or None,
                })
                st.success(f"Service '{name}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Service name is required.")
