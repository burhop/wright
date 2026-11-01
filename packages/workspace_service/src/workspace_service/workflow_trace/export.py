"""Self-contained, file-origin workflow review package rendering."""

from __future__ import annotations

import base64
import hashlib
import html
import io
import json
import re
import zipfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from .review_model import build_review_model


ExportMode = Literal["report_only", "full_data"]


@dataclass(frozen=True, slots=True)
class TraceExportResource:
    subject_id: str
    name: str
    media_type: str
    data: bytes | None
    digest: str | None
    role: str = "output"
    availability: str = "retained"
    report_asset: bool = False


def _safe_name(value: str, fallback: str) -> str:
    leaf = PurePosixPath(value.replace("\\", "/")).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", leaf).strip(".-")
    return cleaned[:180] or fallback


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, indent=2, default=str
    ).encode("utf-8")


def _html(
    review: Mapping[str, Any],
    manifest: Mapping[str, Any],
    viewer_models: Mapping[str, Any],
    viewer_documents: Mapping[str, Any],
) -> bytes:
    model = json.dumps(
        {
            "review": review,
            "manifest": manifest,
            "viewerModels": viewer_models,
            "viewerDocuments": viewer_documents,
        },
        ensure_ascii=False,
        default=str,
    ).replace("<", "\\u003c")
    assets = Path(__file__).parent / "portable"
    css = (assets / "review.css").read_text(encoding="utf-8")
    script = (assets / "document-viewer.js").read_text(encoding="utf-8") + (
        assets / "review.js"
    ).read_text(encoding="utf-8")
    viewer = (
        (assets / "stl-viewer.js").read_text(encoding="utf-8") if viewer_models else ""
    )
    if viewer_documents:
        viewer += (assets / "pdf-viewer.js").read_text(encoding="utf-8")
    title = html.escape(str(review["title"]))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; worker-src blob:; style-src 'unsafe-inline'; img-src 'self' data: file: blob:; connect-src 'none'; base-uri 'none'; object-src 'none'">
