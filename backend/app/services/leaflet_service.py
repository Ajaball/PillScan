"""
Leaflet Summarizer Service
==========================

Takes a photo of a medication leaflet / prescription (the paper folded inside
the medicine box) and returns a plain-language **Arabic** summary produced by a
vision-capable LLM.

The provider is switchable via `LLM_PROVIDER` (``gemini`` or ``openai``) so the
team can use whichever key is available. Network calls go through ``httpx`` —
no extra SDK dependency is required.

If no API key is configured the service returns a clearly-labelled placeholder
(``is_configured = False``) instead of failing, so the full scan → summary flow
can still be demonstrated offline without fabricating medical content.
"""

import base64
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.config import get_settings
from app.utils.crypto import decrypt_secret

settings = get_settings()


class LeafletServiceError(Exception):
    """Raised when the vision LLM call fails or returns an unusable response."""


# ── Prompt ────────────────────────────────────────────────────────────────

# Sent to the model together with the image. Kept in Arabic so the model
# answers in Arabic, and scoped so it stays a *summary of what the leaflet
# says* — never medical advice of its own.
SUMMARY_PROMPT_AR = (
    "أنت مساعد صيدلي. سأعطيك صورة نشرة دواء (الورقة الموجودة داخل علبة الدواء) "
    "أو وصفة طبية. اقرأ ما هو مكتوب في الصورة ولخّصه للمريض بلغة عربية بسيطة "
    "وواضحة.\n\n"
    "نظّم الملخّص تحت هذه العناوين (تجاهل أي عنوان لا تتوفر معلوماته في الصورة):\n"
    "• اسم الدواء والمادة الفعّالة\n"
    "• دواعي الاستعمال (لماذا يُستخدم)\n"
    "• الجرعة وطريقة الاستخدام\n"
    "• أهم التحذيرات وموانع الاستعمال\n"
    "• الآثار الجانبية الشائعة\n"
    "• طريقة التخزين\n\n"
    "قواعد مهمة:\n"
    "- اكتب بالعربية فقط.\n"
    "- لخّص فقط ما هو مكتوب فعلياً في الصورة، ولا تخترع معلومات.\n"
    "- إذا كانت الصورة غير واضحة أو لا تحتوي على نشرة/وصفة دواء، فاذكر ذلك بوضوح.\n"
    "- استخدم نقاطاً قصيرة تحت كل عنوان."
)

# Shown to the user under every summary (added by the API, not the model).
DISCLAIMER_AR = (
    "هذا الملخّص للمعلومة فقط وقد يحتوي على أخطاء، ولا يغني عن استشارة الطبيب "
    "أو الصيدلي. ارجع دائماً إلى النشرة الأصلية."
)
DISCLAIMER_EN = (
    "This summary is for information only, may contain mistakes, and is not a "
    "substitute for a doctor or pharmacist. Always refer to the original leaflet."
)

# Returned (as the "summary") when no provider key is configured.
NOT_CONFIGURED_MESSAGE_AR = (
    "🔑 خدمة التلخيص بالذكاء الاصطناعي غير مُفعّلة بعد.\n\n"
    "لتشغيلها، افتح: حسابي ← الإعدادات ← إعدادات الذكاء الاصطناعي، "
    "ثم أضف مفتاح API الخاص بك:\n"
    "• لِـ Gemini (جوجل)\n"
    "• أو لِـ OpenAI (شات جي بي تي)\n\n"
    "بعد إضافة المفتاح، أعد تصوير النشرة وسيظهر الملخّص الحقيقي هنا."
)


def _guess_ext_mime(content_type: Optional[str]) -> str:
    """Normalise the image MIME type for the provider payloads."""
    if content_type and content_type.startswith("image/"):
        return content_type
    return "image/jpeg"


@dataclass
class LLMConfig:
    """Effective LLM configuration for one summarization request."""
    provider: str            # 'gemini' | 'openai'
    model: str
    api_key: Optional[str]   # None when nothing is configured


