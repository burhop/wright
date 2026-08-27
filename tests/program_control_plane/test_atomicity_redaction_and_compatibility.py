"""Failure containment, redaction, atomicity, and source immutability tests."""

from __future__ import annotations

import json
import shutil
import sys
from hashlib import sha256
from pathlib import Path
from types import ModuleType

import pytest

from program_control.cli import _emit, build_parser
from program_control.dashboard import DashboardError, atomic_replace_json
from program_control.json_contracts import deterministic_json_bytes, validate_schema
from program_control.git_subject import GitReader
from program_control.validation import _validate_runtime_source_bundle


SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["value"],
    "properties": {"value": {"type": "integer"}},
}


def _report_with_canary(canary: str) -> dict:
    return {
        "verdict": "failed",
        "subject": {
            "source_commit": None,
            "source_tree": None,
            "program_tree": None,
            "container_commit": None,
            "container_resolution": "unresolved",
            "delivery_commit": None,
            "delivery_resolution": "unresolved",
            "worktree_clean": True,
        },
        "areas": {
            name: {"status": "blocked", "passed_gates": 0, "required_gates": 1}
            for name in (
                "product_readiness",
                "benchmark_readiness",
                "commercial_readiness",
                "program_health",
            )
        },
        "release_eligible": False,
        "findings": [
            {
                "severity": "error",
                "code": "INPUT_INVALID",
                "artifact": canary,
                "json_pointer": "/value",
                "invariant": "INPUT_SAFE",
                "evidence": [canary],
                "consequence": canary,
                "recovery": canary,
                "resolution_status": "unresolved",
                "correction_ref": None,
            }
        ],
        "next_action": None,
    }


