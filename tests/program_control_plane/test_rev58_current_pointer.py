"""Regression coverage for revision-58 raw identity after later revisions."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from program_control.git_subject import GitReader
from program_control.json_contracts import canonical_digest
from program_control.validation import validate_rev58_raw_identity_repair


PROGRAM_ROOT = "docs/programs/engineering-process-platform"


class BlobOverrideReader:
    """Delegate Git evidence except for explicit synthetic committed blobs."""

    def __init__(
        self, reader: GitReader, overrides: dict[tuple[str, str], bytes]
    ) -> None:
        self.reader = reader
        self.overrides = overrides

    def __getattr__(self, name: str) -> Any:
        return getattr(self.reader, name)

    def read_blob_requests(
        self, requests: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], bytes]:
        request_list = list(requests)
        delegated = [
            request for request in request_list if request not in self.overrides
        ]
        blobs = self.reader.read_blob_requests(delegated) if delegated else {}
        blobs.update(
            {
                request: self.overrides[request]
                for request in request_list
                if request in self.overrides
            }
        )
        return blobs


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def _fixture(
    repository_root: Path, *, valid_transition: bool
) -> tuple[BlobOverrideReader, str, dict[str, Any]]:
    current = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository_root, text=True
    ).strip()
    program = repository_root / PROGRAM_ROOT
    state58 = json.loads(
        (program / "evidence/states/program-state-revision-0058.json").read_text(
            encoding="utf-8"
        )
    )
    state59 = dict(state58)
    state59["revision"] = 59
    state59["last_transition"] = "TR-0058"
    transition58 = {
        "transition_id": "TR-0058",
        "prior_revision": 58,
        "new_revision": 59,
        "prior_state_digest": canonical_digest(state58),
        "new_state_digest": canonical_digest(state59),
    }
    if not valid_transition:
        transition58["prior_state_digest"] = "0" * 64
    state59_bytes = _json_bytes(state59)
    overrides = {
        (current, f"{PROGRAM_ROOT}/program-state.json"): state59_bytes,
        (
            current,
            f"{PROGRAM_ROOT}/evidence/states/program-state-revision-0059.json",
        ): state59_bytes,
        (
            current,
            f"{PROGRAM_ROOT}/evidence/transitions/TR-0058.json",
        ): _json_bytes(transition58),
    }
    evidence = json.loads(
        (
            program / "evidence/verification/VER-EPP-F01-REV58-RAW-IDENTITY-001.json"
        ).read_text(encoding="utf-8")
    )
    return BlobOverrideReader(GitReader(repository_root), overrides), current, evidence


def test_rev58_archive_remains_valid_after_a_contiguous_successor(
    repository_root: Path,
) -> None:
    reader, current, evidence = _fixture(repository_root, valid_transition=True)

    findings, corrected = validate_rev58_raw_identity_repair(
        reader, current, PROGRAM_ROOT, evidence
    )

    assert findings == []
    assert corrected


def test_rev58_archive_rejects_a_successor_with_a_broken_digest_link(
    repository_root: Path,
) -> None:
    reader, current, evidence = _fixture(repository_root, valid_transition=False)

    findings, corrected = validate_rev58_raw_identity_repair(
        reader, current, PROGRAM_ROOT, evidence
    )

    assert [finding.code for finding in findings] == [
        "REV58_RAW_IDENTITY_REPAIR_INVALID"
    ]
    assert corrected == frozenset()
