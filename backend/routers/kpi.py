import uuid
from datetime import date
from fastapi import APIRouter, Depends, Request
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import kpi_table, patients_table, appointments_table, pipeline_table
from backend.schemas.kpi import KPISnapshotCreate

router = APIRouter(prefix="/kpi", tags=["kpi"])


def _to_airtable(data: dict) -> dict:
    mapping = {
        "period": "Period",
        "snapshot_date": "Snapshot Date",
        "total_revenue": "Total Revenue",
        "new_patients": "New Patients",
        "total_appointments": "Total Appointments",
        "completed_appointments": "Completed Appointments",
        "no_show_rate": "No-Show Rate",
        "avg_revenue_per_patient": "Avg Revenue Per Patient",
        "new_leads": "New Leads",
        "leads_converted": "Leads Converted",
        "conversion_rate": "Conversion Rate",
        "data_source": "Data Source",
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


@router.get("/snapshots")
def list_snapshots(period: str = None, token: TokenData = Depends(verify_token)):
    formula = f"{{Period}}='{period}'" if period else None
    records = kpi_table().all(formula=formula, sort=[{"field": "Snapshot Date", "direction": "desc"}])
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.post("/snapshots", status_code=201)
def create_snapshot(body: KPISnapshotCreate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = _to_airtable(body.model_dump())
    fields["Snapshot ID"] = f"KPI-{uuid.uuid4().hex[:8].upper()}"
    record = kpi_table().create(fields)
    log_action(token.username, "CREATE", "KPI", resource_id=record["id"], ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.get("/live")
def live_kpis(token: TokenData = Depends(verify_token)):
    """Compute real-time KPIs directly from Airtable tables."""
    patients = patients_table().all()
    appointments = appointments_table().all()
    leads = pipeline_table().all()

    total_patients = len([p for p in patients if p["fields"].get("Status") == "Active"])
    new_patients_mtd = 0
    total_revenue = 0.0
    completed = 0
    no_shows = 0
    today = date.today()

    for appt in appointments:
        f = appt["fields"]
        revenue = float(f.get("Revenue") or 0)
        total_revenue += revenue
        if f.get("Status") == "Completed":
            completed += 1
        if f.get("Status") == "No-Show":
            no_shows += 1

    total_appts = len(appointments)
    no_show_rate = round(no_shows / total_appts * 100, 1) if total_appts else 0
    avg_revenue = round(total_revenue / total_patients, 2) if total_patients else 0

    pipeline_leads = len(leads)
    converted = len([l for l in leads if l["fields"].get("Stage") == "Converted"])
    conversion_rate = round(converted / pipeline_leads * 100, 1) if pipeline_leads else 0

    return {
        "total_active_patients": total_patients,
        "total_revenue": round(total_revenue, 2),
        "total_appointments": total_appts,
        "completed_appointments": completed,
        "no_show_rate": no_show_rate,
        "avg_revenue_per_patient": avg_revenue,
        "pipeline_leads": pipeline_leads,
        "converted_leads": converted,
        "conversion_rate": conversion_rate,
        "as_of": today.isoformat(),
    }
