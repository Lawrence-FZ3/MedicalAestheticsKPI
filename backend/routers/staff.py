import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import date
from backend.auth import verify_token, TokenData
from backend.airtable_client import staff_table, appointments_table

router = APIRouter(prefix="/staff", tags=["staff"])


class StaffCreate(BaseModel):
    full_name: str
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    start_date: Optional[date] = None
    compensation_type: Optional[str] = None
    base_compensation: Optional[float] = None
    commission_rate: Optional[float] = None
    active: bool = True
    notes: Optional[str] = None


@router.get("/")
def list_staff(active_only: bool = True, token: TokenData = Depends(verify_token)):
    formula = "{Active}=1" if active_only else None
    records = staff_table().all(formula=formula, sort=[{"field": "Full Name", "direction": "asc"}])
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.post("/", status_code=201)
def create_staff(body: StaffCreate, token: TokenData = Depends(verify_token)):
    fields = {
        "Staff ID": f"STF-{uuid.uuid4().hex[:8].upper()}",
        "Full Name": body.full_name,
        "Role": body.role,
        "Active": body.active,
    }
    if body.email:
        fields["Email"] = body.email
    if body.phone:
        fields["Phone"] = body.phone
    if body.start_date:
        fields["Start Date"] = body.start_date.strftime("%Y-%m-%d")
    if body.compensation_type:
        fields["Compensation Type"] = body.compensation_type
    if body.base_compensation is not None:
        fields["Base Compensation"] = body.base_compensation
    if body.commission_rate is not None:
        fields["Commission Rate"] = body.commission_rate
    if body.notes:
        fields["Notes"] = body.notes
    record = staff_table().create(fields)
    return {"id": record["id"], **record["fields"]}


@router.get("/performance")
def staff_performance(token: TokenData = Depends(verify_token)):
    """Revenue and appointment counts grouped by provider."""
    appts = appointments_table().all(formula="{Status}='Completed'")
    performance: dict = {}
    for a in appts:
        f = a["fields"]
        provider = f.get("Provider", "Unknown")
        rev = float(f.get("Revenue") or 0)
        if provider not in performance:
            performance[provider] = {"appointments": 0, "revenue": 0.0}
        performance[provider]["appointments"] += 1
        performance[provider]["revenue"] += rev

    for p in performance:
        appts_count = performance[p]["appointments"]
        revenue = performance[p]["revenue"]
        performance[p]["revenue"] = round(revenue, 2)
        performance[p]["avg_revenue_per_appt"] = round(revenue / appts_count, 2) if appts_count else 0

    return sorted(performance.items(), key=lambda x: x[1]["revenue"], reverse=True)
