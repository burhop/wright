from __future__ import annotations

from pathlib import Path
import json

from jsonschema import Draft202012Validator, ValidationError
import pytest

from scripts.release.evidence import (
    EvidenceError,
    HermesCapabilityEvidence,
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
            "0.1.5",
            "wright_engineering-0.1.5-py3-none-any.whl",
            SHA,
            SHA,
            SHA,
            SHA,
        ),
        hermes_capability=HermesCapabilityEvidence(
            "0.19.0",
            "python-distribution-v1",
            "hermes plugins install-package",
            "released",
        ),
        native_platform_results=[
            {
                "platform": "ubuntu-24.04-x64",
                "status": "passed",
                "forbidden_executables": [],
                "source_isolation": True,
            }
        ],
        stable_hermes_channel={
            "channel": "stable",
            "version": "0.1.5",
            "verification_url": "https://example.invalid/wright/stable/0.1.5",
        },
        native_public_verification={"lifecycle": LIFECYCLE, "wheel_sha256": SHA},
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
        "hermes_capability",
        "native_platform_results",
        "stable_hermes_channel",
        "native_public_verification",
    ],
)
def test_production_release_rejects_missing_native_evidence(field: str) -> None:
    evidence = _production_evidence()
    setattr(evidence, field, [] if field == "native_platform_results" else None)
    with pytest.raises(EvidenceError, match="native|Hermes|stable|public"):
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


def test_fixture_hermes_cannot_become_production_evidence() -> None:
    evidence = _production_evidence()
    evidence.hermes_capability = HermesCapabilityEvidence(
        "candidate", "python-distribution-v1", "fixture", "fixture"
    )
    with pytest.raises(EvidenceError, match="released Hermes"):
        evidence.validate()
