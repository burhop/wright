"""Record visible guest interaction; expose no host shell or product API tools."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import threading
import time
from datetime import datetime, timezone
import zlib

from .vm import VMBackend, VMError
from .journey import CATEGORIES, STATES

# Reuse the existing stdlib redaction module without core's telemetry bootstrap.
_redaction_path = (
    Path(__file__).resolve().parents[2] / "packages/core/src/core/redaction.py"
)
_redaction_spec = importlib.util.spec_from_file_location(
    "_wright_beta_redaction", _redaction_path
)
_redaction = importlib.util.module_from_spec(_redaction_spec)
_redaction_spec.loader.exec_module(_redaction)
redact_evidence, redact_text = _redaction.redact_evidence, _redaction.redact_text


def ppm_to_png(data: bytes) -> tuple[bytes, int, int]:
    """Convert QMP's RGB P6 screenshot without an imaging dependency."""
    position = 0
    tokens = []
    while len(tokens) < 4:
        while position < len(data) and data[position] in b" \r\n\t":
            position += 1
        if position < len(data) and data[position] == ord("#"):
            end = data.find(b"\n", position)
            if end < 0:
                raise VMError("Incomplete PPM comment")
            position = end + 1
            continue
        match = re.match(rb"[^\s#]+", data[position:])
        if not match:
            raise VMError("Incomplete PPM header")
        tokens.append(match.group())
        position += len(match.group())
    if tokens[0] != b"P6" or tokens[3] != b"255":
        raise VMError("Expected an 8-bit RGB PPM screenshot")
    try:
        width, height = int(tokens[1]), int(tokens[2])
    except ValueError as error:
        raise VMError("Invalid screenshot dimensions") from error
    if not (1 <= width <= 8192 and 1 <= height <= 8192):
        raise VMError("Screenshot dimensions exceed limit")
    if data[position : position + 2] == b"\r\n":
        position += 2
    elif data[position : position + 1] in (b"\n", b" ", b"\t"):
        position += 1
    else:
        raise VMError("PPM header has no pixel separator")
    pixels = data[position:]
    if len(pixels) != width * height * 3:
        raise VMError("PPM pixel length disagrees with dimensions")

    def chunk(kind, value):
        return (
            struct.pack(">I", len(value))
            + kind
            + value
            + struct.pack(">I", zlib.crc32(kind + value) & 0xFFFFFFFF)
        )

    rows = b"".join(
        b"\0" + pixels[y * width * 3 : (y + 1) * width * 3] for y in range(height)
    )
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b"")
    return png, width, height


TOOLS = [
    {
        "type": "function",
        "name": "desktop",
        "description": "See and operate the customer's virtual desktop. Use its browser UI for Wright. Move hovers the pointer at x/y. Positive scroll moves down; supply both x/y to scroll at that visible position, or omit both to use the current pointer position. Keys use QEMU names; chords such as ctrl+l are supported. Every action returns the resulting screen and evidence ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "enum": [
                        "screenshot",
                        "click",
                        "move",
                        "key",
                        "type_text",
                        "scroll",
                        "wait",
                    ]
                },
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "button": {"enum": ["left", "right", "middle"]},
                "key": {"type": "string"},
                "text": {"type": "string", "maxLength": 2000},
                "delta": {"type": "integer", "minimum": -20, "maximum": 20},
                "seconds": {"type": "number", "minimum": 0, "maximum": 15},
                "intent": {"type": "string", "minLength": 1, "maxLength": 240},
                "wait_for": {"enum": ["wright", "external"]},
            },
            "required": ["action", "intent"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "feedback_note",
        "description": "Record a short beta-tester observation or expectation with earlier evidence IDs. This is feedback, not proof that a product action succeeded.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "maxLength": 3000},
                "evidence_refs": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["text", "evidence_refs"],
            "additionalProperties": False,
        },
    },
]

from .activity_diary import ACTIVITY_STATES

