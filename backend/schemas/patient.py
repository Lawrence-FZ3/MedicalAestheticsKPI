from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


class PatientCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    lead_source: Optional[str] = None
    status: str = "Active"
    notes: Optional[str] = None
    external_id: Optional[str] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    lead_source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    total_spend: Optional[float] = None
    visit_count: Optional[int] = None
    last_visit_date: Optional[date] = None
