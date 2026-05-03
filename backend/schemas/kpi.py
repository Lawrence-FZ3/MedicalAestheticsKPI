from pydantic import BaseModel
from typing import Optional
from datetime import date


class KPISnapshotCreate(BaseModel):
    period: str
    snapshot_date: date
    total_revenue: Optional[float] = None
    new_patients: Optional[int] = None
    total_appointments: Optional[int] = None
    completed_appointments: Optional[int] = None
    no_show_rate: Optional[float] = None
    avg_revenue_per_patient: Optional[float] = None
    new_leads: Optional[int] = None
    leads_converted: Optional[int] = None
    conversion_rate: Optional[float] = None
    data_source: str = "Manual"
    notes: Optional[str] = None
