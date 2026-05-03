"""Base agent class — thin wrapper around Claude Haiku."""
import anthropic
from backend.config import get_settings

_settings = get_settings()

# Shared Anthropic client (re-used across all agents)
_client = anthropic.Anthropic(api_key=_settings.anthropic_api_key)

MODEL = "claude-haiku-4-5"  # cheapest model, $1/$5 per 1M tokens


def call_claude(system: str, user: str, max_tokens: int = 2048) -> str:
    """Single-turn Claude call. Returns the text response."""
    response = _client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text
