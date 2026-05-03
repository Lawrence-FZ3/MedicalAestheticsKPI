from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date


class LeadCreate(BaseModel):
    lead_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    stage: str = "New Lead"
    lead_source: Optional[str] = None
    assigned_to: Optional[str] = None
    treatment_interest: Optional[List[str]] = None
    estimated_value: Optional[float] = None
    next_follow_up: Optional[date] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    lead_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    stage: Optional[str] = None
    lead_source: Optional[str] = None
    assigned_to: Optional[str] = None
    treatment_interest: Optional[List[str]] = None
    estimated_value: Optional[float] = None
    last_contact: Optional[date] = None
    next_follow_up: Optional[date] = None
    notes: Optional[str] = None
