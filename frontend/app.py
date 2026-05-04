"""
Zentox Aesthetics CRM — Streamlit Entry Point
HIPAA notice: This application accesses Protected Health Information.
Unauthorized access is prohibited and monitored.
"""
import streamlit as st
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.utils.api_client import login, is_authenticated

st.set_page_config(
    page_title="Zentox Aesthetics",
    page_icon="https://zentoxaesthetics.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- HIPAA session timeout (60 min) ---
if "last_activity" not in st.session_state:
    st.session_state["last_activity"] = time.time()

if is_authenticated():
    elapsed = time.time() - st.session_state.get("last_activity", time.time())
    if elapsed > 3600:
        st.session_state.clear()
        st.warning("Session expired for security. Please log in again.")
        st.rerun()
    st.session_state["last_activity"] = time.time()

# --- Brand CSS (matches zentoxaesthetics.com) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Jost:wght@200;300;400;500&display=swap');

/* ── Global background & typography ── */
html, body, [data-testid="stApp"] {
    background-color: #F8F4EE !important;
    font-family: 'Jost', sans-serif !important;
    color: #1a1a1a !important;
}

/* ── Main content area ── */
[data-testid="stMain"] {
    background-color: #F8F4EE !important;
}
[data-testid="block-container"] {
    background-color: #F8F4EE !important;
    padding-top: 2rem !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1a1a1a !important;
    border-right: 1px solid #2a2a2a !important;
}
[data-testid="stSidebar"] * {
    color: #e8e0d4 !important;
    font-family: 'Jost', sans-serif !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stSidebar"] a:hover {
    color: #c9b99a !important;
}
[data-testid="stSidebarNav"] { display: none; }

/* ── Cards / Metrics ── */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border-radius: 4px !important;
    padding: 18px 20px !important;
    border: 1px solid #E8E0D4 !important;
    box-shadow: none !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.7rem !important;
    color: #888 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 400 !important;
    font-size: 1.8rem !important;
    color: #1a1a1a !important;
}

/* ── Headings ── */
h1, h2, h3 {
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #1a1a1a !important;
}
h1 { font-size: 1.4rem !important; }
h2 { font-size: 1.1rem !important; }

