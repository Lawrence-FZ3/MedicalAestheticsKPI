"""
Agent 1 — Data Scientist
Receives raw imported data (as a JSON string or CSV-like text) and returns a
cleaned, normalized dataset with a brief audit trail of changes made.
"""
import json
from .base import call_claude

SYSTEM = """You are a medical-aesthetics data scientist working inside a HIPAA-compliant CRM.
Your job is to clean and normalize raw imported data.

Rules:
- Standardize date formats to YYYY-MM-DD
- Capitalize names properly (title case)
- Strip leading/trailing whitespace from all text fields
- Normalize phone numbers to (XXX) XXX-XXXX format where possible
- Normalize US state abbreviations to 2-letter uppercase
- Flag (do NOT remove) records with missing required fields: name, date, or amount
- Remove exact duplicate rows
- Return ONLY valid JSON with two keys:
  1. "cleaned_data": array of cleaned records
  2. "audit": array of strings describing each change made (be concise)

Do not include any explanation outside the JSON object."""


def clean_data(raw_data: list[dict]) -> dict:
    """Clean and normalize a list of raw records. Returns cleaned_data + audit."""
    payload = json.dumps(raw_data, default=str)
    prompt = f"Clean and normalize this dataset:\n\n{payload}"
    raw_response = call_claude(SYSTEM, prompt, max_tokens=4096)

    # Extract JSON even if the model wraps it in a code block
    text = raw_response.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"cleaned_data": raw_data, "audit": ["Warning: could not parse cleaner output; returning raw data."]}
