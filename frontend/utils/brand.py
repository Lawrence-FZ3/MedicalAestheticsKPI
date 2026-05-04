"""
Zentox Aesthetics brand CSS — inject on every page with apply_brand().
Matches zentoxaesthetics.com: warm cream background, Jost + Cormorant Garamond,
clean minimal black-and-cream palette.
"""
import streamlit as st


def apply_brand(page_title: str = ""):
    """Call at the top of every page (after set_page_config) to apply brand styles."""
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500&family=Jost:wght@200;300;400;500&display=swap');

html, body, [data-testid="stApp"] {
    background-color: #F8F4EE !important;
    font-family: 'Jost', sans-serif !important;
    color: #1a1a1a !important;
}
[data-testid="stMain"], [data-testid="block-container"] {
    background-color: #F8F4EE !important;
}
[data-testid="stSidebar"] {
    background: #1a1a1a !important;
    border-right: 1px solid #2a2a2a !important;
}
[data-testid="stSidebar"] * {
    color: #e8e0d4 !important;
    font-family: 'Jost', sans-serif !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stSidebarNav"] { display: none; }
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
h1, h2, h3 {
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #1a1a1a !important;
}
h1 { font-size: 1.3rem !important; }
h2 { font-size: 1.0rem !important; }
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
.stButton > button:hover { border-color: #1a1a1a !important; }
[data-testid="stTabs"] [data-testid="stTab"] {
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.72rem !important;
}
[data-testid="stDataFrame"] { border: 1px solid #E8E0D4 !important; }
hr { border-color: #E8E0D4 !important; }
[data-testid="stAlert"] {
    border-radius: 2px !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 300 !important;
}
</style>
""", unsafe_allow_html=True)

    if page_title:
        st.markdown(
            f"<h1 style='padding-bottom:4px'>{page_title}</h1>"
            f"<hr style='border-color:#E8E0D4; margin-bottom:24px;'>",
            unsafe_allow_html=True,
        )
