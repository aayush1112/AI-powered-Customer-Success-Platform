from __future__ import annotations

_TEMPLATE = """\
You are a customer success AI assistant. Your task is to analyze meeting notes and return a structured JSON analysis.

STRICT OUTPUT RULES:
1. Return ONLY a valid JSON object. No markdown, no code fences, no explanation, no extra text.
2. The JSON must have exactly these four keys: "summary", "sentiment", "action_items", "risks".
3. "summary": A concise 1–3 sentence summary of the meeting. Must not be empty.
4. "sentiment": MUST be exactly one of: "POSITIVE", "NEUTRAL", "NEGATIVE". No other values accepted.
   - POSITIVE: customer is satisfied, optimistic, or relationship is healthy
   - NEGATIVE: customer is frustrated, at risk, or serious concerns were raised
   - NEUTRAL: factual/status update with no strong positive or negative signal
5. "action_items": JSON array of strings. Each string is a concrete next step. Use [] if none.
6. "risks": JSON array of strings. Each string is a specific risk or concern. Use [] if none.

EXAMPLE OUTPUT (follow this exact shape):
{{
  "summary": "The customer completed onboarding successfully and is satisfied with platform performance. A follow-up is scheduled for next week.",
  "sentiment": "POSITIVE",
  "action_items": ["Send API documentation link", "Schedule follow-up for next Tuesday"],
  "risks": ["Customer raised concern about API rate limits"]
}}

MEETING NOTES TO ANALYZE:
{notes}
"""


def build_insight_prompt(notes: str) -> str:
    """Return a fully rendered prompt ready to send to Gemini."""
    safe_notes = notes.strip() if notes else "(No meeting notes were recorded.)"
    return _TEMPLATE.format(notes=safe_notes)
