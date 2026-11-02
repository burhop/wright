from __future__ import annotations

import json
from pathlib import Path
import tomllib

import pytest
import yaml

from scripts.release.dev_candidate import prepare


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 40


@pytest.fixture
def candidate(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nversion = "0.1.9"\n')
    package = tmp_path / "src/wright_engineering"
    package.mkdir(parents=True)
    (package / "compatibility.json").write_text(
        json.dumps({"runtime_version": "0.1.9", "data_schema": {"min": 0, "max": 23}})
    )
    return tmp_path


def test_snapshot_versions_metadata_and_preserves_schema(candidate: Path) -> None:
    version = prepare(candidate, source_sha=SHA, run_id="123", run_attempt="1")
    assert version == "0.1.10.dev1230001"
    assert (
        tomllib.loads((candidate / "pyproject.toml").read_text())["project"]["version"]
        == version
    )
    package = candidate / "src/wright_engineering"
    compatibility = json.loads((package / "compatibility.json").read_text())
    assert compatibility["runtime_version"] == version
    assert compatibility["runtime_specifier"] == f"=={version}"
    assert compatibility["data_schema"] == {"min": 0, "max": 23}
    provenance = json.loads((package / "dev-release.json").read_text())
    assert provenance["source_commit"] == SHA
    assert provenance["channel"] == "testpypi-dev"
    assert provenance["base_version"] == "0.1.9"


@pytest.mark.parametrize(
    "source,run,attempt",
    [("dev", "1", "1"), (SHA, "0", "1"), (SHA, "1", "x"), (SHA, "1", "10000")],
)
def test_invalid_identity_does_not_mutate(
    candidate: Path, source: str, run: str, attempt: str
) -> None:
    before = (candidate / "pyproject.toml").read_bytes()
    with pytest.raises(ValueError):
        prepare(candidate, source_sha=source, run_id=run, run_attempt=attempt)
    assert (candidate / "pyproject.toml").read_bytes() == before


def test_retries_have_distinct_versions(candidate: Path, tmp_path: Path) -> None:
    first = prepare(candidate, source_sha=SHA, run_id="123", run_attempt="1")
    (candidate / "pyproject.toml").write_text('[project]\nversion = "0.1.9"\n')
    second = prepare(candidate, source_sha=SHA, run_id="123", run_attempt="2")
    assert first != second


@pytest.mark.parametrize("version", ["0.1.10.dev1", "0.1.10-rc.1"])
def test_nonstable_base_rejected(candidate: Path, version: str) -> None:
    (candidate / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
    with pytest.raises(ValueError, match="stable three-part"):
        prepare(candidate, source_sha=SHA, run_id="123", run_attempt="1")


def test_dev_publication_cannot_enter_production_jobs() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text())
    jobs = workflow["jobs"]
    assert "!inputs.publish_dev" in jobs["preflight-and-python-build"]["if"]
    assert "inputs.publish_dev" in jobs["dev-python-build"]["if"]
    for name, job in jobs.items():
        if name.startswith("dev-"):
            needs = job.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            assert all(parent.startswith("dev-") for parent in needs)
            environment = job.get("environment", {})
            assert environment.get("name") in (None, "testpypi")
        elif name != "preflight-and-python-build":
            needs = job.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            assert needs
            assert all(not parent.startswith("dev-") for parent in needs)
    publisher = jobs["dev-publish-testpypi"]
    assert publisher["permissions"] == {"id-token": "write"}
    publish = publisher["steps"][-1]
    assert publish["with"]["repository-url"] == "https://test.pypi.org/legacy/"
    assert "skip-existing" not in publish["with"]
