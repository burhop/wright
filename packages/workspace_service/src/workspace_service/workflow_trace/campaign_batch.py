"""Batch inventory and portable exports for retained engineering campaigns."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import zipfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import build_canonical_trace, canonical_artifact_paths
from .export import ExportMode, TraceExportResource, build_trace_export


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _attempt_number(path: Path) -> int:
    match = re.fullmatch(r"attempt-(\d+)", path.parent.name)
    return int(match.group(1)) if match else -1


def _family(case_id: str) -> str:
    return re.sub(r"-\d+$", "", case_id)


def build_campaign_inventory(bundle: Path, completed_manifest: Path) -> dict[str, Any]:
    """Pin one immutable retained run and input revision for every campaign case."""
    bundle = bundle.resolve(strict=True)
    status = json.loads((bundle / "status.json").read_text(encoding="utf-8"))
    manifest = json.loads(completed_manifest.read_text(encoding="utf-8"))
    completed = {
        item["case_id"]: item
        for item in manifest.get("selection", [])
        if isinstance(item, Mapping) and isinstance(item.get("case_id"), str)
    }
    datasets = {
        item["scenario_id"]: item
        for item in status.get("datasets", [])
        if isinstance(item, Mapping) and isinstance(item.get("scenario_id"), str)
    }
    with sqlite3.connect(bundle / "campaign.sqlite3") as database:
        revisions = {
            fingerprint: json.loads(document)
            for fingerprint, document in database.execute(
                "SELECT fingerprint, document FROM dataset_revisions"
            )
        }
    cases = []
    for case_id in sorted(datasets):
        selected = completed.get(case_id)
        reason = "completed acceptance selection"
        if selected is None:
            attempts = sorted(
                (bundle / "output" / case_id).glob("attempt-*/run.json"),
                key=_attempt_number,
            )
            if not attempts:
                raise ValueError(f"campaign case has no retained run: {case_id}")
            run_path = attempts[-1].relative_to(bundle).as_posix()
            reason = "latest retained incomplete attempt"
        else:
            run_path = str(selected["run_path"])
        source = (bundle / run_path).resolve(strict=True)
        source.relative_to(bundle)
        record = json.loads(source.read_text(encoding="utf-8"))
        if record.get("scenario_id") != case_id:
            raise ValueError(f"campaign identity mismatch: {run_path}")
        dataset = datasets[case_id]
        revision_key = f"{record.get('dataset_digest')}/{record.get('template_digest')}"
        revision = revisions.get(revision_key)
        if not isinstance(revision, Mapping):
            raise ValueError(f"campaign dataset revision is unavailable: {case_id}")
        if revision.get("scenario_id") != case_id:
            raise ValueError(f"campaign dataset revision identity mismatch: {case_id}")
        produced = [
            item
            for item in record.get("produced_files", [])
            if isinstance(item, Mapping) and isinstance(item.get("path"), str)
        ]
        missing = []
        for item in produced:
            relative = PurePosixPath(str(item["path"]).replace("\\", "/"))
            if relative.is_absolute() or ".." in relative.parts:
                missing.append(str(item["path"]))
                continue
            artifact = source.parent / "artifacts" / Path(*relative.parts)
            if not artifact.is_file():
                missing.append(str(item["path"]))
        error = str(record.get("error") or "").strip()
        cases.append(
            {
                "case_id": case_id,
                "family": _family(case_id),
                "title": dataset.get("title") or case_id.replace("-", " ").title(),
                "summary": dataset.get("summary"),
                "attempt_id": record.get("attempt_id"),
                "run_id": record.get("run_id"),
                "run_path": run_path,
                "run_sha256": _sha256(source),
                "status": record.get("status"),
                "selection_reason": reason,
                "dataset_digest": record.get("dataset_digest"),
                "template_digest": record.get("template_digest"),
                "dataset_path": revision.get("path"),
                "produced_artifacts": len(produced),
                "produced_bytes": sum(
                    int(item.get("size_bytes") or 0) for item in produced
                ),
                "missing_artifacts": missing,
                "completed_steps": len(record.get("completed_step_ids") or []),
                "required_steps": len(record.get("required_step_ids") or []),
                "error_code": record.get("error_code"),
                "stopping_reason": error or None,
                "known_gaps": [
                    gap
                    for gap, present in (
                        ("run did not complete", record.get("status") != "completed"),
                        ("some produced artifact bytes are unavailable", bool(missing)),
                        ("executed prompts were not retained", True),
                        (
                            "activity timing may be incomplete in this historical record",
                            True,
                        ),
                    )
                    if present
                ],
            }
        )
    metrics = Counter(str(item["status"]) for item in cases)
    return {
        "schema_version": 1,
        "kind": "wright_engineering_campaign_report_inventory",
        "campaign_id": status.get("campaign_id"),
        "source_bundle": str(bundle),
        "source_status_sha256": _sha256(bundle / "status.json"),
        "case_count": len(cases),
        "status_counts": dict(sorted(metrics.items())),
        "selection": [
            {
                "case_id": item["case_id"],
                "attempt_id": item["attempt_id"],
                "run_path": item["run_path"],
            }
            for item in cases
        ],
        "cases": cases,
    }


def _resource_data(workspace: Path, artifact: Mapping[str, Any]) -> bytes | None:
    location = artifact.get("workspace_path")
    if not isinstance(location, str) or not location:
        return None
    relative = PurePosixPath(location.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        return None
    path = (workspace / Path(*relative.parts)).resolve(strict=True)
    path.relative_to(workspace.resolve())
    return path.read_bytes()


def export_resources(
    workspace: Path, inspection: Mapping[str, Any], mode: ExportMode
) -> list[TraceExportResource]:
    """Load the same bounded report resources as the interactive export route."""
    resources = []
    for artifact in canonical_artifact_paths(inspection):
        media_type = str(artifact.get("media_type") or "application/octet-stream")
        size = artifact.get("bytes")
        report_asset = media_type in {
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
        } or (
            media_type == "image/svg+xml"
            and isinstance(size, int)
            and size <= 2 * 1024 * 1024
        )
        readable_record = (
            media_type == "application/json"
            and isinstance(size, int)
            and size <= 2 * 1024 * 1024
        )
        readable_input = (
            artifact.get("role")
            in {
                "input",
                "run_input",
                "input_reconstruction",
                "source_document",
                "review_visualization",
            }
            and media_type in {"text/plain", "text/markdown"}
            and isinstance(size, int)
            and size <= 64 * 1024
        )
        package_metadata = (
            media_type == "model/3mf"
            and isinstance(size, int)
            and size <= 8 * 1024 * 1024
        )
        viewer_source = (
            media_type == "model/stl"
            and isinstance(size, int)
            and size <= 8 * 1024 * 1024
        )
        data = None
        availability = "omitted_from_export" if mode == "report_only" else "retained"
        if (
            mode == "full_data"
            or report_asset
            or readable_record
            or readable_input
            or package_metadata
            or viewer_source
        ):
            try:
                data = _resource_data(workspace, artifact)
            except (FileNotFoundError, OSError, ValueError):
                availability = "missing"
        role = str(artifact.get("role") or "output")
        if role in {"input", "run_input"}:
            role = "input"
        elif role not in {
            "input_reconstruction",
            "source_document",
            "review_visualization",
        }:
            role = "output"
        digest = artifact.get("sha256")
        resources.append(
            TraceExportResource(
                subject_id=str(artifact["artifact_id"]),
                name=str(artifact.get("label") or artifact["artifact_id"]),
                media_type=media_type,
                data=data,
                digest=str(digest)
                if isinstance(digest, str) and len(digest) == 64
                else None,
                role=role,
                availability=availability,
                report_asset=report_asset,
            )
        )
    return resources


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def _catalog(
    entries: Sequence[Mapping[str, Any]], inventory: Mapping[str, Any]
) -> bytes:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for entry in entries:
        groups.setdefault(str(entry["family"]), []).append(entry)
    rows = []
    for family, items in sorted(groups.items()):
        cards = []
        for item in items:
            status = html.escape(str(item["status"]))
            report = html.escape(str(item["report_path"]), quote=True)
            archive = html.escape(str(item["archive_path"]), quote=True)
            cards.append(
                f'<article><div class="state {status}">{status}</div>'
                f"<h3>{html.escape(str(item['title']))}</h3>"
                f"<p>{html.escape(str(item.get('summary') or 'Recorded engineering workflow.'))}</p>"
                f"<dl><dt>Attempt</dt><dd>{html.escape(str(item['attempt_id']))}</dd>"
                f"<dt>Outputs</dt><dd>{item['produced_artifacts']}</dd></dl>"
                f'<a class="primary" href="{report}">Open engineering review</a>'
                f'<a href="{archive}">Download ZIP</a></article>'
            )
        rows.append(
            f'<section><h2>{html.escape(family.replace("-", " ").title())}</h2><div class="grid">{"".join(cards)}</div></section>'
        )
    counts = inventory.get("status_counts") or {}
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Engineering campaign reviews</title><style>
body{{font:16px/1.45 system-ui,sans-serif;color:#1d2b27;margin:0;background:#f6f8f7}}main{{max-width:1180px;margin:auto;padding:32px}}header{{border-bottom:1px solid #cad6d1;padding-bottom:24px}}h1{{font-size:2rem;margin:.2rem 0}}h2{{margin-top:36px}}.summary{{color:#536760}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}article{{background:white;border:1px solid #ccd8d3;padding:18px;border-radius:6px}}h3{{margin:.4rem 0}}dl{{display:grid;grid-template-columns:auto 1fr;gap:3px 12px}}dt{{color:#64756f}}dd{{margin:0}}a{{display:inline-block;margin:10px 14px 0 0;color:#006b57}}a.primary{{font-weight:700}}.state{{font-size:.75rem;text-transform:uppercase;font-weight:700;color:#08785e}}.state.failed{{color:#9a3e25}}@media(max-width:560px){{main{{padding:20px}}}}
</style></head><body><main><header><div>Wright engineering review</div><h1>Campaign report catalog</h1><p class="summary">{len(entries)} pinned reports: {counts.get("completed", 0)} completed and {counts.get("failed", 0)} stopped with recorded blockers. Every link is package-relative and works offline.</p></header>{"".join(rows)}</main></body></html>""".encode(
        "utf-8"
    )


