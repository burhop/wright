from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rehearsal_records_native_fixture_without_external_mutation() -> None:
    source = (ROOT / "scripts/release-rehearsal.py").read_text(encoding="utf-8")
    assert "--native-build-evidence" in source
    assert "--native-lifecycle-evidence" in source
    assert '"fixture"' in source
    assert '"external_mutation": False' in source
    assert "local://no-mutation" in source


def test_feature_workflows_cannot_publish_any_stable_subject() -> None:
    candidate = (ROOT / ".github/workflows/native-hermes-pr.yml").read_text(
        encoding="utf-8"
    )
    forbidden = (
        "environment: pypi",
        "environment: dockerhub",
        "environment: release",
        "packages: write",
        "id-token: write",
        "deploy: true",
    )
    for value in forbidden:
        assert value not in candidate
