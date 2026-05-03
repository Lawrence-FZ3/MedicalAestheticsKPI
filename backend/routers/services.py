import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.auth import verify_token, TokenData
from backend.airtable_client import services_table

router = APIRouter(prefix="/services", tags=["services"])


class ServiceCreate(BaseModel):
    service_name: str
    category: Optional[str] = None
    price: Optional[float] = None
    duration_min: Optional[int] = None
    active: bool = True
    description: Optional[str] = None


@router.get("/")
def list_services(active_only: bool = True, token: TokenData = Depends(verify_token)):
    formula = "{Active}=1" if active_only else None
    records = services_table().all(formula=formula, sort=[{"field": "Service Name", "direction": "asc"}])
    return [{"id": r["id"], **r["fields"]} for r in records]


@router.post("/", status_code=201)
def create_service(body: ServiceCreate, token: TokenData = Depends(verify_token)):
    fields = {"Service ID": f"SVC-{uuid.uuid4().hex[:8].upper()}"}
    if body.service_name:
        fields["Service Name"] = body.service_name
    if body.category:
        fields["Category"] = body.category
    if body.price is not None:
        fields["Price"] = body.price
    if body.duration_min is not None:
        fields["Duration (min)"] = body.duration_min
    fields["Active"] = body.active
    if body.description:
        fields["Description"] = body.description
    record = services_table().create(fields)
    return {"id": record["id"], **record["fields"]}


@router.patch("/{record_id}")
def update_service(record_id: str, body: ServiceCreate, token: TokenData = Depends(verify_token)):
    fields = {}
    if body.service_name:
        fields["Service Name"] = body.service_name
    if body.category:
        fields["Category"] = body.category
    if body.price is not None:
        fields["Price"] = body.price
    if body.duration_min is not None:
        fields["Duration (min)"] = body.duration_min
    fields["Active"] = body.active
    if body.description:
        fields["Description"] = body.description
    record = services_table().update(record_id, fields)
    return {"id": record["id"], **record["fields"]}
