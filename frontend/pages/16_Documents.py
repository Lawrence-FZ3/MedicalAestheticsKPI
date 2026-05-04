import streamlit as st
import pandas as pd
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, delete, is_authenticated
import requests

st.set_page_config(page_title="Documents | Zentox", page_icon="📁", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("📁 Document Library")
st.caption("Upload bank statements, contracts, agreements, reports, and more. All documents are parsed and available for AI analysis.")

CATEGORIES = ["Bank Statement", "Contract", "Agreement", "Report", "Invoice", "Tax Document", "Slide Deck", "Other"]

tab_library, tab_upload, tab_viewer = st.tabs(["📚 Library", "⬆️ Upload", "🔍 View & Analyze"])

# ============================================================
# TAB 1 — Library
# ============================================================
with tab_library:
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        cat_filter = st.selectbox("Filter by category", ["All"] + CATEGORIES)
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    try:
        params = {}
        if cat_filter != "All":
            params["category"] = cat_filter
        docs = get("/documents/", params=params)
    except Exception as e:
        st.error(f"Error loading documents: {e}")
        docs = []

    if docs:
        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Documents", len(docs))
        c2.metric("Analyzed by AI", sum(1 for d in docs if d.get("AI Analysis Run")))
        types = list({d.get("File Type", "") for d in docs if d.get("File Type")})
        c3.metric("File Types", len(types))
        total_kb = sum(float(d.get("File Size KB") or 0) for d in docs)
        c4.metric("Total Size", f"{total_kb/1024:.1f} MB" if total_kb > 1024 else f"{total_kb:.0f} KB")

        st.markdown("---")

        df = pd.DataFrame([{
            "Name": d.get("Document Name", ""),
            "Category": d.get("Category", ""),
            "Type": d.get("File Type", ""),
            "Size": f"{d.get('File Size KB', 0):.1f} KB",
            "Uploaded": d.get("Upload Date", ""),
            "By": d.get("Uploaded By", ""),
            "AI Run": "✅" if d.get("AI Analysis Run") else "—",
            "id": d.get("id", ""),
        } for d in docs])

        st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### Actions")
        selected_name = st.selectbox("Select a document", [d.get("Document Name", "") for d in docs])
        selected = next((d for d in docs if d.get("Document Name") == selected_name), None)

        if selected:
            doc_id = selected.get("id")
            ac1, ac2, ac3 = st.columns(3)

            with ac1:
                # Download button via API
                if st.button("⬇️ Download", use_container_width=True):
                    st.session_state["view_doc_id"] = doc_id
                    st.session_state["view_doc_name"] = selected_name
                    try:
                        token = st.session_state.get("token", "")
                        api_url = st.session_state.get("api_url", "http://localhost:8000")
                        resp = requests.get(
                            f"{api_url}/documents/{doc_id}/download",
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=30,
                        )
                        if resp.status_code == 200:
                            st.download_button(
                                label=f"Save {selected_name}",
                                data=resp.content,
                                file_name=selected_name,
                                use_container_width=True,
                            )
                        else:
                            st.error("Could not retrieve file.")
                    except Exception as e:
                        st.error(f"Download error: {e}")

            with ac2:
                send_email = st.checkbox("Email report", value=True, key="lib_email")
                if st.button("🤖 Run AI Analysis", use_container_width=True):
                    try:
                        result = post(f"/documents/{doc_id}/analyze", {"send_email": send_email})
                        st.success(result.get("message", "Pipeline started!"))
                    except Exception as e:
                        st.error(f"Error: {e}")

            with ac3:
                if st.button("🗑️ Delete", use_container_width=True, type="secondary"):
                    try:
                        delete(f"/documents/{doc_id}")
                        st.success(f"'{selected_name}' deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("No documents yet. Upload some in the **⬆️ Upload** tab.")

# ============================================================
# TAB 2 — Upload
# ============================================================
with tab_upload:
    st.subheader("Upload a Document")
    st.markdown("Supported formats: **PDF, Excel (.xlsx/.xls/.csv), PowerPoint (.pptx), Word (.docx), Markdown (.md), Text (.txt)**")

    with st.form("upload_form", clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "xlsx", "xls", "csv", "pptx", "ppt", "docx", "doc", "md", "markdown", "txt", "text"],
        )
        c1, c2 = st.columns(2)
        category = c1.selectbox("Category", CATEGORIES)
        notes = c2.text_input("Notes (optional)", placeholder="e.g. Chase Bank – March 2025")
        run_ai = st.checkbox("Automatically run AI analysis after upload", value=False)
        send_email = st.checkbox("Email the AI report to info@fivezero3.net", value=True)

        submitted = st.form_submit_button("⬆️ Upload & Parse", use_container_width=True, type="primary")

        if submitted and uploaded_file:
            with st.spinner(f"Uploading and parsing {uploaded_file.name}..."):
                try:
                    token = st.session_state.get("token", "")
                    api_url = st.session_state.get("api_url", "http://localhost:8000")
                    resp = requests.post(
                        f"{api_url}/documents/upload",
                        headers={"Authorization": f"Bearer {token}"},
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        data={"category": category, "notes": notes or ""},
                        timeout=60,
                    )
                    if resp.status_code == 200:
                        result = resp.json()
                        st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Characters parsed", f"{result.get('parsed_chars', 0):,}")
                        col2.metric("Table rows", result.get("table_rows", 0))
                        col3.metric("File size", f"{result.get('file_size_kb', 0):.1f} KB")
                        if result.get("parse_error"):
                            st.warning(f"Parse warning: {result['parse_error']}")

                        if run_ai:
                            doc_id = result.get("id")
                            if doc_id:
                                with st.spinner("Running AI analysis..."):
                                    try:
                                        ai_resp = post(f"/documents/{doc_id}/analyze", {"send_email": send_email})
                                        st.info(ai_resp.get("message", "AI pipeline started."))
                                    except Exception as e:
                                        st.error(f"AI error: {e}")
                    else:
                        st.error(f"Upload failed: {resp.text}")
                except Exception as e:
                    st.error(f"Upload error: {e}")

# ============================================================
# TAB 3 — Viewer
# ============================================================
with tab_viewer:
    st.subheader("View Parsed Content")

    try:
        all_docs = get("/documents/")
    except Exception:
        all_docs = []

    if not all_docs:
        st.info("No documents uploaded yet.")
        st.stop()

    doc_options = {f"{d.get('Document Name','')} ({d.get('Category','')})": d.get("id") for d in all_docs}
    selected_label = st.selectbox("Choose a document to view", list(doc_options.keys()))
    selected_id = doc_options.get(selected_label)

    if selected_id and st.button("Load Content"):
        with st.spinner("Fetching parsed text..."):
            try:
                data = get(f"/documents/{selected_id}/parsed-text")
                st.session_state["viewer_data"] = data
            except Exception as e:
                st.error(f"Error: {e}")

    viewer_data = st.session_state.get("viewer_data")
    if viewer_data:
        st.markdown(f"**Document:** {viewer_data.get('Document Name', '')}")
        text = viewer_data.get("Parsed Text", "")
        if text:
            st.text_area("Parsed Content", value=text, height=400)
            st.caption(f"{len(text):,} characters extracted")
        else:
            st.warning("No parsed text available for this document.")

        st.markdown("---")
        send_email_v = st.checkbox("Email the AI report", value=True, key="viewer_email")
        if st.button("🤖 Send to AI Pipeline", type="primary"):
            try:
                result = post(f"/documents/{selected_id}/analyze", {"send_email": send_email_v})
                st.success(result.get("message", "Pipeline started! Check the AI Agents page."))
            except Exception as e:
                st.error(f"Error: {e}")