def export_prepared_campaign(
    workspace: Path,
    inventory: Mapping[str, Any],
    output: Path,
    *,
    mode: ExportMode,
    case_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Export selected prepared runs, extract their viewers, and write a catalog."""
    workspace = workspace.resolve(strict=True)
    output = output.resolve()
    selected = set(case_ids or ())
    index = json.loads(
        (workspace / "trace-review-index.json").read_text(encoding="utf-8")
    )
    indexed = {item["case_id"]: item for item in index["runs"]}
    cases = {item["case_id"]: item for item in inventory["cases"]}
    requested = sorted(selected or cases.keys())
    unknown = set(requested) - cases.keys()
    if unknown:
        raise ValueError(f"unknown campaign cases: {', '.join(sorted(unknown))}")
    entries = []
    for case_id in requested:
        metadata = cases[case_id]
        prepared = indexed.get(case_id)
        if prepared is None:
            raise ValueError(f"campaign case was not prepared: {case_id}")
        run_path = workspace / prepared["run_path"]
        record = json.loads(run_path.read_text(encoding="utf-8"))
        inspection = build_canonical_trace(
            record,
            workspace_id="campaign-review",
            session_id="offline-export",
            path=prepared["run_path"],
        )
        resources = export_resources(workspace, inspection, mode)
        archive_data = build_trace_export(
            inspection=inspection,
            evidence={
                "run_id": record.get("run_id"),
                "source": "pinned-campaign-run-record",
                "input_provenance": record.get("trace_input_pack"),
                "authorization": {
                    key: record[key]
                    for key in (
                        "approval_actor",
                        "approval_evidence",
                        "execution_kind",
                        "external_effects",
                    )
                    if key in record
                },
                "approval_events": [
                    event
                    for event in record.get("step_events", [])
                    if event.get("kind") == "approval_decided"
                ],
            },
            mode=mode,
            resources=resources,
            source_record=record,
        )
        archive_relative = Path("packages") / f"{case_id}-{mode.replace('_', '-')}.zip"
        archive_path = output / archive_relative
        _write_atomic(archive_path, archive_data)
        report_relative = Path("reports") / case_id / mode
        report_path = output / report_relative
        if report_path.exists():
            shutil.rmtree(report_path)
        report_path.mkdir(parents=True)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(report_path)
        entries.append(
            {
                **metadata,
                "mode": mode,
                "archive_path": archive_relative.as_posix(),
                "archive_sha256": _sha256(archive_path),
                "archive_bytes": archive_path.stat().st_size,
                "report_path": (report_relative / "index.html").as_posix(),
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    catalog = {"schema_version": 1, "mode": mode, "reports": entries}
    _write_atomic(
        output / "catalog.json", json.dumps(catalog, indent=2).encode() + b"\n"
    )
    _write_atomic(
        output / "inventory.json", json.dumps(inventory, indent=2).encode() + b"\n"
    )
    _write_atomic(output / "index.html", _catalog(entries, inventory))
    return catalog


__all__ = [
    "build_campaign_inventory",
    "export_prepared_campaign",
    "export_resources",
]