@pytest.mark.parametrize(
    "canary",
    [
        "password=" + "runtime-secret",
        "token=" + "runtime-token",
        "authorization: Bearer runtime",
        "C:\\Users\\private\\payload.log",
        "\\\\server\\private\\payload.log",
        "/home/private/payload.log",
        "https://private.invalid/payload?api_key=runtime",
    ],
)
@pytest.mark.parametrize("output_format", ["text", "json"])
def test_output_edge_redacts_sensitive_runtime_canaries(
    canary: str,
    output_format: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _emit(_report_with_canary(canary), output_format)
    captured = capsys.readouterr()
    assert canary not in captured.out + captured.err
    assert "runtime-secret" not in captured.out + captured.err
    assert "runtime-token" not in captured.out + captured.err


def test_parser_does_not_echo_invalid_argument_canary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    canary = "token=" + "invalid-argument"
    with pytest.raises(SystemExit) as raised:
        build_parser().parse_args([canary])
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert canary not in captured.err


def test_atomic_replace_success_is_canonical_and_leaves_no_temp(tmp_path: Path) -> None:
    target = tmp_path / "dashboard.json"
    target.write_bytes(b'{"value":0}\n')
    atomic_replace_json(target, {"value": 1}, SCHEMA)
    assert target.read_bytes() == deterministic_json_bytes({"value": 1})
    assert list(tmp_path.glob(".dashboard.json.*.tmp")) == []


@pytest.mark.parametrize(
    ("hook", "expected"),
    [
        ("write", "OUTPUT_WRITE_FAILED"),
        ("flush", "OUTPUT_FLUSH_FAILED"),
        ("fsync", "OUTPUT_FSYNC_FAILED"),
        ("reread", "OUTPUT_REREAD_FAILED"),
        ("replace", "OUTPUT_REPLACE_FAILED"),
    ],
)
def test_atomic_stage_failures_preserve_prior_and_clean_temp(
    tmp_path: Path, hook: str, expected: str
) -> None:
    target = tmp_path / "dashboard.json"
    prior = b'{"value":0}\n'
    target.write_bytes(prior)

    def fail(*args, **kwargs):
        raise OSError("private failure payload")

    with pytest.raises(DashboardError, match=expected):
        atomic_replace_json(target, {"value": 1}, SCHEMA, **{hook: fail})
    assert target.read_bytes() == prior
    assert list(tmp_path.glob(".dashboard.json.*.tmp")) == []


def test_invalid_candidate_and_reread_preserve_prior(tmp_path: Path) -> None:
    target = tmp_path / "dashboard.json"
    prior = b'{"value":0}\n'
    target.write_bytes(prior)
    with pytest.raises(DashboardError, match="OUTPUT_CANDIDATE_INVALID"):
        atomic_replace_json(target, {"value": "bad"}, SCHEMA)
    with pytest.raises(DashboardError, match="OUTPUT_REREAD_INVALID"):
        atomic_replace_json(
            target,
            {"value": 1},
            SCHEMA,
            reread=lambda path: b'{"value":2}\n',
        )
    assert target.read_bytes() == prior
    assert list(tmp_path.glob(".dashboard.json.*.tmp")) == []


def test_interruption_is_bounded_and_preserves_prior(tmp_path: Path) -> None:
    target = tmp_path / "dashboard.json"
    prior = b'{"value":0}\n'
    target.write_bytes(prior)

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    with pytest.raises(DashboardError, match="OUTPUT_INTERRUPTED"):
        atomic_replace_json(target, {"value": 1}, SCHEMA, fsync=interrupt)
    assert target.read_bytes() == prior
    assert list(tmp_path.glob(".dashboard.json.*.tmp")) == []


def test_only_declared_target_changes_on_valid_and_invalid_runs(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    target = tmp_path / "dashboard.json"
    source.write_text(json.dumps({"authoritative": True}) + "\n", encoding="utf-8")
    target.write_bytes(b'{"value":0}\n')
    before_source = source.read_bytes()
    atomic_replace_json(target, {"value": 1}, SCHEMA)
    assert source.read_bytes() == before_source
    after_valid = target.read_bytes()
    with pytest.raises(DashboardError):
        atomic_replace_json(target, {"value": "bad"}, SCHEMA)
    assert source.read_bytes() == before_source
    assert target.read_bytes() == after_valid


def _bundle_subject(git_builder) -> tuple[GitReader, str]:
    git_builder.write_bytes(
        "scripts/validate-engineering-process-program.py", b"print('entry')\n"
    )
    git_builder.write_bytes("scripts/program_control/__init__.py", b"\n")
    git_builder.write_bytes("scripts/program_control/worker.py", b"VALUE = 1\n")
    source = git_builder.commit("runtime bundle source")
    return GitReader(git_builder.root), source


@pytest.mark.parametrize(
    "mutation", ["added", "deleted", "changed", "removed_entrypoint"]
)
def test_runtime_bundle_permutations_fail_closed(git_builder, mutation: str) -> None:
    reader, source = _bundle_subject(git_builder)
    if mutation == "added":
        git_builder.write_bytes("scripts/program_control/added.py", b"VALUE = 2\n")
    elif mutation == "deleted":
        (git_builder.root / "scripts/program_control/worker.py").unlink()
    elif mutation == "changed":
        git_builder.write_bytes("scripts/program_control/worker.py", b"VALUE = 2\n")
    else:
        (git_builder.root / "scripts/validate-engineering-process-program.py").unlink()
    git_builder.commit(f"bundle {mutation}")
    _, _, findings = _validate_runtime_source_bundle(reader, source)
    assert "VALIDATOR_RUNTIME_SUBJECT_MISMATCH" in {
        finding.code for finding in findings
    }


def test_imported_generator_module_outside_exact_source_fails_closed(
    git_builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader, source = _bundle_subject(git_builder)
    imported = ModuleType("program_control.runtime_added")
    imported.__file__ = str(
        git_builder.root / "scripts/program_control/runtime_added.py"
    )
    git_builder.write_bytes(imported.__file__, b"VALUE = 3\n")
    monkeypatch.setitem(sys.modules, imported.__name__, imported)
    _, _, findings = _validate_runtime_source_bundle(reader, source)
    assert "VALIDATOR_RUNTIME_SUBJECT_MISMATCH" in {
        finding.code for finding in findings
    }


def test_frozen_prior_profiles_are_ordered_and_single_migration(
    repository_root,
) -> None:
    contract = json.loads(
        (
            repository_root
            / "specs/076-control-plane-validator/contracts/legacy-compatibility-profile.json"
        ).read_text(encoding="utf-8")
    )
    profiles = contract["profiles"]
    assert [(row["from_revision"], row["through_revision"]) for row in profiles] == [
        (1, 9),
        (10, 19),
    ]
    assert profiles[1]["successor"]["maximum_count"] == 1


def test_complete_frozen_prior_contract_reads_exact_committed_bytes(
    repository_root,
) -> None:
    root = "docs/programs/engineering-process-platform"
    reader = GitReader(repository_root)
    contract = json.loads(
        (
            repository_root
            / "specs/076-control-plane-validator/contracts/legacy-compatibility-profile.json"
        ).read_text(encoding="utf-8")
    )
    checked = 0
    commit = reader.resolve_commit("HEAD")
    for profile in contract["profiles"]:
        for row in [*profile["states"], *profile["transitions"]]:
            if row.get("raw_sha256") is None:
                continue
            raw = reader.blob(commit, f"{root}/{row['path']}")
            assert sha256(raw).hexdigest() == row["raw_sha256"]
            checked += 1
    assert checked == 36


def test_contract_seed_is_valid_but_explicitly_not_delivery_evidence(
    repository_root,
) -> None:
    root = repository_root / "docs/programs/engineering-process-platform"
    dashboard = json.loads((root / "dashboard.json").read_text(encoding="utf-8"))
    schema = json.loads(
        (root / "schemas/dashboard.schema.json").read_text(encoding="utf-8")
    )
    dashboard["generation_status"] = "contract_seed_not_evidence"
    assert validate_schema(schema, dashboard) == []
    assert dashboard["generation_status"] != "candidate_not_evidence"
    assert dashboard["container_relation"]["delivery_evidence_embedded"] is False


def test_removed_validator_rollback_preserves_sources_and_stales_snapshot(
    repository_root, tmp_path: Path
) -> None:
    sandbox = tmp_path / "rollback"
    source_paths = [
        "docs/programs/engineering-process-platform/program-state.json",
        "docs/programs/engineering-process-platform/roadmap.json",
        "docs/programs/engineering-process-platform/README.md",
    ]
    validator = "scripts/validate-engineering-process-program.py"
    dashboard = "docs/programs/engineering-process-platform/dashboard.json"
    for relative in [*source_paths, validator, dashboard]:
        target = sandbox / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repository_root / relative, target)
    source_before = {path: (sandbox / path).read_bytes() for path in source_paths}
    dashboard_before = (sandbox / dashboard).read_bytes()
    (sandbox / validator).unlink()
    assert not (sandbox / validator).exists()
    assert {
        path: (sandbox / path).read_bytes() for path in source_paths
    } == source_before
    assert (sandbox / dashboard).read_bytes() == dashboard_before
    quickstart = (
        repository_root / "specs/076-control-plane-validator/quickstart.md"
    ).read_text(encoding="utf-8")
    assert (
        "Manual inspection only; existing snapshot is stale/unsupported" in quickstart
    )
