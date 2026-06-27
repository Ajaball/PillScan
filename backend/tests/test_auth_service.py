"""
PillScan — Auth Service Unit Tests
====================================

Pure unit tests for password hashing, JWT generation, and token validation.
No database or network calls needed.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from fastapi import HTTPException


class TestPasswordHashing:
    """Unit tests for bcrypt password hashing."""

    def test_hash_password_returns_hash(self):
        """hash_password should return a bcrypt hash string."""
        hashed = hash_password("MySecurePassword123")
        assert hashed is not None
        assert hashed != "MySecurePassword123"
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_verify_correct_password(self):
        """verify_password should return True for correct password."""
        password = "HelloWorld@2026"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """verify_password should return False for wrong password."""
        hashed = hash_password("CorrectPassword")
        assert verify_password("WrongPassword", hashed) is False

    def test_hash_is_unique(self):
        """Same password should produce different hashes (salt)."""
        password = "SamePassword"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # Different salts
        # But both should verify
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_empty_password(self):
        """Empty password should still hash and verify."""
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False


class TestJWTTokens:
    """Unit tests for JWT token creation and decoding."""

    def test_create_access_token(self):
        """Access token should be a non-empty JWT string."""
        token = create_access_token("user-uuid-123", "user@test.sa")
        assert token is not None
        assert len(token) > 50  # JWT tokens are long
        assert token.count('.') == 2  # JWTs have 3 parts

    def test_create_refresh_token(self):
        """Refresh token should be a non-empty JWT string."""
        token = create_refresh_token("user-uuid-123")
        assert token is not None
        assert token.count('.') == 2

    def test_decode_access_token(self):
        """Decoded access token should contain correct claims."""
        user_id = "test-user-uuid-456"
        email = "decoded@test.sa"
        token = create_access_token(user_id, email)
        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_refresh_token(self):
        """Decoded refresh token should have type 'refresh'."""
        user_id = "refresh-user-uuid"
        token = create_refresh_token(user_id)
        payload = decode_token(token)

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_decode_invalid_token_raises(self):
        """Invalid token should raise HTTPException with 401."""
        with pytest.raises(HTTPException) as exc_info:
            decode_token("this.is.not-a-valid-jwt")
        assert exc_info.value.status_code == 401

    def test_access_and_refresh_tokens_differ(self):
        """Access and refresh tokens for same user should be different."""
        user_id = "same-user-uuid"
        access = create_access_token(user_id, "user@test.sa")
        refresh = create_refresh_token(user_id)
        assert access != refresh
