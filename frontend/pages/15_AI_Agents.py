import streamlit as st
import pandas as pd
import json
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated

st.set_page_config(page_title="AI Agents | Zentox", page_icon="🤖", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("🤖 AI Agent Pipeline")
st.caption("3-agent system: Data Cleaner → Business Analyst → Growth Strategist → Email report to info@fivezero3.net")

st.info(
    "**How it works:** Paste or upload data → Agent 1 cleans it → Agent 2 finds patterns → "
    "Agent 3 builds your strategy → Results emailed to **info@fivezero3.net** and displayed here."
)

# --- Tabs ---
tab_run, tab_results, tab_about = st.tabs(["▶️ Run Pipeline", "📋 Latest Results", "ℹ️ About"])

# ============================================================
# TAB 1 — Run Pipeline
# ============================================================
with tab_run:
    st.subheader("Select a Data Source")

    source = st.radio(
        "Data source",
        ["📥 Live Appointments (from CRM)", "📥 Live Patients (from CRM)", "📥 Live Expenses (from CRM)", "📂 Upload JSON / CSV"],
        horizontal=True,
    )

    data_label = st.text_input("Dataset label (shown in the email)", value="Zentox CRM Data")
    context = st.text_area(
        "Additional context for the Analyst (optional)",
        placeholder="e.g. This is Q1 2025 data. We ran a Botox promo in February.",
        height=80,
    )
    send_email = st.checkbox("Email the report to info@fivezero3.net", value=True)

    raw_data = []

    if "Appointments" in source:
        with st.spinner("Fetching appointments..."):
            try:
                raw_data = get("/appointments/", params={"limit": 200})
                st.success(f"Loaded {len(raw_data)} appointment records.")
            except Exception as e:
                st.error(f"Could not fetch appointments: {e}")

    elif "Patients" in source:
        with st.spinner("Fetching patients..."):
            try:
                raw_data = get("/patients/", params={"limit": 200})
                st.success(f"Loaded {len(raw_data)} patient records.")
            except Exception as e:
                st.error(f"Could not fetch patients: {e}")

    elif "Expenses" in source:
        with st.spinner("Fetching expenses..."):
            try:
                raw_data = get("/financials/expenses")
                st.success(f"Loaded {len(raw_data)} expense records.")
            except Exception as e:
                st.error(f"Could not fetch expenses: {e}")

    else:
        uploaded = st.file_uploader("Upload JSON or CSV file", type=["json", "csv"])
        if uploaded:
            if uploaded.name.endswith(".json"):
                raw_data = json.load(uploaded)
            else:
                df_upload = pd.read_csv(uploaded)
                raw_data = df_upload.to_dict(orient="records")
            st.success(f"Loaded {len(raw_data)} records from {uploaded.name}.")
            data_label = uploaded.name

    if raw_data:
        with st.expander(f"Preview — first 5 of {len(raw_data)} records"):
            st.json(raw_data[:5])

    st.markdown("---")
    col_run, col_mode = st.columns([2, 1])
    with col_mode:
        sync_mode = st.checkbox("Synchronous mode (wait for result)", value=len(raw_data) <= 50)
    with col_run:
        run_btn = st.button("🚀 Run AI Pipeline", disabled=not raw_data, use_container_width=True, type="primary")

    if run_btn and raw_data:
        payload = {
            "data": raw_data,
            "data_label": data_label,
            "context": context,
            "send_email": send_email,
        }

        if sync_mode:
            with st.spinner("Running 3-agent pipeline... (this may take 30–90 seconds)"):
                try:
                    result = post("/agents/run-sync", payload)
                    st.session_state["agent_result"] = result
                    st.success("Pipeline complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
        else:
            with st.spinner("Submitting pipeline job..."):
                try:
                    job = post("/agents/run", payload)
                    job_id = job.get("job_id")
                    st.session_state["agent_job_id"] = job_id
                    st.info(f"Job started: `{job_id}` — switch to **📋 Latest Results** tab and refresh to see progress.")
                except Exception as e:
                    st.error(f"Could not start job: {e}")

# ============================================================
# TAB 2 — Results
# ============================================================
with tab_results:
    # Poll background job if one is running
    job_id = st.session_state.get("agent_job_id")
    if job_id and "agent_result" not in st.session_state:
        with st.spinner(f"Polling job `{job_id}`..."):
            try:
                job_status = get(f"/agents/status/{job_id}")
                status = job_status.get("status")
                if status == "complete":
                    st.session_state["agent_result"] = job_status.get("result", {})
                    st.session_state.pop("agent_job_id", None)
                    st.success("Pipeline complete!")
                    st.rerun()
                elif status == "error":
                    st.error(f"Pipeline error: {job_status.get('error')}")
                else:
                    st.info(f"Status: **{status}** — refresh this tab to check again.")
                    if st.button("🔄 Refresh status"):
                        st.rerun()
            except Exception as e:
                st.error(f"Could not poll job: {e}")

    result = st.session_state.get("agent_result")

    if not result:
        st.info("No results yet. Run the pipeline from the **▶️ Run Pipeline** tab.")
        st.stop()

    # --- Header metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Records In", result.get("records_in", 0))
    col2.metric("Records Out (cleaned)", result.get("records_out", 0))
    col3.metric("Email Sent", "✅ Yes" if result.get("email_sent") else "❌ No")
    timings = result.get("timings", {})
    total_sec = sum(timings.values())
    col4.metric("Total Runtime", f"{total_sec:.1f}s")

    st.markdown("---")

    # --- Executive Summary ---
    strategy = result.get("strategy", {})
    analysis = result.get("analysis", {})

    st.markdown("### 📣 Executive Summary")
    st.success(strategy.get("executive_summary", "No summary available."))

    # --- Key Metrics ---
    metrics = analysis.get("key_metrics", {})
    if metrics:
        st.markdown("### 📊 Key Metrics")
        cols = st.columns(min(len(metrics), 4))
        for i, (k, v) in enumerate(metrics.items()):
            cols[i % 4].metric(k, v)

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        # Quick Wins
        quick_wins = strategy.get("quick_wins", [])
        if quick_wins:
            st.markdown("### ⚡ Quick Wins")
            for qw in quick_wins:
                impact = qw.get("impact", "")
                color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(impact, "⚪")
                with st.expander(f"{color} {qw.get('action', '')} — {qw.get('timeline', '')}"):
                    st.write(f"**Impact:** {impact} | **Effort:** {qw.get('effort', '')}")

        # Trends
        trends = analysis.get("trends", [])
        if trends:
            st.markdown("### 📈 Trends")
            for t in trends:
                st.markdown(f"- {t}")

    with col_right:
        # Growth Initiatives
        initiatives = strategy.get("growth_initiatives", [])
        if initiatives:
            st.markdown("### 🚀 Growth Initiatives")
            for gi in initiatives:
                with st.expander(f"{gi.get('initiative', '')} — {gi.get('timeline', '')}"):
                    st.write(gi.get("rationale", ""))
                    st.caption(f"Target: {gi.get('kpi_target', '')}")

        # Anomalies + Risk Flags
        anomalies = analysis.get("anomalies", []) + strategy.get("risk_flags", [])
        if anomalies:
            st.markdown("### ⚠️ Anomalies & Risk Flags")
            for a in anomalies:
                st.warning(a)

    st.markdown("---")

    col_mkt, col_ops = st.columns(2)
    with col_mkt:
        mkt = strategy.get("marketing_recommendations", [])
        if mkt:
            st.markdown("### 📣 Marketing")
            for m in mkt:
                st.markdown(f"- {m}")

    with col_ops:
        ops = strategy.get("operational_recommendations", [])
        if ops:
            st.markdown("### ⚙️ Operations")
            for o in ops:
                st.markdown(f"- {o}")

    # --- Data Cleaning Audit ---
    audit = result.get("audit_trail", [])
    if audit:
        with st.expander(f"🔧 Data Cleaning Audit ({len(audit)} changes)"):
            for item in audit:
                st.markdown(f"- {item}")

    # --- Timings ---
    with st.expander("⏱️ Agent Timings"):
        for agent, secs in timings.items():
            st.write(f"**{agent}:** {secs}s")

    # --- Raw JSON ---
    with st.expander("📄 Full Raw Result (JSON)"):
        st.json(result)

    if st.button("🗑️ Clear Results"):
        st.session_state.pop("agent_result", None)
        st.session_state.pop("agent_job_id", None)
        st.rerun()

# ============================================================
# TAB 3 — About
# ============================================================
with tab_about:
    st.markdown("""
### 🤖 How the 3-Agent Pipeline Works

| Agent | Role | Model | What it does |
|-------|------|-------|-------------|
| **Agent 1 — Data Scientist** | Cleaner | Claude Haiku | Standardizes dates, normalizes phone numbers, title-cases names, removes duplicates, flags missing fields |
| **Agent 2 — Business Analyst** | Analyst | Claude Haiku | Finds revenue trends, top services/providers, anomalies, no-show patterns, period-over-period changes |
| **Agent 3 — Growth Strategist** | Strategist | Claude Haiku | Produces prioritized quick wins, 90-day growth initiatives, marketing & ops recommendations |

### 💰 Cost Estimate
- **Model:** `claude-haiku-4-5` ($1.00 input / $5.00 output per 1M tokens)
- **Typical pipeline cost:** ~$0.002–$0.015 per run (< 2 cents for most datasets)
- **Volume:** 100 runs/month ≈ $0.20–$1.50

### 📧 Email Delivery
Results are emailed in a rich HTML report to **info@fivezero3.net** after every run.
Configure your SMTP credentials in `.env` (see `.env.example`).

### 🔒 HIPAA Note
No PHI is transmitted outside your system. The agents receive structured records
(same data visible in your CRM) and process them server-side. The email report
contains aggregate insights and recommendations only — no individual patient identifiers.
""")
