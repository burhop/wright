from pathlib import Path
import json

from jsonschema import Draft202012Validator
import pytest

from scripts.release.evidence import (
    EvidenceError,
    OciCandidate,
    PythonArtifact,
    ReleaseEvidence,
    ReleaseIdentity,
)


IDENTITY = ReleaseIdentity("0.1.0", "0.1.0", "v0.1.0", "a" * 40)
ROOT = Path(__file__).resolve().parents[2]


def _artifact(kind: str) -> PythonArtifact:
    suffix = ".whl" if kind == "wheel" else ".tar.gz"
    return PythonArtifact(f"wright_engineering-0.1.0{suffix}", kind, "b" * 64, "c" * 64)


def test_evidence_round_trips_deterministically(tmp_path: Path) -> None:
    evidence = ReleaseEvidence(
        release_identity=IDENTITY,
        python_artifacts=[_artifact("wheel"), _artifact("sdist")],
        stage_results=[{"stage": "preflight", "external_mutation": False}],
    )
    path = tmp_path / "evidence.json"
    digest = evidence.write(path)
    assert len(digest) == 64
    assert ReleaseEvidence.read(path).to_dict() == evidence.to_dict()
    schema = json.loads(
        (
            ROOT
            / "specs/047-python-oci-release-train/contracts/release-evidence.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema).validate(evidence.to_dict())


def test_evidence_rejects_duplicate_or_out_of_order_stages() -> None:
    evidence = ReleaseEvidence(
        release_identity=IDENTITY,
        stage_results=[{"stage": "promoted"}, {"stage": "preflight"}],
    )
    with pytest.raises(EvidenceError, match="ordered"):
        evidence.validate()


def test_dry_run_rejects_external_mutation() -> None:
    evidence = ReleaseEvidence(
        release_identity=IDENTITY,
        stage_results=[{"stage": "preflight", "external_mutation": True}],
    )
    with pytest.raises(EvidenceError, match="external mutation"):
        evidence.validate()


def test_oci_gate_and_promotion_subjects_must_match_candidate() -> None:
    digest = "sha256:" + "d" * 64
    evidence = ReleaseEvidence(
        release_identity=IDENTITY,
        oci_candidate=OciCandidate("ghcr.io/burhop/wright", digest),
        oci_gate_evidence={"candidate_digest": digest},
        promotions=[
            {
                "source_digest": digest,
                "resolved_digest": "sha256:" + "e" * 64,
            }
        ],
    )
    with pytest.raises(EvidenceError, match="preserve"):
        evidence.validate()
