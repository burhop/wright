from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.surfaces.messages import (
    AuthorizedSurfaceBinding,
    SurfaceMessageRouter,
)


pytestmark = pytest.mark.workspace_surfaces
NOW = datetime(2026, 7, 30, 12, 0, tzinfo=UTC)


def _binding(**overrides) -> AuthorizedSurfaceBinding:
    values = {
        "workspace_id": "workspace-1",
        "session_id": "session-1",
        "surface_id": "surface-1",
        "instance_id": "instance-1",
        "generation": 3,
        "document_origin": "https://s-presentation.preview.test",
        "presentation_id": "presentation",
        "active": True,
    }
    values.update(overrides)
    return AuthorizedSurfaceBinding(**values)


def _message(**overrides):
    values = {
        "protocolVersion": "1.0",
        "kind": "request",
        "messageId": "00000000-0000-4000-8000-000000000001",
        "correlationId": "00000000-0000-4000-8000-000000000002",
        "binding": {
            "workspaceId": "workspace-1",
            "sessionId": "session-1",
            "surfaceId": "surface-1",
            "instanceId": "instance-1",
            "generation": 3,
            "documentOrigin": "https://s-presentation.preview.test",
            "presentationId": "presentation",
        },
        "operation": "tool.call",
        "sequence": 0,
        "createdAt": NOW.isoformat(),
        "deadlineAt": (NOW + timedelta(seconds=10)).isoformat(),
        "idempotencyKey": "message-request-0001",
        "payload": {"value": 4},
    }
    values.update(overrides)
    return values


def test_exact_binding_generation_and_active_presentation_are_required() -> None:
    router = SurfaceMessageRouter(clock=lambda: NOW)
    assert router.route(binding=_binding(), message=_message()).code == "OK"
    assert (
        router.route(
            binding=_binding(workspace_id="workspace-2"),
            message=_message(messageId="00000000-0000-4000-8000-000000000003"),
        ).code
        == "SURFACE_MESSAGE_BINDING_MISMATCH"
    )
    assert (
        router.route(
            binding=_binding(generation=4),
            message=_message(messageId="00000000-0000-4000-8000-000000000004"),
        ).code
        == "SURFACE_MESSAGE_STALE_GENERATION"
    )
    assert (
        router.route(
            binding=_binding(active=False),
            message=_message(messageId="00000000-0000-4000-8000-000000000005"),
        ).code
        == "SURFACE_MESSAGE_PRESENTATION_GONE"
    )


def test_schema_deadline_size_and_depth_fail_with_stable_codes() -> None:
    router = SurfaceMessageRouter(
        clock=lambda: NOW, maximum_message_bytes=1024, maximum_json_depth=4
    )
    assert (
        router.route(binding=_binding(), message=_message(protocolVersion="2.0")).code
        == "SURFACE_MESSAGE_INVALID"
    )
    assert (
        router.route(
            binding=_binding(),
            message=_message(
                messageId="00000000-0000-4000-8000-000000000006",
                deadlineAt=(NOW - timedelta(seconds=1)).isoformat(),
            ),
        ).code
        == "SURFACE_MESSAGE_DEADLINE"
    )
    assert (
        router.route(
            binding=_binding(),
            message=_message(
                messageId="00000000-0000-4000-8000-000000000007",
                payload={"large": "x" * 2000},
            ),
        ).code
        == "SURFACE_MESSAGE_TOO_LARGE"
    )
    assert (
        router.route(
            binding=_binding(),
            message=_message(
                messageId="00000000-0000-4000-8000-000000000008",
                payload={"a": {"b": {"c": {"d": {"e": True}}}}},
            ),
        ).code
        == "SURFACE_MESSAGE_TOO_DEEP"
    )


def test_replay_is_idempotent_but_conflicting_reuse_is_rejected() -> None:
    calls: list[object] = []
    router = SurfaceMessageRouter(
        clock=lambda: NOW,
        handlers={"tool.call": lambda payload: calls.append(payload) or {"answer": 8}},
    )
    first = router.route(binding=_binding(), message=_message())
    replay = router.route(binding=_binding(), message=_message())
    assert replay == first
    assert calls == [{"value": 4}]
    conflicting = router.route(
        binding=_binding(), message=_message(payload={"value": 5})
    )
    assert conflicting.code == "SURFACE_MESSAGE_REPLAY"


def test_sequence_rate_and_cancellation_are_bounded() -> None:
    cancelled: list[str] = []
    router = SurfaceMessageRouter(
        clock=lambda: NOW,
        maximum_messages_per_minute=2,
        cancel=lambda reply_to: cancelled.append(reply_to),
    )
    assert router.route(binding=_binding(), message=_message()).ok
    out_of_order = router.route(
        binding=_binding(),
        message=_message(messageId="00000000-0000-4000-8000-000000000010", sequence=0),
    )
    assert out_of_order.code == "SURFACE_MESSAGE_SEQUENCE"
    cancel = _message(
        kind="cancel",
        messageId="00000000-0000-4000-8000-000000000011",
        replyTo="00000000-0000-4000-8000-000000000001",
        sequence=1,
        operation="request.cancel",
    )
    assert router.route(binding=_binding(), message=cancel).code == "CANCELLED"
    assert cancelled == ["00000000-0000-4000-8000-000000000001"]
    limited = router.route(
        binding=_binding(),
        message=_message(messageId="00000000-0000-4000-8000-000000000012", sequence=2),
    )
    assert limited.code == "SURFACE_MESSAGE_RATE_LIMIT"
