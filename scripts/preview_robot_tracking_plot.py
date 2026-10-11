"""Render improved plots into a NEW offline directory; never resume a saved run.

The retained bag, alignment and old analysis are read-only sources. This is
presentation/operation verification, not a registered campaign attempt or pass.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import robot_tracking_operations as operations


def preview(bag: Path, alignment: Path, reference: Path, output: Path):
    if any(output.resolve().is_relative_to(source.resolve())
           for source in (bag, alignment.parent, reference)):
        raise ValueError("Preview output must be outside the retained input and analysis directories")
    sources = [*sorted(bag.iterdir()), alignment,
               reference / "timeline.csv", reference / "tracking-metrics.json",
               reference / "trajectory-overlay.svg"]
    before = {str(path): operations.sha(path) for path in sources if path.is_file()}
    result = operations.analyze_tracking_bag(bag, alignment, output)
    original = json.loads((reference / "tracking-metrics.json").read_text(encoding="utf-8"))
    # Only the implementation identity and added presentation links may differ.
    comparison = {key: result.get(key) == value for key, value in original.items()
                  if key not in {"operation_sha256", "plot_files"}}
    timeline_unchanged = (output / "timeline.csv").read_bytes() == (reference / "timeline.csv").read_bytes()
    source_unchanged = before == {name: operations.sha(name) for name in before}
    receipt = {"scope": "Offline plot revision preview; not campaign output or engineering approval",
               "observed_at": datetime.now(timezone.utc).isoformat(),
               "source_files": before, "source_files_unchanged": source_unchanged,
               "original_metric_values_unchanged": comparison,
               "timeline_bytes_unchanged": timeline_unchanged,
               "operation_sha256": operations.sha(operations.__file__),
               "outputs": [{"name": path.name, "sha256": operations.sha(path)}
                           for path in sorted(output.iterdir()) if path.is_file()]}
    operations.write_json(output / "preview-provenance.json", receipt)
    if not source_unchanged or not timeline_unchanged or not all(comparison.values()):
        raise ValueError("Preview verification failed; inspect preview-provenance.json; original evidence was not replaced")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bag", type=Path, required=True)
    parser.add_argument("--alignment", type=Path, required=True)
    parser.add_argument("--reference-analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = preview(args.bag, args.alignment, args.reference_analysis, args.output)
    print(json.dumps({"status": "verified_preview", "output": str(args.output),
                      "source_files_unchanged": receipt["source_files_unchanged"],
                      "timeline_bytes_unchanged": receipt["timeline_bytes_unchanged"]}))
