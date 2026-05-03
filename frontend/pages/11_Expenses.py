import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated

st.set_page_config(page_title="Expenses | Zentox", page_icon="💸", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("💸 Expense Tracker")

CATEGORIES = ["Payroll", "Rent", "Marketing", "Supplies & Products", "Equipment", "Software & Subscriptions", "Professional Fees", "Insurance", "Utilities", "Training & Education", "Other"]

tab1, tab2 = st.tabs(["📋 Expense Log", "➕ Add Expense"])

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        cat_filter = st.selectbox("Category", ["All"] + CATEGORIES)
    with col2:
        start_f = st.date_input("From", value=date.today().replace(day=1))
    with col3:
        end_f = st.date_input("To", value=date.today())

    try:
        params = {"start_date": str(start_f), "end_date": str(end_f)}
        if cat_filter != "All":
            params["category"] = cat_filter
        expenses = get("/financials/expenses", params=params)
    except Exception as e:
        st.error(f"Error: {e}")
        expenses = []

    if expenses:
        total = sum(float(e.get("Amount") or 0) for e in expenses)
        st.metric("Total Expenses (filtered)", f"${total:,.2f}")

        df = pd.DataFrame([{
            "Date": e.get("Date", ""),
            "Vendor": e.get("Vendor", ""),
            "Description": e.get("Description", ""),
            "Category": e.get("Category", ""),
            "Amount": f"${float(e.get('Amount') or 0):,.2f}",
            "Payment Method": e.get("Payment Method", ""),
            "Tax Deductible": "✅" if e.get("Tax Deductible") else "❌",
            "Recurring": "🔄" if e.get("Recurring") else "",
        } for e in expenses])
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Category breakdown chart
        cat_totals = {}
        for e in expenses:
            cat = e.get("Category", "Other")
            cat_totals[cat] = cat_totals.get(cat, 0) + float(e.get("Amount") or 0)
        if cat_totals:
            fig = px.pie(
                pd.DataFrame(list(cat_totals.items()), columns=["Category", "Amount"]),
                values="Amount", names="Category",
                title="Expense Breakdown by Category",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No expenses found for this period.")

with tab2:
    with st.form("new_expense"):
        c1, c2 = st.columns(2)
        exp_date = c1.date_input("Date", value=date.today())
        vendor = c2.text_input("Vendor / Payee")
        description = c1.text_input("Description")
        category = c2.selectbox("Category", CATEGORIES)
        amount = c1.number_input("Amount ($)", min_value=0.01, step=1.0)
        payment_method = c2.selectbox("Payment Method", ["Business Card", "ACH", "Check", "Cash", "Wire"])
        tax_deductible = c1.checkbox("Tax Deductible", value=True)
        recurring = c2.checkbox("Recurring")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Expense")
        if submitted and vendor and amount > 0:
            payload = {
                "date": str(exp_date),
                "vendor": vendor,
                "description": description or vendor,
                "category": category,
                "amount": float(amount),
                "payment_method": payment_method,
                "tax_deductible": tax_deductible,
                "recurring": recurring,
                "notes": notes or None,
            }
            try:
                post("/financials/expenses", payload)
                st.success(f"Expense of ${amount:,.2f} to {vendor} saved!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
