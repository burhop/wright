from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from scripts.program_status import publisher
from scripts.program_status.publisher import (
    ProgramStatusPublishError,
    ProgramStatusPublishRequest,
    publish_program_status,
    watch_program_status,
)


REPOSITORY = Path(__file__).resolve().parents[2]


def request(data_root: Path, source: str = "HEAD") -> ProgramStatusPublishRequest:
    return ProgramStatusPublishRequest(REPOSITORY, source, data_root)


def canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def test_publishes_exact_dashboard_and_deterministic_identity(tmp_path: Path) -> None:
    first = publish_program_status(request(tmp_path))
    installed = (tmp_path / "current.json").read_bytes()
    bundle = json.loads(installed)

    dashboard_raw = publisher._git_blob(
        REPOSITORY, first.source_commit, publisher.DASHBOARD_PATH
    )
    dashboard = json.loads(dashboard_raw)
    assert bundle["dashboard"] == dashboard
    assert (
        bundle["source"]["snapshot_raw_sha256"]
        == hashlib.sha256(dashboard_raw).hexdigest()
    )
    assert bundle["source"]["commit"] == first.source_commit
    assert bundle["source"]["tree"] == first.source_tree
    assert bundle["source"]["program_tree"] == first.program_tree
    assert bundle["supplement"]["governance"]["limits"] == {
        "wip_max": 1,
        "repair_max": 2,
        "push_max": 2,
    }
    assert bundle["supplement"]["use_cases"]["process_100"]["benchmark_qualified"] == 0
    histories = {series["id"]: series for series in bundle["supplement"]["history"]}
    assert histories["feature_tasks"]["availability"] == "available"
    expected_completed, expected_total = publisher._task_counts(
        publisher._git_blob(
            REPOSITORY,
            first.source_commit,
            "specs/077-browser-program-status/tasks.md",
        )
    )
    assert histories["feature_tasks"]["observations"][-1]["value"] == expected_completed
    assert (
        histories["feature_tasks"]["observations"][-1]["denominator"] == expected_total
    )
    assert histories["benchmark_qualified"]["observations"][-1]["value"] == 0
    assert histories["benchmark_qualified"]["observations"][-1]["denominator"] == 100
    for observation in histories["feature_tasks"]["observations"]:
        assert len(observation["commit"]) == 40
        assert observation["observed_at"]
        assert observation["evidence"]
        assert isinstance(observation["value"], int)
        assert isinstance(observation["denominator"], int)
    evidence_index = bundle["supplement"]["evidence_index"]
    for series in histories.values():
        for observation in series["observations"]:
            for reference in observation["evidence"]:
                matches = [
                    detail
                    for detail in evidence_index
                    if all(detail[key] == reference[key] for key in reference)
                ]
                assert len(matches) == 1
                assert matches[0]["availability"] == "identity_only"
    assert first.changed is True

    second = publish_program_status(request(tmp_path))
    assert second == publisher.ProgramStatusPublishResult(
        source_commit=first.source_commit,
        source_tree=first.source_tree,
        program_tree=first.program_tree,
        bundle_id=first.bundle_id,
        installed_artifact="current.json",
        changed=False,
    )
    assert (tmp_path / "current.json").read_bytes() == installed


def test_nonexistent_subject_fails_without_installing(tmp_path: Path) -> None:
    with pytest.raises(ProgramStatusPublishError) as raised:
        publish_program_status(request(tmp_path, "does-not-exist"))

    assert raised.value.code == "PROGRAM_STATUS_GIT_READ_FAILED"
    assert not (tmp_path / "current.json").exists()


def test_replacement_failure_preserves_prior_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prior = b"prior-valid-bundle"
    current = tmp_path / "current.json"
    current.write_bytes(prior)

    def fail_replace(_source: Path, _destination: Path) -> None:
        raise PermissionError("simulated Windows sharing violation")

    monkeypatch.setattr(publisher.os, "replace", fail_replace)
    with pytest.raises(ProgramStatusPublishError) as raised:
        publish_program_status(request(tmp_path))

    assert raised.value.code == "PROGRAM_STATUS_INSTALL_FAILED"
    assert current.read_bytes() == prior
    assert list(tmp_path.glob(".current.json.*.tmp")) == []


