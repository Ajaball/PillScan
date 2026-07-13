"""
Pill Identification Service (Vision LLM fallback)
=================================================

Identifies a medication from a photo using the Gemini vision model
and returns structured candidates. Used by the scan
router as a fallback when the local CV model (YOLOv8 + EfficientNet) is
unavailable, disabled, or produces no usable/mappable prediction.

The model is asked to reply in strict JSON so results can be mapped to the
drug database. Returns ``None`` when no provider key is configured (so the
caller can degrade to an honest "not identified" instead of a fake match).
"""

import base64
import json
import re
from typing import Optional

import httpx

from app.config import get_settings
from app.services import llm_keys

settings = get_settings()


class PillIdError(Exception):
    """Raised when the vision LLM call fails or returns an unusable response."""


IDENTIFY_PROMPT = (
    "You are a pharmacist assistant. Look at the photo of a medication "
    "(pill, tablet, capsule, blister strip, or box) and identify the medicine.\n\n"
    "Respond with ONLY a JSON object — no markdown, no explanation — using "
    "exactly this shape:\n"
    "{\n"
    '  "identified": true or false,\n'
    '  "candidates": [\n'
    '    {"name_en": "brand name", "name_ar": "الاسم بالعربية", '
    '"generic_en": "active ingredient", "strength": "e.g. 500mg", '
    '"dosage_form": "e.g. tablet", "confidence": 0.0}\n'
    "  ]\n"
    "}\n\n"
    "Rules:\n"
    "- Provide up to 3 candidates, most likely first.\n"
    "- confidence is your certainty from 0 to 1.\n"
    "- If you cannot identify any medicine, return "
    '{"identified": false, "candidates": []}.\n'
    "- Fill name_ar in Arabic (transliterate if there is no common Arabic name).\n"
    "- Use empty strings for fields you cannot determine.\n"
    "- Output valid JSON only."
)


def is_configured(user=None) -> bool:
    """True when at least one Gemini API key (user or server) is available."""
    return bool(llm_keys.resolve_gemini_keys(user))


def _gemini_generation_config(temperature: float) -> dict:
    """
    Build the Gemini generationConfig.

    Gemini 2.5 models enable "thinking" by default, which spends the output
    token budget on internal reasoning and can return empty text. We give a
    high token budget and disable thinking on 2.5 models so the tokens go to
    the actual answer. (thinkingConfig is only valid on thinking-capable
    models, so it is omitted for 2.0 and earlier.)
    """
    config = {"temperature": temperature, "maxOutputTokens": 8192}
    if "2.5" in (settings.GEMINI_MODEL or ""):
        config["thinkingConfig"] = {"thinkingBudget": 0}
    return config


async def _call_gemini(image_b64: str, mime_type: str, api_key: str) -> str:
    url = (
        f"{settings.GEMINI_API_BASE}/models/{settings.GEMINI_MODEL}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": IDENTIFY_PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                ]
            }
        ],
        "generationConfig": _gemini_generation_config(temperature=0.1),
    }
    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)
    if response.status_code != 200:
        raise PillIdError(f"Gemini API error {response.status_code}: {response.text[:200]}")
    data = response.json()

    # Input blocked by safety filters (no candidates returned at all).
    block = (data.get("promptFeedback") or {}).get("blockReason")
    if block:
        raise PillIdError(f"Gemini blocked the request (promptFeedback: {block})")

    candidates = data.get("candidates") or []
    if not candidates:
        raise PillIdError(f"Gemini returned no candidates: {str(data)[:200]}")

    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        # e.g. finishReason SAFETY / MAX_TOKENS / RECITATION with no usable text.
        finish = candidate.get("finishReason", "UNKNOWN")
        raise PillIdError(f"Gemini returned empty text (finishReason: {finish})")
    return text


def _extract_json(text: str) -> dict:
    """Parse the model's reply into a dict, tolerating code fences / extra prose."""
    cleaned = text.strip()
    # Strip ```json ... ``` fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Fall back to the first {...} block in the text
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise PillIdError(f"Could not parse JSON from model reply: {text[:200]}")


def _normalize_candidates(parsed: dict) -> list[dict]:
    """Clean and clamp the candidate list from the parsed model reply."""
    raw = parsed.get("candidates") or []
    candidates = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name_en = str(item.get("name_en", "") or "").strip()
        name_ar = str(item.get("name_ar", "") or "").strip()
        if not name_en and not name_ar:
            continue
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        candidates.append({
            "name_en": name_en,
            "name_ar": name_ar,
            "generic_en": str(item.get("generic_en", "") or "").strip(),
            "strength": str(item.get("strength", "") or "").strip(),
            "dosage_form": str(item.get("dosage_form", "") or "").strip(),
            "confidence": confidence,
        })
    return candidates


async def identify_pill(
    image_bytes: bytes,
    content_type: Optional[str],
    user=None,
) -> Optional[dict]:
    """
    Identify a medication from an image using Gemini.

    Tries the user's Gemini keys (settings page) first, then any server env
    keys, moving to the next key automatically when one fails or is exhausted.

    Returns:
        {"provider": "gemini", "model": str, "candidates": [ {name_en, name_ar,
         generic_en, strength, dosage_form, confidence}, ... ]}
        or None if no Gemini key is configured.

    Raises:
        PillIdError when every configured key fails or the reply is unparseable.
    """
    keys = llm_keys.resolve_gemini_keys(user)
    if not keys:
        return None

    model = settings.GEMINI_MODEL
    mime_type = content_type if (content_type or "").startswith("image/") else "image/jpeg"
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        text = await llm_keys.call_with_failover(
            keys, lambda key: _call_gemini(image_b64, mime_type, key)
        )
    except PillIdError:
        raise
    except Exception as e:  # noqa: BLE001 - normalise any failover error
        raise PillIdError(str(e))

    parsed = _extract_json(text)
    candidates = _normalize_candidates(parsed)

    return {"provider": "gemini", "model": model, "candidates": candidates}
