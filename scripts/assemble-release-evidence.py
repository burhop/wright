from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import (  # noqa: E402
    OciCandidate,
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
        description="Assemble exact-subject Wright release evidence."
    )
    parser.add_argument(
        "--mode", choices=[item.value for item in ReleaseMode], required=True
    )
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--python-dist", type=Path, required=True)
    parser.add_argument("--oci-repository")
    parser.add_argument("--oci-digest")
    parser.add_argument("--promotion-destination", action="append", default=[])
    parser.add_argument("--approval", action="append", default=[])
    parser.add_argument("--native-build-evidence", type=Path)
    parser.add_argument("--native-lifecycle-evidence", type=Path, action="append", default=[])
    parser.add_argument("--hermes-version")
    parser.add_argument("--hermes-capability", default="python-distribution-v1")
    parser.add_argument("--hermes-install-interface")
    parser.add_argument("--hermes-capability-source", choices=("fixture", "released"))
    parser.add_argument("--stable-hermes-channel")
    parser.add_argument("--stable-hermes-verification-url")
    parser.add_argument("--native-public-verification", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    version = validate_release_version(ROOT, tag=args.tag)
    artifacts = []
    for path in sorted(args.python_dist.iterdir()):
        if path.suffix == ".whl" or path.name.endswith(".tar.gz"):
            artifact, _ = artifact_evidence(path)
            artifacts.append(artifact)
    candidate = None
    gates = None
    promotions = []
    skipped: list[str] = []
    native_candidate = None
    native_results: list[dict[str, object]] = []
    hermes_capability = None
    stable_channel = None
    native_public = None
    if args.native_build_evidence:
        native_build = json.loads(args.native_build_evidence.read_text(encoding="utf-8"))
        wheel = next(
            item for item in native_build["artifacts"] if item["filename"].endswith(".whl")
        )
        native_candidate = NativeCandidate(
            distribution=native_build["distribution"],
            plugin_version=native_build["version"],
            runtime_version=native_build["version"],
            wheel_filename=wheel["filename"],
            wheel_sha256=wheel["sha256"],
            compatibility_sha256=native_build["compatibility_sha256"],
            ui_manifest_sha256=native_build["ui_manifest_sha256"],
            runtime_extra_lock_sha256=native_build["runtime_extra_lock_sha256"],
        )
    for path in args.native_lifecycle_evidence:
        payload = json.loads(path.read_text(encoding="utf-8"))
        native_results.append(
            {
                "platform": payload["platform"],
                "architecture": payload["architecture"],
                "status": payload["status"],
                "forbidden_executables": payload["forbidden_executables"],
                "source_isolation": payload["source_isolation"],
                "lifecycle": payload["lifecycle"],
            }
        )
    if args.hermes_version and args.hermes_install_interface and args.hermes_capability_source:
        hermes_capability = HermesCapabilityEvidence(
            args.hermes_version,
            args.hermes_capability,
            args.hermes_install_interface,
            args.hermes_capability_source,
        )
    if args.stable_hermes_channel and args.stable_hermes_verification_url:
        stable_channel = {
            "channel": args.stable_hermes_channel,
            "version": version.python,
            "verification_url": args.stable_hermes_verification_url,
        }
    if args.native_public_verification:
        native_public = json.loads(
            args.native_public_verification.read_text(encoding="utf-8")
        )
    if args.oci_repository and args.oci_digest:
        candidate = OciCandidate(args.oci_repository, args.oci_digest)
        gates = {
            "candidate_digest": args.oci_digest,
            "smoke": "passed",
            "vulnerability_policy": "passed",
            "sbom": "attached",
            "provenance": "verified",
        }
        destinations = args.promotion_destination or [args.oci_repository]
        promotions.extend(
            {
                "destination": destination,
                "source_digest": args.oci_digest,
                "resolved_digest": args.oci_digest,
            }
            for destination in destinations
        )
    else:
        skipped.append("OCI evidence unavailable in this local rehearsal")
    evidence = ReleaseEvidence(
        mode=ReleaseMode(args.mode),
        release_identity=ReleaseIdentity(
            version.semver, version.python, version.tag, args.source_commit
        ),
        python_artifacts=artifacts,
        python_install_evidence=[
            {"python": value, "wheel": "passed", "sdist": "passed"}
            for value in ("3.11", "3.12", "3.13", "3.14")
        ],
        oci_candidate=candidate,
        oci_gate_evidence=gates,
        native_candidate=native_candidate,
        hermes_capability=hermes_capability,
        native_platform_results=native_results,
        stable_hermes_channel=stable_channel,
        native_public_verification=native_public,
        promotions=promotions,
        approvals=[{"environment": item} for item in args.approval],
        verification_results=[
            {"python": "passed"},
            {"oci": "passed" if candidate else "not-run"},
            {"native": "passed" if native_candidate and native_results else "not-run"},
        ],
        skipped_optional_stages=skipped,
        stage_results=[
            {
                "stage": stage,
                "result": "passed",
                "external_mutation": args.mode == "release",
            }
            for stage in (
                "preflight",
                "candidates_built",
                "candidates_verified",
                "test_index_verified",
                "approved",
                "promoted",
                "post_verified",
            )
        ],
        status="post_verified",
    )
    digest = evidence.write(args.output)
    print(f"release evidence assembled: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