def _resolve_config(user: Optional[Any] = None) -> LLMConfig:
    """
    Determine which provider + API key to use, preferring the settings the
    **user** entered in the app over the server-wide ``.env`` defaults.

    Resolution order for the provider:
        user.llm_provider → settings.LLM_PROVIDER → "gemini"

    For each provider's key: the user's stored (encrypted) key wins; otherwise
    fall back to the server key from ``.env``.
    """
    gemini_key = settings.GEMINI_API_KEY
    openai_key = settings.OPENAI_API_KEY
    provider = None

    if user is not None:
        provider = getattr(user, "llm_provider", None)
        user_gemini = decrypt_secret(getattr(user, "gemini_api_key", None))
        user_openai = decrypt_secret(getattr(user, "openai_api_key", None))
        if user_gemini:
            gemini_key = user_gemini
        if user_openai:
            openai_key = user_openai

    provider = (provider or settings.LLM_PROVIDER or "gemini").lower()

    if provider == "openai":
        return LLMConfig(provider="openai", model=settings.OPENAI_MODEL, api_key=openai_key)
    return LLMConfig(provider="gemini", model=settings.GEMINI_MODEL, api_key=gemini_key)


async def _summarize_with_gemini(image_b64: str, mime_type: str, api_key: str, model: str) -> str:
    """Call Google Gemini's generateContent endpoint and return the text."""
    url = (
        f"{settings.GEMINI_API_BASE}/models/{model}:generateContent"
        f"?key={api_key}"
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": SUMMARY_PROMPT_AR},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}},
                ]
            }
        ],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
    }

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(url, json=payload)

    if response.status_code != 200:
        raise LeafletServiceError(
            f"Gemini API error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    try:
        candidates = data["candidates"]
        parts = candidates[0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError):
        raise LeafletServiceError(f"Unexpected Gemini response shape: {str(data)[:300]}")

    if not text:
        raise LeafletServiceError("Gemini returned an empty summary.")
    return text


async def _summarize_with_openai(image_b64: str, mime_type: str, api_key: str, model: str) -> str:
    """Call OpenAI's chat completions endpoint (vision) and return the text."""
    url = f"{settings.OPENAI_API_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SUMMARY_PROMPT_AR},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_b64}"},
                    },
                ],
            }
        ],
    }

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise LeafletServiceError(
            f"OpenAI API error {response.status_code}: {response.text[:300]}"
        )

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError):
        raise LeafletServiceError(f"Unexpected OpenAI response shape: {str(data)[:300]}")

    if not text:
        raise LeafletServiceError("OpenAI returned an empty summary.")
    return text


def is_configured(user: Optional[Any] = None) -> bool:
    """True when the effective provider (per-user or server default) has a key."""
    return bool(_resolve_config(user).api_key)


async def summarize_leaflet(
    image_bytes: bytes,
    content_type: Optional[str],
    user: Optional[Any] = None,
) -> dict:
    """
    Summarize a medication leaflet image in Arabic.

    The provider and API key are resolved from the ``user``'s own settings when
    available, falling back to the server-wide ``.env`` configuration.

    Returns a dict:
        {
            "summary": str,          # Arabic summary (or a setup message)
            "provider": str,         # "gemini" | "openai"
            "model": str,            # model id used
            "is_configured": bool,   # False when no API key is set
            "disclaimer_ar": str,
            "disclaimer_en": str,
        }

    Raises LeafletServiceError if a configured provider call fails.
    """
    config = _resolve_config(user)

    base_result = {
        "provider": config.provider,
        "model": config.model,
        "disclaimer_ar": DISCLAIMER_AR,
        "disclaimer_en": DISCLAIMER_EN,
    }

    if not config.api_key:
        return {
            **base_result,
            "summary": NOT_CONFIGURED_MESSAGE_AR,
            "is_configured": False,
        }

    mime_type = _guess_ext_mime(content_type)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    if config.provider == "openai":
        summary = await _summarize_with_openai(image_b64, mime_type, config.api_key, config.model)
    else:
        summary = await _summarize_with_gemini(image_b64, mime_type, config.api_key, config.model)

    return {**base_result, "summary": summary, "is_configured": True}