<title>{title} | Engineering review</title><style>{css}</style></head>
<body><main id="report"></main><dialog id="detail" aria-labelledby="detail-title"></dialog>
<script id="wright-trace-data" type="application/json">{model}</script>{f"<script>{viewer}</script>" if viewer else ""}<script>{script}</script></body></html>""".encode(
        "utf-8"
    )


def build_trace_export(
    *,
    inspection: Mapping[str, Any],
    evidence: Mapping[str, Any],
    mode: ExportMode,
    resources: Iterable[TraceExportResource] = (),
    source_record: Mapping[str, Any] | None = None,
) -> bytes:
    if mode not in {"report_only", "full_data"}:
        raise ValueError("unsupported trace export mode")
    resource_list = list(resources)
    entries: list[dict[str, Any]] = []
    payloads: list[tuple[str, bytes]] = []
    used_paths: set[str] = set()
    for index, resource in enumerate(resource_list, start=1):
        included = resource.data is not None and (
            mode == "full_data" or resource.report_asset
        )
        package_path = None
        digest = resource.digest
        availability = resource.availability
        if resource.data is not None:
            actual = hashlib.sha256(resource.data).hexdigest()
            if digest is not None and actual != digest:
                raise ValueError(
                    f"trace export resource digest mismatch: {resource.subject_id}"
                )
            digest = actual
        if included:
            filename = _safe_name(resource.name, f"resource-{index}")
            role = _safe_name(resource.role, "output")
            prefix = (
                "inputs/reconstructed"
                if resource.role == "input_reconstruction"
                else "evidence/visualizations"
                if resource.role == "review_visualization"
                else "evidence/sources"
                if resource.role == "source_document"
                else "inputs"
                if resource.role in {"input", "run_input"} and mode == "full_data"
                else "assets/previews"
                if mode == "report_only" and resource.report_asset
                else f"outputs/{role}"
            )
            candidate = f"{prefix}/{filename}"
            suffix = 2
            while candidate in used_paths:
                candidate = f"{prefix}/{index}-{suffix}-{filename}"
                suffix += 1
            used_paths.add(candidate)
            package_path = candidate
            payloads.append((candidate, resource.data or b""))
            availability = "included"
        elif resource.data is not None:
            availability = "omitted_from_export"
        entries.append(
            {
                "subject_id": resource.subject_id,
                "name": resource.name,
                "role": resource.role,
                "media_type": resource.media_type,
                "package_path": package_path,
                "digest": digest,
                "bytes": len(resource.data) if resource.data is not None else None,
                "availability": availability,
                "report_asset": resource.report_asset,
            }
        )
    report = dict(inspection)
    report["evidence"] = dict(evidence)
    review = build_review_model(inspection, resource_list, source_record)
    resource_by_subject = {resource.subject_id: resource for resource in resource_list}
    document_by_id = {document["id"]: document for document in review["documents"]}
    viewer_models = {}
    mesh_budget = 32 * 1024 * 1024
    for document_id in review.get(
        "geometry_models", review.get("interactive_models", [])
    ):
        document = document_by_id.get(document_id)
        resource = (
            resource_by_subject.get(document.get("subject_id")) if document else None
        )
        if (
            resource is not None
            and resource.media_type == "model/stl"
            and resource.data
            and len(resource.data) <= min(mesh_budget, 8 * 1024 * 1024)
        ):
            viewer_models[document_id] = {
                "base64": base64.b64encode(resource.data).decode("ascii"),
                "bytes": len(resource.data),
                "digest": hashlib.sha256(resource.data).hexdigest(),
            }
            mesh_budget -= len(resource.data)
        elif document:
            document["viewer_unavailable_reason"] = (
                "The retained model exceeds the inline viewer budget or its bytes are unavailable."
            )
    viewer_documents = {}
    included_subjects = {
        entry["subject_id"] for entry in entries if entry["package_path"]
    }
    pdf_budget = 32 * 1024 * 1024
    for document in review["documents"]:
        resource = resource_by_subject.get(document["subject_id"])
        if resource is None or resource.media_type != "application/pdf":
            continue
        if resource.subject_id not in included_subjects:
            document["viewer_unavailable_reason"] = (
                "The PDF is not included in this export."
            )
        elif resource.data and len(resource.data) <= min(pdf_budget, 16 * 1024 * 1024):
            viewer_documents[document["id"]] = {
                "base64": base64.b64encode(resource.data).decode("ascii"),
                "digest": hashlib.sha256(resource.data).hexdigest(),
            }
            pdf_budget -= len(resource.data)
        else:
            document["viewer_unavailable_reason"] = (
                "This PDF exceeds the inline viewer size limit; the original is available below."
            )
    assets = Path(__file__).parent / "portable"
    license_paths = [assets / "DOCUMENT-LICENSES.txt"]
    if viewer_models:
        license_paths.append(assets / "THREE-LICENSE.txt")
    if viewer_documents:
        license_paths.extend(sorted(assets.glob("PDFJS-*.txt")))
    viewer_licenses = []
    for license_path in license_paths:
        data = license_path.read_bytes()
        path = f"assets/licenses/{license_path.name}"
        payloads.append((path, data))
        viewer_licenses.append(
            {
                "name": license_path.name,
                "package_path": path,
                "digest": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    manifest = {
        "schema_version": 1,
        "mode": mode,
        "run_id": (inspection.get("run") or {}).get("run_id"),
        "entries": entries,
        "viewer_licenses": viewer_licenses,
        "viewer_capabilities": {
            "stl": "interactive-offline-viewer"
            if viewer_models
            else "original-file-when-available",
            "step": "recorded-preview-and-original-when-available",
            "3mf": "recorded-preview-and-original-when-available",
            "interactive_viewer_bundled": bool(viewer_models or viewer_documents),
            "pdf": "interactive-offline-viewer"
            if viewer_documents
            else "original-file-when-available",
        },
    }
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, data in (
            ("index.html", _html(review, manifest, viewer_models, viewer_documents)),
            ("manifest.json", _json_bytes(manifest)),
            ("report/report.json", _json_bytes(report)),
            ("evidence/run-evidence.json", _json_bytes(evidence)),
            *payloads,
        ):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            bundle.writestr(entry, data)
    return archive.getvalue()


__all__ = ["TraceExportResource", "build_trace_export"]
