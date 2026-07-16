"""
Leaflet Summarizer Service
==========================

Takes a photo of a medication leaflet / prescription (the paper folded inside
the medicine box) and returns a plain-language **Arabic** summary produced by a
vision-capable LLM.

The app is **Gemini-only**. A user can enter up to five Gemini keys on the AI
settings page; they are tried in order, moving to the next key automatically
when one is exhausted or fails. Server env keys are a shared fallback. Network
calls go through ``httpx`` — no extra SDK dependency is required.

If no API key is configured the service returns a clearly-labelled placeholder
(``is_configured = False``) instead of failing, so the full scan → summary flow
can still be demonstrated offline without fabricating medical content.
"""

import base64
from typing import Any, Optional

from app.config import get_settings
from app.services import llm_keys

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
    "ثم أضف مفتاح Gemini (جوجل) واحد على الأقل. يمكنك إضافة حتى 5 مفاتيح، "
    "وسيتنقّل التطبيق بينها تلقائيًا إذا انتهى رصيد أحدها.\n\n"
    "بعد إضافة المفتاح، أعد تصوير النشرة وسيظهر الملخّص الحقيقي هنا."
)


def _guess_ext_mime(content_type: Optional[str]) -> str:
    """Normalise the image MIME type for the provider payloads."""
    if content_type and content_type.startswith("image/"):
        return content_type
    return "image/jpeg"


async def _summarize_with_gemini(image_b64: str, mime_type: str, api_key: str, model: str) -> str:
    """
    Call Gemini and return the Arabic summary text.

    The heavy lifting (model fallback, error classification, timeouts, network
    errors) lives in ``llm_keys.gemini_generate``; the ``model`` argument is kept
    for backward compatibility but model selection is handled centrally there.
    """
    parts = [
        {"text": SUMMARY_PROMPT_AR},
        {"inline_data": {"mime_type": mime_type, "data": image_b64}},
    ]
    try:
        return await llm_keys.gemini_generate(parts, api_key, temperature=0.2)
    except llm_keys.GeminiError as e:
        raise LeafletServiceError(str(e))


def is_configured(user: Optional[Any] = None) -> bool:
    """True when at least one Gemini key (user or server) is available."""
    return bool(llm_keys.resolve_gemini_keys(user))


async def summarize_leaflet(
    image_bytes: bytes,
    content_type: Optional[str],
    user: Optional[Any] = None,
    db: Any = None,
) -> dict:
    """
    Summarize a medication leaflet image in Arabic using Gemini.

    Tries the user's Gemini keys (settings page) first, then any server env
    keys, moving to the next key automatically when one fails or is exhausted.

    Returns a dict:
        {
            "summary": str,          # Arabic summary (or a setup message)
            "provider": "gemini",
            "model": str,            # model id used
            "is_configured": bool,   # False when no API key is set
            "disclaimer_ar": str,
            "disclaimer_en": str,
        }

    Raises LeafletServiceError if every configured key fails.
    """
    model = settings.GEMINI_MODEL
    base_result = {
        "provider": "gemini",
        "model": model,
        "disclaimer_ar": DISCLAIMER_AR,
        "disclaimer_en": DISCLAIMER_EN,
    }

    keys = await llm_keys.resolve_gemini_keys_async(user, db)
    if not keys:
        return {
            **base_result,
            "summary": NOT_CONFIGURED_MESSAGE_AR,
            "is_configured": False,
        }

    mime_type = _guess_ext_mime(content_type)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    try:
        summary = await llm_keys.call_with_failover(
            keys, lambda key: _summarize_with_gemini(image_b64, mime_type, key, model)
        )
    except LeafletServiceError:
        raise
    except Exception as e:  # noqa: BLE001 - normalise any failover error
        raise LeafletServiceError(str(e))

    return {**base_result, "summary": summary, "is_configured": True}
