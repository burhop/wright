#!/usr/bin/env python3
"""Generate Wright's served engineering MCP dashboard artifact."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "tool_registry" / "src"))

from tool_registry.canonical_catalog import load_canonical_entries  # noqa: E402
from tool_registry.engineering_status_builder import build_engineering_status  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--as-of", type=date.fromisoformat, default=datetime.now(UTC).date()
    )
    parser.add_argument("--process-chains", type=Path, required=True)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT
        / "packages"
        / "tool_registry"
        / "src"
        / "tool_registry"
        / "catalog"
        / "engineering-status.json",
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
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
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
