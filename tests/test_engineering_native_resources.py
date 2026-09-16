from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from core.native_application import NativeApplicationConflict
from data_vault.migrations import upgrade_database
from data_vault.native_application_repository import NativeApplicationRepository
from tool_registry.native_application_lifecycle import NativeApplicationLifecycle

spec = importlib.util.spec_from_file_location(
    "native_resources",
    Path(__file__).resolve().parents[1] / "scripts/engineering_native_resources.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Adapter:
    def __init__(self):
        self.alive = True
        self.quit_count = 0

    def inspect(self, session):
        return {
            "alive": self.alive,
            "identity": session["identity"],
            "native_session_id": session["native_session_id"],
            "version": session["version"],
            "healthy": True,
            "modal": False,
            "endpoint_matches": True,
            "document_state_known": True,
            "documents": [],
            "active_operation": False,
        }

    def quit_application(self, session):
        self.quit_count += 1
        self.alive = False
        return {"requested": True}


@pytest.fixture
def bound(tmp_path):
    db = tmp_path / "native.db"
    upgrade_database(db)
    repo = NativeApplicationRepository(str(db))
    adapter = Adapter()
    service = NativeApplicationLifecycle(repo, adapter)
    identity = {
        "pid": 123,
        "creation_time": "2026-09-13T00:00:00Z",
        "executable": "C:/native.exe",
    }
    service.register_session(
        {
            "session_id": "native-session",
            "resource_id": "host/native",
            "app_kind": "native",
            "host": "host",
            "version": "1",
            "ownership": "owned",
            "identity": identity,
            "native_session_id": "native-session",
            "launch_receipt": {
                "ownership_basis": "dedicated_launch",
                "baseline_absent": True,
                "native_session_verified": True,
                "identity": identity,
            },
        },
        trace_id="test",
    )
    proof = {"verified": True, "identity": identity, "session_id": "native-session"}
    binding = module.NativeResourceBinding(
        service,
        ensure_session=lambda case: "native-session",
        verify_binding=lambda case, session: proof,
    )
    controller = module.NativeCaseLeaseController(
        resources={"host/native": binding},
        bindings={"canonical-resource": ["host/native"]},
        owner_id="worker",
    )
    case = {
        "scenario_id": "case-1",
        "attempt_id": "attempt-1",
        "resource_key": "canonical-resource",
    }
    return controller, service, repo, adapter, proof, case


def test_native_controller_holds_one_lease_across_all_canonical_posts(bound):
    controller, _, repo, adapter, _, case = bound
    controller.startup([case])
    handles = controller.before_dispatch(case, {}, "start")
    assert (
        controller.before_dispatch(
            case, {"native_resource_leases": handles}, "decision:checkpoint"
        )
        == handles
    )
    session = repo.get_session("native-session")
    assert session["active_operation"] and session["lease_id"] == handles[0]["lease_id"]
    result = controller.finish_case(
        case,
        {
            "phase": "completed",
            "runtime_status": "completed",
            "native_resource_leases": handles,
        },
        known_terminal=True,
        evidence_reference="canonical-run.json",
    )
    assert result["status"] == "completed" and adapter.quit_count == 1
    assert repo.get_lease(handles[0]["lease_id"])["state"] == "released"


def test_native_controller_unknown_terminal_never_quits_or_releases(bound):
    controller, _, repo, adapter, _, case = bound
    handles = controller.before_dispatch(case, {}, "start")
    result = controller.finish_case(
        case,
        {"phase": "outcome_unknown", "native_resource_leases": handles},
        known_terminal=False,
        evidence_reference="deadline.json",
    )
    assert result["status"] == "cleanup_blocked" and adapter.quit_count == 0
    assert repo.get_lease(handles[0]["lease_id"])["state"] == "quarantined"
    assert controller.startup([case])["sessions"][0]["state"] == "cleanup_blocked"
    with pytest.raises(NativeApplicationConflict, match="restart reconciliation"):
        controller.before_dispatch(
            case, {"native_resource_leases": handles}, "resume:checkpoint"
        )


def test_native_controller_requires_exact_executor_binding(bound):
    controller, _, repo, adapter, proof, case = bound
    proof["identity"] = {**proof["identity"], "creation_time": "reused-pid"}
    with pytest.raises(NativeApplicationConflict, match="not bound"):
        controller.before_dispatch(case, {}, "start")
    assert repo.get_session("native-session")["lease_id"] is None
    assert adapter.quit_count == 0


def test_prior_unknown_resource_is_rejected_before_new_native_launch(bound):
    controller, service, _, _, _, case = bound
    lease = service.acquire(
        "native-session",
        owner_id="prior-worker",
        case_id="prior-case",
        attempt="prior-attempt",
        trace_id="prior",
    )
    service.begin_operation(
        "native-session", lease["lease_id"], "prior-operation", trace_id="prior"
    )
    calls = []
    controller.resources["host/native"].ensure_session = lambda case: calls.append(
        "launch"
    )
    with pytest.raises(NativeApplicationConflict, match="before launch"):
        controller.before_dispatch(case, {}, "start")
    assert calls == []
