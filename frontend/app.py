"""
Zentox Aesthetics CRM — Streamlit Entry Point
HIPAA notice: This application accesses Protected Health Information.
Unauthorized access is prohibited and monitored.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.api_client import login, is_authenticated

st.set_page_config(
    page_title="Zentox Aesthetics CRM",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- HIPAA session timeout (60 min) ---
import time
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = time.time()

if is_authenticated():
    elapsed = time.time() - st.session_state.get("last_activity", time.time())
    if elapsed > 3600:
        st.session_state.clear()
        st.warning("Session expired for security. Please log in again.")
        st.rerun()
    st.session_state["last_activity"] = time.time()

# --- Custom CSS ---
st.markdown("""
<style>
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%); }
[data-testid="stSidebar"] * { color: #eee !important; }
.metric-card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.stMetric { background: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
</style>
""", unsafe_allow_html=True)

# --- Login gate ---
if not is_authenticated():
    st.markdown("## 💎 Zentox Aesthetics CRM")
    st.markdown("---")
    st.markdown(
        "⚠️ **HIPAA Notice:** This system contains Protected Health Information (PHI). "
        "Access is restricted to authorized personnel only. All access is monitored and logged."
    )
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("### Sign In")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    st.stop()

# --- Sidebar nav ---
with st.sidebar:
    st.markdown("## 💎 Zentox CRM")
    st.markdown(f"👤 **{st.session_state.get('username', 'User')}**")
    st.markdown("---")
    st.page_link("pages/01_Dashboard.py", label="📊 Dashboard")
    st.markdown("**— CRM —**")
    st.page_link("pages/02_Patients.py", label="👥 Patients")
    st.page_link("pages/03_Pipeline.py", label="🔀 Pipeline")
    st.page_link("pages/04_Appointments.py", label="📅 Appointments")
    st.page_link("pages/06_Services.py", label="🩺 Services")
    st.markdown("**— Financials —**")
    st.page_link("pages/05_Financials.py", label="📈 KPI Snapshots")
    st.page_link("pages/08_Income_Statement.py", label="📑 Income Statement")
    st.page_link("pages/09_Cash_Flow.py", label="💸 Cash Flow")
    st.page_link("pages/10_Balance_Sheet.py", label="⚖️ Balance Sheet")
    st.page_link("pages/11_Expenses.py", label="🧾 Expenses")
    st.markdown("**— Operations —**")
    st.page_link("pages/12_Staff.py", label="👩‍⚕️ Staff")
    st.page_link("pages/13_Inventory.py", label="📦 Inventory")
    st.page_link("pages/14_MedSpa_KPIs.py", label="🏥 MedSpa KPIs")
    st.page_link("pages/07_Integrations.py", label="🔌 Integrations")
    st.markdown("---")
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("## Welcome to Zentox Aesthetics CRM")
st.info("Use the sidebar to navigate. Start with **📊 Dashboard** for your live KPIs.")
