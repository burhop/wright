"""Prepare a uniquely versioned TestPyPI snapshot without changing release metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tomllib


def prepare(root: Path, *, source_sha: str, run_id: str, run_attempt: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("source must be a full Git commit SHA")
    if not all(re.fullmatch(r"[1-9][0-9]*", item) for item in (run_id, run_attempt)):
        raise ValueError("run identity must contain positive integers")
    if int(run_attempt) > 9999:
        raise ValueError("run attempt exceeds the unique version field")
    metadata = root / "pyproject.toml"
    text = metadata.read_text(encoding="utf-8")
    base = tomllib.loads(text)["project"]["version"]
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", base)
    if match is None:
        raise ValueError("dev snapshots require a stable three-part base version")
    major, minor, patch = map(int, match.groups())
    version = f"{major}.{minor}.{patch + 1}.dev{run_id}{int(run_attempt):04d}"
    old = f'version = "{base}"'
    if text.count(old) != 1:
        raise ValueError("ambiguous root version declaration")
    compatibility_path = root / "src/wright_engineering/compatibility.json"
    compatibility = json.loads(compatibility_path.read_text(encoding="utf-8"))
    compatibility.update(runtime_version=version, runtime_specifier=f"=={version}")
    provenance = {
        "schema_version": 1,
        "channel": "testpypi-dev",
        "source_commit": source_sha,
        "base_version": base,
        "version": version,
        "workflow_run": f"https://github.com/burhop/wright/actions/runs/{run_id}",
        "run_attempt": int(run_attempt),
    }
    metadata.write_text(text.replace(old, f'version = "{version}"'), encoding="utf-8")
    compatibility_path.write_text(
        json.dumps(compatibility, indent=2) + "\n", encoding="utf-8"
    )
    (root / "src/wright_engineering/dev-release.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return version


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-attempt", required=True)
    args = parser.parse_args()
    print(
        prepare(
            args.root,
            source_sha=args.source_sha,
            run_id=args.run_id,
            run_attempt=args.run_attempt,
        )
    )


if __name__ == "__main__":
    main()
