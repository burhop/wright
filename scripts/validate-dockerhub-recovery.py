from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import ReleaseEvidence, ReleaseMode  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate retained Wright release evidence before recovering its exact "
            "OCI digest to Docker Hub."
        )
    )
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--tag-commit", required=True)
    parser.add_argument("--expected-digest", required=True)
    parser.add_argument("--source-repository", required=True)
    args = parser.parse_args(argv)

    evidence = ReleaseEvidence.read(args.evidence)
    identity = evidence.release_identity
    candidate = evidence.oci_candidate
    if evidence.mode is not ReleaseMode.RELEASE:
        raise SystemExit("recovery requires production release evidence")
    if evidence.status != "post_verified":
        raise SystemExit("recovery requires post-verified release evidence")
    if identity.tag != args.tag:
        raise SystemExit("requested tag does not match release evidence")
    if identity.source_commit != args.tag_commit:
        raise SystemExit("Git tag commit does not match release evidence")
    if candidate is None:
        raise SystemExit("release evidence has no OCI candidate")
    if candidate.repository != args.source_repository:
        raise SystemExit("source repository does not match release evidence")
    if candidate.digest != args.expected_digest:
        raise SystemExit("expected digest does not match release evidence")
    if {"oci": "passed"} not in evidence.verification_results:
        raise SystemExit("release evidence does not record successful OCI verification")

    print(
        f"validated Docker Hub recovery subject: {identity.tag} "
        f"{candidate.repository}@{candidate.digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
