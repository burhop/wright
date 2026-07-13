from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.release.evidence import ReleaseEvidence, ReleaseIdentity  # noqa: E402
from scripts.release.version import validate_release_version  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one Wright release identity."
    )
    parser.add_argument("--tag", required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--allow-dirty", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.allow_dirty and _git("status", "--porcelain"):
        parser.error("release preflight requires a clean checkout")
    source_commit = args.source_commit or _git("rev-parse", "HEAD")
    if source_commit != _git("rev-parse", "HEAD"):
        parser.error("source commit must equal the checked-out reviewed commit")
    version = validate_release_version(ROOT, tag=args.tag)
    evidence = ReleaseEvidence(
        release_identity=ReleaseIdentity(
            version=version.semver,
            python_version=version.python,
            tag=version.tag,
            source_commit=source_commit,
        ),
        stage_results=[
            {"stage": "preflight", "result": "passed", "external_mutation": False}
        ],
    )
    if args.output:
        evidence.write(args.output)
    print(json.dumps(evidence.to_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
