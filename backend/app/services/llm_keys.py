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


def resolve_gemini_keys(user: Optional[Any] = None) -> List[str]:
    """
    Ordered, de-duplicated Gemini API keys to try for a request:
    the user's own keys first (settings page), then any server env keys.
    """
    ordered = user_gemini_keys(user) + env_gemini_keys()
    seen = set()
    result: List[str] = []
    for k in ordered:
        if k not in seen:
            seen.add(k)
            result.append(k)
    return result


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
