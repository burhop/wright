from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.surfaces.runtime_reconciliation import (
    PersistedRuntime,
    ReconciliationEvidence,
    RuntimeReconciler,
)


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]

NOW = datetime(2026, 7, 30, tzinfo=UTC)


def _record(**changes) -> PersistedRuntime:
    value = PersistedRuntime(
        runtime_id="runtime-1",
        instance_id="instance-1",
        workspace_id="workspace-1",
        generation=3,
        state="ready",
        ownership="launched",
        platform="posix",
        authority_expires_at=NOW - timedelta(seconds=1),
    )
    return replace(value, **changes)


class Store:
    def __init__(self, records) -> None:
        self.records = {item.runtime_id: item for item in records}
        self.transitions = []

    def list_nonterminal(self):
        return tuple(self.records.values())

    def transition(self, record, *, state, diagnostic_code, fresh_authority=False):
        updated = replace(
            record,
            state=state,
            revision=record.revision + 1,
            authority_expires_at=(NOW + timedelta(minutes=5) if fresh_authority else None),
        )
        self.records[record.runtime_id] = updated
        self.transitions.append((record.runtime_id, state, diagnostic_code, fresh_authority))
        return updated


class Evidence:
    def __init__(self, values) -> None:
        self.values = values

    async def inspect(self, record):
        return self.values[record.runtime_id]


class Authority:
    def __init__(self) -> None:
        self.revoked = []
        self.issued = []

    def revoke(self, record):
        self.revoked.append(record.runtime_id)

    def issue(self, record, evidence):
        self.issued.append((record.runtime_id, evidence.listener_port))


class Stopper:
    def __init__(self, complete=True) -> None:
        self.calls = []
        self.complete = complete

    async def stop_stale_owned(self, record, *, deadline):
        self.calls.append(record.runtime_id)
        return self.complete


def _evidence(**changes):
    value = ReconciliationEvidence(
        classification="exact",
        generation=3,
        pid=123,
        creation_time=55.0,
        containment_id="pgid:123",
        executable_matches=True,
        listener_address="127.0.0.1",
        listener_port=43123,
        listener_owned=True,
    )
    return replace(value, **changes)


async def test_valid_runtime_gets_fresh_authority_only_after_full_evidence() -> None:
    store = Store([_record()])
    authority = Authority()
    stopper = Stopper()
    results = await RuntimeReconciler(
        store=store,
        evidence=Evidence({"runtime-1": _evidence()}),
        authority=authority,
        stopper=stopper,
        workspace_valid=lambda _record: True,
        source_valid=lambda _record: True,
        clock=lambda: NOW,
    ).reconcile()

    assert results[0].state == "ready"
    assert results[0].fresh_authority is True
    assert authority.revoked == ["runtime-1"]
    assert authority.issued == [("runtime-1", 43123)]
    assert stopper.calls == []


async def test_stale_owned_tree_is_stopped_but_unprovable_tree_is_never_touched() -> None:
    stale = _record(runtime_id="stale", instance_id="stale-instance")
    unknown = _record(runtime_id="unknown", instance_id="unknown-instance")
    store = Store([stale, unknown])
    stopper = Stopper()
    results = await RuntimeReconciler(
        store=store,
        evidence=Evidence(
            {
                "stale": _evidence(classification="stale-owned"),
                "unknown": _evidence(classification="unprovable"),
            }
        ),
        authority=Authority(),
        stopper=stopper,
        workspace_valid=lambda _record: True,
        source_valid=lambda _record: True,
        clock=lambda: NOW,
    ).reconcile()

    assert {item.runtime_id: item.state for item in results} == {
        "stale": "stopped",
        "unknown": "failed",
    }
    assert stopper.calls == ["stale"]


@pytest.mark.parametrize(
    ("evidence", "code"),
    [
        (_evidence(generation=2), "SURFACE_RECONCILE_GENERATION_MISMATCH"),
        (
            _evidence(listener_owned=False),
            "SURFACE_RECONCILE_ENDPOINT_OCCUPIED",
        ),
        (
            _evidence(containment_id=None),
            "SURFACE_RECONCILE_OWNERSHIP_UNPROVABLE",
        ),
    ],
)
async def test_mismatch_occupied_port_and_missing_containment_fail_without_kill(
    evidence, code
) -> None:
    store = Store([_record()])
    stopper = Stopper()
    authority = Authority()
    result = (
        await RuntimeReconciler(
            store=store,
            evidence=Evidence({"runtime-1": evidence}),
            authority=authority,
            stopper=stopper,
            workspace_valid=lambda _record: True,
            source_valid=lambda _record: True,
            clock=lambda: NOW,
        ).reconcile()
    )[0]
    assert result.state == "failed"
    assert result.diagnostic_code == code
    assert stopper.calls == []
    assert authority.issued == []


async def test_expired_authority_is_never_extended_when_workspace_is_invalid() -> None:
    store = Store([_record(authority_expires_at=NOW - timedelta(hours=1))])
    authority = Authority()
    result = (
        await RuntimeReconciler(
            store=store,
            evidence=Evidence({"runtime-1": _evidence()}),
            authority=authority,
            stopper=Stopper(),
            workspace_valid=lambda _record: False,
            source_valid=lambda _record: True,
            clock=lambda: NOW,
        ).reconcile()
    )[0]
    assert result.state == "failed"
    assert result.fresh_authority is False
    assert authority.revoked == ["runtime-1"]
    assert authority.issued == []
