#!/usr/bin/env python3
"""Verify campaign review archives and extracted reports without network access."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(root: Path, expected: int | None = None) -> dict:
    root = root.resolve(strict=True)
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    reports = catalog.get("reports") or []
    if expected is not None and len(reports) != expected:
        raise ValueError(f"expected {expected} reports, found {len(reports)}")
    failures = []
    verified = []
    for report in reports:
        case_id = str(report.get("case_id") or "unknown")
        try:
            archive_path = (root / report["archive_path"]).resolve(strict=True)
            report_path = (root / report["report_path"]).resolve(strict=True)
            archive_path.relative_to(root)
            report_path.relative_to(root)
            if _sha256(archive_path.read_bytes()) != report["archive_sha256"]:
                raise ValueError("catalog archive digest mismatch")
            if b"wright-trace-data" not in report_path.read_bytes():
                raise ValueError("offline report model is unavailable")
            with zipfile.ZipFile(archive_path) as archive:
                bad = archive.testzip()
                if bad:
                    raise ValueError(f"ZIP integrity failure: {bad}")
                names = set(archive.namelist())
                for required in (
                    "index.html",
                    "manifest.json",
                    "report/report.json",
                    "evidence/run-evidence.json",
                ):
                    if required not in names:
                        raise ValueError(f"missing package member: {required}")
                manifest = json.loads(archive.read("manifest.json"))
                for item in [
                    *manifest.get("entries", []),
                    *manifest.get("viewer_licenses", []),
                ]:
                    packaged = item.get("package_path")
                    if packaged is None:
                        continue
                    pure = PurePosixPath(packaged)
                    if (
                        pure.is_absolute()
                        or ".." in pure.parts
                        or packaged not in names
                    ):
                        raise ValueError(f"invalid package link: {packaged}")
                    payload = archive.read(packaged)
                    if item.get("digest") and _sha256(payload) != item["digest"]:
                        raise ValueError(f"resource digest mismatch: {packaged}")
                    extracted = report_path.parent.joinpath(*pure.parts)
                    if not extracted.is_file() or extracted.read_bytes() != payload:
                        raise ValueError(f"extracted resource mismatch: {packaged}")
            verified.append(case_id)
        except (KeyError, OSError, ValueError, zipfile.BadZipFile) as error:
            failures.append({"case_id": case_id, "error": str(error)})
    return {
        "schema_version": 1,
        "reports": len(reports),
        "verified": len(verified),
        "failures": failures,
        "case_ids": verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--expected", type=int)
    args = parser.parse_args()
    result = verify(args.root, args.expected)
    print(json.dumps(result, indent=2))
    return 1 if result["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
