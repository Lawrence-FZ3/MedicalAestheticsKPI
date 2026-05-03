"""
Agent 2 — Business Analyst
Receives the cleaned dataset and produces structured insights: trends,
anomalies, top performers, and KPI commentary.
"""
import json
from .base import call_claude

SYSTEM = """You are a senior business analyst specializing in medical-aesthetics (MedSpa) practices.
You receive a cleaned dataset and produce a concise, actionable analysis report.

Structure your response as valid JSON with these keys:
{
  "summary": "2-3 sentence high-level summary",
  "key_metrics": {"metric_name": value_or_string, ...},
  "trends": ["trend description", ...],
  "anomalies": ["anomaly description", ...],
  "top_performers": {"category": ["item1", "item2"], ...},
  "opportunities": ["opportunity description", ...]
}

Focus on:
- Revenue trends and patient visit frequency
- No-show rates and appointment utilization
- Top services and providers by revenue
- Month-over-month or period-over-period changes
- Any suspicious outliers or data gaps

Return ONLY the JSON object. No markdown, no preamble."""


def analyze_data(cleaned_data: list[dict], context: str = "") -> dict:
    """Analyze cleaned records. Returns structured insight dict."""
    payload = json.dumps(cleaned_data, default=str)
    user_msg = f"Context: {context}\n\nDataset:\n{payload}" if context else f"Dataset:\n{payload}"
    raw_response = call_claude(SYSTEM, user_msg, max_tokens=3000)

    text = raw_response.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"summary": raw_response, "key_metrics": {}, "trends": [], "anomalies": [], "top_performers": {}, "opportunities": []}
