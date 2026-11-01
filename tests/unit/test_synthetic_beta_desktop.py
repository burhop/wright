"""Recorder fixtures; they do not establish real guest usability."""

import json
from pathlib import Path
import struct
import sys
import zlib

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from synthetic_beta_testing.desktop import TOOLS, VisibleSession, ppm_to_png
from synthetic_beta_testing.vm import VMError


class Guest:
    def __init__(self, root):
        self.root = root
        (root / "sessions/test").mkdir(parents=True)
        self.calls = []

    def state(self, session):
        return {"live": True}

    def screenshot(self, session, target):
        Path(target).write_bytes(b"P6\n2 1\n255\n\x00\x10\xff\x20\x00\x40")

    def input(self, session, operation, **kwargs):
        self.calls.append((session, operation, kwargs))


def test_png_retains_actual_pixels():
    png, width, height = ppm_to_png(b"P6\n# screen\n2 1\n255\n\x00\x10\xff\x20\x00\x40")
    assert (width, height) == (2, 1)
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    compressed = b""
    while offset < len(png):
        size = struct.unpack(">I", png[offset : offset + 4])[0]
        kind = png[offset + 4 : offset + 8]
        if kind == b"IDAT":
            compressed += png[offset + 8 : offset + 8 + size]
        offset += size + 12
    assert zlib.decompress(compressed) == b"\x00\x00\x10\xff\x20\x00\x40"


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"P3 1 1 255\n000",
        b"P6\n1 1\n65535\n123456",
        b"P6\n100000 100000\n255\n",
        b"P6\n2 1\n255\n123",
    ],
)
def test_invalid_capture_rejected(data):
    with pytest.raises(VMError):
        ppm_to_png(data)


def test_recorder_returns_screen_and_real_references(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    result = session("desktop", {"action": "screenshot"})
    assert result["image_url"].startswith("data:image/png;base64,")
    assert json.loads(result["text"])["screen_width"] == 2
    event = json.loads(session.events.read_text())
    assert (session.root / event["captures"][0]["path"]).is_file()
    note = session(
        "feedback_note",
        {"text": "I expected a browser", "evidence_refs": [event["id"]]},
    )
    assert note["success"]
    assert not session(
        "feedback_note", {"text": "invented", "evidence_refs": ["fake"]}
    )["success"]


def test_no_host_shell_or_hidden_api_tool(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    result = session("host_shell", {"command": "cat private"})
    assert not result["success"]
    assert not guest.calls


def test_cancel_and_budget_stop_before_guest_input(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20, max_actions=0)
    with pytest.raises(VMError, match="budget"):
        session("desktop", {"action": "key", "key": "ret"})
    session.max_actions = 10
    session.cancel()
    with pytest.raises(VMError, match="deadline"):
        session("desktop", {"action": "key", "key": "ret"})
    assert not guest.calls


def test_failed_wait_is_recorded_and_text_is_redacted(tmp_path):
    session = VisibleSession(Guest(tmp_path), "test", 20)
    assert not session("desktop", {"action": "wait", "seconds": 90})["success"]
    session("feedback_note", {"text": "password=example-secret", "evidence_refs": []})
    assert "example-secret" not in session.events.read_text()
    assert "[REDACTED]" in session.events.read_text()


def test_existing_attempt_cannot_be_overwritten(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    session("feedback_note", {"text": "recorded", "evidence_refs": []})
    with pytest.raises(VMError, match="already exists"):
        VisibleSession(guest, "test", 20)


def test_move_exposes_only_visible_pointer_and_retains_screen_contract(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    session("desktop", {"action": "screenshot"})
    result = session("desktop", {"action": "move", "x": 1, "y": 0})
    assert result["success"]
    assert guest.calls == [
        ("test", "pointer", {"x": 1, "y": 0, "width": 2, "height": 1})
    ]
    assert result["image_url"].startswith("data:image/png;base64,")
    assert json.loads(result["text"])["screen_width"] == 2
    assert "move" in TOOLS[0]["inputSchema"]["properties"]["action"]["enum"]
    assert {item["name"] for item in TOOLS} == {"desktop", "feedback_note"}


def test_positioned_scroll_moves_before_wheel_event_with_current_dimensions(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    session("desktop", {"action": "screenshot"})
    result = session("desktop", {"action": "scroll", "x": 1, "y": 0, "delta": 3})
    assert result["success"]
    assert guest.calls == [
        ("test", "pointer", {"x": 1, "y": 0, "width": 2, "height": 1}),
        ("test", "scroll", {"delta": 3}),
    ]


def test_regular_scroll_keeps_current_pointer_position(tmp_path):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    assert session("desktop", {"action": "scroll", "delta": -2})["success"]
    assert guest.calls == [("test", "scroll", {"delta": -2})]


@pytest.mark.parametrize(
    "arguments",
    [
        {"action": "scroll", "x": 1, "delta": 2},
        {"action": "scroll", "y": 1, "delta": 2},
        {"action": "scroll", "x": 1280, "y": 0, "delta": 2},
        {"action": "scroll", "x": 0, "y": 0, "delta": 0},
        {"action": "move", "x": -1, "y": 0},
        {"action": "move", "x": 0, "y": 800},
        {"action": "move", "x": True, "y": 0},
        {"action": "move", "x": 0},
        {"action": "move", "x": 0, "y": 0, "hidden_api": "/private"},
    ],
)
def test_invalid_pointer_or_partial_scroll_has_no_guest_input(tmp_path, arguments):
    guest = Guest(tmp_path)
    session = VisibleSession(guest, "test", 20)
    assert not session("desktop", arguments)["success"]
    assert guest.calls == []


def test_journey_markers_use_controller_clock_and_require_real_event_refs(tmp_path):
    from synthetic_beta_testing.journey import JourneyRecorder, read_events, project

    session = VisibleSession(Guest(tmp_path), "test", 20)
    session.journey = JourneyRecorder.begin(
        session.root,
        {
            "schema_version": 1,
            "id": "fixture",
            "label": "Fixture",
            "steps": [{"id": "open", "label": "Open Wright"}],
        },
    )
    args = {
        "step_id": "open",
        "status": "started",
        "note": "",
        "categories": [],
        "evidence_refs": [],
    }
    assert session("journey_step", args)["success"]
    session("desktop", {"action": "screenshot"})
    args.update(
        status="blocked",
        note="password=example-secret",
        categories=["setup_access"],
        evidence_refs=["fake"],
    )
    assert not session("journey_step", args)["success"]
    args["evidence_refs"] = ["e00002"]
    assert session("journey_step", args)["success"]
    session.journey.finish()
    assert "example-secret" not in session.journey.path.read_text()
    assert (
        project(session.journey.plan, read_events(session.root))["steps"][0]["status"]
        == "blocked"
    )
