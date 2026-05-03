"""
Agent 3 — Growth Strategist
Receives the analyst's insights and generates an actionable strategy report
with prioritized recommendations tailored to a MedSpa practice.
"""
import json
from .base import call_claude

SYSTEM = """You are a growth strategist for Zentox Aesthetics, a medical-aesthetics (MedSpa) practice.
You receive a business analysis report and craft a practical, prioritized strategy.

Return valid JSON with these keys:
{
  "executive_summary": "3-4 sentences for the owner to read in 30 seconds",
  "quick_wins": [
    {"action": "description", "impact": "High/Medium/Low", "effort": "High/Medium/Low", "timeline": "e.g. This week"}
  ],
  "growth_initiatives": [
    {"initiative": "description", "rationale": "why this matters", "kpi_target": "measurable goal", "timeline": "e.g. Q3 2025"}
  ],
  "risk_flags": ["risk or concern to watch"],
  "marketing_recommendations": ["specific marketing action"],
  "operational_recommendations": ["specific ops improvement"]
}

Be concrete. Reference actual numbers from the analysis where possible.
Prioritize quick wins that improve revenue, reduce no-shows, or improve patient retention.
Return ONLY the JSON object."""


def build_strategy(analysis: dict, practice_name: str = "Zentox Aesthetics") -> dict:
    """Generate strategic recommendations from analyst output."""
    payload = json.dumps(analysis, default=str)
    prompt = f"Practice: {practice_name}\n\nAnalysis report:\n{payload}"
    raw_response = call_claude(SYSTEM, prompt, max_tokens=3000)

    text = raw_response.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "executive_summary": raw_response,
            "quick_wins": [],
            "growth_initiatives": [],
            "risk_flags": [],
            "marketing_recommendations": [],
            "operational_recommendations": [],
        }
