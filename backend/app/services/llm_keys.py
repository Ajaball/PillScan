"""
Gemini API Key Resolution & Failover
====================================

The app uses **Gemini only**. A user can enter up to five of their own Gemini
API keys on the AI-settings page; the app tries them **in order** and moves on
to the next key automatically when one is empty, exhausted (quota/rate-limit),
or otherwise fails. Server-wide keys from the environment are appended as a
shared fallback.

This module centralises: which key slots exist, how to resolve the ordered key
list for a request, and a generic "try each key until one works" helper.
"""

import re
from typing import Any, Awaitable, Callable, List, Optional, TypeVar

import httpx

from app.config import get_settings
from app.utils.crypto import decrypt_secret

settings = get_settings()

# Number of Gemini key slots a user can fill on the AI-settings page.
USER_KEY_SLOTS = 5

T = TypeVar("T")


def user_key_attr(slot: int) -> str:
    """Model/column attribute name for a user key slot (1-based)."""
    return "gemini_api_key" if slot == 1 else f"gemini_api_key_{slot}"


def _env_key(slot: int) -> Optional[str]:
    attr = "GEMINI_API_KEY" if slot == 1 else f"GEMINI_API_KEY_{slot}"
    return getattr(settings, attr, None)


def user_gemini_keys(user: Optional[Any]) -> List[str]:
    """Decrypted, non-empty Gemini keys the user stored, in slot order."""
    if user is None:
        return []
    keys: List[str] = []
    for slot in range(1, USER_KEY_SLOTS + 1):
        val = decrypt_secret(getattr(user, user_key_attr(slot), None))
        if val and val.strip():
            keys.append(val.strip())
    return keys


def env_gemini_keys() -> List[str]:
    """Non-empty Gemini keys configured server-wide (environment), in order."""
    keys: List[str] = []
    for slot in range(1, USER_KEY_SLOTS + 1):
        val = _env_key(slot)
        if val and val.strip():
            keys.append(val.strip())
    return keys


def _dedupe(keys: List[str]) -> List[str]:
    """De-duplicate while preserving order."""
    seen = set()
    result: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


def resolve_gemini_keys(user: Optional[Any] = None) -> List[str]:
    """
    Ordered, de-duplicated Gemini API keys to try for a request:
    the user's own keys first (settings page), then any server env keys.

    NOTE: this synchronous variant does NOT include admin-shared keys (it has no
    DB access). Request paths that can share the admin's keys with every user
    use :func:`resolve_gemini_keys_async` instead.
    """
    return _dedupe(user_gemini_keys(user) + env_gemini_keys())


async def admin_shared_keys(db: Any) -> List[str]:
    """
    Gemini keys stored by ADMIN accounts, shared with **all** users.

    This is what lets the admin add a key once (in the app's AI settings) and
    have it power pill identification, the leaflet summary, and the drug
    assistant for every user — without putting the key in server env vars.
    Returns an empty list if ``db`` is None or no admin has a key configured.
    """
    if db is None:
        return []
    # Imported here to avoid any import-time cycle with the models package.
    from sqlalchemy import select, or_
    from app.models.user import User

    result = await db.execute(
        select(User).where(or_(User.role == "ADMIN", User.is_admin == True))  # noqa: E712
    )
    keys: List[str] = []
    for admin in result.scalars().all():
        keys.extend(user_gemini_keys(admin))
    return keys


async def resolve_gemini_keys_async(user: Optional[Any], db: Any) -> List[str]:
    """
    Ordered, de-duplicated Gemini keys for a request, including admin-shared keys:
      1. the requesting user's own keys (AI settings),
      2. keys shared by any admin account,
      3. server env keys.
    """
    ordered = (
        user_gemini_keys(user)
        + await admin_shared_keys(db)
        + env_gemini_keys()
    )
    return _dedupe(ordered)


async def call_with_failover(
    keys: List[str],
    call: Callable[[str], Awaitable[T]],
) -> T:
    """
    Invoke ``call(key)`` for each key in turn, returning the first success.

    If a key raises (bad/blocked key, quota/rate-limit exhausted, transient
    upstream error, empty response…), the next key is tried automatically. If
    every key fails, the last exception is re-raised so the caller can degrade.
    """
    if not keys:
        raise RuntimeError("No Gemini API keys configured.")

    last_error: Optional[BaseException] = None
    for index, key in enumerate(keys, start=1):
        try:
            return await call(key)
        except Exception as e:  # noqa: BLE001 - deliberately try the next key
            last_error = e
            print(f"[LLM] Gemini key #{index} failed, trying next: {e}")

    assert last_error is not None
    raise last_error


def is_thinking_capable(model: str) -> bool:
    """Gemini 2.5+ models enable "thinking" by default; 2.0 and earlier don't support it."""
    match = re.match(r"gemini-(\d+)\.(\d+)", model or "")
    if not match:
        return False
    major, minor = int(match.group(1)), int(match.group(2))
    return (major, minor) >= (2, 5)


