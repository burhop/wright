"""Add dated input-lineage observations without editing enrolled attempts."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from engineering_dataset_input_bindings import build_bindings, digest, validate_bindings
from workspace_service.workspace_path import WorkspacePath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-snapshot", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    snapshot = Path(args.audit_snapshot).read_bytes()
    audit = json.loads(snapshot)
    root = Path(args.output_root)
    if root.exists():
        raise ValueError(
            "Use a fresh observation directory; existing evidence is immutable"
        )
    root.mkdir(parents=True)
    rows = []
    for case in audit["cases"]:
        report = json.loads(Path(case["staging_report"]).read_text(encoding="utf-8"))
        workspace = WorkspacePath(report["workspace_root"])
        saved = workspace.resolve(case["source_path"], must_exist=True)
        if digest(saved.read_bytes()) != case["source_digest"]:
            raise ValueError("Saved canonical source no longer matches audit identity")
        report = {
            **report,
            "source": str(saved),
            "source_sha256": case["source_digest"],
        }
        manifests = [
            item
            for item in report["input_manifest"]
            if item["path"].endswith("/scenario.json")
        ]
        if len(manifests) != 1:
            raise ValueError("One original staged manifest is required")
        manifest = json.loads(
            workspace.resolve(manifests[0]["path"], must_exist=True).read_bytes()
        )
        document = build_bindings(report, manifest=manifest)
        validate_bindings(
            document,
            workspace_root=report["workspace_root"],
            source_path=saved,
            require_complete=False,
        )
        if document["dataset_digest"] != case["dataset_digest"]:
            raise ValueError("Observed staged input revision differs from audit")
        target = (
            root / case["scenario_id"] / (case["attempt_id"] + ".input-bindings.json")
        )
        target.parent.mkdir()
        raw = json.dumps(document, indent=2, ensure_ascii=False).encode() + b"\n"
        target.write_bytes(raw)
        rows.append(
            {
                "scenario_id": case["scenario_id"],
                "attempt_id": case["attempt_id"],
                "source_digest": case["source_digest"],
                "dataset_digest": case["dataset_digest"],
                "complete": document["complete"],
                "evidence": str(target),
                "sha256": digest(raw),
                "unresolved": [
                    row["raw_file"]
                    for row in document["bindings"]
                    if row["status"] != "mapped"
                ],
            }
        )
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "audit_snapshot_sha256": digest(snapshot),
        "scope": "read_only_observation_existing_input_preparation",
        "existing_grants_modified": False,
        "workflow_dispatched": False,
        "cases_observed": len(rows),
        "complete_mappings": sum(row["complete"] for row in rows),
        "cases": rows,
    }
    (root / "summary.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "observed": len(rows),
                "complete": result["complete_mappings"],
                "summary": str(root / "summary.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
