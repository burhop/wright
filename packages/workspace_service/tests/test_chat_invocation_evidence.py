from types import SimpleNamespace

import pytest

from workspace_service.chat_invocation_evidence import ChatInvocationRecorder


def application(root):
    return SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {
                    "workspace_id": "workspace",
                    "local_path": str(root),
                }
                if session == "session"
                else None
            )
        ),
        ensure_workspace_path_safe=lambda path: path,
    )


def capture(session="session"):
    return {
        "schema_version": "wright.workflow-invocation/1",
        "operation": "hermes-chat-http",
        "capture_scope": "primary_adapter_request",
        "request_fields": {"session_id": session, "api_key": "private-key"},
    }


def recorder(app, root, request_id="turn"):
    return ChatInvocationRecorder(
        app,
        workspace_id="workspace",
        workspace_dir=str(root),
        session_id="session",
        request_id=request_id,
    )


@pytest.mark.asyncio
async def test_actual_chat_sidecar_reopens_confined_and_immutable(tmp_path):
    app = application(tmp_path)
    record = recorder(app, tmp_path)
    await record.observe(capture())
    receipt = record.receipts[0]
    reopened = recorder(application(tmp_path), tmp_path)
    persisted = reopened.read(receipt)
    assert persisted["scope"] == {
        "workspace_id": "workspace",
        "session_id": "session",
        "request_id": "turn",
    }
    assert "private-key" not in str(persisted)
    with pytest.raises(FileExistsError):
        await reopened.observe(capture())
    with pytest.raises(ValueError, match="outside this request"):
        recorder(app, tmp_path, "another-turn").read(receipt)
    with pytest.raises(ValueError, match="Invalid scoped"):
        await record.observe(capture("another-session"))


@pytest.mark.asyncio
async def test_session_rebinding_cannot_write_into_previous_scope(tmp_path):
    app = application(tmp_path)
    record = recorder(app, tmp_path)
    app.lifecycle.get_by_session = lambda session: {
        "workspace_id": "another",
        "local_path": str(tmp_path),
    }
    with pytest.raises(ValueError, match="outside"):
        await record.observe(capture())
    assert not (tmp_path / ".wright").exists()