# ── Centralised Gemini call (model fallback + error classification) ────────

class GeminiError(Exception):
    """
    A classified Gemini failure. ``kind`` is one of:
    'invalid_key', 'permission', 'quota', 'model', 'blocked', 'empty',
    'timeout', 'network', 'http'. ``message_ar`` is a user-facing Arabic message.
    """

    _AR = {
        "invalid_key": "مفتاح Gemini غير صالح. تحقّق من المفتاح في إعدادات الذكاء الاصطناعي.",
        "permission": "خدمة Generative Language غير مُفعّلة لهذا المفتاح في Google.",
        "quota": "انتهى رصيد/حد استخدام المفاتيح. حاول لاحقًا أو أضف مفتاحًا آخر.",
        "model": "النموذج غير متاح لهذا المفتاح.",
        "blocked": "تعذّر تنفيذ الطلب (حجب من مرشّح الأمان).",
        "empty": "لم يرجع النموذج نتيجة. حاول مرة أخرى.",
        "timeout": "استغرقت الخدمة وقتًا أطول من المعتاد. حاول مرة أخرى.",
        "network": "تعذّر الاتصال بخدمة الذكاء الاصطناعي. تحقّق من الشبكة.",
        "http": "خطأ من خدمة الذكاء الاصطناعي. حاول مرة أخرى.",
    }

    def __init__(self, message: str, *, kind: str = "http"):
        super().__init__(message)
        self.kind = kind
        self.message_ar = self._AR.get(kind, self._AR["http"])


def gemini_models() -> List[str]:
    """Primary model followed by fallbacks (de-duplicated, non-empty)."""
    models = [settings.GEMINI_MODEL] + list(getattr(settings, "GEMINI_MODEL_FALLBACKS", []) or [])
    return _dedupe([m for m in models if m and m.strip()])


def _generation_config(model: str, temperature: float, max_output_tokens: int) -> dict:
    config = {"temperature": temperature, "maxOutputTokens": max_output_tokens}
    if is_thinking_capable(model):
        # Disable "thinking" so the token budget produces the actual answer.
        config["thinkingConfig"] = {"thinkingBudget": 0}
    return config


async def gemini_generate(
    parts: list,
    api_key: str,
    *,
    temperature: float = 0.2,
    max_output_tokens: int = 8192,
) -> str:
    """
    Call Gemini ``generateContent`` with the given content parts and return the
    text. Tries each model from :func:`gemini_models` on a 404 (model not found)
    so a bad/unavailable primary model does not break identification. All other
    failures raise a classified :class:`GeminiError` (invalid key, quota,
    timeout, network, …) so callers can show an accurate message.
    """
    timeout = settings.LLM_TIMEOUT_SECONDS
    last_model_error: Optional[GeminiError] = None

    for model in gemini_models():
        url = (
            f"{settings.GEMINI_API_BASE}/models/{model}:generateContent"
            f"?key={api_key}"
        )
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": _generation_config(model, temperature, max_output_tokens),
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
        except httpx.TimeoutException as e:
            raise GeminiError(f"Timeout after {timeout}s: {e}", kind="timeout")
        except httpx.HTTPError as e:
            raise GeminiError(f"Network error: {e}", kind="network")

        status = resp.status_code
        body = resp.text or ""

        if status == 404:
            # Model not found — remember and try the next fallback model.
            last_model_error = GeminiError(f"Model '{model}' not found", kind="model")
            continue
        if status == 400 and ("API_KEY_INVALID" in body or "API key not valid" in body):
            raise GeminiError("API key not valid", kind="invalid_key")
        if status == 403 or "SERVICE_DISABLED" in body or "PERMISSION_DENIED" in body:
            raise GeminiError(f"Permission denied: {body[:200]}", kind="permission")
        if status == 429 or "RESOURCE_EXHAUSTED" in body:
            raise GeminiError("Quota/rate limit exhausted", kind="quota")
        if status != 200:
            raise GeminiError(f"HTTP {status}: {body[:200]}", kind="http")

        try:
            data = resp.json()
        except (ValueError, TypeError) as e:
            raise GeminiError(f"Invalid JSON from Gemini: {e}", kind="http")

        block = (data.get("promptFeedback") or {}).get("blockReason")
        if block:
            raise GeminiError(f"Blocked: {block}", kind="blocked")

        candidates = data.get("candidates") or []
        if not candidates:
            raise GeminiError(f"No candidates: {str(data)[:200]}", kind="empty")

        parts_out = (candidates[0].get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts_out).strip()
        if not text:
            finish = candidates[0].get("finishReason", "UNKNOWN")
            raise GeminiError(f"Empty text (finishReason: {finish})", kind="empty")
        return text

    # Every model returned 404.
    raise last_model_error or GeminiError("No Gemini model available", kind="model")
