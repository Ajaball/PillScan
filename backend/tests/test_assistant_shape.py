"""
Tests for the assistant's fixed three-field response shape and its handling of
incomplete / malformed model output.
"""

from app.services import assistant_service as A


def test_normalize_full_response_in_order():
    parsed = {
        "name": "بنادول",
        "sideEffects": ["غثيان", "طفح جلدي"],
        "usageTimes": ["صباحًا", "مساءً بعد الأكل"],
        "recognized": True,
        # An extra field the model might leak must be ignored.
        "dosage": "500mg",
    }
    out = A._normalize(parsed, "Panadol", "gemini-x")
    # Exactly the three display fields, in order, then recognized.
    assert list(out.keys())[:4] == ["name", "sideEffects", "usageTimes", "recognized"]
    assert "dosage" not in out
    assert out["recognized"] is True
    assert out["name"] == "بنادول"
    assert out["sideEffects"] == ["غثيان", "طفح جلدي"]
    assert out["usageTimes"] == ["صباحًا", "مساءً بعد الأكل"]


def test_normalize_coerces_string_to_list():
    parsed = {"name": "X", "sideEffects": "غثيان", "usageTimes": "صباحًا", "recognized": True}
    out = A._normalize(parsed, "X", "m")
    assert out["sideEffects"] == ["غثيان"]
    assert out["usageTimes"] == ["صباحًا"]


def test_normalize_incomplete_recognized_flips_to_false():
    """recognized=true but no side effects AND no usage times → treated as unrecognised."""
    parsed = {"name": "X", "sideEffects": [], "usageTimes": [], "recognized": True}
    out = A._normalize(parsed, "X", "m")
    assert out["recognized"] is False
    assert out["message"]


def test_normalize_missing_fields_are_safe():
    out = A._normalize({}, "Aspirin", "m")
    assert out["name"] == "Aspirin"        # falls back to the queried name
    assert out["sideEffects"] == []
    assert out["usageTimes"] == []
    assert out["recognized"] is False


def test_parse_json_strips_code_fences():
    assert A._parse_json('```json\n{"name":"X","recognized":false}\n```') == {
        "name": "X", "recognized": False
    }


def test_parse_json_extracts_embedded_object():
    parsed = A._parse_json('بعض النص {"name":"Y","recognized":true} نص إضافي')
    assert parsed and parsed["name"] == "Y"


def test_parse_json_returns_none_on_garbage():
    assert A._parse_json("this is not json at all") is None