/* ── Buttons ── */
[data-testid="baseButton-primary"],
.stButton > button[kind="primary"] {
    background-color: #1a1a1a !important;
    color: #F8F4EE !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    font-size: 0.75rem !important;
}
.stButton > button {
    background-color: transparent !important;
    color: #1a1a1a !important;
    border: 1px solid #C8BFB4 !important;
    border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.1em !important;
    font-size: 0.75rem !important;
}
.stButton > button:hover {
    border-color: #1a1a1a !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select,
textarea {
    background-color: #FFFFFF !important;
    border: 1px solid #D8D0C4 !important;
    border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important;
    color: #1a1a1a !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-testid="stTab"] {
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E8E0D4 !important;
}

/* ── Divider ── */
hr { border-color: #E8E0D4 !important; }

/* ── Info / Warning / Success banners ── */
[data-testid="stAlert"] {
    border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Login gate ──
if not is_authenticated():
    # Centered login card
    st.markdown("""
    <div style='text-align:center; padding: 60px 0 20px 0;'>
        <div style='font-family:"Jost",sans-serif; font-size:0.7rem; letter-spacing:0.25em;
                    text-transform:uppercase; color:#888; margin-bottom:8px;'>
            Internal Operations
        </div>
        <div style='font-family:"Cormorant Garamond",serif; font-size:3.2rem;
                    font-weight:300; letter-spacing:0.08em; color:#1a1a1a;'>
            za
        </div>
        <div style='font-family:"Jost",sans-serif; font-size:0.65rem; letter-spacing:0.3em;
                    text-transform:uppercase; color:#1a1a1a; margin-top:4px;'>
            Zentox Aesthetics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#E8E0D4; margin: 0 25% 32px 25%;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown(
            "<p style='font-family:Jost,sans-serif; font-size:0.65rem; letter-spacing:0.15em; "
            "text-transform:uppercase; color:#999; text-align:center; margin-bottom:20px;'>"
            "⚠ HIPAA — Authorized access only. All sessions are logged.</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="username")
            password = st.text_input("Password", type="password", placeholder="password")
            submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                if login(username, password):
                    st.success("Welcome back.")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    st.stop()

# ── Sidebar navigation ──
with st.sidebar:
    st.markdown("""
    <div style='padding: 24px 16px 8px 16px;'>
        <div style='font-family:"Cormorant Garamond",serif; font-size:2.4rem;
                    font-weight:300; color:#e8e0d4; letter-spacing:0.05em;'>za</div>
        <div style='font-family:"Jost",sans-serif; font-size:0.55rem; letter-spacing:0.28em;
                    text-transform:uppercase; color:#888; margin-top:2px;'>
            Zentox Aesthetics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<div style='padding: 4px 16px 12px; font-size:0.7rem; color:#888; "
        f"font-family:Jost,sans-serif; letter-spacing:0.06em;'>"
        f"{st.session_state.get('username', 'User')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr style='border-color:#2a2a2a; margin:0 0 8px 0;'>", unsafe_allow_html=True)

    st.page_link("pages/01_Dashboard.py", label="Dashboard")

    st.markdown("<div style='font-size:0.55rem;letter-spacing:0.2em;text-transform:uppercase;"
                "color:#555;padding:12px 0 4px 0;font-family:Jost,sans-serif;'>CRM</div>",
                unsafe_allow_html=True)
    st.page_link("pages/02_Patients.py", label="Patients")
    st.page_link("pages/03_Pipeline.py", label="Pipeline")
    st.page_link("pages/04_Appointments.py", label="Appointments")
    st.page_link("pages/06_Services.py", label="Services")

    st.markdown("<div style='font-size:0.55rem;letter-spacing:0.2em;text-transform:uppercase;"
                "color:#555;padding:12px 0 4px 0;font-family:Jost,sans-serif;'>Financials</div>",
                unsafe_allow_html=True)
    st.page_link("pages/05_Financials.py", label="KPI Snapshots")
    st.page_link("pages/08_Income_Statement.py", label="Income Statement")
    st.page_link("pages/09_Cash_Flow.py", label="Cash Flow")
    st.page_link("pages/10_Balance_Sheet.py", label="Balance Sheet")
    st.page_link("pages/11_Expenses.py", label="Expenses")

    st.markdown("<div style='font-size:0.55rem;letter-spacing:0.2em;text-transform:uppercase;"
                "color:#555;padding:12px 0 4px 0;font-family:Jost,sans-serif;'>Operations</div>",
                unsafe_allow_html=True)
    st.page_link("pages/12_Staff.py", label="Staff")
    st.page_link("pages/13_Inventory.py", label="Inventory")
    st.page_link("pages/14_MedSpa_KPIs.py", label="MedSpa KPIs")
    st.page_link("pages/07_Integrations.py", label="Integrations")

    st.markdown("<div style='font-size:0.55rem;letter-spacing:0.2em;text-transform:uppercase;"
                "color:#555;padding:12px 0 4px 0;font-family:Jost,sans-serif;'>Intelligence</div>",
                unsafe_allow_html=True)
    st.page_link("pages/15_AI_Agents.py", label="AI Agent Pipeline")
    st.page_link("pages/16_Documents.py", label="Document Library")

    st.markdown("<hr style='border-color:#2a2a2a; margin: 16px 0 8px 0;'>", unsafe_allow_html=True)
    if st.button("Sign Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ── Home ──
st.markdown("""
<div style='padding: 40px 0 8px 0;'>
    <div style='font-family:"Jost",sans-serif; font-size:0.6rem; letter-spacing:0.28em;
                text-transform:uppercase; color:#999;'>Welcome</div>
    <div style='font-family:"Cormorant Garamond",serif; font-size:2.8rem;
                font-weight:300; color:#1a1a1a; letter-spacing:0.04em; margin-top:4px;'>
        Zentox Aesthetics
    </div>
    <div style='font-family:"Jost",sans-serif; font-size:0.65rem; letter-spacing:0.18em;
                text-transform:uppercase; color:#888; margin-top:2px;'>
        Internal Operations Platform
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<hr style='border-color:#E8E0D4;'>", unsafe_allow_html=True)
st.info("Select a module from the sidebar to get started. Begin with **Dashboard** for your live KPIs.")
