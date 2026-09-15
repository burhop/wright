"""Local, lineage-bound capture packages for verified engineering runs."""

from __future__ import annotations

import hashlib
import io
import json
import re
import time
import zipfile
from pathlib import PurePosixPath
from typing import Any, Mapping, Sequence


class WorkflowDemoCaptureError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


_SENSITIVE_KEY = re.compile(
    r"(?:password|secret|token|api[_-]?key|credential|card|cvv)", re.I
)
_SENSITIVE_TEXT = re.compile(
    r"(?:AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]+PRIVATE KEY-----|(?:password|api[_-]?key|token)\s*[:=]\s*\S+)",
    re.I,
)
_PRIVATE_PATH = re.compile(r"(?:[A-Za-z]:\\Users\\[^\\\s]+|/home/[^/\s]+)")
_TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".svg", ".html", ".xml"}


def _reject_sensitive(value: Any, path: str = "capture") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or _SENSITIVE_KEY.search(key):
                raise WorkflowDemoCaptureError(
                    "capture_sensitive_content",
                    f"Remove credentials or payment data from {path} before capture.",
                )
            _reject_sensitive(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_sensitive(item, f"{path}[{index}]")
    elif isinstance(value, str) and (
        _SENSITIVE_TEXT.search(value) or _PRIVATE_PATH.search(value)
    ):
        raise WorkflowDemoCaptureError(
            "capture_sensitive_content",
            f"Remove secrets or private host paths from {path} before capture.",
        )


def _all_results(results: Sequence[Mapping[str, Any]]):
    for result in results:
        yield result
        exports = result.get("exports", [])
        if isinstance(exports, list):
            yield from _all_results(
                [item for item in exports if isinstance(item, Mapping)]
            )


class WorkflowDemoCaptureService:
    def __init__(self, files) -> None:
        self._files = files

    async def create(
        self,
        *,
        workspace_dir: str,
        run_log_path: str,
        expected_run_id: str,
        artifact_ids: Sequence[str],
        caption: str,
    ) -> dict[str, Any]:
        if (
            not isinstance(run_log_path, str)
            or not run_log_path.startswith("runs/")
            or PurePosixPath(run_log_path).suffix != ".json"
        ):
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "Choose a saved Wright workflow run."
            )
        if (
            not isinstance(caption, str)
            or not caption.strip()
            or len(caption.encode("utf-8")) > 8_000
        ):
            raise WorkflowDemoCaptureError(
                "capture_caption_invalid", "Enter a bounded caption draft."
            )
        if (
            not isinstance(artifact_ids, Sequence)
            or isinstance(artifact_ids, (str, bytes))
            or not 1 <= len(artifact_ids) <= 12
            or len(set(artifact_ids)) != len(artifact_ids)
            or not all(isinstance(item, str) and item for item in artifact_ids)
        ):
            raise WorkflowDemoCaptureError(
                "capture_artifacts_invalid",
                "Select one to twelve distinct run artifacts.",
            )
        raw = await self._files.read_reference(workspace_dir, run_log_path)
        if len(raw) > 16 * 1024 * 1024:
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "The saved run exceeds the capture limit."
            )
        try:
            record = json.loads(raw)
        except (UnicodeDecodeError, ValueError) as error:
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "The saved run record is invalid."
            ) from error
        if not isinstance(record, dict):
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "The saved run record is invalid."
            )
        result = record.get("result")
        verification = result.get("verification") if isinstance(result, dict) else None
        rights = result.get("capture_rights") if isinstance(result, dict) else None
        if record.get("status") != "completed" or not (
            isinstance(verification, dict)
            and verification.get("status") == "verified"
            and isinstance(verification.get("assertions"), list)
            and verification["assertions"]
        ):
            raise WorkflowDemoCaptureError(
                "capture_run_unverified",
                "Only a completed run with recorded engineering verification can be captured.",
            )
        if not expected_run_id or result.get("run_id") != expected_run_id:
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "The capture request does not match this run."
            )
        if not (
            isinstance(rights, dict)
            and rights.get("capture_allowed") is True
            and isinstance(rights.get("attribution"), str)
            and rights["attribution"].strip()
        ):
            raise WorkflowDemoCaptureError(
                "capture_rights_missing",
                "Record approved input rights and attribution before capture.",
            )
        results = result.get("results", [])
        if not isinstance(results, list):
            raise WorkflowDemoCaptureError(
                "capture_run_invalid", "The run has no valid engineering results."
            )
        by_id = {
            item["id"]: item
            for item in _all_results(
                [candidate for candidate in results if isinstance(candidate, Mapping)]
            )
            if isinstance(item.get("id"), str)
        }
        if any(artifact_id not in by_id for artifact_id in artifact_ids):
            raise WorkflowDemoCaptureError(
                "capture_artifact_not_found",
                "A selected artifact does not belong to this exact run.",
            )
        _reject_sensitive(caption, "caption")
        _reject_sensitive(rights, "rights")
        _reject_sensitive(verification, "verification")

        selected = []
        payloads: list[tuple[str, bytes]] = []
        total = 0
        for artifact_id in artifact_ids:
            item = by_id[artifact_id]
            representations = item.get("representations", [])
            representation = next(
                (
                    rep
                    for rep in representations
                    if isinstance(rep, dict)
                    and rep.get("kind") == "workspace_file"
                    and rep.get("durability") == "persistent"
                    and isinstance(rep.get("sha256"), str)
                ),
                None,
            )
            if not representation:
                raise WorkflowDemoCaptureError(
                    "capture_artifact_not_local",
                    "Every capture artifact must be a persistent verified workspace file.",
                )
            path = representation.get("location")
            if not isinstance(path, str) or PurePosixPath(path).is_absolute():
                raise WorkflowDemoCaptureError(
                    "capture_artifact_not_local", "A capture artifact path is unsafe."
                )
            reader = getattr(
                self._files, "read_capture_file", self._files.read_reference
            )
            content = await reader(workspace_dir, path)
            digest = hashlib.sha256(content).hexdigest()
            if digest != representation["sha256"] or (
                representation.get("size_bytes") is not None
                and len(content) != representation["size_bytes"]
            ):
                raise WorkflowDemoCaptureError(
                    "capture_artifact_changed",
                    "A selected artifact changed after verification; run verification again.",
                )
            total += len(content)
            if len(content) > 20 * 1024 * 1024 or total > 64 * 1024 * 1024:
                raise WorkflowDemoCaptureError(
                    "capture_artifacts_too_large",
                    "The selected capture exceeds 64 MiB.",
                )
            if PurePosixPath(path).suffix.lower() in _TEXT_EXTENSIONS:
                try:
                    _reject_sensitive(content.decode("utf-8"), path)
                except UnicodeDecodeError as error:
                    raise WorkflowDemoCaptureError(
                        "capture_artifact_invalid",
                        f"The text artifact {path} is not valid UTF-8.",
                    ) from error
            archive_name = (
                f"artifacts/{len(payloads) + 1:02d}-{PurePosixPath(path).name}"
            )
            payloads.append((archive_name, content))
            selected.append(
                {
                    "id": artifact_id,
                    "name": item.get("name"),
                    "artifact_role": item.get("artifact_role", "deliverable"),
                    "archive_path": archive_name,
                    "source_path": path,
                    "sha256": digest,
                    "size_bytes": len(content),
                    "provenance": item.get("provenance"),
                }
            )
        manifest = {
            "schema_version": 1,
            "kind": "wright_engineering_demo_capture",
            "created_at": int(time.time()),
            "source": {
                "run_id": result.get("run_id"),
                "run_log_path": run_log_path,
                "workflow_path": record.get("workflow_path"),
                "definition_digest": record.get("source_digest"),
            },
            "verification": verification,
            "rights": rights,
            "artifacts": selected,
            "disclosures": {
                "fixture_or_simulation": result.get("evidence_class", "live") != "live",
                "external_action_outcome": (
                    (result.get("approval") or {}).get("external_action") or {}
                ).get("outcome"),
                "physical_completion_claimed": False,
                "published": False,
            },
        }
        _reject_sensitive(manifest)
        manifest_bytes = json.dumps(
            manifest, ensure_ascii=False, indent=2, sort_keys=True
        ).encode("utf-8")
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
            for name, content in [
                ("manifest.json", manifest_bytes),
                ("caption.md", caption.strip().encode("utf-8")),
                *payloads,
            ]:
                entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o600 << 16
                bundle.writestr(entry, content)
        archive_bytes = archive.getvalue()
        run_id = str(result.get("run_id") or "verified-run")
        safe_run_id = re.sub(r"[^A-Za-z0-9._-]", "-", run_id)[:80]
        path = await self._files.write_generated_bytes(
            workspace_dir,
            f"captures/{safe_run_id}.demo-capture.zip",
            archive_bytes,
            "indexed",
        )
        return {
            "path": path,
            "size_bytes": len(archive_bytes),
            "sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "manifest_digest": manifest_digest,
            "artifact_count": len(selected),
            "published": False,
        }
