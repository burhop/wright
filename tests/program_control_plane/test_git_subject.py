"""Exact Git-object identity and runtime validator-bundle boundary tests."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

from program_control.git_subject import (
    SAFE_GIT_COMMANDS,
    GitReader,
    GitSubjectError,
    ensure_safe_checkout_target,
    normalize_repo_path,
)
from program_control.validation import _validate_runtime_source_bundle


def _bundle_repo(git_builder) -> tuple[GitReader, str]:
    git_builder.write_bytes(
        "scripts/validate-engineering-process-program.py", b"print('entry')\n"
    )
    git_builder.write_bytes("scripts/program_control/__init__.py", b"\n")
    git_builder.write_bytes("scripts/program_control/worker.py", b"VALUE = 1\n")
    commit = git_builder.commit("bundle")
    return GitReader(git_builder.root), commit


def test_lf_blob_identity_is_independent_of_checkout_representation(
    git_builder,
) -> None:
    git_builder._git(["config", "core.autocrlf", "true"])
    path = "program data/value.txt"
    git_builder.write_bytes(path, b"one\ntwo\n")
    commit = git_builder.commit("lf source")
    checkout = git_builder.root / path
    checkout.write_bytes(b"one\r\ntwo\r\n")
    git_builder._git(["add", "--", path])

    reader = GitReader(git_builder.root)
    assert (
        hashlib.sha256(reader.blob(commit, path)).hexdigest()
        == hashlib.sha256(b"one\ntwo\n").hexdigest()
    )
    assert checkout.read_bytes() != reader.blob(commit, path)
    assert git_builder.git_output("status", "--porcelain", "--", path) == ""


def test_worktree_observation_maps_unset_autocrlf_without_failing(
    git_builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    reader, _ = _bundle_repo(git_builder)

    observation = reader.worktree_observation()

    assert observation["autocrlf"] == "unset"
    assert observation["dirty_path_count"] == 0


def test_paths_with_spaces_and_batched_blob_reads_are_exact(git_builder) -> None:
    git_builder.write_bytes("folder with spaces/a.json", b"{}\n")
    git_builder.write_bytes("folder with spaces/b.json", b"[]\n")
    commit = git_builder.commit("spaces")
    reader = GitReader(git_builder.root)
    assert reader.read_blobs(
        commit, ["folder with spaces/b.json", "folder with spaces/a.json"]
    ) == {
        "folder with spaces/a.json": b"{}\n",
        "folder with spaces/b.json": b"[]\n",
    }


@pytest.mark.parametrize(
    "path", ["../escape", "/absolute", "C:/drive", "//server/share", "a/../b"]
)
def test_unsafe_repository_paths_are_rejected(path: str) -> None:
    with pytest.raises(GitSubjectError):
        normalize_repo_path(path)


def test_symlink_parent_is_rejected_when_platform_supports_it(
    git_builder, tmp_path: Path
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = git_builder.root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("host does not permit unprivileged symlink creation")
    with pytest.raises(GitSubjectError):
        ensure_safe_checkout_target(git_builder.root, "linked/output.json")


def test_missing_and_detached_git_contexts_fail_closed(
    git_builder, tmp_path: Path
) -> None:
    with pytest.raises(GitSubjectError):
        GitReader.discover(tmp_path / "not-created")
    reader, commit = _bundle_repo(git_builder)
    git_builder._git(["checkout", "--detach", "-q", commit])
    with pytest.raises(GitSubjectError):
        reader.current_branch()


def test_dirty_untracked_and_ignored_bundle_paths_are_observable(git_builder) -> None:
    reader, _ = _bundle_repo(git_builder)
    git_builder.write_bytes("scripts/program_control/worker.py", b"VALUE = 2\n")
    git_builder.write_bytes("scripts/program_control/untracked.py", b"VALUE = 3\n")
    git_builder.write_bytes(".gitignore", b"scripts/program_control/ignored.py\n")
    git_builder.write_bytes("scripts/program_control/ignored.py", b"VALUE = 4\n")
    records = reader.status_for_paths(
        ["scripts/validate-engineering-process-program.py", "scripts/program_control"]
    )
    rendered = b"\n".join(records)
    assert b"worker.py" in rendered
    assert b"untracked.py" in rendered
    assert b"ignored.py" in rendered


def test_runtime_head_bundle_must_equal_explicit_source(git_builder) -> None:
    reader, source = _bundle_repo(git_builder)
    git_builder.write_bytes("scripts/program_control/worker.py", b"VALUE = 2\n")
    git_builder.commit("changed bundle")
    _, _, findings = _validate_runtime_source_bundle(reader, source)
    assert {finding.code for finding in findings} == {
        "VALIDATOR_RUNTIME_SUBJECT_MISMATCH"
    }


def test_loaded_program_control_module_cannot_escape_bundle(
    git_builder, monkeypatch: pytest.MonkeyPatch
) -> None:
    reader, source = _bundle_repo(git_builder)
    escaped = ModuleType("program_control.escaped")
    escaped.__file__ = str(git_builder.root / "outside.py")
    monkeypatch.setitem(sys.modules, "program_control.escaped", escaped)
    _, _, findings = _validate_runtime_source_bundle(reader, source)
    assert "VALIDATOR_RUNTIME_SUBJECT_MISMATCH" in {
        finding.code for finding in findings
    }


def test_reader_allowlist_contains_no_mutating_git_commands() -> None:
    assert SAFE_GIT_COMMANDS.isdisjoint(
        {
            "add",
            "apply",
            "checkout",
            "clean",
            "commit",
            "merge",
            "mv",
            "push",
            "reset",
            "rm",
        }
    )


def test_authoritative_manifest_is_complete_typed_and_deterministic(
    repository_root: Path,
) -> None:
    reader = GitReader(repository_root)
    program_root = "docs/programs/engineering-process-platform"
    policy = json.loads(
        (repository_root / program_root / "lifecycle-policy.json").read_text(
            encoding="utf-8"
        )
    )
    first, first_digest = reader.authoritative_manifest("HEAD", program_root, policy)
    second, second_digest = reader.authoritative_manifest("HEAD", program_root, policy)
    paths = [row["path"] for row in first]
    assert first == second
    assert first_digest == second_digest
    assert paths == sorted(paths)
    assert len(paths) == len(set(paths))
    assert f"{program_root}/dashboard.json" not in paths
    assert (
        f"{program_root}/evidence/verification/EPP-F01-dashboard-delivery.json"
        not in paths
    )
    correction = next(
        row
        for row in first
        if row["path"].endswith("COR-EPP-F01-US1-TR0027-INPUT-ORIGIN-001.json")
    )
    assert correction["role"] == "append_only_evidence"
    assert correction["schema_version"] == "1.0"
    assert correction["schema_id"].endswith("transition-input-correction.schema.json")
