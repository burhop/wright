"""Immutable preparation/presentation metadata supplements existing run authority."""

from concurrent.futures import ThreadPoolExecutor
import json

import pytest

from core.process_interactions import (
    InputSnapshot,
    InteractionResponse,
    ProcessRef,
    StartReceipt,
    ValueBinding,
)
from core.process_interfaces import (
    AuthoringJob,
    BuildReport,
    CodingRole,
    InterfaceManifest,
    InterfaceRevision,
    ProcessUI,
    RoleResolution,
)
from core.process_validation import canonical_digest
from data_vault.migrations import MIGRATIONS, database_status, upgrade_database
from data_vault.process_input_repository import (
    ProcessInputRepository,
    ProcessRecordConflict,
)
from data_vault.process_interface_repository import ProcessInterfaceRepository
from data_vault.state_store import connect_state_db
from data_vault.workflow_continuation_repository import (
    WorkflowContinuationCheckpoint,
    WorkflowContinuationRepository,
)

NOW = "2026-09-30T12:00:00Z"
LATER = "2026-09-30T12:01:00Z"
DIGEST = "a" * 64


def process(workspace="workspace"):
    return ProcessRef(
        workspace_id=workspace,
        source_path="workflows/analysis.wflow",
        source_digest=DIGEST,
    )


def inputs(identifier="inputs", value=100):
    return InputSnapshot.create(
        snapshot_id=identifier,
        process=process(),
        created_at=NOW,
        bindings=(ValueBinding(input_id="width", value=value),),
    )


def receipt(snapshot, run_id="run", **changes):
    return StartReceipt(
        **{
            "principal_id": "user",
            "process": snapshot.process,
            "request_id": "start-one",
            "payload_digest": canonical_digest(
                {"process": snapshot.process, "bindings": snapshot.bindings}
            ),
            "input_snapshot_id": snapshot.snapshot_id,
            "input_digest": snapshot.digest,
            "run_id": run_id,
            "created_at": NOW,
            **changes,
        }
    )


def response(**changes):
    return InteractionResponse.create(
        **{
            "response_id": "response",
            "workspace_id": "workspace",
            "run_id": "run",
            "checkpoint_id": "checkpoint",
            "subject_digest": DIGEST,
            "schema_digest": DIGEST,
            "input_digest": DIGEST,
            "value": {"selection": "a"},
            "actor": "user",
            "reason": "Select candidate a.",
            "request_id": "respond-one",
            "created_at": NOW,
            **changes,
        }
    )


def role():
    return RoleResolution(
        profile=CodingRole(instructions_version="1", instructions_digest=DIGEST),
        adapter="hermes",
        model_reference="configured-default",
        configuration_digest=DIGEST,
        effective_instructions_digest=DIGEST,
    )


def job(**changes):
    return AuthoringJob(
        **{
            "job_id": "job",
            "request_id": "generate-one",
            "request_digest": DIGEST,
            "process": process(),
            "role_resolution": role(),
            "state": "queued",
            "created_at": NOW,
            "updated_at": NOW,
            **changes,
        }
    )


def ui():
    return ProcessUI(
        ui_id="ui", process=process(), title="Analysis", created_at=NOW, updated_at=NOW
    )


def revision(identifier="revision", parent=None):
    manifest = InterfaceManifest(
        ui_id="ui",
        revision_id=identifier,
        parent_revision=parent,
        title="Analysis",
        process=process(),
        client_version="0.1.0",
        kit_version="0.1.0",
    )
    build = BuildReport(
        build_id="build-" + identifier,
        source_digest=DIGEST,
        manifest_digest=canonical_digest(manifest),
        toolchain_digest=DIGEST,
        bundle_digest=DIGEST,
        state="built",
        created_at=NOW,
    )
    return InterfaceRevision(
        manifest=manifest,
        source_digest=DIGEST,
        build=build,
        role_resolution=role(),
        generation_request_digest=DIGEST,
        created_at=NOW,
        previewed_at=NOW,
    )


