import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import appointments_table
from backend.schemas.appointment import AppointmentCreate, AppointmentUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _to_airtable(data: dict) -> dict:
    mapping = {
        "provider": "Provider",
        "service": "Service",
        "appointment_date": "Appointment Date",
        "status": "Status",
        "duration_min": "Duration (min)",
        "revenue": "Revenue",
        "source": "Source",
        "notes": "Notes",
    }
    result = {}
    for py_key, at_key in mapping.items():
        if py_key in data and data[py_key] is not None:
            val = data[py_key]
            if hasattr(val, "isoformat"):
                val = val.isoformat()
            result[at_key] = val
    return result


@router.get("/")
def list_appointments(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    formulas = []
    if status:
        formulas.append(f"{{Status}}='{status}'")
    if provider:
        formulas.append(f"{{Provider}}='{provider}'")
    formula = f"AND({','.join(formulas)})" if len(formulas) > 1 else (formulas[0] if formulas else None)
    records = appointments_table().all(formula=formula, sort=[{"field": "Appointment Date", "direction": "desc"}])
    log_action(token.username, "VIEW", "Appointment", ip_address=request.client.host if request else "")
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.get("/{record_id}")
def get_appointment(record_id: str, request: Request = None, token: TokenData = Depends(verify_token)):
    try:
        record = appointments_table().get(record_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Appointment not found")
    log_action(token.username, "VIEW", "Appointment", resource_id=record_id, ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.post("/", status_code=201)
def create_appointment(body: AppointmentCreate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable(body.model_dump())
    fields["Appointment ID"] = f"APT-{uuid.uuid4().hex[:8].upper()}"
    record = appointments_table().create(fields)
    log_action(token.username, "CREATE", "Appointment", resource_id=record["id"], ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.patch("/{record_id}")
def update_appointment(record_id: str, body: AppointmentUpdate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable({k: v for k, v in body.model_dump().items() if v is not None})
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    record = appointments_table().update(record_id, fields)
    log_action(token.username, "UPDATE", "Appointment", resource_id=record_id, ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.get("/stats/summary")
def appointment_stats(token: TokenData = Depends(verify_token)):
    records = appointments_table().all()
    total = len(records)
    by_status: dict = {}
    revenue_total = 0.0
    for r in records:
        f = r["fields"]
        s = f.get("Status", "Unknown")
        by_status[s] = by_status.get(s, 0) + 1
        revenue_total += float(f.get("Revenue") or 0)
    no_show_rate = round(by_status.get("No-Show", 0) / total * 100, 1) if total else 0
    return {
        "total": total,
        "by_status": by_status,
        "total_revenue": revenue_total,
        "no_show_rate": no_show_rate,
    }
