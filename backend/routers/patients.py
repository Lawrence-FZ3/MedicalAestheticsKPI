import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import patients_table
from backend.schemas.patient import PatientCreate, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


def _to_airtable(data: dict) -> dict:
    mapping = {
        "full_name": "Full Name",
        "email": "Email",
        "phone": "Phone",
        "date_of_birth": "Date of Birth",
        "gender": "Gender",
        "address": "Address",
        "lead_source": "Lead Source",
        "status": "Status",
        "notes": "Notes",
        "external_id": "External ID",
        "total_spend": "Total Spend",
        "visit_count": "Visit Count",
        "last_visit_date": "Last Visit Date",
        "first_visit_date": "First Visit Date",
    }
    result = {}
    for py_key, at_key in mapping.items():
        if py_key in data and data[py_key] is not None:
            val = data[py_key]
            if isinstance(val, date):
                val = val.strftime("%Y-%m-%d")
            result[at_key] = val
    return result


@router.get("/")
def list_patients(
    status: Optional[str] = None,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    formula = f"{{Status}}='{status}'" if status else None
    records = patients_table().all(formula=formula)
    log_action(token.username, "VIEW", "Patient", ip_address=request.client.host if request else "", details=f"Listed patients (filter={status})")
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.get("/{record_id}")
def get_patient(record_id: str, request: Request = None, token: TokenData = Depends(verify_token)):
    try:
        record = patients_table().get(record_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Patient not found")
    log_action(token.username, "VIEW", "Patient", resource_id=record_id, ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.post("/", status_code=201)
def create_patient(body: PatientCreate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable(body.model_dump())
    fields["Patient ID"] = f"PAT-{uuid.uuid4().hex[:8].upper()}"
    if "First Visit Date" not in fields:
        fields["First Visit Date"] = date.today().strftime("%Y-%m-%d")
    record = patients_table().create(fields)
    log_action(token.username, "CREATE", "Patient", resource_id=record["id"], ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.patch("/{record_id}")
def update_patient(record_id: str, body: PatientUpdate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable({k: v for k, v in body.model_dump().items() if v is not None})
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    record = patients_table().update(record_id, fields)
    log_action(token.username, "UPDATE", "Patient", resource_id=record_id, ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.delete("/{record_id}", status_code=204)
def delete_patient(record_id: str, request: Request = None, token: TokenData = Depends(verify_token)):
    patients_table().delete(record_id)
    log_action(token.username, "DELETE", "Patient", resource_id=record_id, ip_address=request.client.host if request else "")
