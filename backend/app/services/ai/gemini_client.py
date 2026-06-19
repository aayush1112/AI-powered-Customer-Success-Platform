from __future__ import annotations

import asyncio
import json
import time

import structlog

from app.core.config import settings

logger = structlog.get_logger()


class GeminiClient:
    """Async wrapper around the Google Generative AI SDK.

    Sends a text prompt and expects a JSON response.
    Retries up to settings.GEMINI_MAX_RETRIES times with exponential backoff.
    Returns None if all attempts fail so the caller can apply a fallback.
    """

    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            logger.warning(
                "gemini_api_key_missing",
                message="GEMINI_API_KEY is not set — AI calls will use the fallback path",
            )
            self._ready = False
            return

        try:
            import google.generativeai as genai  # type: ignore[import-untyped]

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=settings.GEMINI_TEMPERATURE,
                ),
            )
            self._ready = True
            logger.info("gemini_client_initialized", model=settings.GEMINI_MODEL)
        except Exception as exc:
            logger.error("gemini_client_init_failed", error=str(exc))
            self._ready = False

    async def generate_json(
        self,
        prompt: str,
        *,
        max_retries: int | None = None,
    ) -> dict | None:
        """Send *prompt* to Gemini and return the parsed JSON dict.

        Returns None on any unrecoverable failure so callers can fall back
        gracefully instead of propagating an error to the user.
        """
        if not self._ready:
            logger.warning("gemini_skipped", reason="client not ready")
            return None

        retries = max_retries if max_retries is not None else settings.GEMINI_MAX_RETRIES
        last_error: Exception | None = None

        for attempt in range(retries):
            try:
                t0 = time.monotonic()
                logger.info("gemini_request_start", attempt=attempt + 1, model=settings.GEMINI_MODEL)

                response = await self._model.generate_content_async(prompt)  # type: ignore[attr-defined]
                elapsed_ms = round((time.monotonic() - t0) * 1000)

                raw_text: str = response.text
                if not raw_text:
                    raise ValueError("Gemini returned an empty response")

                parsed: dict = json.loads(raw_text)
                logger.info(
                    "gemini_request_success",
                    attempt=attempt + 1,
                    elapsed_ms=elapsed_ms,
                )
                return parsed

            except json.JSONDecodeError as exc:
                last_error = exc
                logger.warning(
                    "gemini_json_parse_error",
                    attempt=attempt + 1,
                    error=str(exc),
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "gemini_attempt_failed",
                    attempt=attempt + 1,
                    error_type=type(exc).__name__,
                    error=str(exc),
                )

            if attempt < retries - 1:
                backoff = 2**attempt  # 1 s, 2 s for 3-retry default
                logger.info("gemini_retry_backoff", seconds=backoff)
                await asyncio.sleep(backoff)

        logger.error(
            "gemini_all_retries_failed",
            retries=retries,
            last_error=str(last_error),
        )
        return None
