"""Optional campaign resource leases; canonical execution stays in Wright.

Bindings are injected by a selected-host launch wrapper. This module never
selects a provider from a template ID, fabricates document ownership, or imports
arbitrary adapter code from a manifest. A provider/session binding proof is
required before dispatching a workflow against a managed resource.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence

from core.native_application import NativeApplicationConflict
from tool_registry.native_application_lifecycle import (
    NativeApplicationLifecycle,
    same_process,
)


class NativeResourceBinding:
    def __init__(
        self,
        lifecycle: NativeApplicationLifecycle,
        *,
        ensure_session: Callable[[dict], str],
        verify_binding: Callable[[dict, dict], dict],
        capture_documents: Callable[[dict, dict, dict], Sequence[dict]] | None = None,
    ):
        self.lifecycle = lifecycle
        self.ensure_session = ensure_session
        self.verify_binding = verify_binding
        self.capture_documents = capture_documents


class NativeCaseLeaseController:
    def __init__(
        self,
        *,
        resources: Mapping[str, NativeResourceBinding],
        bindings: Mapping[str, Sequence[str]],
        owner_id: str,
    ):
        if not owner_id:
            raise ValueError("Native lease owner identity is required")
        self.resources = dict(resources)
        self.bindings = {
            key: tuple(sorted(set(value))) for key, value in bindings.items()
        }
        if any(
            resource not in self.resources
            for values in self.bindings.values()
            for resource in values
        ):
            raise ValueError(
                "Native resource binding references an unavailable adapter"
            )
        self.owner_id = owner_id
        self.handles: dict[tuple[str, str], list[dict]] = {}

    @staticmethod
    def _key(case):
        return case["scenario_id"], case["attempt_id"]

    @staticmethod
    def _trace(case):
        return (
            "campaign-native-"
            + hashlib.sha256(
                (case["scenario_id"] + "/" + case["attempt_id"]).encode()
            ).hexdigest()[:24]
        )

    def _resource_ids(self, case):
        return self.bindings.get(
            case.get("resource_key", "shared-engineering-host"), ()
        )

    def startup(self, cases):
        observations = []
        needed = {resource for case in cases for resource in self._resource_ids(case)}
        for resource_id in sorted(needed):
            service = self.resources[resource_id].lifecycle
            for session in service.repository.list_sessions():
                if (
                    session["resource_id"] != resource_id
                    or session["state"] == "exited"
                ):
                    continue
                observed = service.reconcile(
                    session["session_id"], trace_id="campaign-native-startup"
                )
                observations.append(
                    {
                        "resource_id": resource_id,
                        "session_id": session["session_id"],
                        "state": observed["state"],
                        "blocker": observed.get("blocker"),
                    }
                )
        return {"sessions": observations}

    def before_dispatch(self, case, state, operation):
        key, trace_id = self._key(case), self._trace(case)
        if key in self.handles:
            return list(self.handles[key])
        if state.get("native_resource_leases"):
            raise NativeApplicationConflict(
                "Persisted native case leases require explicit restart reconciliation"
            )
        handles = []
        created_sessions = []
        try:
            for resource_id in self._resource_ids(case):
                binding = self.resources[resource_id]
                service = binding.lifecycle
                existing = service.repository.list_sessions()
                for candidate in existing:
                    if candidate["resource_id"] == resource_id and (
                        candidate.get("lease_id")
                        or candidate.get("active_operation")
                        or candidate.get("cleanup_in_progress")
                        or candidate["state"] == "cleanup_blocked"
                    ):
                        raise NativeApplicationConflict(
                            "Native resource is retained by prior work; reconcile before launch"
                        )
                session_id = binding.ensure_session(case)
                session = service.repository.get_session(session_id)
                if session["resource_id"] != resource_id:
                    raise NativeApplicationConflict(
                        "Native session does not match configured resource"
                    )
                if session_id not in {item["session_id"] for item in existing}:
                    created_sessions.append((resource_id, session_id))
                proof = binding.verify_binding(case, session)
                if (
                    proof.get("verified") is not True
                    or proof.get("session_id") != session_id
                    or not same_process(session["identity"], proof.get("identity"))
                ):
                    raise NativeApplicationConflict(
                        "Canonical provider is not bound to the managed native session"
                    )
                lease = service.acquire(
                    session_id,
                    owner_id=self.owner_id,
                    case_id=case["scenario_id"],
                    attempt=case["attempt_id"],
                    trace_id=trace_id,
                )
                handle = {
                    "resource_id": resource_id,
                    "session_id": session_id,
                    "lease_id": lease["lease_id"],
                    "operation_id": trace_id + ":workflow",
                    "binding_proof": proof,
                }
                handles.append(handle)
                service.begin_operation(
                    session_id,
                    lease["lease_id"],
                    handle["operation_id"],
                    trace_id=trace_id,
                )
            self.handles[key] = handles
            return list(handles)
        except BaseException:
            # No POST was made. Release only resources acquired by this call;
            # an existing conflicting resource remains untouched.
            for handle in reversed(handles):
                service = self.resources[handle["resource_id"]].lifecycle
                session = service.repository.get_session(handle["session_id"])
                if session.get("active_operation"):
                    service.finish_operation(
                        handle["session_id"],
                        handle["operation_id"],
                        outcome="failed_known",
                        evidence_reference="native-pre-dispatch-rejection",
                        trace_id=trace_id,
                    )
                service.cleanup(
                    handle["session_id"],
                    handle["operation_id"] + ":acquire-rollback",
                    reason="pre_dispatch_rejected",
                    trace_id=trace_id,
                )
            acquired_sessions = {handle["session_id"] for handle in handles}
            for resource_id, session_id in reversed(created_sessions):
                if session_id not in acquired_sessions:
                    self.resources[resource_id].lifecycle.cleanup(
                        session_id,
                        trace_id + ":binding-rejected",
                        reason="native_binding_rejected",
                        trace_id=trace_id,
                    )
            raise

    def finish_case(
        self, case, state, *, known_terminal: bool, evidence_reference: str
    ):
        key, trace_id = self._key(case), self._trace(case)
        handles = self.handles.pop(key, None) or state.get("native_resource_leases", [])
        receipts = []
        for handle in reversed(handles):
            binding = self.resources[handle["resource_id"]]
            service, session_id = binding.lifecycle, handle["session_id"]
            session = service.repository.get_session(session_id)
            try:
                if known_terminal:
                    # An HTTP terminal record alone cannot prove a native
                    # mutation stopped. Match its live native session as well.
                    service.observe(session_id)
                    if binding.capture_documents:
                        for document in binding.capture_documents(case, state, session):
                            service.register_document(
                                session_id,
                                handle["lease_id"],
                                document,
                                trace_id=trace_id,
                            )
                if session.get("active_operation"):
                    service.finish_operation(
                        session_id,
                        handle["operation_id"],
                        outcome=(
                            "succeeded"
                            if state.get("runtime_status") == "completed"
                            else "failed_known"
                        )
                        if known_terminal
                        else "unknown",
                        evidence_reference=evidence_reference,
                        trace_id=trace_id,
                    )
                receipt = service.cleanup(
                    session_id,
                    handle["operation_id"] + ":case-final",
                    reason=state.get("phase", "runner_interrupted"),
                    trace_id=trace_id,
                )
            except BaseException as exc:
                latest = service.repository.get_session(session_id)
                if latest.get("active_operation"):
                    service.finish_operation(
                        session_id,
                        handle["operation_id"],
                        outcome="unknown",
                        evidence_reference=evidence_reference,
                        trace_id=trace_id,
                    )
                receipt = service.cleanup(
                    session_id,
                    handle["operation_id"] + ":case-final",
                    reason="native_terminal_unverified",
                    trace_id=trace_id,
                )
                receipt = {**receipt, "observation_error_type": type(exc).__name__}
            receipts.append({"resource_id": handle["resource_id"], **receipt})
        return {
            "status": "cleanup_blocked"
            if any(receipt["status"] != "completed" for receipt in receipts)
            else "completed",
            "resources": receipts,
        }
