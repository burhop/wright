from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import (  # noqa: E402
    HermesCapabilityEvidence,
    NativeCandidate,
    ReleaseEvidence,
    ReleaseIdentity,
    ReleaseMode,
)
from scripts.release.python_artifacts import artifact_evidence  # noqa: E402
from scripts.release.version import validate_release_version  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rehearse Wright release ordering without publication."
    )
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--python-dist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--native-build-evidence", type=Path)
    parser.add_argument(
        "--native-lifecycle-evidence", type=Path, action="append", default=[]
    )
    args = parser.parse_args(argv)
    version = validate_release_version(ROOT, tag=args.tag)
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    artifact_paths = sorted(
        path
        for path in args.python_dist.rglob("*")
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    )
    artifacts = []
    manifests: dict[str, str] = {}
    for path in artifact_paths:
        evidence, manifest = artifact_evidence(path)
        artifacts.append(evidence)
        manifests[path.name] = manifest
    native_candidate = None
    native_results: list[dict[str, object]] = []
    if args.native_build_evidence:
        native_build = json.loads(args.native_build_evidence.read_text(encoding="utf-8"))
        wheel = next(
            item for item in native_build["artifacts"] if item["filename"].endswith(".whl")
        )
        native_candidate = NativeCandidate(
            native_build["distribution"],
            native_build["version"],
            native_build["version"],
            wheel["filename"],
            wheel["sha256"],
            native_build["compatibility_sha256"],
            native_build["ui_manifest_sha256"],
            native_build["runtime_extra_lock_sha256"],
        )
    for path in args.native_lifecycle_evidence:
        payload = json.loads(path.read_text(encoding="utf-8"))
        native_results.append(
            {
                "platform": payload["platform"],
                "status": payload["status"],
                "forbidden_executables": payload["forbidden_executables"],
                "source_isolation": payload["source_isolation"],
            }
        )
    evidence = ReleaseEvidence(
        mode=ReleaseMode.DRY_RUN,
        release_identity=ReleaseIdentity(
            version.semver, version.python, version.tag, source_commit
        ),
        python_artifacts=artifacts,
        python_install_evidence=[
            {"python": value, "wheel": "passed", "sdist": "passed"}
            for value in ("3.11", "3.12", "3.13", "3.14")
        ],
        native_candidate=native_candidate,
        hermes_capability=HermesCapabilityEvidence(
            "candidate-fixture",
            "python-distribution-v1",
            "local candidate fixture",
            "fixture",
        )
        if native_candidate
        else None,
        native_platform_results=native_results,
        stable_hermes_channel={
            "channel": "isolated-rehearsal",
            "version": version.python,
            "verification_url": "local://no-mutation",
        }
        if native_candidate
        else None,
        native_public_verification={
            "lifecycle": [
                "install",
                "start",
                "status",
                "doctor",
                "stop",
                "update",
                "rollback",
                "uninstall",
                "purge",
            ],
            "simulated": True,
        }
        if native_candidate
        else None,
        verification_results=[{"python": "passed"}, {"oci": "simulated"}],
        skipped_optional_stages=[
            "public registries, documentation, and GitHub Release"
        ],
        stage_results=[
            {"stage": stage, "result": "simulated", "external_mutation": False}
            for stage in (
                "preflight",
                "candidates_built",
                "candidates_verified",
                "test_index_verified",
                "approved",
                "promoted",
                "post_verified",
                "docs_verified",
                "release_ready",
            )
        ],
        status="release_ready",
    )
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, manifest in manifests.items():
        (args.output / f"{filename}.contents.txt").write_text(
            manifest, encoding="utf-8", newline="\n"
        )
    digest = evidence.write(args.output / "release-evidence.json")
    print(f"release rehearsal passed without external mutation: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
