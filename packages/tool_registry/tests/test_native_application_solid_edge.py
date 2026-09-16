from __future__ import annotations

from copy import deepcopy
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from tool_registry.native_application_lifecycle import same_process
from tool_registry.native_application_solid_edge import (
    SolidEdgeLifecycleError,
    SolidEdgeComChannel,
    SolidEdgeNativeApplicationAdapter,
)
from tool_registry.native_application_solid_edge_host import SolidEdgeComHost


IDENTITY = {
    "pid": 101,
    "creation_time": "2026-09-13T01:00:00+00:00",
    "executable": "C:/SolidEdge/Edge.exe",
}


def session(ownership="owned"):
    return {
        "identity": dict(IDENTITY),
        "ownership": ownership,
        "native_session_id": "se-101",
        "launch_receipt": {"identity": dict(IDENTITY), "native_session_verified": True},
        "policy": {
            "startup_timeout_seconds": 1,
            "document_close_timeout_seconds": 1,
            "quit_timeout_seconds": 0.01,
        },
    }


class Document:
    def __init__(self, collection, path, *, dirty=False, close_works=True):
        self.collection = collection
        self.FullName = str(path)
        self.Dirty = dirty
        self.close_works = close_works
        self.saved = []
        self.closed = []

    def SaveAs(self, path):
        Path(path).write_bytes(b"native-recovery")
        self.saved.append(path)
        self.FullName = path
        self.Dirty = False

    def Close(self, save):
        self.closed.append(save)
        if self.close_works:
            self.collection.values.remove(self)


class Documents:
    def __init__(self):
        self.values = []

    @property
    def Count(self):
        return len(self.values)

    def Item(self, index):
        return self.values[index - 1]


def environment():
    docs = Documents()
    quit_calls = []
    app = SimpleNamespace(
        ProcessID=101,
        Version="226.0",
        Documents=docs,
        DoIdle=lambda: None,
        Quit=lambda: quit_calls.append(True),
    )
    host = SolidEdgeComHost(
        get_application=lambda: app,
        identity_reader=lambda _: dict(IDENTITY),
        same_process=same_process,
        native_identity=lambda doc: id(doc),
        modal_reader=lambda _: False,
    )
    return host, app, quit_calls


def owned(row):
    return {
        **row,
        "ownership": "owned",
        "preexisted": False,
        "creation_evidence": "diagnostic-created-doc",
    }


def test_opaque_document_identity_survives_save_as_and_user_document_is_preserved(
    tmp_path,
):
    host, app, _ = environment()
    user = Document(app.Documents, tmp_path / "user.psm", dirty=True)
    created = Document(app.Documents, tmp_path / "campaign.psm", dirty=True)
    app.Documents.values = [user, created]
    row = host.handle("inspect", session())["documents"][1]
    managed = owned(row) | {"recovery_path": str(tmp_path / "recovery.psm")}
    receipt = host.handle("save", session(), managed)
    assert receipt["saved"] and len(receipt["sha256"]) == 64
    assert (
        host.handle("inspect", session())["documents"][1]["native_id"]
        == row["native_id"]
    )
    managed["current_path"] = receipt["path"]
    assert host.handle("close", session(), managed)["closed"]
    assert app.Documents.values == [user]
    assert user.Dirty and not user.closed and not user.saved


def test_dirty_document_close_and_overwrite_are_refused(tmp_path):
    host, app, _ = environment()
    doc = Document(app.Documents, tmp_path / "owned.psm", dirty=True)
    app.Documents.values = [doc]
    managed = owned(host.handle("inspect", session())["documents"][0])
    with pytest.raises(RuntimeError, match="Dirty"):
        host.handle("close", session(), managed)
    recovery = tmp_path / "existing.psm"
    recovery.write_bytes(b"prior-evidence")
    with pytest.raises(RuntimeError, match="new absolute"):
        host.handle("save", session(), managed | {"recovery_path": str(recovery)})
    assert not doc.closed and not doc.saved
    assert recovery.read_bytes() == b"prior-evidence"


def test_document_still_open_cannot_get_new_id_and_claim_closed(tmp_path):
    host, app, _ = environment()
    doc = Document(app.Documents, tmp_path / "owned.psm", close_works=False)
    app.Documents.values = [doc]
    managed = owned(host.handle("inspect", session())["documents"][0])
    with pytest.raises(RuntimeError, match="remained open"):
        host.handle("close", session(), managed)


def test_borrowed_app_and_untracked_documents_prevent_quit(tmp_path):
    host, app, calls = environment()
    with pytest.raises(RuntimeError, match="owned application"):
        host.handle("quit", session("borrowed"))
    app.Documents.values = [Document(app.Documents, tmp_path / "untracked.psm")]
    with pytest.raises(RuntimeError, match="no open documents"):
        host.handle("quit", session())
    assert calls == []


