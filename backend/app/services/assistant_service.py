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

import httpx

from app.config import get_settings
from app.services import llm_keys

settings = get_settings()


class AssistantServiceError(Exception):
    """Raised when the assistant LLM call fails on every configured key."""


# System prompt — Arabic, JSON-only, with strict safety rules. Kept verbatim as
# the product spec requires.
SYSTEM_PROMPT_AR = (
    "أنت مساعد دوائي متخصص تُجيب بالعربية. قدّم معلومات دوائية عامة وموثوقة عن "
    "الدواء المطلوب بصيغة JSON بالحقول: name، uses (دواعي الاستعمال)، dosage "
    "(الجرعة الاعتيادية)، sideEffects (مصفوفة)، contraindications (مصفوفة)، "
    "interactions (مصفوفة تفاعلات دوائية مهمة)، storage (طريقة التخزين)، warnings "
    "(مصفوفة تحذيرات)، recognized (true/false). قواعد صارمة: لا تقدّم تشخيصاً ولا "
    "تصف علاجاً لحالة بعينها؛ إن لم تتعرّف على الدواء أو لم تكن متأكداً اجعل "
    "recognized=false ووضّح ذلك بدل اختلاق معلومات؛ لا تشجّع على إساءة الاستخدام "
    "أو الجرعات الزائدة. أعد JSON فقط دون أي نص إضافي."
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


def _generation_config(model: str, temperature: float) -> dict:
    """
    Build the Gemini generationConfig — kept identical in shape to the working
    pill-ID / leaflet services (which this app already relies on). Notably it
    does NOT set ``responseMimeType``: that field is rejected by the model this
    app uses and made every key fail. JSON is requested via the prompt instead
    and parsed defensively below. Thinking-capable models get thinking disabled
    so the token budget produces the actual answer rather than internal reasoning.
    """
    config = {"temperature": temperature, "maxOutputTokens": 8192}
    if llm_keys.is_thinking_capable(model):
        config["thinkingConfig"] = {"thinkingBudget": 0}
    return config


async def _ask_gemini(drug_name: str, api_key: str, model: str) -> str:
    """Call Gemini generateContent (text only) and return the raw text."""
    url = (
        f"{settings.GEMINI_API_BASE}/models/{model}:generateContent"
        f"?key={api_key}"
    )
    config = _generation_config(model, temperature=0.2)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SYSTEM_PROMPT_AR},
                    {"text": f"اسم الدواء: {drug_name}"},
                ]
            }
        ],
        "generationConfig": config,
    }

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise AssistantServiceError(
            f"Gemini API error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    block = (data.get("promptFeedback") or {}).get("blockReason")
    if block:
        raise AssistantServiceError(f"Gemini blocked the request ({block})")

    candidates = data.get("candidates") or []
    if not candidates:
        raise AssistantServiceError(f"Gemini returned no candidates: {str(data)[:200]}")

    parts = (candidates[0].get("content") or {}).get("parts") or []
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        finish = candidates[0].get("finishReason", "UNKNOWN")
        raise AssistantServiceError(f"Gemini returned empty text (finishReason: {finish})")
    return text


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
    """Shape the parsed model output into the response contract."""
    return {
        "name": str(parsed.get("name") or drug_name).strip(),
        "uses": str(parsed.get("uses") or "").strip(),
        "dosage": str(parsed.get("dosage") or "").strip(),
        "sideEffects": _as_list(parsed.get("sideEffects")),
        "contraindications": _as_list(parsed.get("contraindications")),
        "interactions": _as_list(parsed.get("interactions")),
        "storage": str(parsed.get("storage") or "").strip(),
        "warnings": _as_list(parsed.get("warnings")),
        "recognized": bool(parsed.get("recognized", False)),
        "provider": "gemini",
        "model": model,
        "is_configured": True,
        "disclaimer_ar": DISCLAIMER_AR,
    }


async def get_drug_info(drug_name: str, user: Optional[Any] = None, db: Any = None) -> dict:
    """
    Look up general drug information for ``drug_name`` via Gemini.

    Uses the requesting user's own keys, then admin-shared keys (when ``db`` is
    provided), then server env keys. Returns a dict matching ``DrugInfoResponse``.
    Never raises for the "not configured" or "unparseable" cases — it returns
    recognized=False with a clear message instead. Raises
    ``AssistantServiceError`` only if every configured key errored.
    """
    model = settings.GEMINI_MODEL
    base = {
        "name": drug_name,
        "uses": "",
        "dosage": "",
        "sideEffects": [],
        "contraindications": [],
        "interactions": [],
        "storage": "",
        "warnings": [],
        "recognized": False,
        "provider": "gemini",
        "model": model,
        "disclaimer_ar": DISCLAIMER_AR,
    }

    keys = await llm_keys.resolve_gemini_keys_async(user, db)
    if not keys:
        return {**base, "is_configured": False, "warnings": [NOT_CONFIGURED_MESSAGE_AR]}

    raw = await llm_keys.call_with_failover(
        keys, lambda key: _ask_gemini(drug_name, key, model)
    )

    parsed = _parse_json(raw)
    if parsed is None:
        # Network/API succeeded but the reply wasn't valid JSON — clear fallback.
        return {
            **base,
            "is_configured": True,
            "recognized": False,
            "warnings": ["تعذّر تحليل رد المساعد. حاول مرة أخرى."],
        }

    return _normalize(parsed, drug_name, model)
