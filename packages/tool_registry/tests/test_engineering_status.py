import hashlib
import json

import pytest

from tool_registry.engineering_status import (
    EngineeringStatusError,
    load_engineering_status,
    load_engineering_status_evidence,
)


def test_bundled_engineering_status_is_complete_and_evidence_bound() -> None:
    status = load_engineering_status()
    assert status["counts"] == {"curated": 10, "follow_up": 56, "removed": 12}
    assert status["qualification_counts"]["passing"] == 10
    assert len(status["records"]) == 78
    assert len(status["chains"]) == 3
    assert "evidence_payloads" not in status

    content, digest = load_engineering_status_evidence("process-chains")
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == digest
    assert json.loads(content)["cleanup"] == "passed"

    content, digest = load_engineering_status_evidence(
        "server-review-kernelcad-mcp"
    )
    assert hashlib.sha256(content.encode("utf-8")).hexdigest() == digest
    assert "EALLOWGIT" in json.loads(content)["server_stderr"]


def test_engineering_status_rejects_unknown_evidence() -> None:
    with pytest.raises(EngineeringStatusError, match="Unknown"):
        load_engineering_status_evidence("../not-allowed")