def test_reopened_same_path_is_a_different_native_document(tmp_path):
    host, app, _ = environment()
    path = tmp_path / "same.psm"
    original = Document(app.Documents, path)
    app.Documents.values = [original]
    managed = owned(host.handle("inspect", session())["documents"][0])
    app.Documents.values = [Document(app.Documents, path)]
    with pytest.raises(RuntimeError, match="identity/path changed"):
        host.handle("close", session(), managed)
    assert not app.Documents.values[0].closed


def test_rot_process_mismatch_rejects_all_native_actions():
    host, app, calls = environment()
    app.ProcessID = 999
    with pytest.raises(RuntimeError, match="different process"):
        host.handle("quit", session())
    assert calls == []


def test_adapter_pid_reuse_prevents_com_request():
    channel = SimpleNamespace(
        request=lambda *args: pytest.fail("COM must not be called")
    )
    reused = deepcopy(IDENTITY)
    reused["creation_time"] = "2026-09-14T01:00:00+00:00"
    adapter = SolidEdgeNativeApplicationAdapter(
        channel=channel, identity_reader=lambda _: reused
    )
    assert adapter.inspect(session())["endpoint_matches"] is False
    with pytest.raises(SolidEdgeLifecycleError, match="PID identity changed"):
        adapter.quit_application(session())


def test_adapter_preserves_borrowed_app_without_contacting_com():
    channel = SimpleNamespace(
        request=lambda *args: pytest.fail("COM must not be called")
    )
    adapter = SolidEdgeNativeApplicationAdapter(
        channel=channel, identity_reader=lambda _: dict(IDENTITY)
    )
    with pytest.raises(SolidEdgeLifecycleError, match="cannot be quit"):
        adapter.quit_application(session("borrowed"))


def test_adapter_uses_persisted_bounds_and_requires_new_approved_recovery_file(
    tmp_path,
):
    calls = []
    channel = SimpleNamespace(
        request=lambda *args: calls.append(args) or {"saved": True}
    )
    adapter = SolidEdgeNativeApplicationAdapter(
        channel=channel,
        identity_reader=lambda _: dict(IDENTITY),
        allowed_roots=(tmp_path,),
    )
    managed = owned({"native_id": "doc-1", "path": None}) | {
        "recovery_path": str(tmp_path / "new.psm")
    }
    adapter.save_document(session(), managed)
    assert calls[0][0] == "save" and calls[0][2] == 1
    outside = tmp_path.parent / "outside.psm"
    with pytest.raises(SolidEdgeLifecycleError, match="outside"):
        adapter.save_document(session(), managed | {"recovery_path": str(outside)})
    assert len(calls) == 1


def test_adapter_double_quit_after_verified_exit_does_not_contact_com():
    channel = SimpleNamespace(
        request=lambda *args: pytest.fail("COM must not be called")
    )
    adapter = SolidEdgeNativeApplicationAdapter(
        channel=channel, identity_reader=lambda _: None
    )
    assert adapter.quit_application(session())["already_exited"]
    assert adapter.inspect(session())["alive"] is False


def test_timed_out_com_call_quarantines_channel_and_never_sends_a_second_mutation():
    channel = SolidEdgeComChannel()
    stream = StringIO()
    channel.process = SimpleNamespace(stdin=stream)
    with pytest.raises(SolidEdgeLifecycleError, match="unknown"):
        channel.request("close", {"session": session()}, timeout=0.001)
    first_request = stream.getvalue()
    with pytest.raises(SolidEdgeLifecycleError, match="quarantined"):
        channel.request("quit", {"session": session()}, timeout=0.001)
    channel.release()
    assert stream.getvalue() == first_request


def test_application_window_pid_evidence_can_replace_unavailable_processid_dispatch():
    host, app, _ = environment()
    del app.ProcessID
    host.application_pid_reader = lambda _: 101
    assert host.handle("inspect", session())["endpoint_matches"]
    host.application_pid_reader = lambda _: 999
    with pytest.raises(RuntimeError, match="different process"):
        host.handle("inspect", session())


def test_cold_rot_registration_without_window_interface_is_unready_not_owned():
    host, _, _ = environment()

    def not_ready(_):
        raise AttributeError("SolidEdge.Application.hWnd")

    host.application_pid_reader = not_ready
    observation = host.handle("inspect", session())
    assert observation["endpoint_matches"] is False and observation["healthy"] is False
    with pytest.raises(RuntimeError, match="not registered"):
        host.handle("quit", session())
