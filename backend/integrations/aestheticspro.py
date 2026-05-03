"""
AestheticsPro integration — pulls patients and appointments via REST API.
Docs: https://developers.aestheticspro.com  (API key required)
"""
import httpx
from datetime import date
from backend.config import get_settings

settings = get_settings()


class AestheticsProClient:
    def __init__(self):
        self.base_url = settings.aestheticspro_api_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {settings.aestheticspro_api_key}",
            "Content-Type": "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        with httpx.Client(timeout=30) as client:
            resp = client.get(f"{self.base_url}{path}", headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json()

    def get_patients(self, page: int = 1, page_size: int = 100) -> list[dict]:
        data = self._get("/api/v1/patients", params={"page": page, "pageSize": page_size})
        return data.get("patients", data) if isinstance(data, dict) else data

    def get_appointments(self, start_date: date, end_date: date) -> list[dict]:
        data = self._get("/api/v1/appointments", params={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        })
        return data.get("appointments", data) if isinstance(data, dict) else data

    def map_patient(self, raw: dict) -> dict:
        """Normalize AestheticsPro patient fields to Zentox schema."""
        return {
            "full_name": f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip(),
            "email": raw.get("email"),
            "phone": raw.get("phone") or raw.get("mobilePhone"),
            "date_of_birth": raw.get("dateOfBirth"),
            "gender": raw.get("gender"),
            "address": raw.get("address"),
            "lead_source": "AestheticsPro",
            "status": "Active",
            "external_id": str(raw.get("id", "")),
        }

    def map_appointment(self, raw: dict) -> dict:
        """Normalize AestheticsPro appointment fields to Zentox schema."""
        return {
            "provider": raw.get("providerName", ""),
            "service": raw.get("serviceName", "") or raw.get("appointmentType", ""),
            "appointment_date": raw.get("startTime") or raw.get("date"),
            "status": raw.get("status", "Scheduled"),
            "duration_min": raw.get("duration"),
            "revenue": raw.get("amount") or raw.get("revenue"),
            "source": "AestheticsPro",
        }
