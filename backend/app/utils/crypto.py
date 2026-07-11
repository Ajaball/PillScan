"""
Secret Encryption Utility
=========================

Encrypts user-supplied secrets (LLM API keys) before they are stored in the
database, and decrypts them when needed for an outgoing API call. Keys are
**never** stored in plaintext.

Design note
-----------
This uses only the Python standard library (``hashlib`` + ``hmac`` + ``os``),
deliberately avoiding a dependency on the ``cryptography`` package: that package
requires a compiled native backend (``_cffi_backend``) which is not reliably
importable in every environment this project runs in, and we do not want the
whole app to crash on startup just to store an API key.

The scheme is an HMAC-authenticated SHA-256 keystream cipher (encrypt-then-MAC):

    key      = SHA256(JWT_SECRET_KEY)                     (32 bytes)
    keystream= SHA256(key || nonce || counter) blocks     (CTR-style)
    cipher   = plaintext XOR keystream
    mac      = HMAC-SHA256(key, nonce || cipher)
    token    = base64url( nonce(16) || mac(32) || cipher )

This keeps keys non-recoverable at rest without the server secret and detects
tampering. It is intentionally simple; for stronger guarantees swap in a vetted
AEAD library once its native backend is guaranteed in the deploy environment.

⚠️  The encryption key is derived from ``JWT_SECRET_KEY``; rotating that secret
makes previously stored API keys undecryptable — users would just re-enter them.
"""

import base64
import hashlib
import hmac
import os
from functools import lru_cache
from typing import Optional

from app.config import get_settings

_NONCE_LEN = 16
_MAC_LEN = 32


@lru_cache()
def _key() -> bytes:
    """32-byte key derived from the app's JWT secret."""
    settings = get_settings()
    return hashlib.sha256(settings.JWT_SECRET_KEY.encode("utf-8")).digest()


def _keystream(nonce: bytes, length: int) -> bytes:
    """Generate `length` bytes of keystream from key+nonce in counter mode."""
    key = _key()
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt_secret(plaintext: Optional[str]) -> Optional[str]:
    """
    Encrypt a secret string for storage. Returns ``None`` for empty/None input
    so callers can clear a stored key by passing an empty value.
    """
    if not plaintext:
        return None
    data = plaintext.encode("utf-8")
    nonce = os.urandom(_NONCE_LEN)
    cipher = bytes(b ^ k for b, k in zip(data, _keystream(nonce, len(data))))
    mac = hmac.new(_key(), nonce + cipher, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(nonce + mac + cipher)
    return token.decode("utf-8")


def decrypt_secret(token: Optional[str]) -> Optional[str]:
    """
    Decrypt a stored secret. Returns ``None`` if the value is empty, malformed,
    tampered with, or was encrypted under a different secret — the caller then
    behaves as if no key were configured instead of crashing.
    """
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
    except (ValueError, TypeError):
        return None
    if len(raw) < _NONCE_LEN + _MAC_LEN:
        return None

    nonce = raw[:_NONCE_LEN]
    mac = raw[_NONCE_LEN:_NONCE_LEN + _MAC_LEN]
    cipher = raw[_NONCE_LEN + _MAC_LEN:]

    expected = hmac.new(_key(), nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        return None  # tampered or wrong key

    try:
        data = bytes(b ^ k for b, k in zip(cipher, _keystream(nonce, len(cipher))))
        return data.decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def mask_secret(plaintext: Optional[str]) -> Optional[str]:
    """
    Produce a safe hint of a secret for display (e.g. ``••••••••abcd``) without
    revealing it. Returns ``None`` when there is nothing configured.
    """
    if not plaintext:
        return None
    tail = plaintext[-4:] if len(plaintext) >= 4 else plaintext
    return f"••••••••{tail}"
