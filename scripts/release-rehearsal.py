from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import ReleaseEvidence, ReleaseIdentity, ReleaseMode  # noqa: E402
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
