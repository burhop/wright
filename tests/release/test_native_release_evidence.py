from __future__ import annotations

from pathlib import Path
import json

from jsonschema import Draft202012Validator, ValidationError
import pytest

from scripts.release.evidence import (
    EvidenceError,
    ManagerAdapterEvidence,
    NativeCandidate,
    OciCandidate,
    PythonArtifact,
    ReleaseEvidence,
    ReleaseIdentity,
    ReleaseMode,
)


ROOT = Path(__file__).resolve().parents[2]
SHA = "a" * 64
DIGEST = "sha256:" + "b" * 64
LIFECYCLE = [
    "install",
    "start",
    "status",
    "doctor",
    "stop",
    "update",
    "rollback",
    "uninstall",
    "purge",
]


def _adapters(source: str = "released") -> list[ManagerAdapterEvidence]:
    return [
        ManagerAdapterEvidence(
            "hermes",
            "0.19.0",
            "hermes-git-plugin-v1",
            "git",
            "git:0123456789abcdef0123456789abcdef01234567",
            source,
        ),
        ManagerAdapterEvidence(
            "codex", "2026.07", "mcp-v1", "mcp-config", "codex-profile:0.1.5", source
        ),
    ]


def _production_evidence() -> ReleaseEvidence:
    return ReleaseEvidence(
        mode=ReleaseMode.RELEASE,
        release_identity=ReleaseIdentity("0.1.5", "0.1.5", "v0.1.5", "c" * 40),
        python_artifacts=[
            PythonArtifact("wright_engineering-0.1.5.whl", "wheel", SHA, SHA),
            PythonArtifact("wright_engineering-0.1.5.tar.gz", "sdist", SHA, SHA),
        ],
        oci_candidate=OciCandidate("ghcr.io/burhop/wright", DIGEST),
        oci_gate_evidence={"candidate_digest": DIGEST},
        native_candidate=NativeCandidate(
            "wright-engineering",
            "0.1.5",
            "wright_engineering-0.1.5-py3-none-any.whl",
            SHA,
            SHA,
            SHA,
            SHA,
        ),
        manager_adapters=_adapters(),
        native_platform_results=[
            {
                "platform": "ubuntu-24.04-x64",
                "status": "passed",
                "forbidden_executables": [],
                "source_isolation": True,
            }
        ],
        manager_adapter_channels=[
            {
                "manager_id": item.manager_id,
                "immutable_identity": item.immutable_identity,
            }
            for item in _adapters()
        ],
        native_public_verification={
            "release_mode": "upgrade",
            "lifecycle": LIFECYCLE,
            "wheel_sha256": SHA,
        },
        stage_results=[
            {"stage": "preflight", "external_mutation": True},
            {"stage": "promoted", "external_mutation": True},
            {"stage": "post_verified", "external_mutation": True},
        ],
        status="post_verified",
    )


def test_native_release_evidence_round_trips_and_satisfies_schema(
    tmp_path: Path,
) -> None:
    evidence = _production_evidence()
    path = tmp_path / "evidence.json"
    evidence.write(path)
    loaded = ReleaseEvidence.read(path)
    assert loaded.native_candidate == evidence.native_candidate
    assert loaded.manager_adapters == evidence.manager_adapters
    schema = json.loads(
        (
            ROOT
            / "specs/047-python-oci-release-train/contracts/release-evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(loaded.to_dict())


@pytest.mark.parametrize(
    "field",
    [
        "native_candidate",
        "manager_adapters",
        "native_platform_results",
        "manager_adapter_channels",
        "native_public_verification",
    ],
)
def test_production_release_rejects_missing_native_evidence(field: str) -> None:
    evidence = _production_evidence()
    setattr(
        evidence,
        field,
        []
        if field
        in {"manager_adapters", "native_platform_results", "manager_adapter_channels"}
        else None,
    )
    with pytest.raises(EvidenceError, match="native|manager|public"):
        evidence.validate()


def test_schema_rejects_omitted_native_field() -> None:
    payload = _production_evidence().to_dict()
    del payload["native_candidate"]
    schema = json.loads(
        (
            ROOT
            / "specs/047-python-oci-release-train/contracts/release-evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(payload)


def test_fixture_manager_adapters_cannot_become_production_evidence() -> None:
    evidence = _production_evidence()
    evidence.manager_adapters = _adapters("fixture")
    with pytest.raises(EvidenceError, match="released manager adapters"):
        evidence.validate()


def test_initial_native_release_requires_no_public_predecessor() -> None:
    evidence = _production_evidence()
    evidence.native_public_verification = {
        "release_mode": "initial_native_release",
        "previous_stable": None,
        "lifecycle": [
            "install",
            "start",
            "status",
            "doctor",
            "stop",
            "uninstall",
            "purge",
        ],
    }
    evidence.validate()
    evidence.native_public_verification["previous_stable"] = {"version": "0.1.5"}
    with pytest.raises(EvidenceError, match="cannot claim a public predecessor"):
        evidence.validate()