ACTIVITY_TOOL = {
    "type": "function", "name": "activity_note",
    "description": "Declare your current observable activity or a change of approach without touching the UI. Give a short intent/state, never private reasoning or credentials. The controller records time; do not invent a thinking duration.",
    "inputSchema": {"type": "object", "properties": {
        "state": {"enum": sorted(set(ACTIVITY_STATES) - {"preparing_environment", "recording_observation", "native_pause"})},
        "summary": {"type": "string", "minLength": 1, "maxLength": 240},
        "evidence_refs": {"type": "array", "items": {"type": "string"}},
    }, "required": ["state", "summary", "evidence_refs"], "additionalProperties": False},
}

JOURNEY_TOOL = {
    "type": "function",
    "name": "journey_step",
    "description": "Record a timed transition in your declared customer journey. This records your experience, not verified product success. Finish the current step before starting another; revisit a step to record a retry.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "step_id": {"type": "string"},
            "status": {"enum": sorted(STATES)},
            "note": {"type": "string", "maxLength": 3000},
            "categories": {"type": "array", "items": {"enum": sorted(CATEGORIES)}},
            "evidence_refs": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["step_id", "status", "note", "categories", "evidence_refs"],
        "additionalProperties": False,
    },
}


class VisibleSession:
    def __init__(
        self,
        backend: VMBackend,
        session_id: str,
        timeout_seconds: float,
        max_actions=300,
        *,
        recording_id: str | None = None,
    ):
        self.backend = backend
        self.session_id = session_id
        self.recording_id = recording_id or session_id
        self.root = backend._session(self.recording_id)
        if not backend.state(session_id)["live"]:
            raise VMError("Customer guest is not live")
        self.events = self.root / "events.jsonl"
        if self.events.exists():
            raise VMError(
                "Observed session already exists; retain it and use a fresh clone"
            )
        self.capture_root = self.root / "captures"
        self.capture_root.mkdir(exist_ok=True)
        self.deadline = time.monotonic() + timeout_seconds
        self.max_actions = max_actions
        self.cancelled = threading.Event()
        self.sequence = 0
        self.width, self.height = 1280, 800
        self.known_events: set[str] = set()
        self.journey = None

    def cancel(self):
        self.cancelled.set()

    def native_pause(self, boundary, duration_ms):
        self._check()
        if self.journey is not None:
            self.journey.activity(
                "native_pause" if boundary == "item/started" else "reviewing_deciding",
                f"Native AI pause requested for {duration_ms} ms" if boundary == "item/started"
                else "AI tester resumed after native pause; choosing next action",
            )

    def _check(self):
        if self.cancelled.is_set() or time.monotonic() >= self.deadline:
            raise VMError("Customer action deadline reached")
        if self.sequence >= self.max_actions:
            raise VMError("Customer action budget reached")

    def _pointer_coordinates(self, arguments):
        x, y = arguments.get("x"), arguments.get("y")
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, int)
            or not isinstance(y, int)
            or not 0 <= x < self.width
            or not 0 <= y < self.height
        ):
            raise VMError(
                "Pointer requires integer x/y coordinates inside the current visible screen"
            )
        return x, y

    def _screen(self, event_id):
        self._check()
        raw_root = self.capture_root
        if self.recording_id != self.session_id:
            # QMP may write only inside its actual owned VM directory. Keep the
            # temporary capture there; retain the PNG in this visit's record.
            raw_root = self.backend._session(self.session_id) / "recording-scratch" / self.recording_id
            raw_root.mkdir(parents=True, exist_ok=True)
        raw = raw_root / f"{event_id}.ppm"
        self.backend.screenshot(self.session_id, raw)
        png, self.width, self.height = ppm_to_png(raw.read_bytes())
        path = self.capture_root / f"{event_id}.png"
        path.write_bytes(png)
        raw.unlink()
        return path, png

    def __call__(self, name, arguments):
        self._check()
        if not isinstance(arguments, dict):
            raise VMError("Expected typed action arguments")
        event_id = f"e{self.sequence + 1:05d}"
        started = time.monotonic()
        captures = []
        png = None
        action = {"tool": name, **arguments}
        success = True
        result = "Visible guest action performed; inspect the resulting screen."
        try:
            if name == "activity_note" and self.journey is not None:
                if set(arguments) != {"state", "summary", "evidence_refs"}:
                    raise VMError("Activity declaration requires typed fields")
                if (arguments["state"] not in ACTIVITY_TOOL["inputSchema"]["properties"]["state"]["enum"]
                        or not isinstance(arguments["summary"], str)
                        or not 1 <= len(arguments["summary"]) <= 240
                        or not isinstance(arguments["evidence_refs"], list)
                        or any(ref not in self.known_events for ref in arguments["evidence_refs"])):
                    raise VMError("Invalid activity declaration or evidence reference")
                self.journey.activity(**redact_evidence(arguments), source="customer_declaration")
                result = "Activity state recorded; no product action performed."
            elif name == "journey_step" and self.journey is not None:
                self.journey.activity("recording_observation", "Recording a high-level activity transition")
                if set(arguments) != {
                    "step_id",
                    "status",
                    "note",
                    "categories",
                    "evidence_refs",
                }:
                    raise VMError("Journey observation needs typed fields")
                refs = arguments["evidence_refs"]
                if not isinstance(refs, list) or any(
                    ref not in self.known_events for ref in refs
                ):
                    raise VMError("Journey observation references an unknown event")
                self.journey.step(**redact_evidence(arguments), actor="customer")
                result = "Timed journey observation recorded; product success is not independently verified."
            elif name == "feedback_note":
                if self.journey is not None:
                    self.journey.activity("feedback", "Recording beta feedback")
                if set(arguments) != {"text", "evidence_refs"}:
                    raise VMError(
                        "Feedback requires text and existing evidence references"
                    )
                if (
                    not isinstance(arguments["text"], str)
                    or not 1 <= len(arguments["text"]) <= 3000
                ):
                    raise VMError("Feedback text exceeds limit")
                refs = arguments["evidence_refs"]
                if not isinstance(refs, list) or any(
                    ref not in self.known_events for ref in refs
                ):
                    raise VMError("Feedback references an unknown event")
                result = "Customer feedback recorded; it is a self-report, not verified product state."
            elif name == "desktop":
                operation = arguments.get("action")
                allowed = {
                    "action",
                    "x",
                    "y",
                    "button",
                    "key",
                    "text",
                    "delta",
                    "seconds",
                    "intent",
                    "wait_for",
                }
                if set(arguments) - allowed:
                    raise VMError("Unsupported desktop argument")
                intent = arguments.get("intent")
                if not isinstance(intent, str) or not 1 <= len(intent) <= 240:
                    raise VMError("Desktop action needs a brief intent for the activity diary")
                if operation == "wait" and arguments.get("wait_for") not in {"wright", "external"}:
                    raise VMError("A wait must name Wright or the external service being observed")
                state = ("waiting_" + arguments["wait_for"] if operation == "wait"
                         else "typing" if operation == "type_text"
                         else "screen_capture" if operation == "screenshot" else "navigating")
                if self.journey is not None:
                    self.journey.activity(state, redact_text(intent), evidence_refs=[event_id])
                if operation == "screenshot":
                    pass
                elif operation == "move":
                    x, y = self._pointer_coordinates(arguments)
                    self.backend.input(
                        self.session_id,
                        "pointer",
                        x=x,
                        y=y,
                        width=self.width,
                        height=self.height,
                    )
                elif operation == "click":
                    self.backend.input(
                        self.session_id,
                        "click",
                        x=arguments["x"],
                        y=arguments["y"],
                        width=self.width,
                        height=self.height,
                        button=arguments.get("button", "left"),
                    )
                elif operation == "key":
                    keys = arguments["key"].lower().split("+")
                    aliases = {
                        "control": "ctrl",
                        "enter": "ret",
                        "return": "ret",
                        "escape": "esc",
                        "space": "spc",
                        "pageup": "pgup",
                        "pagedown": "pgdn",
                        "backspace": "backspace",
                        "super": "meta_l",
                    }
                    keys = [aliases.get(key, key) for key in keys]
                    if not 1 <= len(keys) <= 4 or any(
                        not re.fullmatch(r"[a-z0-9_-]+", key) for key in keys
                    ):
                        raise VMError("Invalid key chord")
                    held = []
                    try:
                        for key in keys[:-1]:
                            self.backend.input(
                                self.session_id, "key", qcode=key, down=True
                            )
                            held.append(key)
                        self.backend.input(self.session_id, "key", qcode=keys[-1])
                    finally:
                        for key in reversed(held):
                            self.backend.input(
                                self.session_id, "key", qcode=key, down=False
                            )
                elif operation == "type_text":
                    text = arguments["text"]
                    if not isinstance(text, str) or len(text) > 2000:
                        raise VMError("Typed text exceeds limit")
                    if any(
                        not (" " <= char <= "~" or char in "\n\t")
                        for char in text
                    ):
                        raise VMError(
                            "Only printable US-ASCII, newline and tab are supported; no text was typed. Use straight quotes for typographical apostrophes."
                        )
                    for offset in range(0, len(text), 32):
                        self._check()
                        self.backend.input(
                            self.session_id,
                            "type_text",
                            text=text[offset : offset + 32],
                        )
                elif operation == "scroll":
                    if ("x" in arguments) != ("y" in arguments):
                        raise VMError(
                            "Positioned scroll requires both x and y coordinates"
                        )
                    delta = arguments["delta"]
                    if (
                        isinstance(delta, bool)
                        or not isinstance(delta, int)
                        or not 0 < abs(delta) <= 20
                    ):
                        raise VMError("Scroll must be 1–20 signed ticks")
                    if "x" in arguments:
                        x, y = self._pointer_coordinates(arguments)
                        self.backend.input(
                            self.session_id,
                            "pointer",
                            x=x,
                            y=y,
                            width=self.width,
                            height=self.height,
                        )
                    self.backend.input(self.session_id, "scroll", delta=delta)
                elif operation == "wait":
                    seconds = arguments["seconds"]
                    if (
                        isinstance(seconds, bool)
                        or not isinstance(seconds, (int, float))
                        or not 0 <= seconds <= 15
                    ):
                        raise VMError("Wait must be between 0 and 15 seconds")
                    if seconds > self.deadline - time.monotonic():
                        raise VMError("Wait exceeds remaining session budget")
                    if self.cancelled.wait(seconds):
                        raise VMError("Customer session cancelled")
                else:
                    raise VMError("Unsupported visible desktop action")
                self._check()
                # Permit a short visible repaint, not a claim that background work finished.
                self.cancelled.wait(0.15)
                path, png = self._screen(event_id)
                captures = [
                    {
                        "path": str(path.relative_to(self.root)),
                        "sha256": hashlib.sha256(png).hexdigest(),
                    }
                ]
            else:
                raise VMError("Only visible desktop and feedback tools are permitted")
        except (VMError, KeyError, TypeError, ValueError) as error:
            success = False
            result = str(error)
        self.sequence += 1
        event = {
            "id": event_id,
            "session_id": self.recording_id,
            "time": datetime.now(timezone.utc).isoformat(),
            "action": redact_evidence(action),
            "observed_result": redact_text(result),
            "success": success,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "captures": captures,
        }
        with self.events.open("a") as stream:
            stream.write(json.dumps(event) + "\n")
        self.known_events.add(event_id)
        if self.journey is not None and (name != "activity_note" or not success):
            self.journey.activity("reviewing_deciding", "Reviewing the returned observation and choosing the next action; includes AI/controller delay", evidence_refs=[event_id])
        response = {
            "success": success,
            "text": json.dumps(
                {
                    "event_id": event_id,
                    "result": result,
                    "screen_width": self.width,
                    "screen_height": self.height,
                    "remaining_seconds": max(
                        0, round(self.deadline - time.monotonic())
                    ),
                    "actions_remaining": self.max_actions - self.sequence,
                }
            ),
        }
        if png:
            response["image_url"] = (
                "data:image/png;base64," + base64.b64encode(png).decode()
            )
        return response
