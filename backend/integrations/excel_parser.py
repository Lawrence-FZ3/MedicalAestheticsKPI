"""
Excel import — parses uploaded .xlsx/.xls reports from any source
and normalizes them into Zentox schema dicts.
"""
import io
from typing import Literal
import pandas as pd


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    df = df.dropna(how="all")
    return df


def parse_patient_excel(file_bytes: bytes) -> list[dict]:
    df = _clean_df(pd.read_excel(io.BytesIO(file_bytes)))
    patients = []
    for _, row in df.iterrows():
        patients.append({
            "full_name": str(row.get("full_name") or row.get("name") or row.get("patient_name") or "").strip(),
            "email": str(row.get("email", "") or "").strip() or None,
            "phone": str(row.get("phone") or row.get("mobile") or "").strip() or None,
            "date_of_birth": str(row.get("date_of_birth") or row.get("dob") or "").strip() or None,
            "gender": str(row.get("gender", "") or "").strip() or None,
            "lead_source": str(row.get("lead_source") or row.get("source") or "Other").strip(),
            "status": str(row.get("status", "Active")).strip(),
            "notes": str(row.get("notes", "") or "").strip() or None,
            "external_id": str(row.get("external_id") or row.get("patient_id") or "").strip() or None,
        })
    return [p for p in patients if p["full_name"]]


def parse_appointment_excel(file_bytes: bytes) -> list[dict]:
    df = _clean_df(pd.read_excel(io.BytesIO(file_bytes)))
    appointments = []
    for _, row in df.iterrows():
        appointments.append({
            "provider": str(row.get("provider") or row.get("provider_name") or "").strip(),
            "service": str(row.get("service") or row.get("treatment") or "").strip(),
            "appointment_date": str(row.get("appointment_date") or row.get("date") or "").strip(),
            "status": str(row.get("status", "Completed")).strip(),
            "duration_min": int(row["duration_min"]) if "duration_min" in row and pd.notna(row["duration_min"]) else None,
            "revenue": float(row["revenue"]) if "revenue" in row and pd.notna(row["revenue"]) else None,
            "source": "Manual",
        })
    return [a for a in appointments if a["provider"] or a["service"]]


def parse_financial_excel(file_bytes: bytes) -> list[dict]:
    """Generic QuickBooks / Excel P&L export parser."""
    df = _clean_df(pd.read_excel(io.BytesIO(file_bytes)))
    transactions = []
    for _, row in df.iterrows():
        transactions.append({
            "date": str(row.get("date") or row.get("transaction_date") or "").strip(),
            "description": str(row.get("description") or row.get("memo") or "").strip(),
            "amount": float(row["amount"]) if "amount" in row and pd.notna(row["amount"]) else 0.0,
            "category": str(row.get("category") or row.get("account") or "").strip(),
            "type": str(row.get("type") or row.get("transaction_type") or "Income").strip(),
        })
    return [t for t in transactions if t["amount"] != 0]
