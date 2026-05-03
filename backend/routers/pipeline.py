import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, HTTPException
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import pipeline_table
from backend.schemas.pipeline import LeadCreate, LeadUpdate

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

STAGE_ORDER = [
    "New Lead", "Contacted", "Consultation Scheduled",
    "Consultation Done", "Treatment Planned", "Converted", "Lost",
]


def _to_airtable(data: dict) -> dict:
    mapping = {
        "lead_name": "Lead Name",
        "email": "Email",
        "phone": "Phone",
        "stage": "Stage",
        "lead_source": "Lead Source",
        "assigned_to": "Assigned To",
        "treatment_interest": "Treatment Interest",
        "estimated_value": "Estimated Value",
        "date_created": "Date Created",
        "last_contact": "Last Contact",
        "next_follow_up": "Next Follow-Up",
        "notes": "Notes",
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
def list_leads(
    stage: Optional[str] = None,
    assigned_to: Optional[str] = None,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    formulas = []
    if stage:
        formulas.append(f"{{Stage}}='{stage}'")
    if assigned_to:
        formulas.append(f"{{Assigned To}}='{assigned_to}'")
    formula = f"AND({','.join(formulas)})" if len(formulas) > 1 else (formulas[0] if formulas else None)
    records = pipeline_table().all(formula=formula)
    log_action(token.username, "VIEW", "Pipeline", ip_address=request.client.host if request else "")
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.get("/board")
def pipeline_board(token: TokenData = Depends(verify_token)):
    """Returns leads grouped by stage for kanban display."""
    records = pipeline_table().all()
    board: dict = {stage: [] for stage in STAGE_ORDER}
    for r in records:
        stage = r["fields"].get("Stage", "New Lead")
        if stage in board:
            board[stage].append({"id": r["id"], **r["fields"]})
    return board


@router.post("/", status_code=201)
def create_lead(body: LeadCreate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable(body.model_dump())
    fields["Lead ID"] = f"LEAD-{uuid.uuid4().hex[:8].upper()}"
    fields["Date Created"] = date.today().strftime("%Y-%m-%d")
    record = pipeline_table().create(fields)
    log_action(token.username, "CREATE", "Pipeline", resource_id=record["id"], ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.patch("/{record_id}")
def update_lead(record_id: str, body: LeadUpdate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable({k: v for k, v in body.model_dump().items() if v is not None})
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    record = pipeline_table().update(record_id, fields)
    log_action(token.username, "UPDATE", "Pipeline", resource_id=record_id, ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}
