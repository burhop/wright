#!/usr/bin/env python3
"""Validate, classify, and build standalone Wright integration status artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from uuid import uuid4

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "tool_registry" / "src"))

from tool_registry.canonical_catalog import load_canonical_entries  # noqa: E402
from engineering_mcp_status import (  # noqa: E402
    build_engineering_status,
    history_snapshot,
    load_assessments,
    public_projection,
    qa_projection,
    record_history,
    semantic_sha256,
)

STATUS_DIR = ROOT / "docs" / "mcp-catalog" / "status"
DEFAULT_ASSESSMENTS = STATUS_DIR / "assessments.yaml"
ASSESSMENTS_SCHEMA = STATUS_DIR / "assessments.schema.json"
STATUS_SCHEMA = STATUS_DIR / "status.schema.json"
HISTORY_SCHEMA = STATUS_DIR / "history.schema.json"


def _validate(payload: dict, schema_path: Path, label: str) -> None:
    schema = json.loads(schema_path.read_text("utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        details = "; ".join(
            f"{'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ValueError(f"Invalid {label}: {details}")


def _assert_accounting(status: dict, catalog_ids: set[str]) -> None:
    record_ids = [record["server_id"] for record in status["records"]]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("Status contains duplicate canonical IDs")
    if set(record_ids) != catalog_ids:
        raise ValueError("Status membership differs from the canonical catalog")
    derived = {
        item["id"]: sum(record["portfolio_category"] == item["id"] for record in status["records"])
        for item in status["category_key"]
    }
    if derived != status["category_counts"] or sum(derived.values()) != status["total"]:
        raise ValueError("Status category accounting does not reconcile")
    if status["green"]["count"] != sum(status["green"]["components"].values()):
        raise ValueError("Green component accounting does not reconcile")
    if status["fully_qualified_count"] != status["category_counts"]["works"]:
        raise ValueError("Fully qualified count differs from Works")


def _assert_public_safe(payload: dict) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    forbidden_keys = {
        "owner", "evidence_href", "evidence_sha256", "failure", "restriction_reference",
        "command", "log", "raw_log", "tenant_id", "account_id",
    }
    forbidden_fragments = ("file://", "D:\\\\", "C:\\\\", "/home/", "/Users/", "\\\\.\\pipe\\")

    def walk(value):
        if isinstance(value, dict):
            overlap = forbidden_keys & set(value)
            if overlap:
                raise ValueError(f"Public projection contains QA-only fields: {sorted(overlap)}")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    if any(fragment.lower() in serialized.lower() for fragment in forbidden_fragments):
        raise ValueError("Public projection contains a local path")


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _stage_output(
    destination: Path,
    *,
    status: dict,
    history: dict,
    evidence_payloads: dict | None,
    include_publishing_handoff: bool = False,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    # tempfile.mkdtemp intentionally creates a private directory. On Windows its
    # restrictive ACL survives the atomic rename and prevents the standalone
    # dashboard process from reading the published files. A random sibling made
    # with normal directory creation inherits the repository's permissions.
    stage = destination.parent / f".{destination.name}-{uuid4().hex}"
    stage.mkdir()
    _write_json(stage / "status.json", status)
    _write_json(stage / "history.json", history)
    shutil.copyfile(ROOT / "scripts" / "engineering-mcp-dashboard.html", stage / "index.html")
    shutil.copyfile(STATUS_SCHEMA, stage / "status.schema.json")
    shutil.copyfile(HISTORY_SCHEMA, stage / "history.schema.json")
    public_readme = STATUS_DIR / "public-readme.md"
    if public_readme.exists():
        shutil.copyfile(public_readme, stage / "README.md")
    if include_publishing_handoff:
        shutil.copyfile(
            ROOT / "docs" / "mcp-status" / "PUBLISHING.md",
            stage / "PUBLISHING.md",
        )
    if evidence_payloads:
        evidence_dir = stage / "evidence"
        evidence_dir.mkdir()
        for evidence_id, payload in evidence_payloads.items():
            (evidence_dir / f"{evidence_id}.json").write_text(payload["content"], encoding="utf-8")
    return stage


def _publish(stage: Path, destination: Path) -> None:
    backup = destination.with_name(f".{destination.name}.last-good")
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        destination.rename(backup)
    try:
        stage.rename(destination)
    except Exception:
        if backup.exists() and not destination.exists():
            backup.rename(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", type=date.fromisoformat, default=datetime.now(UTC).date())
    parser.add_argument("--process-chains", type=Path)
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--assessments", type=Path, default=DEFAULT_ASSESSMENTS)
    parser.add_argument("--history", type=Path)
    parser.add_argument("--record-snapshot", action="store_true")
    parser.add_argument("--change-reason")
    parser.add_argument("--correction-for")
    parser.add_argument("--correction-reason")
    parser.add_argument("--output-dir", type=Path, help="Legacy alias for --qa-output")
    parser.add_argument("--qa-output", type=Path)
    parser.add_argument("--public-output", type=Path)
    args = parser.parse_args()
    qa_output = args.qa_output or args.output_dir
    if qa_output is None and args.public_output is None:
        parser.error("at least one output directory is required")

    entries = load_canonical_entries()
    catalog_ids = {entry.id for entry in entries}
    assessments = load_assessments(
        args.assessments.resolve(), catalog_ids=catalog_ids, schema_path=ASSESSMENTS_SCHEMA
    )
    previous = json.loads(args.previous_report.read_text("utf-8")) if args.previous_report else None
    result = build_engineering_status(
        entries,
        as_of=args.as_of,
        repository_root=ROOT,
        process_chains_path=args.process_chains.resolve() if args.process_chains else None,
        previous_report=previous,
        assessments=assessments,
    )
    evidence_payloads = result["evidence_payloads"]
    qa = qa_projection(result)
    public = public_projection(result)
    _assert_accounting(qa, catalog_ids)
    _assert_accounting(public, catalog_ids)
    _assert_public_safe(public)
    _validate(qa, STATUS_SCHEMA, "QA status")
    _validate(public, STATUS_SCHEMA, "public status")
    if qa["category_counts"] != public["category_counts"]:
        raise ValueError("Public and QA category counts differ")

    history = json.loads(args.history.read_text("utf-8")) if args.history and args.history.exists() else None
    if args.record_snapshot:
        snapshot = history_snapshot(qa, observed_at=result["generated_at"])
        snapshot_already_recorded = bool(
            history
            and any(
                item["snapshot_id"] == snapshot["snapshot_id"]
                for item in history.get("snapshots", [])
            )
        )
        if history and history.get("snapshots") and not args.correction_for and not snapshot_already_recorded:
            if not args.change_reason:
                raise ValueError("A new snapshot after the initial observation requires --change-reason")
            snapshot["change_reason"] = args.change_reason
        history, _ = record_history(
            history,
            snapshot,
            correction_for=args.correction_for,
            correction_reason=args.correction_reason,
        )
    history = history or {"schema_version": 1, "snapshots": []}
    _validate(history, HISTORY_SCHEMA, "status history")

    staged: list[tuple[Path, Path]] = []
    try:
        if qa_output:
            destination = qa_output.resolve()
            staged.append((_stage_output(destination, status=qa, history=history, evidence_payloads=evidence_payloads), destination))
        if args.public_output:
            destination = args.public_output.resolve()
            staged.append((
                _stage_output(
                    destination,
                    status=public,
                    history=history,
                    evidence_payloads=None,
                    include_publishing_handoff=True,
                ),
                destination,
            ))
        for stage, destination in staged:
            _publish(stage, destination)
    finally:
        for stage, _ in staged:
            if stage.exists():
                shutil.rmtree(stage)

    print(json.dumps({
        "snapshot_id": qa["snapshot_id"],
        "total": qa["total"],
        "category_counts": qa["category_counts"],
        "green": qa["green"],
        "qa_semantic_sha256": semantic_sha256(qa),
        "public_semantic_sha256": semantic_sha256(public),
        "history_points": len(history["snapshots"]),
        "qa_output": str(qa_output.resolve()) if qa_output else None,
        "public_output": str(args.public_output.resolve()) if args.public_output else None,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