def test_additive_migration_preserves_v2_checkpoint_and_legacy_run(tmp_path):
    db_path = tmp_path / "old.db"
    upgrade_database(db_path, migrations=MIGRATIONS[:21])
    old = WorkflowContinuationCheckpoint(
        checkpoint_id="old",
        workspace_id="workspace",
        workflow_id="workflow",
        run_id="old-run",
        step_id="review",
        action_kind="local_review",
        subject={"sha256": DIGEST},
        subject_digest=DIGEST,
        state="pending",
        continuation={"version": 2, "cursor": 4},
        actor=None,
        reason=None,
        created_at=1,
        updated_at=1,
        expires_at=None,
        external_action=None,
    )
    existing = WorkflowContinuationRepository(str(db_path))
    existing.create(old)
    historical = tmp_path / "historical-run.json"
    raw = b'{"version":2,"state":"waiting_for_approval","run_id":"old-run"}\n'
    historical.write_bytes(raw)
    with connect_state_db(db_path) as db:
        prior_ledger = [
            dict(row) for row in db.execute("SELECT * FROM wright_schema_migrations")
        ]
    upgraded = upgrade_database(db_path)
    assert upgraded.applied == (
        {"version": 22, "name": "process_working_interfaces"},
        {"version": 23, "name": "process_ui_authoring_provenance"},
    )
    assert existing.get("old") == old
    assert historical.read_bytes() == raw
    with connect_state_db(db_path) as db:
        assert [
            dict(row)
            for row in db.execute(
                "SELECT * FROM wright_schema_migrations WHERE version<=21"
            )
        ] == prior_ledger
        tables = {
            row[0]
            for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "process_runs" not in tables
    assert database_status(db_path).ready


def test_snapshot_is_immutable_scoped_and_read_after_reopen(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInputRepository(path)
    original = repo.put_snapshot(inputs())
    assert repo.put_snapshot(original) == original
    assert ProcessInputRepository(path).get_snapshot("workspace", "inputs") == original
    with pytest.raises(KeyError):
        repo.get_snapshot("other-workspace", "inputs")
    with pytest.raises(ProcessRecordConflict):
        repo.put_snapshot(inputs(value=101))
    with connect_state_db(path) as db:
        with pytest.raises(Exception, match="immutable"):
            db.execute("UPDATE process_input_snapshots SET payload_json='{}'")


def test_existing_083_database_keeps_its_ledger_when_authoring_records_are_added(
    tmp_path,
):
    path = tmp_path / "m2.db"
    upgrade_database(path, migrations=MIGRATIONS[:22])
    with connect_state_db(path) as db:
        prior = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM wright_schema_migrations ORDER BY version"
            )
        ]
    upgraded = upgrade_database(path)
    assert upgraded.applied == (
        {"version": 23, "name": "process_ui_authoring_provenance"},
    )
    with connect_state_db(path) as db:
        assert [
            dict(row)
            for row in db.execute(
                "SELECT * FROM wright_schema_migrations WHERE version<=22 ORDER BY version"
            )
        ] == prior
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='process_ui_authoring_records'"
        ).fetchone()


def test_atomic_start_retry_returns_recorded_identity_and_rejects_conflict(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInputRepository(path)
    snapshot = inputs()
    first, created = repo.reserve_start(snapshot, receipt(snapshot))
    assert created
    retry_inputs = inputs(identifier="retry-inputs")
    retried, created = ProcessInputRepository(path).reserve_start(
        retry_inputs, receipt(retry_inputs, "retry-run")
    )
    assert not created and retried == first
    with pytest.raises(KeyError):
        repo.get_snapshot("workspace", "retry-inputs")
    assert repo.start_receipt("user", process(), "start-one") == first
    changed = inputs(identifier="changed", value=101)
    with pytest.raises(ProcessRecordConflict):
        repo.reserve_start(changed, receipt(changed))
    with pytest.raises(KeyError):
        repo.start_receipt("other-user", process(), "start-one")


def test_start_rejects_snapshot_identity_mismatch_without_partial_writes(tmp_path):
    repo = ProcessInputRepository(tmp_path / "state.db")
    snapshot = inputs()
    with pytest.raises(ProcessRecordConflict):
        repo.reserve_start(snapshot, receipt(snapshot, input_digest="b" * 64))
    with pytest.raises(KeyError):
        repo.get_snapshot("workspace", "inputs")


def test_concurrent_starts_allocate_once(tmp_path):
    repo = ProcessInputRepository(tmp_path / "state.db")

    def reserve(index):
        snap = inputs(identifier=f"inputs-{index}")
        return repo.reserve_start(snap, receipt(snap, f"run-{index}"))

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(reserve, range(4)))
    assert sum(created for _, created in results) == 1
    assert len({item.run_id for item, _ in results}) == 1


