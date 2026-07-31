from __future__ import annotations

import time

import pytest

from workspace_service.surfaces.display_service import (
    DisplayContractError,
    DisplayEnvelopeLimits,
    validate_display_envelope,
)


pytestmark = pytest.mark.workspace_surfaces


def _envelope(**changes):
    value = {
        "schemaVersion": 1,
        "displayId": "loads",
        "revision": 1,
        "idempotencyKey": "display-request-0001",
        "title": "Loads",
        "durability": "durable",
        "accessibility": {"description": "Load by time."},
        "representations": [
            {
                "mediaType": "text/plain",
                "encoding": "utf-8",
                "data": "Load: 10 N",
                "activeHtml": False,
            }
        ],
    }
    value.update(changes)
    return value


@pytest.mark.parametrize(
    "representation",
    [
        {"mediaType": "image/png", "encoding": "utf-8", "data": "x"},
        {"mediaType": "text/plain", "encoding": "base64", "data": "eA=="},
        {"mediaType": "application/vnd.plotly.v1+json", "encoding": "utf-8", "data": "{}"},
        {"mediaType": "image/svg+xml", "encoding": "utf-8", "data": "<svg/>", "activeHtml": True},
        {"mediaType": "application/javascript", "encoding": "utf-8", "data": "bad()"},
    ],
)
def test_media_type_encoding_shape_and_active_mode_are_allowlisted(representation) -> None:
    with pytest.raises(DisplayContractError):
        validate_display_envelope(_envelope(representations=[representation]))


def test_accessibility_idempotency_and_revision_are_mandatory_and_bounded() -> None:
    for changes in (
        {"accessibility": {}},
        {"idempotencyKey": "short"},
        {"revision": 0},
        {"displayId": "bad/display"},
    ):
        with pytest.raises(DisplayContractError):
            validate_display_envelope(_envelope(**changes))


def test_nested_json_non_finite_item_depth_and_byte_limits_are_enforced() -> None:
    json_representation = {
        "mediaType": "application/vnd.plotly.v1+json",
        "encoding": "json",
        "data": {"data": [{"y": [1.0, 2.0]}]},
    }
    assert validate_display_envelope(
        _envelope(representations=[json_representation])
    ).display_id == "loads"
    limits = DisplayEnvelopeLimits(
        maximum_encoded_bytes=128,
        maximum_json_depth=3,
        maximum_json_items=3,
        validation_seconds=0.2,
    )
    for data in (
        {"a": {"b": {"c": {"d": 1}}}},
        {"items": [1, 2, 3, 4]},
        {"value": float("nan")},
        {"text": "x" * 256},
    ):
        with pytest.raises(DisplayContractError):
            validate_display_envelope(
                _envelope(
                    representations=[{**json_representation, "data": data}]
                ),
                limits=limits,
            )


def test_validation_time_budget_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    ticks = iter((0.0, 1.0, 2.0, 3.0))
    monkeypatch.setattr(time, "monotonic", lambda: next(ticks))
    with pytest.raises(DisplayContractError, match="time"):
        validate_display_envelope(
            _envelope(), limits=DisplayEnvelopeLimits(validation_seconds=0.01)
        )