def test_bundle_identity_recomputes_from_canonical_payload(tmp_path: Path) -> None:
    result = publish_program_status(request(tmp_path))
    bundle = json.loads((tmp_path / "current.json").read_bytes())
    payload = {
        "source": bundle["source"],
        "dashboard": bundle["dashboard"],
        "supplement": bundle["supplement"],
    }

    assert hashlib.sha256(canonical(payload)).hexdigest() == result.bundle_id
    assert bundle["bundle_id"] == result.bundle_id


def test_committed_watch_publishes_once_and_refreshes_heartbeat(tmp_path: Path) -> None:
    result = watch_program_status(request(tmp_path), poll_seconds=0.001, max_polls=2)

    assert result is not None
    assert result.changed is True
    heartbeat = json.loads((tmp_path / "publisher.json").read_bytes())
    assert heartbeat["state"] == "active"
    assert heartbeat["mode"] == "committed_watch"
    assert heartbeat["observed_commit"] == result.source_commit
    assert heartbeat["last_success_at"]


def test_committed_watch_records_bounded_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(
        _request: ProgramStatusPublishRequest,
    ) -> publisher.ProgramStatusPublishResult:
        raise ProgramStatusPublishError(
            "PROGRAM_STATUS_TEST_FAILURE", "test failure", "repair_test_subject"
        )

    monkeypatch.setattr(publisher, "publish_program_status", reject)
    assert watch_program_status(request(tmp_path), max_polls=1) is None

    heartbeat = json.loads((tmp_path / "publisher.json").read_bytes())
    assert heartbeat["state"] == "failed"
    assert heartbeat["failure_code"] == "PROGRAM_STATUS_TEST_FAILURE"
    assert heartbeat["recovery"] == "repair_test_subject"


def test_action_preserves_human_approval_boundary() -> None:
    evidence = [{"id": "state", "path": publisher.STATE_PATH, "sha256": "a" * 64}]

    action = publisher._action(
        "APPROVE_NEXT_GATE",
        "Approve the next exact subject",
        "current_program_action",
        evidence,
        eligible=False,
        blocker="Human approval is required.",
        requires_human_approval=True,
    )

    assert action["eligibility"] == "requires_approval"
    assert action["authority_state"] == "not_authorized"
    assert action["requires_human_approval"] is True
    assert action["blocker"] == "Human approval is required."


def test_initial_test_ledger_append_only_attestation_is_proven() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")

    assert publisher._verify_test_ledger_append_only(REPOSITORY, subject) is None

    subject["ledger"] = {**subject["ledger"], "ledger_revision": 2}
    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._verify_test_ledger_append_only(REPOSITORY, subject)

    assert raised.value.code == "PROGRAM_STATUS_TEST_LEDGER_INVALID"


def test_frozen_source_catalog_selects_only_its_20_committed_inputs() -> None:
    subject = publisher._load_subject(REPOSITORY, "HEAD")
    selected = publisher._load_closed_catalog_sources(REPOSITORY, subject)

    assert set(selected) == set(subject["source_catalog"]["sources"])
    for name, rule in subject["source_catalog"]["sources"].items():
        paths = [path for path, _raw in selected[name]]
        if rule["path_kind"] == "exact":
            assert paths == [rule["path"]]
        else:
            pattern = re.compile(rule["path_pattern"])
            assert all(pattern.fullmatch(path) for path in paths)


def test_customer_story_maturity_is_derived_without_duplicate_definitions() -> None:
    raw = publisher._git_blob(REPOSITORY, "HEAD", publisher.CUSTOMER_CATALOG_PATH)

    assert publisher._customer_story_maturity(raw) == {
        "ready_to_specify": 5,
        "shaped": 15,
        "candidate": 45,
        "discovery_shaped": 15,
        "discovery": 14,
        "discovery_separate_t4_authority_required": 1,
        "fully_defined": 5,
    }

    with pytest.raises(ProgramStatusPublishError) as raised:
        publisher._customer_story_maturity(raw + b"\n### EPP-US-001 duplicate\n")
    assert raised.value.code == "PROGRAM_STATUS_CUSTOMER_CATALOG_INVALID"
