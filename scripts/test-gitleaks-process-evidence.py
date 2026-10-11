#!/usr/bin/env python3
"""Scanner-backed checks for approved, exact Feature 083 public identities."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import runpy
import uuid

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/security/process-interface-public-identities.json"


def main() -> int:
    entries = json.loads(FIXTURE.read_text(encoding="utf-8"))["entries"]
    assert len(entries) == 47
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        grouped[entry["path"]].append(entry)
    work = ROOT / "test-results" / ("gitleaks-process-evidence-" + uuid.uuid4().hex)
    scan = runpy.run_path(str(ROOT / "scripts/test-gitleaks-native-evidence.py"))[
        "scan"
    ]

    def write(directory: Path, path: str, matches: list[str]) -> None:
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            "{\n" + ",\n".join('"' + match for match in matches) + "\n}\n",
            encoding="utf-8",
        )

    positive = work / "positive"
    negative = work / "negative"
    synthetic = hashlib.sha256(b"public-evidence-negative-control-only").hexdigest()
    for path, records in grouped.items():
        matches = sorted({record["match"] for record in records})
        write(positive, path, matches)
        write(
            negative,
            path,
            matches
            + ['api_key": "' + synthetic + '"']
            + sorted(
                {
                    record["match"].replace(record["value"], synthetic)
                    for record in records
                }
            ),
        )
        write(negative, "unapproved-path/" + path, matches)

    code, findings = scan(positive, work / "positive-report")
    assert code == 0 and not findings, "Approved public identities remain flagged"
    code, findings = scan(negative, work / "negative-report")
    assert code == 1 and findings, "Scanner missed synthetic negative controls"
    for path, records in grouped.items():
        observed = [f for f in findings if f["File"] == path]
        assert any(f["Match"].startswith('api_key"') for f in observed), path
        for field in {r["field"] for r in records}:
            assert any(f["Match"].startswith(field + '"') for f in observed), (
                path,
                field,
                "changed value was incorrectly allowed",
            )
        assert any(f["File"] == "unapproved-path/" + path for f in findings), path
    summary = {
        "status": "passed",
        "approved_entries": len(entries),
        "approved_paths": len(grouped),
        "negative_findings": len(findings),
        "scope": "exact positives; neighboring API key; changed value; unapproved path",
    }
    (work / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({**summary, "evidence": str(work)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
