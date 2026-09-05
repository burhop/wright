import pytest

from core.canonical_json import canonical_json_bytes
from core.native_runtime_json import runtime_json_bytes, runtime_json_loads


def test_literal_text_and_fractional_data_round_trip_without_changing_documents():
    value = {"text": "e\u0301", "fraction": 0.5}
    assert runtime_json_loads(runtime_json_bytes(value)) == value
    with pytest.raises(ValueError):
        canonical_json_bytes(value)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"x":1,"x":2}',
        b"NaN",
        b"Infinity",
        b"1e999",
        b'"\\ud800"',
        b"\xef\xbb\xbf{}",
        b"[" * 65 + b"0" + b"]" * 65,
    ],
)
def test_runtime_data_still_rejects_ambiguous_nonfinite_or_unbounded_input(raw):
    with pytest.raises(ValueError):
        runtime_json_loads(raw)


def test_runtime_data_byte_limit_applies_in_both_directions():
    with pytest.raises(ValueError):
        runtime_json_bytes("é", max_bytes=3)
    with pytest.raises(ValueError):
        runtime_json_loads(b'"abcd"', max_bytes=3)
