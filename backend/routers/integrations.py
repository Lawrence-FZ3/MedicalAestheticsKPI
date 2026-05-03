"""
Sync router — triggers data pulls from AestheticsPro, GetWeave, QuickBooks,
and handles Excel file uploads. All actions are audit-logged.
"""
import uuid
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import patients_table, appointments_table
from backend.integrations.aestheticspro import AestheticsProClient
from backend.integrations.getweave import GetWeaveClient
from backend.integrations.quickbooks import QuickBooksClient
from backend.integrations.excel_parser import parse_patient_excel, parse_appointment_excel, parse_financial_excel
from backend.config import get_settings

router = APIRouter(prefix="/integrations", tags=["integrations"])
settings = get_settings()


def _upsert_patient(fields: dict) -> dict:
    external_id = fields.get("external_id", "")
    if external_id:
        existing = patients_table().all(formula=f"{{External ID}}='{external_id}'")
        if existing:
            return {"action": "skipped", "id": existing[0]["id"]}
    at_fields = {
        "Patient ID": f"PAT-{uuid.uuid4().hex[:8].upper()}",
        "Full Name": fields.get("full_name", ""),
        "Lead Source": fields.get("lead_source", "Other"),
        "Status": fields.get("status", "Active"),
        "External ID": external_id,
    }
    if fields.get("email"):
        at_fields["Email"] = fields["email"]
    if fields.get("phone"):
        at_fields["Phone"] = fields["phone"]
    if fields.get("date_of_birth"):
        at_fields["Date of Birth"] = str(fields["date_of_birth"])[:10]
    if fields.get("gender"):
        at_fields["Gender"] = fields["gender"]
    if fields.get("notes"):
        at_fields["Notes"] = fields["notes"]
    at_fields["First Visit Date"] = date.today().strftime("%Y-%m-%d")
    record = patients_table().create(at_fields)
    return {"action": "created", "id": record["id"]}


def _upsert_appointment(fields: dict) -> dict:
    at_fields = {
        "Appointment ID": f"APT-{uuid.uuid4().hex[:8].upper()}",
        "Provider": fields.get("provider", ""),
        "Service": fields.get("service", ""),
        "Status": fields.get("status", "Scheduled"),
        "Source": fields.get("source", "Manual"),
    }
    if fields.get("appointment_date"):
        at_fields["Appointment Date"] = str(fields["appointment_date"])
    if fields.get("duration_min"):
        at_fields["Duration (min)"] = int(fields["duration_min"])
    if fields.get("revenue") is not None:
        at_fields["Revenue"] = float(fields["revenue"])
    if fields.get("notes"):
        at_fields["Notes"] = fields["notes"]
    record = appointments_table().create(at_fields)
    return {"action": "created", "id": record["id"]}


@router.post("/sync/aestheticspro")
def sync_aestheticspro(
    days_back: int = 30,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    if not settings.aestheticspro_api_key:
        raise HTTPException(status_code=400, detail="AestheticsPro API key not configured")
    client = AestheticsProClient()
    results = {"patients": {"created": 0, "skipped": 0}, "appointments": {"created": 0}}
    for raw in client.get_patients():
        res = _upsert_patient(client.map_patient(raw))
        results["patients"][res["action"]] = results["patients"].get(res["action"], 0) + 1
    end = date.today()
    start = end - timedelta(days=days_back)
    for raw in client.get_appointments(start, end):
        _upsert_appointment(client.map_appointment(raw))
        results["appointments"]["created"] += 1
    log_action(token.username, "SYNC", "System", ip_address=request.client.host if request else "", details=f"AestheticsPro sync: {results}")
    return results


@router.post("/sync/getweave")
def sync_getweave(
    days_back: int = 30,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    if not settings.getweave_api_key:
        raise HTTPException(status_code=400, detail="GetWeave API key not configured")
    client = GetWeaveClient()
    results = {"contacts": {"created": 0, "skipped": 0}, "appointments": {"created": 0}}
    for raw in client.get_contacts():
        res = _upsert_patient(client.map_contact(raw))
        results["contacts"][res["action"]] = results["contacts"].get(res["action"], 0) + 1
    end = date.today()
    start = end - timedelta(days=days_back)
    for raw in client.get_appointments(start, end):
        _upsert_appointment(client.map_appointment(raw))
        results["appointments"]["created"] += 1
    log_action(token.username, "SYNC", "System", ip_address=request.client.host if request else "", details=f"GetWeave sync: {results}")
    return results


@router.get("/sync/quickbooks/revenue")
def sync_quickbooks_revenue(token: TokenData = Depends(verify_token)):
    if not settings.qbo_client_id:
        raise HTTPException(status_code=400, detail="QuickBooks credentials not configured")
    client = QuickBooksClient()
    return client.get_revenue_summary()


@router.post("/upload/patients")
async def upload_patients_excel(
    file: UploadFile = File(...),
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")
    content = await file.read()
    patients = parse_patient_excel(content)
    results = {"created": 0, "skipped": 0}
    for p in patients:
        res = _upsert_patient(p)
        results[res["action"]] = results.get(res["action"], 0) + 1
    log_action(token.username, "SYNC", "Patient", ip_address=request.client.host if request else "", details=f"Excel upload: {results}")
    return {**results, "total_rows": len(patients)}


@router.post("/upload/appointments")
async def upload_appointments_excel(
    file: UploadFile = File(...),
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")
    content = await file.read()
    appointments = parse_appointment_excel(content)
    results = {"created": 0}
    for a in appointments:
        _upsert_appointment(a)
        results["created"] += 1
    log_action(token.username, "SYNC", "Appointment", ip_address=request.client.host if request else "", details=f"Excel upload: {results}")
    return {**results, "total_rows": len(appointments)}


@router.post("/upload/financial")
async def upload_financial_excel(
    file: UploadFile = File(...),
    token: TokenData = Depends(verify_token),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="File must be .xlsx or .xls")
    content = await file.read()
    transactions = parse_financial_excel(content)
    return {"parsed_rows": len(transactions), "preview": transactions[:5]}
