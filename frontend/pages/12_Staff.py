import streamlit as st
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated

st.set_page_config(page_title="Staff | Zentox", page_icon="👩‍⚕️", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("👩‍⚕️ Staff & Provider Management")

tab1, tab2, tab3 = st.tabs(["👥 Staff Directory", "📊 Provider Performance", "➕ Add Staff"])

with tab1:
    show_all = st.checkbox("Show inactive staff", value=False)
    try:
        staff = get("/staff/", params={"active_only": not show_all})
    except Exception as e:
        st.error(f"Error: {e}")
        staff = []

    if staff:
        df = pd.DataFrame([{
            "Name": s.get("Full Name", ""),
            "Role": s.get("Role", ""),
            "Email": s.get("Email", ""),
            "Phone": s.get("Phone", ""),
            "Comp Type": s.get("Compensation Type", ""),
            "Base Comp": f"${float(s.get('Base Compensation') or 0):,.2f}",
            "Commission": f"{float(s.get('Commission Rate') or 0):.1f}%",
            "Active": "✅" if s.get("Active") else "❌",
            "Start Date": s.get("Start Date", ""),
        } for s in staff])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No staff records yet.")

with tab2:
    try:
        performance = get("/staff/performance")
    except Exception as e:
        st.error(f"Error: {e}")
        performance = []

    if performance:
        rows = [{"Provider": p, **stats} for p, stats in performance]
        df_perf = pd.DataFrame(rows)
        if "revenue" in df_perf.columns:
            df_perf["revenue"] = df_perf["revenue"].apply(lambda x: f"${float(x):,.2f}")
        if "avg_revenue_per_appt" in df_perf.columns:
            df_perf["avg_revenue_per_appt"] = df_perf["avg_revenue_per_appt"].apply(lambda x: f"${float(x):,.2f}")
        st.dataframe(df_perf, use_container_width=True, hide_index=True)

        # Revenue by provider chart
        chart_data = pd.DataFrame([
            {"Provider": p, "Revenue": float(str(stats.get("revenue", "0")).replace("$", "").replace(",", ""))}
            for p, stats in performance
        ])
        if not chart_data.empty:
            fig = px.bar(chart_data, x="Provider", y="Revenue", color="Provider",
                         color_discrete_sequence=px.colors.qualitative.Bold,
                         title="Revenue by Provider (All-time Completed Appointments)")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            fig.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No performance data yet. Appointments with provider names will appear here.")

with tab3:
    ROLES = ["Nurse Practitioner", "Physician Assistant", "RN", "Esthetician", "Medical Director", "Front Desk", "Practice Manager", "Other"]
    with st.form("new_staff"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name *")
        role = c2.selectbox("Role", ROLES)
        email = c1.text_input("Email")
        phone = c2.text_input("Phone")
        start_date = c1.date_input("Start Date", value=None)
        comp_type = c2.selectbox("Compensation Type", ["Salary", "Hourly", "Commission", "Hybrid"])
        base_comp = c1.number_input("Base Compensation ($)", min_value=0.0, step=100.0)
        commission = c2.number_input("Commission Rate (%)", min_value=0.0, max_value=100.0, step=0.5)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Staff Member")
        if submitted and name:
            payload = {
                "full_name": name,
                "role": role,
                "email": email or None,
                "phone": phone or None,
                "start_date": str(start_date) if start_date else None,
                "compensation_type": comp_type,
                "base_compensation": float(base_comp) if base_comp else None,
                "commission_rate": float(commission) if commission else None,
                "active": True,
                "notes": notes or None,
            }
            try:
                post("/staff/", payload)
                st.success(f"Staff member '{name}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