def test_response_retries_are_exact_and_one_checkpoint_has_one_response(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInputRepository(path)
    original, created = repo.put_response(response())
    assert created
    retried, created = ProcessInputRepository(path).put_response(
        response(response_id="retry", created_at=LATER)
    )
    assert not created and retried == original
    assert repo.get_response("workspace", "response") == original
    assert not original.integration_test
    with pytest.raises(KeyError):
        repo.get_response("other", "response")
    for changed in (
        {"value": {"selection": "b"}},
        {"subject_digest": "b" * 64},
        {"actor": "other"},
        {"integration_test": True},
        {"request_id": "another"},
    ):
        with pytest.raises(ProcessRecordConflict):
            repo.put_response(response(response_id="new", **changed))


def test_saved_revisions_are_immutable_scoped_and_activation_is_cas(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInterfaceRepository(path)
    repo.create_ui(ui())
    first = repo.save_revision("workspace", revision())
    assert repo.save_revision("workspace", first) == first
    assert repo.get_ui("workspace", "ui").active_revision is None
    active = repo.activate(
        "workspace", "ui", "revision", expected_revision=None, updated_at=LATER
    )
    assert active.active_revision == "revision"
    second = repo.save_revision("workspace", revision("second", "revision"))
    with pytest.raises(ProcessRecordConflict):
        repo.activate(
            "workspace", "ui", "second", expected_revision=None, updated_at=LATER
        )
    repo.activate(
        "workspace", "ui", "second", expected_revision="revision", updated_at=LATER
    )
    rollback = repo.activate(
        "workspace", "ui", "revision", expected_revision="second", updated_at=LATER
    )
    assert rollback.active_revision == "revision"
    assert (
        ProcessInterfaceRepository(path).get_revision("workspace", "ui", "second")
        == second
    )
    assert len(repo.list_revisions("workspace", "ui")) == 2
    with pytest.raises(KeyError):
        repo.get_revision("other", "ui", "revision")
    changed = first.model_copy(update={"generation_request_digest": "b" * 64})
    with pytest.raises(ProcessRecordConflict):
        repo.save_revision("workspace", changed)


def test_revision_cannot_cross_ui_process_or_parent_scope(tmp_path):
    repo = ProcessInterfaceRepository(tmp_path / "state.db")
    repo.create_ui(ui())
    with pytest.raises(ProcessRecordConflict):
        repo.save_revision("other", revision())
    with pytest.raises(ProcessRecordConflict):
        repo.save_revision("workspace", revision(parent="missing"))
    candidate = revision()
    foreign = candidate.manifest.model_copy(update={"process": process("other")})
    candidate = candidate.model_copy(
        update={
            "manifest": foreign,
            "build": candidate.build.model_copy(
                update={"manifest_digest": canonical_digest(foreign)}
            ),
        }
    )
    with pytest.raises(ProcessRecordConflict):
        repo.save_revision("workspace", candidate)


def test_jobs_are_durable_idempotent_and_compare_and_swap(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInterfaceRepository(path)
    original, created = repo.create_job(job())
    assert created
    retry, created = repo.create_job(
        job(job_id="retry", created_at=LATER, updated_at=LATER)
    )
    assert not created and retry == original
    with pytest.raises(ProcessRecordConflict):
        repo.create_job(job(job_id="conflict", request_digest="b" * 64))
    resolved = original.model_copy(update={"state": "resolving", "updated_at": LATER})
    assert (
        repo.update_job(resolved, expected_digest=canonical_digest(original))
        == resolved
    )
    assert ProcessInterfaceRepository(path).get_job("workspace", "job") == resolved
    with pytest.raises(ProcessRecordConflict):
        repo.update_job(resolved, expected_digest=canonical_digest(original))
    with pytest.raises(KeyError):
        repo.get_job("other", "job")
    with pytest.raises(ProcessRecordConflict):
        repo.update_job(
            resolved.model_copy(update={"state": "saved", "revision_id": "not-built"}),
            expected_digest=canonical_digest(resolved),
        )
    with pytest.raises(ProcessRecordConflict):
        repo.update_job(
            resolved.model_copy(update={"process": process("other")}),
            expected_digest=canonical_digest(resolved),
        )


def test_raw_saved_evidence_cannot_be_deleted(tmp_path):
    path = tmp_path / "state.db"
    repo = ProcessInterfaceRepository(path)
    repo.create_ui(ui())
    repo.save_revision("workspace", revision())
    with connect_state_db(path) as db:
        with pytest.raises(Exception, match="immutable"):
            db.execute("DELETE FROM process_ui_revisions")
        saved = db.execute("SELECT payload_json FROM process_ui_revisions").fetchone()[
            0
        ]
        assert json.loads(saved)["build"]["bundle_digest"] == DIGEST


def test_job_repairs_are_bounded_and_terminal_jobs_cannot_restart(tmp_path):
    repo = ProcessInterfaceRepository(tmp_path / "state.db")
    current, _ = repo.create_job(job())

    def move(state, attempt=None, **fields):
        nonlocal current
        changes = {"state": state, "updated_at": LATER, **fields}
        if attempt is not None:
            changes["repair_attempt"] = attempt
        candidate = current.model_copy(update=changes)
        current = repo.update_job(candidate, expected_digest=canonical_digest(current))

    for state in ("resolving", "generating", "validating"):
        move(state)
    with pytest.raises(ProcessRecordConflict):
        move("generating")
    move("generating", 1)
    move("validating")
    move("building")
    move("generating", 2)
    move("cancelled")
    with pytest.raises(ProcessRecordConflict):
        move("generating", 2)


def test_concurrent_response_retains_one_subject_decision(tmp_path):
    repo = ProcessInputRepository(tmp_path / "state.db")

    def submit(index):
        try:
            _, created = repo.put_response(
                response(
                    response_id=f"response-{index}", value={"selection": str(index)}
                )
            )
            return created
        except ProcessRecordConflict:
            return False

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(submit, range(4)))
    assert sum(outcomes) == 1
