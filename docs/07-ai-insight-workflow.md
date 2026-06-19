# AI Insight Workflow

## Overview

The AI Insight module generates structured, actionable summaries of customer interactions using **Google Gemini** (`gemini-2.5-flash`). Insights are generated on-demand, cached per interaction, and can be regenerated at any time.

---

## Data Flow

```
POST /api/v1/insights/generate/{interaction_id}
        │
        ▼
InsightService.generate(interaction_id, customer_id, force_regenerate)
        │
        ├─► AiInsightRepository.get_by_interaction_id(interaction_id)
        │   ├─► EXISTS + force=False → return cached insight (no Gemini call)
        │   └─► NOT EXISTS or force=True → continue
        │
        ├─► InteractionRepository.get_by_id(interaction_id)
        │   └─► NotFoundException if not found
        │
        ├─► CustomerRepository.get_by_id(customer_id)
        │
        ├─► build_prompt(interaction, customer)   ← prompts.py
        │   └─► Structured text prompt with context
        │
        ├─► GeminiClient.generate(prompt)
        │   ├─► Attempt 1 ... GEMINI_MAX_RETRIES
        │   ├─► Exponential backoff on transient errors
        │   └─► Returns raw JSON string
        │
        ├─► parse_gemini_response(raw_json)
        │   ├─► Extract: summary, sentiment, action_items[], risks[]
        │   └─► Fallback insight if parse fails
        │
        ├─► AiInsightRepository.upsert(interaction_id, parsed)
        │   └─► INSERT ... ON CONFLICT (interaction_id) DO UPDATE
        │
        └─► Return AiInsightResponse
```

---

## Prompt Engineering

Location: `app/services/ai/prompts.py`

The prompt provides Gemini with:
1. **Customer context** — company name, industry, current status
2. **Interaction metadata** — type (CALL/EMAIL/MEETING/NOTE), subject, occurred_at
3. **Interaction notes** — verbatim content from the CSM
4. **Output format specification** — strict JSON schema instruction

Example prompt structure:
```
You are a customer success AI assistant. Analyze the following customer interaction
and provide structured insights.

Customer: {company_name} ({industry}) — Status: {status}
Interaction: {type} on {date} — "{subject}"
Notes: {notes}

Respond with a JSON object matching this schema:
{
  "summary": "2-3 sentence plain-English summary of the interaction",
  "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
  "action_items": ["action 1", "action 2", ...],
  "risks": ["risk 1", ...]
}

Respond with JSON only. No markdown, no explanation.
```

---

## GeminiClient (`app/services/ai/gemini_client.py`)

```python
class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate(self, prompt: str) -> str:
        for attempt in range(settings.GEMINI_MAX_RETRIES):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt,
                    generation_config={"temperature": settings.GEMINI_TEMPERATURE}
                )
                return response.text
            except Exception as exc:
                if attempt == settings.GEMINI_MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # exponential backoff
```

**Key design decisions:**
- `asyncio.to_thread` wraps the synchronous Gemini SDK call to avoid blocking the event loop
- `temperature=0.1` ensures deterministic, factual output rather than creative variance
- Retries with exponential backoff handle transient API errors

---

## Fallback Behaviour

When Gemini is unreachable, returns an empty/invalid API key, or the response cannot be parsed:

```python
FALLBACK_INSIGHT = AiInsight(
    summary="Insight generation is currently unavailable. Please try again later.",
    sentiment=SentimentType.NEUTRAL,
    action_items=[],
    risks=[],
    is_fallback=True,
)
```

The `is_fallback` flag in the API response allows the frontend to display a distinct UI state (e.g., a warning banner) instead of treating a fallback as a real insight.

---

## Regeneration

Any ADMIN or MANAGER can regenerate an insight:

```
POST /api/v1/insights/generate/{interaction_id}?force=true
```

The `force=true` parameter bypasses the cached record and calls Gemini regardless. The previous insight is overwritten in the database.

---

## GET Endpoint

```
GET /api/v1/insights/{interaction_id}
```

Returns the stored insight for the interaction without calling Gemini. Returns 404 if no insight has been generated yet.

---

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `GEMINI_API_KEY` | `""` | Required in production; empty triggers fallback |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `GEMINI_MAX_RETRIES` | `3` | Number of retry attempts on failure |
| `GEMINI_TEMPERATURE` | `0.1` | Lower = more deterministic output |

---

## Cost Considerations

`gemini-2.5-flash` is Gemini's most cost-efficient model. Insight generation is billed per token. Approximate token count per request:
- Prompt: ~300–600 tokens (varies with notes length)
- Response: ~150–300 tokens

To control costs in production:
- Implement per-user or per-team rate limits
- Cache generated insights (already done via DB persistence)
- Monitor token usage via Google AI Studio or Cloud Billing
