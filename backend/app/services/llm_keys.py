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
