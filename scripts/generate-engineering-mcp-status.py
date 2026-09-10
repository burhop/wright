#!/usr/bin/env python3
"""Generate the standalone engineering MCP curation dashboard."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "tool_registry" / "src"))

from tool_registry.canonical_catalog import load_canonical_entries  # noqa: E402

from engineering_mcp_status import build_engineering_status  # noqa: E402


def _write_evidence(output_dir: Path, result: dict) -> None:
    evidence_dir = output_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    for evidence_id, payload in result.pop("evidence_payloads").items():
        (evidence_dir / f"{evidence_id}.json").write_text(
            payload["content"], encoding="utf-8"
        )

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of", type=date.fromisoformat, default=datetime.now(UTC).date()
    )
    parser.add_argument("--process-chains", type=Path, required=True)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    args = parser.parse_args()
    previous = (
        json.loads(args.previous_report.read_text("utf-8"))
        if args.previous_report
        else None
    )
    result = build_engineering_status(
        load_canonical_entries(),
        as_of=args.as_of,
        repository_root=ROOT,
        process_chains_path=args.process_chains.resolve(),
        previous_report=previous,
    )
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_evidence(output_dir, result)
    status_path = output_dir / "status.json"
    status_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copyfile(ROOT / "scripts" / "engineering-mcp-dashboard.html", output_dir / "index.html")
    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "dashboard": str(output_dir / "index.html"),
                "counts": result["counts"],
                "qualification_counts": result["qualification_counts"],
                "chains": len(result["chains"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
