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
from typing import Optional

import httpx

from app.config import get_settings

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
    "لتشغيلها، أضف مفتاح API في ملف الإعدادات (‎.env‎):\n"
    "• لِـ Gemini: ‎GEMINI_API_KEY‎\n"
    "• أو لِـ OpenAI: ‎OPENAI_API_KEY‎ مع ضبط ‎LLM_PROVIDER=openai‎\n\n"
    "بعد إضافة المفتاح، أعد تصوير النشرة وسيظهر الملخّص الحقيقي هنا."
)


def _guess_ext_mime(content_type: Optional[str]) -> str:
    """Normalise the image MIME type for the provider payloads."""
    if content_type and content_type.startswith("image/"):
        return content_type
    return "image/jpeg"


async def _summarize_with_gemini(image_b64: str, mime_type: str) -> str:
    """Call Google Gemini's generateContent endpoint and return the text."""
    url = (
        f"{settings.GEMINI_API_BASE}/models/{settings.GEMINI_MODEL}:generateContent"
        f"?key={settings.GEMINI_API_KEY}"
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


async def _summarize_with_openai(image_b64: str, mime_type: str) -> str:
    """Call OpenAI's chat completions endpoint (vision) and return the text."""
    url = f"{settings.OPENAI_API_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
    payload = {
        "model": settings.OPENAI_MODEL,
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


def is_configured() -> bool:
    """True when the selected provider has an API key set."""
    provider = (settings.LLM_PROVIDER or "").lower()
    if provider == "openai":
        return bool(settings.OPENAI_API_KEY)
    return bool(settings.GEMINI_API_KEY)


async def summarize_leaflet(image_bytes: bytes, content_type: Optional[str]) -> dict:
    """
    Summarize a medication leaflet image in Arabic.

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
    provider = (settings.LLM_PROVIDER or "gemini").lower()
    model = settings.OPENAI_MODEL if provider == "openai" else settings.GEMINI_MODEL

    base_result = {
        "provider": provider,
        "model": model,
        "disclaimer_ar": DISCLAIMER_AR,
        "disclaimer_en": DISCLAIMER_EN,
    }

    if not is_configured():
        return {
            **base_result,
            "summary": NOT_CONFIGURED_MESSAGE_AR,
            "is_configured": False,
        }

    mime_type = _guess_ext_mime(content_type)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    if provider == "openai":
        summary = await _summarize_with_openai(image_b64, mime_type)
    else:
        summary = await _summarize_with_gemini(image_b64, mime_type)

    return {**base_result, "summary": summary, "is_configured": True}
