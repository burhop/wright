#!/usr/bin/env python3
"""Build standalone engineering review ZIPs and an offline campaign catalog."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from workspace_service.workflow_trace.campaign_batch import (
    build_campaign_inventory,
    export_prepared_campaign,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = (
    ROOT / "specs" / "083-workflow-trace-review" / "evidence" / "corpus-manifest.json"
)
PREPARE_SCRIPT = ROOT / "scripts" / "prepare-workflow-trace-review-workspace.py"


def _preparer():
    spec = importlib.util.spec_from_file_location(
        "trace_review_workspace", PREPARE_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load the campaign review workspace preparer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.prepare


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bundle", type=Path, help="portable feature-081 campaign bundle"
    )
    parser.add_argument("output", type=Path, help="campaign report output directory")
    parser.add_argument(
        "--completed-manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="reviewed selection of completed attempts",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="prepared review workspace (defaults below the output directory)",
    )
    parser.add_argument(
        "--mode",
        choices=("report_only", "full_data"),
        default="full_data",
    )
    parser.add_argument(
        "--case",
        action="append",
        dest="cases",
        help="export one case; repeat for a selected subset (default: all 30)",
    )
    parser.add_argument(
        "--inventory-only",
        action="store_true",
        help="write the pinned inventory without preparing or exporting reports",
    )
    args = parser.parse_args()

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    inventory = build_campaign_inventory(args.bundle, args.completed_manifest)
    inventory_path = output / "inventory.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    if args.inventory_only:
        print(
            json.dumps(
                {"inventory": str(inventory_path), "cases": inventory["case_count"]},
                indent=2,
            )
        )
        return 0

    selected = set(args.cases or ())
    if selected:
        inventory = {
            **inventory,
            "selection": [
                item for item in inventory["selection"] if item["case_id"] in selected
            ],
        }
    workspace = (args.workspace or (output / ".review-workspace")).resolve()
    selection_path = output / ".selection.json"
    selection_path.write_text(
        json.dumps({"selection": inventory["selection"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    _preparer()(args.bundle, workspace, selection_path)
    catalog = export_prepared_campaign(
        workspace,
        inventory,
        output,
        mode=args.mode,
        case_ids=args.cases,
    )
    print(
        json.dumps(
            {
                "catalog": str(output / "index.html"),
                "mode": args.mode,
                "reports": len(catalog["reports"]),
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
