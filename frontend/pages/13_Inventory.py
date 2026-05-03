import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from frontend.utils.api_client import get, post, is_authenticated

st.set_page_config(page_title="Inventory | Zentox", page_icon="📦", layout="wide")

if not is_authenticated():
    st.warning("Please log in first.")
    st.stop()

st.title("📦 Inventory Management")

tab1, tab2, tab3 = st.tabs(["📋 Stock Levels", "💰 Valuation", "➕ Add Item"])

with tab1:
    low_stock_only = st.checkbox("⚠️ Show low stock only", value=False)
    try:
        inventory = get("/inventory/", params={"low_stock_only": low_stock_only})
    except Exception as e:
        st.error(f"Error: {e}")
        inventory = []

    if inventory:
        df = pd.DataFrame([{
            "SKU": i.get("SKU", ""),
            "Product": i.get("Product Name", ""),
            "Category": i.get("Category", ""),
            "Supplier": i.get("Supplier", ""),
            "In Stock": i.get("Units In Stock", 0),
            "Reorder Level": i.get("Reorder Level", 0),
            "Unit Cost": f"${float(i.get('Unit Cost') or 0):,.2f}",
            "Retail Price": f"${float(i.get('Retail Price') or 0):,.2f}",
            "Status": "⚠️ LOW" if int(i.get("Units In Stock") or 0) <= int(i.get("Reorder Level") or 0) else "✅ OK",
        } for i in inventory])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No inventory items found.")

with tab2:
    try:
        val = get("/inventory/valuation")
    except Exception as e:
        st.error(f"Error: {e}")
        val = {}

    if val:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Inventory at Cost", f"${val.get('total_inventory_at_cost', 0):,.2f}")
        c2.metric("Inventory at Retail", f"${val.get('total_inventory_at_retail', 0):,.2f}")
        c3.metric("Potential Margin", f"${val.get('potential_margin', 0):,.2f}")
        c4.metric("⚠️ Low Stock Items", val.get("low_stock_count", 0))

        low = val.get("low_stock_items", [])
        if low:
            st.warning(f"Items needing reorder: **{', '.join(low)}**")

with tab3:
    with st.form("new_item"):
        c1, c2 = st.columns(2)
        product_name = c1.text_input("Product Name *")
        category = c2.selectbox("Category", ["Injectables", "Skincare Retail", "Consumables", "Equipment", "PPE", "Other"])
        supplier = c1.text_input("Supplier")
        unit_cost = c2.number_input("Unit Cost ($)", min_value=0.0, step=1.0)
        retail_price = c1.number_input("Retail Price ($)", min_value=0.0, step=1.0)
        units = c2.number_input("Units In Stock", min_value=0, step=1)
        reorder_level = c1.number_input("Reorder Level", min_value=0, step=1)
        reorder_qty = c2.number_input("Reorder Qty", min_value=0, step=1)
        notes = st.text_area("Notes")
        if st.form_submit_button("Add Item"):
            if product_name:
                try:
                    post("/inventory/", {
                        "product_name": product_name,
                        "category": category,
                        "supplier": supplier or None,
                        "unit_cost": float(unit_cost) if unit_cost else None,
                        "retail_price": float(retail_price) if retail_price else None,
                        "units_in_stock": int(units),
                        "reorder_level": int(reorder_level),
                        "reorder_qty": int(reorder_qty),
                        "active": True,
                        "notes": notes or None,
                    })
                    st.success(f"'{product_name}' added to inventory!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
