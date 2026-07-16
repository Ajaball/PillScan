"""
Pharmacist Assistant Service
============================

Given a drug name, asks Gemini for general, reliable drug information and returns
it as a structured dict. Reuses the **same** Gemini keys and failover mechanism
as the rest of the app (``app.services.llm_keys``) — no new key, no new client.

The model is instructed to answer with JSON only; the response is parsed
defensively (code-fences stripped, JSON object extracted) with a clear fallback
when parsing fails or every key errors, so the endpoint degrades gracefully
instead of crashing.
"""

import json
import re
from typing import Any, Optional

from app.config import get_settings
from app.services import llm_keys

settings = get_settings()


class AssistantServiceError(Exception):
    """Raised when the assistant LLM call fails on every configured key."""


# System prompt — Arabic, JSON-only, restricted to EXACTLY three fields in a
# fixed order: name, sideEffects, usageTimes (+ recognized). No other fields.
SYSTEM_PROMPT_AR = (
    "أنت مساعد دوائي تُجيب بالعربية. قدّم معلومات دوائية عامة وموثوقة عن الدواء "
    "المطلوب بصيغة JSON فقط، وبهذه الحقول حصراً وبهذا الترتيب:\n"
    "1) name: اسم الدواء (نص).\n"
    "2) sideEffects: الأعراض الجانبية (مصفوفة نصية).\n"
    "3) usageTimes: مواعيد/أوقات الاستخدام المعتادة (مصفوفة نصية، مثل: صباحًا، "
    "مساءً، بعد الأكل).\n"
    "4) recognized: true أو false.\n"
    "قواعد صارمة: لا تُضِف أي حقول أخرى غير الأربعة أعلاه؛ لا تقدّم تشخيصاً ولا "
    "تصف علاجاً لحالة بعينها؛ إن لم تتعرّف على الدواء أو لم تكن متأكداً اجعل "
    "recognized=false ولا تختلق معلومات؛ لا تشجّع على إساءة الاستخدام أو الجرعات "
    "الزائدة. أعد JSON فقط دون أي نص إضافي ودون أي حقول أخرى."
)

# Shown as a persistent banner above the result (added by the API, not the model).
DISCLAIMER_AR = (
    "هذه المعلومات للتوعية فقط ولا تغني عن استشارة الطبيب أو الصيدلي المختص."
)

# Returned (recognized=False) when no Gemini key is configured.
NOT_CONFIGURED_MESSAGE_AR = (
    "🔑 خدمة المساعد الدوائي غير مُفعّلة بعد. افتح: حسابي ← الإعدادات ← إعدادات "
    "الذكاء الاصطناعي، ثم أضف مفتاح Gemini واحدًا على الأقل."
)


def is_configured(user: Optional[Any] = None) -> bool:
    """True when at least one Gemini key (user or server) is available."""
    return bool(llm_keys.resolve_gemini_keys(user))


async def _ask_gemini(drug_name: str, api_key: str, model: str) -> str:
    """
    Call Gemini (text only) and return the raw JSON text.

    Model fallback, error classification, timeouts and network errors are
    handled centrally in ``llm_keys.gemini_generate``.
    """
    parts = [
        {"text": SYSTEM_PROMPT_AR},
        {"text": f"اسم الدواء: {drug_name}"},
    ]
    return await llm_keys.gemini_generate(parts, api_key, temperature=0.2)


def _parse_json(text: str) -> Optional[dict]:
    """Safely parse the model's JSON reply. Returns None on failure."""
    if not text:
        return None
    cleaned = text.strip()
    # Strip ```json ... ``` fences if present.
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass
    # Last resort — grab the outermost {...} block.
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def _as_list(value: Any) -> list:
    """Coerce a field into a list of non-empty strings."""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if value is None or value == "":
        return []
    return [str(value).strip()]


def _normalize(parsed: dict, drug_name: str, model: str) -> dict:
    """
    Shape the parsed model output into the fixed three-field contract. Missing
    or wrongly-typed fields are coerced safely so the response is ALWAYS valid
    and in order: name, sideEffects, usageTimes.
    """
    recognized = bool(parsed.get("recognized", False))
    side_effects = _as_list(parsed.get("sideEffects"))
    usage_times = _as_list(parsed.get("usageTimes"))

    # An "incomplete" recognized reply (no side effects AND no usage times) is
    # treated as not-confidently-recognised rather than shown half-empty.
    if recognized and not side_effects and not usage_times:
        recognized = False

    return {
        "name": str(parsed.get("name") or drug_name).strip(),
        "sideEffects": side_effects,
        "usageTimes": usage_times,
        "recognized": recognized,
        "provider": "gemini",
        "model": model,
        "is_configured": True,
        "disclaimer_ar": DISCLAIMER_AR,
        "message": "" if recognized else "لم يتم التعرف على هذا الدواء بشكل مؤكد.",
    }


async def get_drug_info(drug_name: str, user: Optional[Any] = None, db: Any = None) -> dict:
    """
    Look up general drug information for ``drug_name`` via Gemini and return it in
    the fixed three-field shape (name, sideEffects, usageTimes).

    Uses the requesting user's own keys, then admin-shared keys (when ``db`` is
    provided), then server env keys. Never raises for the "not configured",
    "provider error", or "unparseable" cases — it returns recognized=False with a
    clear ``message`` instead, so the endpoint always degrades gracefully.
    """
    model = settings.GEMINI_MODEL
    base = {
        "name": drug_name,
        "sideEffects": [],
        "usageTimes": [],
        "recognized": False,
        "provider": "gemini",
        "model": model,
        "disclaimer_ar": DISCLAIMER_AR,
        "message": "",
    }

    keys = await llm_keys.resolve_gemini_keys_async(user, db)
    if not keys:
        return {**base, "is_configured": False, "message": NOT_CONFIGURED_MESSAGE_AR}

    # Call Gemini with automatic key failover. A classified GeminiError (invalid
    # key, quota, timeout, network...) becomes a clear Arabic message rather than
    # a generic 502, so the user knows exactly what to fix.
    try:
        raw = await llm_keys.call_with_failover(
            keys, lambda key: _ask_gemini(drug_name, key, model)
        )
    except llm_keys.GeminiError as e:
        return {**base, "is_configured": True, "message": e.message_ar}
    except Exception:  # noqa: BLE001 - never leak a 500 to the client
        return {**base, "is_configured": True, "message": "تعذّر جلب معلومات الدواء. حاول مرة أخرى."}

    parsed = _parse_json(raw)
    if parsed is None:
        # Provider succeeded but the reply wasn't valid JSON — clear fallback.
        return {**base, "is_configured": True, "message": "تعذّر تحليل رد المساعد. حاول مرة أخرى."}

    return _normalize(parsed, drug_name, model)
