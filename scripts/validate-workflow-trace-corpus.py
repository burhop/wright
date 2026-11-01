#!/usr/bin/env python3
"""Validate retained campaign runs against the feature-083 Trace projection."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import zipfile
from collections import defaultdict
from io import BytesIO
from pathlib import Path, PurePosixPath


REPO_ROOT = Path(__file__).resolve().parents[1]
for package in ("core", "data_vault", "workspace_service"):
    sys.path.insert(0, str(REPO_ROOT / "packages" / package / "src"))

from workspace_service.workflow_trace.canonical import (  # noqa: E402
    build_canonical_trace,
    canonical_artifact_paths,
)
from workspace_service.workflow_trace.export import (  # noqa: E402
    TraceExportResource,
    build_trace_export,
)


def _attempt_number(value: str) -> int:
    try:
        return int(value.rsplit("-", 1)[-1])
    except ValueError:
        return -1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _completed_attempts(database: Path) -> dict[str, list[str]]:
    connection = sqlite3.connect(database)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise ValueError(f"campaign database integrity check failed: {integrity}")
        rows = connection.execute(
            "SELECT scenario_id, document FROM attempts WHERE completed = 1"
        ).fetchall()
    finally:
        connection.close()
    attempts: dict[str, list[str]] = defaultdict(list)
    for scenario_id, document in rows:
        record = json.loads(document)
        attempt_id = record.get("attempt_id")
        if isinstance(scenario_id, str) and isinstance(attempt_id, str):
            attempts[scenario_id].append(attempt_id)
    return attempts


def _selection(path: Path) -> list[str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    selected = value.get("selection")
    if not isinstance(selected, list):
        raise ValueError("corpus selection is unavailable")
    case_ids = [item.get("case_id") for item in selected if isinstance(item, dict)]
    if len(case_ids) != 24 or any(not isinstance(value, str) for value in case_ids):
        raise ValueError("corpus selection must contain exactly 24 case identities")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("corpus selection contains duplicate case identities")
    return case_ids


def _artifact_path(bundle: Path, run_path: PurePosixPath, value: dict) -> Path:
    raw = value.get("path")
    if not isinstance(raw, str):
        raise ValueError("campaign artifact path is unavailable")
    relative = PurePosixPath(raw.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"campaign artifact path is unsafe: {raw}")
    return bundle.joinpath(*run_path.parent.parts, "artifacts", *relative.parts)


def validate(bundle: Path, selection_path: Path) -> dict:
    bundle = bundle.resolve(strict=True)
    database = bundle / "campaign.sqlite3"
    bundle_record = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    selected = _selection(selection_path)
    attempts = _completed_attempts(database)
    results = []
    for case_id in selected:
        available = attempts.get(case_id, [])
        if not available:
            raise ValueError(f"no completed campaign attempt exists for {case_id}")
        attempt_id = max(available, key=_attempt_number)
        relative_run = PurePosixPath("output") / case_id / attempt_id / "run.json"
        run_path = bundle.joinpath(*relative_run.parts)
        record = json.loads(run_path.read_text(encoding="utf-8"))
        if record.get("scenario_id") != case_id or record.get("attempt_id") != attempt_id:
            raise ValueError(f"campaign identity mismatch in {relative_run}")
        if record.get("status") != "completed":
            raise ValueError(f"selected campaign run is not completed: {relative_run}")

        artifact_bytes = 0
        for artifact in record.get("produced_files", ()):
            if not isinstance(artifact, dict):
                raise ValueError(f"invalid produced-file entry in {relative_run}")
            artifact_path = _artifact_path(bundle, relative_run, artifact)
            size = artifact_path.stat().st_size
            if size != artifact.get("size_bytes"):
                raise ValueError(f"artifact size mismatch: {artifact_path}")
            if _sha256(artifact_path) != artifact.get("sha256"):
                raise ValueError(f"artifact digest mismatch: {artifact_path}")
            artifact_bytes += size

        trace = build_canonical_trace(
            record,
            workspace_id="campaign-081",
            session_id="retained-evidence",
            path=str(relative_run),
        )
        if trace["run"]["state"] != "succeeded":
            raise ValueError(f"Trace outcome mismatch: {relative_run}")
        if not trace["final_outputs"] or len(trace["final_outputs"]) > 12:
            raise ValueError(f"Trace primary-result projection is invalid: {relative_run}")
        if not trace["completeness"]["outputs_complete"]:
            raise ValueError(f"Trace output projection is incomplete: {relative_run}")
        graph_nodes = {item["node_id"] for item in trace["graph"]["nodes"]}
        if not set(record.get("required_step_ids", ())).issubset(graph_nodes):
            raise ValueError(f"Trace graph omitted a required step: {relative_run}")
        package = build_trace_export(
            inspection=trace,
            evidence={"source": "campaign-081", "content_validated": False},
            mode="report_only",
            resources=[
                TraceExportResource(
                    subject_id=artifact["artifact_id"],
                    name=artifact["label"],
                    media_type=artifact["media_type"],
                    data=None,
                    digest=artifact["sha256"],
                    role=artifact.get("role", "output"),
                    availability="retained",
                )
                for artifact in canonical_artifact_paths(trace)
            ],
        )
        with zipfile.ZipFile(BytesIO(package)) as archive:
            names = set(archive.namelist())
            if {"index.html", "manifest.json", "report/report.json"} - names:
                raise ValueError(f"Trace report package is incomplete: {relative_run}")
            exported = json.loads(archive.read("report/report.json"))
            if exported["run"]["run_id"] != record["run_id"]:
                raise ValueError(f"Trace report identity mismatch: {relative_run}")
            manifest = json.loads(archive.read("manifest.json"))
            if len(manifest["entries"]) != len(record.get("produced_files", ())):
                raise ValueError(f"Trace report omitted an artifact: {relative_run}")
        results.append(
            {
                "case_id": case_id,
                "attempt_id": attempt_id,
                "run_id": record["run_id"],
                "run_path": str(relative_run),
                "artifact_count": len(record.get("produced_files", ())),
                "artifact_bytes": artifact_bytes,
                "step_occurrences": len(trace["steps"]),
                "primary_results": len(trace["final_outputs"]),
                "trace_acceptance": "passed",
                "content_validated": False,
            }
        )
    return {
        "schema_version": 1,
        "bundle_id": bundle_record.get("bundle_id"),
        "campaign_id": bundle_record.get("campaign_id"),
        "sha256sums_digest": _sha256(bundle / "SHA256SUMS.txt"),
        "selected_cases": len(results),
        "trace_acceptance_passed": sum(
            result["trace_acceptance"] == "passed" for result in results
        ),
        "content_validated": 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--selection",
        type=Path,
        default=REPO_ROOT
        / "specs"
        / "083-workflow-trace-review"
        / "evidence"
        / "corpus-manifest.json",
    )
    args = parser.parse_args()
    print(json.dumps(validate(args.bundle, args.selection), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
