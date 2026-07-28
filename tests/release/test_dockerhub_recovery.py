from pathlib import Path
import subprocess
import sys

from scripts.release.evidence import (
    OciCandidate,
    ReleaseEvidence,
    ReleaseIdentity,
    ReleaseMode,
)


ROOT = Path(__file__).resolve().parents[2]
DIGEST = "sha256:" + "d" * 64
COMMIT = "a" * 40


def _write_release_evidence(path: Path) -> None:
    ReleaseEvidence(
        mode=ReleaseMode.RELEASE,
        release_identity=ReleaseIdentity("0.1.4", "0.1.4", "v0.1.4", COMMIT),
        oci_candidate=OciCandidate("ghcr.io/burhop/wright", DIGEST),
        oci_gate_evidence={"candidate_digest": DIGEST},
        verification_results=[{"python": "passed"}, {"oci": "passed"}],
        stage_results=[
            {"stage": "preflight", "result": "passed", "external_mutation": True},
            {
                "stage": "post_verified",
                "result": "passed",
                "external_mutation": True,
            },
        ],
        status="post_verified",
        schema_version=1,
    ).write(path)


def _run(path: Path, *, digest: str = DIGEST) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate-dockerhub-recovery.py"),
            "--evidence",
            str(path),
            "--tag",
            "v0.1.4",
            "--tag-commit",
            COMMIT,
            "--expected-digest",
            digest,
            "--source-repository",
            "ghcr.io/burhop/wright",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_recovery_accepts_exact_post_verified_subject(tmp_path: Path) -> None:
    path = tmp_path / "release-evidence.json"
    _write_release_evidence(path)

    result = _run(path)

    assert result.returncode == 0, result.stderr
    assert f"v0.1.4 ghcr.io/burhop/wright@{DIGEST}" in result.stdout


def test_recovery_rejects_operator_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "release-evidence.json"
    _write_release_evidence(path)

    result = _run(path, digest="sha256:" + "e" * 64)

    assert result.returncode != 0
    assert "expected digest does not match release evidence" in result.stderr
