"""Whole-report and rendering determinism tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fixture_builder import GitFixtureBuilder
from program_control.cli import _support_safe_report, render_text
from program_control.git_subject import GitReader
from program_control.json_contracts import deterministic_json_bytes
from program_control.validation import validate_program


PROGRAM_ROOT = "docs/programs/engineering-process-platform"
FIXED = datetime(2026, 8, 27, 20, 0, tzinfo=timezone.utc)


def test_two_fixed_observation_runs_are_byte_identical(repository_root) -> None:
    reader = GitReader(repository_root)
    first = validate_program(reader, "HEAD", PROGRAM_ROOT, observed_at=FIXED).report
    second = validate_program(reader, "HEAD", PROGRAM_ROOT, observed_at=FIXED).report
    assert deterministic_json_bytes(first) == deterministic_json_bytes(second)
    assert render_text(first) == render_text(second)


def test_shuffled_file_creation_and_mapping_order_produce_same_manifest(
    tmp_path,
) -> None:
    policy = {
        "path_roles": [
            {
                "pattern": "docs/programs/engineering-process-platform/**",
                "role": "operational_state",
            }
        ]
    }
    files = {
        f"{PROGRAM_ROOT}/z.json": b'{"schema_version":"1.0","value":2}\n',
        f"{PROGRAM_ROOT}/a.json": b'{"schema_version":"1.0","value":1}\n',
    }
    builders = [
        GitFixtureBuilder(tmp_path / "forward"),
        GitFixtureBuilder(tmp_path / "reverse"),
    ]
    manifests = []
    orders = (list(files), list(reversed(files)))
    for builder, paths in zip(builders, orders, strict=True):
        for path in paths:
            builder.write_bytes(path, files[path])
        commit = builder.commit("same semantic inputs")
        manifests.append(
            GitReader(builder.root).authoritative_manifest(commit, PROGRAM_ROOT, policy)
        )
    assert manifests[0] == manifests[1]


def test_delivery_observations_are_excluded_from_authoritative_manifest(
    git_builder,
) -> None:
    policy = {
        "path_roles": [
            {
                "pattern": "docs/programs/engineering-process-platform/**",
                "role": "operational_state",
            }
        ]
    }
    source_path = f"{PROGRAM_ROOT}/program-state.json"
    git_builder.write_bytes(source_path, b'{"schema_version":"1.0"}\n')
    git_builder.write_bytes(f"{PROGRAM_ROOT}/dashboard.json", b'{"seed":true}\n')
    source = git_builder.commit("source and seed")
    reader = GitReader(git_builder.root)
    before = reader.authoritative_manifest(source, PROGRAM_ROOT, policy)
    git_builder.write_bytes(f"{PROGRAM_ROOT}/dashboard.json", b'{"candidate":true}\n')
    git_builder.write_bytes(
        f"{PROGRAM_ROOT}/evidence/verification/EPP-F01-dashboard-delivery.json",
        b'{"delivery":true}\n',
    )
    container = git_builder.commit("delivery observations only")
    after = reader.authoritative_manifest(container, PROGRAM_ROOT, policy)
    assert before == after


def test_only_declared_observation_field_changes_between_fixed_runs(
    repository_root,
) -> None:
    reader = GitReader(repository_root)
    first = validate_program(reader, "HEAD", PROGRAM_ROOT, observed_at=FIXED).report
    later = validate_program(
        reader, "HEAD", PROGRAM_ROOT, observed_at=FIXED + timedelta(seconds=1)
    ).report
    assert first["observed_at"] != later["observed_at"]
    first["observed_at"] = "DECLARED_OBSERVATION"
    later["observed_at"] = "DECLARED_OBSERVATION"
    assert _support_safe_report(first) == _support_safe_report(later)
