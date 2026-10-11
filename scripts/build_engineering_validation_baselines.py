"""Generate source-hashed packaged baselines from reviewed requirement definitions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from core.process_validation import Baseline, canonical_json


REPOSITORY = Path(__file__).resolve().parents[1]
DEFINITIONS = REPOSITORY / "packages/workspace_service/src/workspace_service/process_validation/baselines/definitions.json"
INPUTS = REPOSITORY / "tests/datasets/engineering-workflows/scenarios"
DESTINATION = DEFINITIONS.parent


def build(definition: dict) -> Baseline:
    scenario_root = INPUTS / definition["scenario_path"]

    def source_reference(relative: str, locator: str) -> dict:
        source = (
            REPOSITORY / relative[2:]
            if relative.startswith("@/")
            else scenario_root / relative
        )
        raw = source.read_bytes()
        return {
            "artifact_ref": source.relative_to(REPOSITORY).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "locator": locator,
        }

    requirements = []
    for row in definition["requirements"]:
        sources = []
        for relative, locator in row["sources"]:
            sources.append(source_reference(relative, locator))
        requirements.append({
            "id": row["id"], "text": row["text"], "scope": row["scope"],
            "sources": sources, "mandatory": row.get("mandatory", True),
            "review_required": row.get("review_required", False),
        })
    return Baseline.model_validate({
        "id": definition["scenario_id"] + "-basis",
        "version": definition["version"],
        "requirements": requirements,
        "unresolved_decisions": definition.get("unresolved_decisions", []),
        "amendments": [
            source_reference(relative, locator)
            for relative, locator in definition.get("amendments", [])
        ],
    })


def render() -> dict[Path, bytes]:
    definitions = json.loads(DEFINITIONS.read_text(encoding="utf-8"))
    return {
        DESTINATION / (row["scenario_id"] + ".json"):
            (canonical_json(build(row)) + "\n").encode("utf-8")
        for row in definitions["scenarios"]
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()
    stale = [str(path) for path, data in rendered.items() if not path.is_file() or path.read_bytes() != data]
    if args.check:
        if stale:
            raise SystemExit("Stale baselines: " + ", ".join(stale))
    else:
        for path, data in rendered.items():
            path.write_bytes(data)
    print(json.dumps({"baselines": len(rendered), "stale": len(stale), "check": args.check}))


if __name__ == "__main__":
    main()
