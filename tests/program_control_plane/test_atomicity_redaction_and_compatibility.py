"""Failure containment, redaction, atomicity, and source immutability tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from program_control.cli import _emit, build_parser
from program_control.dashboard import DashboardError, atomic_replace_json
from program_control.json_contracts import deterministic_json_bytes


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
