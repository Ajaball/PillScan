"""
Tests for the assistant's comprehensive response shape and its handling of
incomplete / malformed model output.
"""

from app.services import assistant_service as A

# Every display field the comprehensive contract must always expose.
DISPLAY_FIELDS = [
    "name", "activeIngredient", "uses", "dosage",
    "sideEffects", "warnings", "contraindications", "usageTimes",
]


def test_normalize_full_response_has_all_fields():
    parsed = {
        "name": "بنادول",
        "activeIngredient": "باراسيتامول",
        "uses": ["خفض الحرارة", "تسكين الألم"],
        "dosage": ["قرص كل 6 ساعات"],
        "sideEffects": ["غثيان", "طفح جلدي"],
        "warnings": ["لا تتجاوز الجرعة"],
        "contraindications": ["أمراض الكبد الشديدة"],
        "usageTimes": ["صباحًا", "مساءً بعد الأكل"],
        "recognized": True,
    }
    out = A._normalize(parsed, "Panadol", "gemini-x")
    for field in DISPLAY_FIELDS:
        assert field in out
    assert out["recognized"] is True
    assert out["name"] == "بنادول"
    assert out["activeIngredient"] == "باراسيتامول"
    assert out["uses"] == ["خفض الحرارة", "تسكين الألم"]
    assert out["sideEffects"] == ["غثيان", "طفح جلدي"]
    assert out["contraindications"] == ["أمراض الكبد الشديدة"]


def test_normalize_coerces_string_to_list():
    parsed = {"name": "X", "sideEffects": "غثيان", "usageTimes": "صباحًا",
              "uses": "تسكين", "recognized": True}
    out = A._normalize(parsed, "X", "m")
    assert out["sideEffects"] == ["غثيان"]
    assert out["usageTimes"] == ["صباحًا"]
    assert out["uses"] == ["تسكين"]


def test_normalize_recognized_kept_with_any_content():
    """recognized stays True as long as ANY substantive field is present."""
    parsed = {"name": "X", "uses": ["خفض الحرارة"], "sideEffects": [],
              "usageTimes": [], "recognized": True}
    out = A._normalize(parsed, "X", "m")
    assert out["recognized"] is True


def test_normalize_empty_recognized_flips_to_false():
    """recognized=true but every field empty → treated as unrecognised."""
    parsed = {"name": "X", "recognized": True}
    out = A._normalize(parsed, "X", "m")
    assert out["recognized"] is False
    assert out["message"]


def test_normalize_missing_fields_are_safe():
    out = A._normalize({}, "Aspirin", "m")
    assert out["name"] == "Aspirin"        # falls back to the queried name
    assert out["sideEffects"] == []
    assert out["uses"] == []
    assert out["activeIngredient"] == ""
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
