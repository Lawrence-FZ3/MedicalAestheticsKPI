from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AppointmentCreate(BaseModel):
    provider: str
    service: str
    appointment_date: datetime
    status: str = "Scheduled"
    duration_min: Optional[int] = None
    revenue: Optional[float] = None
    source: str = "Manual"
    notes: Optional[str] = None
    patient_record_id: Optional[str] = None


class AppointmentUpdate(BaseModel):
    provider: Optional[str] = None
    service: Optional[str] = None
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    duration_min: Optional[int] = None
    revenue: Optional[float] = None
    notes: Optional[str] = None
