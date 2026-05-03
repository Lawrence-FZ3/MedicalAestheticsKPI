import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, patch, is_authenticated
from frontend.utils.charts import pipeline_funnel, lead_source_bar

st.set_page_config(page_title="Pipeline | Zentox CRM", page_icon="🔀", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("🔀 CRM Pipeline")

STAGES = ["New Lead", "Contacted", "Consultation Scheduled", "Consultation Done", "Treatment Planned", "Converted", "Lost"]
STAGE_COLORS = {"New Lead": "🔵", "Contacted": "🟣", "Consultation Scheduled": "🟦", "Consultation Done": "🟡", "Treatment Planned": "🟠", "Converted": "🟢", "Lost": "🔴"}

tab1, tab2, tab3 = st.tabs(["📋 Kanban Board", "📊 Analytics", "➕ Add Lead"])

# --- KANBAN ---
with tab1:
    try:
        board = get("/pipeline/board")
    except Exception as e:
        st.error(f"Failed to load pipeline: {e}")
        board = {}

    cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        with cols[i]:
            leads = board.get(stage, [])
            st.markdown(f"**{STAGE_COLORS.get(stage, '')} {stage}** ({len(leads)})")
            for lead in leads:
                with st.expander(lead.get("Lead Name", "Unknown")):
                    st.write(f"📧 {lead.get('Email', '-')}")
                    st.write(f"📞 {lead.get('Phone', '-')}")
                    est = lead.get("Estimated Value")
                    if est:
                        st.write(f"💰 ${float(est):,.2f}")
                    interests = lead.get("Treatment Interest", [])
                    if interests:
                        st.write(f"💉 {', '.join(interests)}")
                    follow_up = lead.get("Next Follow-Up")
                    if follow_up:
                        st.write(f"📅 Follow-up: {follow_up}")
                    new_stage = st.selectbox(
                        "Move to stage",
                        STAGES,
                        index=STAGES.index(stage),
                        key=f"stage_{lead['id']}",
                    )
                    if new_stage != stage:
                        try:
                            patch(f"/pipeline/{lead['id']}", {"stage": new_stage})
                            st.success("Stage updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

# --- ANALYTICS ---
with tab2:
    try:
        all_leads = get("/pipeline/")
    except Exception:
        all_leads = []

    if all_leads:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Pipeline Funnel")
            stage_counts = {}
            for l in all_leads:
                s = l.get("Stage", "Unknown")
                stage_counts[s] = stage_counts.get(s, 0) + 1
            fig = pipeline_funnel({s: stage_counts.get(s, 0) for s in STAGES})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Lead Sources")
            source_counts = {}
            for l in all_leads:
                src = l.get("Lead Source", "Other")
                source_counts[src] = source_counts.get(src, 0) + 1
            fig2 = lead_source_bar(source_counts)
            st.plotly_chart(fig2, use_container_width=True)

        total_pipeline_value = sum(float(l.get("Estimated Value") or 0) for l in all_leads)
        converted_value = sum(float(l.get("Estimated Value") or 0) for l in all_leads if l.get("Stage") == "Converted")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Pipeline Value", f"${total_pipeline_value:,.2f}")
        c2.metric("Converted Value", f"${converted_value:,.2f}")
        c3.metric("Total Leads", len(all_leads))
    else:
        st.info("No pipeline data yet.")

# --- ADD LEAD ---
with tab3:
    with st.form("new_lead"):
        c1, c2 = st.columns(2)
        lead_name = c1.text_input("Full Name *")
        email = c2.text_input("Email")
        phone = c1.text_input("Phone")
        stage = c2.selectbox("Stage", STAGES)
        lead_source = c1.selectbox("Lead Source", ["Social Media", "Google Ads", "Referral", "GetWeave", "Walk-in", "Website", "Other"])
        assigned_to = c2.text_input("Assigned To")
        treatment_interest = st.multiselect("Treatment Interest", ["Botox", "Fillers", "Laser", "Skincare", "Body Contouring", "PRP", "Chemical Peel", "Other"])
        est_value = st.number_input("Estimated Value ($)", min_value=0.0, step=50.0)
        follow_up = st.date_input("Next Follow-Up", value=None)
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Lead")
        if submitted and lead_name:
            payload = {
                "lead_name": lead_name,
                "email": email or None,
                "phone": phone or None,
                "stage": stage,
                "lead_source": lead_source,
                "assigned_to": assigned_to or None,
                "treatment_interest": treatment_interest or None,
                "estimated_value": est_value or None,
                "next_follow_up": str(follow_up) if follow_up else None,
                "notes": notes or None,
            }
            try:
                post("/pipeline/", payload)
                st.success(f"Lead '{lead_name}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
