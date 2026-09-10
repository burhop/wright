#!/usr/bin/env python3
"""Apply a reviewed MCP evaluation result set to the canonical catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--results", required=True)
    parser.add_argument("--repository-root", default=".")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    results = json.loads(Path(args.results).read_text(encoding="utf-8"))
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.representer.ignore_aliases = lambda *_: True
    catalog_path = Path(args.catalog)
    original = catalog_path.read_text(encoding="utf-8")
    document = yaml.load(original)
    entries = {entry["id"]: entry for entry in document["servers"]}
    changed = []
    for result in results["results"]:
        entry = entries[result["id"]]
        evidence_path = root / result["evidence"]
        digest = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
        entry["validation_result"] = {
            "status": result["status"],
            "message": result["message"],
            "environment": "wright-clean-debian13-x64",
            "missing_dependencies": result["missing"],
            "validated_at": results["as_of"],
            "evidence_status": "recorded",
        }
        if result["category"] == "Connect and verify":
            entry["credentials_required"] = result["missing"]
        sources = entry.setdefault("source_records", [])
        sources[:] = [source for source in sources if source.get("kind") != "evidence"]
        sources.append({
            "url": result["evidence"],
            "kind": "evidence",
            "primary": False,
            "authority": "publisher" if entry.get("maturity") == "official" else "community",
            "observed_at": results["as_of"],
            "notes": f"SHA-256 {digest}; portfolio category: {result['category']}.",
        })
        entry["curation"]["reviewed_at"] = results["as_of"]
        entry["curation"]["review_due"] = "2026-10-09"
        entry["curation"]["next_action"] = (
            "Review exact evidence at " + result["evidence"] + ". "
            + ("Complete authentication and a read-only Wright gateway task." if result["category"] == "Connect and verify" else
               "Run the smallest recorded host/backend and Wright gateway scenario." if result["category"] == "Environment required" else
               "Complete a deterministic local-page browser task through Wright." if result["category"] == "Preflight passed" else
               "Correct the endpoint or source identity before another execution attempt.")
        )
        if result["category"] == "Excluded archive":
            entry["curation"]["disposition"] = "removed"
            entry["curation"]["reason"] = result["message"]
            entry["installability_tier"] = "non_working"
            entry["verification_state"] = "excluded"
        changed.append(entry)
    updated = original
    yaml.width = 4096
    for entry in changed:
        stream = StringIO()
        yaml.dump({"servers": [entry]}, stream)
        replacement = stream.getvalue().split("servers:\n", 1)[1]
        pattern = re.compile(rf"(?ms)^- id: {re.escape(entry['id'])}\n.*?(?=^- id: |\Z)")
        updated, count = pattern.subn(replacement, updated, count=1)
        if count != 1:
            raise RuntimeError(f"Could not replace catalog entry {entry['id']}")
    catalog_path.write_text(updated, encoding="utf-8")
    print(json.dumps({"updated": len(results["results"]), "as_of": results["as_of"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
