"""
GetWeave integration — pulls contacts, appointments, and communication records.
GetWeave API docs: https://developers.getweave.com
"""
import httpx
from datetime import date
from backend.config import get_settings

settings = get_settings()


class GetWeaveClient:
    def __init__(self):
        self.base_url = settings.getweave_api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.getweave_api_key}",
            "Location-Id": settings.getweave_location_id,
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{self.base_url}{path}", headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json()

    def get_contacts(self, page: int = 1) -> list[dict]:
        data = self._get("/public/v1/contacts", params={"page": page, "pageSize": 100})
        return data.get("data", data) if isinstance(data, dict) else data

    def get_appointments(self, start_date: date, end_date: date) -> list[dict]:
        data = self._get("/public/v1/appointments", params={
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        })
        return data.get("data", data) if isinstance(data, dict) else data

    def map_contact(self, raw: dict) -> dict:
        name_parts = [raw.get("firstName", ""), raw.get("lastName", "")]
        return {
            "full_name": " ".join(p for p in name_parts if p),
            "email": raw.get("email"),
            "phone": raw.get("mobilePhone") or raw.get("homePhone"),
            "date_of_birth": raw.get("birthdate"),
            "gender": raw.get("gender"),
            "lead_source": "GetWeave",
            "status": "Active",
            "external_id": str(raw.get("id", "")),
        }

    def map_appointment(self, raw: dict) -> dict:
        return {
            "provider": raw.get("practitionerName", ""),
            "service": raw.get("appointmentType", ""),
            "appointment_date": raw.get("startTime"),
            "status": raw.get("status", "Scheduled"),
            "duration_min": raw.get("duration"),
            "source": "GetWeave",
        }
