import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from backend.auth import verify_token, TokenData
from backend.airtable_client import inventory_table

router = APIRouter(prefix="/inventory", tags=["inventory"])


class InventoryCreate(BaseModel):
    product_name: str
    category: Optional[str] = None
    supplier: Optional[str] = None
    unit_cost: Optional[float] = None
    retail_price: Optional[float] = None
    units_in_stock: int = 0
    reorder_level: int = 0
    reorder_qty: int = 0
    active: bool = True
    notes: Optional[str] = None


@router.get("/")
def list_inventory(low_stock_only: bool = False, token: TokenData = Depends(verify_token)):
    records = inventory_table().all(sort=[{"field": "Product Name", "direction": "asc"}])
    items = [{"id": r["id"], **r["fields"]} for r in records]
    if low_stock_only:
        items = [
            i for i in items
            if int(i.get("Units In Stock") or 0) <= int(i.get("Reorder Level") or 0)
        ]
    return items


@router.post("/", status_code=201)
def create_inventory_item(body: InventoryCreate, token: TokenData = Depends(verify_token)):
    fields = {
        "SKU": f"SKU-{uuid.uuid4().hex[:6].upper()}",
        "Product Name": body.product_name,
        "Units In Stock": body.units_in_stock,
        "Reorder Level": body.reorder_level,
        "Reorder Qty": body.reorder_qty,
        "Active": body.active,
    }
    if body.category:
        fields["Category"] = body.category
    if body.supplier:
        fields["Supplier"] = body.supplier
    if body.unit_cost is not None:
        fields["Unit Cost"] = body.unit_cost
    if body.retail_price is not None:
        fields["Retail Price"] = body.retail_price
    if body.notes:
        fields["Notes"] = body.notes
    record = inventory_table().create(fields)
    return {"id": record["id"], **record["fields"]}


@router.get("/valuation")
def inventory_valuation(token: TokenData = Depends(verify_token)):
    records = inventory_table().all()
    total_cost = 0.0
    total_retail = 0.0
    low_stock = []
    for r in records:
        f = r["fields"]
        units = float(f.get("Units In Stock") or 0)
        cost = float(f.get("Unit Cost") or 0)
        retail = float(f.get("Retail Price") or 0)
        total_cost += units * cost
        total_retail += units * retail
        if units <= float(f.get("Reorder Level") or 0):
            low_stock.append(f.get("Product Name", "Unknown"))
    return {
        "total_inventory_at_cost": round(total_cost, 2),
        "total_inventory_at_retail": round(total_retail, 2),
        "potential_margin": round(total_retail - total_cost, 2),
        "low_stock_items": low_stock,
        "low_stock_count": len(low_stock),
    }
