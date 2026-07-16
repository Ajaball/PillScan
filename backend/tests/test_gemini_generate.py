"""
Tests for the centralised Gemini call: model fallback on 404 and the
classification of API errors (invalid key, quota, timeout, network).
"""

import httpx
import pytest

from app.services import llm_keys


class _Resp:
    def __init__(self, status_code=200, text="", payload=None):
        self.status_code = status_code
        self.text = text
        self._payload = payload or {}

    def json(self):
        return self._payload


def _client_factory(handler):
    """Build a fake httpx.AsyncClient whose .post delegates to ``handler(url)``."""

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **k):
            return handler(url)

    return FakeClient


def _ok_payload(text="hello"):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


@pytest.mark.asyncio
async def test_model_fallback_on_404(monkeypatch):
    """A 404 on the primary model falls back to the next model automatically."""
    calls = []

    def handler(url):
        calls.append(url)
        # First (primary) model 404s; the next model succeeds.
        if len(calls) == 1:
            return _Resp(404, text="model not found")
        return _Resp(200, payload=_ok_payload("second-model-ok"))

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", _client_factory(handler))
    text = await llm_keys.gemini_generate([{"text": "hi"}], "KEY")
    assert text == "second-model-ok"
    assert len(calls) >= 2  # primary + fallback


@pytest.mark.asyncio
async def test_invalid_key_classified(monkeypatch):
    def handler(url):
        return _Resp(400, text='{"error":{"status":"API_KEY_INVALID"}}')

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", _client_factory(handler))
    with pytest.raises(llm_keys.GeminiError) as ei:
        await llm_keys.gemini_generate([{"text": "hi"}], "BADKEY")
    assert ei.value.kind == "invalid_key"
    assert "غير صالح" in ei.value.message_ar


@pytest.mark.asyncio
async def test_quota_classified(monkeypatch):
    def handler(url):
        return _Resp(429, text="RESOURCE_EXHAUSTED")

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", _client_factory(handler))
    with pytest.raises(llm_keys.GeminiError) as ei:
        await llm_keys.gemini_generate([{"text": "hi"}], "KEY")
    assert ei.value.kind == "quota"


@pytest.mark.asyncio
async def test_timeout_classified(monkeypatch):
    class TimeoutClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", TimeoutClient)
    with pytest.raises(llm_keys.GeminiError) as ei:
        await llm_keys.gemini_generate([{"text": "hi"}], "KEY")
    assert ei.value.kind == "timeout"


@pytest.mark.asyncio
async def test_network_error_classified(monkeypatch):
    class NetClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", NetClient)
    with pytest.raises(llm_keys.GeminiError) as ei:
        await llm_keys.gemini_generate([{"text": "hi"}], "KEY")
    assert ei.value.kind == "network"


@pytest.mark.asyncio
async def test_all_models_404(monkeypatch):
    def handler(url):
        return _Resp(404, text="not found")

    monkeypatch.setattr(llm_keys.httpx, "AsyncClient", _client_factory(handler))
    with pytest.raises(llm_keys.GeminiError) as ei:
        await llm_keys.gemini_generate([{"text": "hi"}], "KEY")
    assert ei.value.kind == "model"
