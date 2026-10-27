"""Opt-in, fixed-file proof of the documented OpenAI native file entrypoint.

This is diagnostic presentation only. Existing Wright source, draft and process
owners retain their authority. Host metadata is checked against a local manifest;
neither a filename nor an opaque resource URI grants workspace access.
"""

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from mcp.server.fastmcp import Context
from mcp.types import ToolAnnotations
from pydantic import Field
from native_file_contracts import StrictModel, FileInput as FileInput, ProbeObservation as ProbeObservation, Capabilities as Capabilities


class ProbeFile(StrictModel):
    absolute_path: str = Field(min_length=1, max_length=4096)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: Literal["workflow", "image"]
    label: str = Field(min_length=1, max_length=100)
    workspace_id: str = Field(min_length=1, max_length=100)
    session_id: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=512)
    run_id: str | None = Field(default=None, max_length=100)


class ProbeManifest(StrictModel):
    schema_version: Literal["wright.native-file-tabs-probe/1"]
    launcher_html: str
    evidence_path: str
    files: list[ProbeFile] = Field(min_length=1, max_length=3)


def _exact_path(value: str, *, exists: bool = True) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=exists) != path:
        raise ValueError("Probe requires an exact absolute path without symlinks")
    return path


def _pinned_file(item: ProbeFile) -> None:
    path = _exact_path(item.absolute_path)
    if not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Probe file is unavailable or exceeds the bounded size")
    if hashlib.sha256(path.read_bytes()).hexdigest() != item.sha256:
        raise ValueError("Probe file changed from its reviewed pin")


def register_native_file_tab_probe(
    mcp, client, *, manifest_path: Path, resource_uri: str,
    working_view_enabled: bool,
):
    manifest = ProbeManifest.model_validate_json(
        _exact_path(str(manifest_path)).read_text(encoding="utf-8")
    )
    launcher = _exact_path(manifest.launcher_html).read_bytes().decode("utf-8")
    evidence = _exact_path(manifest.evidence_path, exists=False)
    if not evidence.parent.is_dir():
        raise ValueError("Probe evidence directory must already exist")
    by_path = {}
    for item in manifest.files:
        _pinned_file(item)
        relative = Path(item.path)
        if (
            relative.is_absolute() or ".." in relative.parts
            or relative.as_posix() != item.path or "\\" in item.path
            or item.absolute_path in by_path
        ):
            raise ValueError("Probe file mapping must be exact and unique")
        if item.kind == "workflow" and not item.path.endswith(".wflow"):
            raise ValueError("Probe workflow mapping requires a workflow file")
        if evidence == Path(item.absolute_path):
            raise ValueError("Probe evidence must not overwrite an input")
        by_path[item.absolute_path] = item
    launcher_uri = "ui://wright/native-tabs-probe/" + hashlib.sha256(
        launcher.encode()
    ).hexdigest() + ".html"
    read = ToolAnnotations(
        readOnlyHint=True, destructiveHint=False, idempotentHint=True,
        openWorldHint=False,
    )

    def receipt(event: dict) -> None:
        record = {
            "schema_version": "wright.native-file-tab-observation/1",
            "at": datetime.now(timezone.utc).isoformat(), **event,
        }
        data = (json.dumps(record, separators=(",", ":")) + "\n").encode()
        _exact_path(str(evidence), exists=False)
        fd = os.open(
            evidence, os.O_WRONLY | os.O_APPEND | os.O_CREAT
            | getattr(os, "O_NOFOLLOW", 0), 0o600,
        )
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size + len(data) > 262144:
                raise ValueError("Probe evidence limit reached or path unavailable")
            os.write(fd, data)
        finally:
            os.close(fd)

    @mcp.resource(
        launcher_uri, title="Wright native document tab test",
        mime_type="text/html;profile=mcp-app",
        meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}},
    )
    async def native_tabs_probe_resource() -> str:
        return launcher

    @mcp.tool(
        title="Test Wright native document tabs", annotations=read,
        meta={
            "ui": {"resourceUri": launcher_uri, "visibility": ["model", "app"]},
            "openai/ui": {"entrypoints": [{"type": "thread"}]},
        },
    )
    async def wright_native_tabs_probe() -> dict[str, Any]:
        """Open the fixed three-file native tab experiment. No engineering runs."""
        for item in manifest.files:
            _pinned_file(item)
            await client.scope(item.workspace_id, item.session_id)
        return {
            "view": "native-tabs-probe",
            "files": [item.model_dump(exclude_none=True) for item in manifest.files],
            "evidence_boundary": "Tool receipts and self-reported iframe observations; native tab display needs direct observation.",
        }

    @mcp.tool(
        title="Wright workflow file", annotations=read,
        meta={
            "ui": {"resourceUri": resource_uri, "visibility": ["app"]},
            "openai/ui": {"entrypoints": [{"type": "file", "extensions": [".wflow"]}]},
        },
    )
    async def wright_workflow_file(file: FileInput) -> dict[str, Any]:
        """Render a file-entrypoint shell; obtain scope only from host metadata."""
        receipt({
            "boundary": "file-entrypoint-invocation",
            "resource_uri_sha256": hashlib.sha256(file.resourceUri.encode()).hexdigest(),
        })
        return {"view": "native-workflow-file", "file": file.model_dump()}

    @mcp.tool(
        title="Resolve Wright workflow file context", annotations=read,
        meta={"ui": {"visibility": ["app"]}},
    )
    async def wright_workflow_file_context(
        request: ProbeObservation, ctx: Context,
    ) -> dict[str, Any]:
        """Resolve only the manifest-pinned path supplied in host request metadata."""
        meta = ctx.request_context.meta
        values = meta.model_dump() if hasattr(meta, "model_dump") else meta
        resource = values.get("openai/resource") if isinstance(values, dict) else None
        path = resource.get("path") if isinstance(resource, dict) else None
        item = by_path.get(path) if isinstance(path, str) else None
        if item is None or item.kind != "workflow":
            raise ValueError("Host file path is missing or outside this fixed probe")
        _pinned_file(item)
        if request.resume is not None and (
            request.resume.workspace_id != item.workspace_id
            or request.resume.session_id != item.session_id
            or request.resume.path != item.path
            or request.resume.expected_sha256 not in (None, item.sha256)
        ):
            raise ValueError("Remembered scope differs from the pinned probe file")
        workspace = await client.scope(item.workspace_id, item.session_id)
        document = await client.call(
            "GET", "/api/workspace/workflow-sources",
            params={"session_id": item.session_id, "path": item.path},
        )
        if (
            document.get("path") != item.path
            or document.get("storage_digest") != item.sha256
        ):
            raise ValueError("Wright source owner differs from the pinned probe file")
        receipt({
            "boundary": "host-metadata-resolved-and-source-owner-read",
            "path": item.path, "workspace_id": item.workspace_id,
            "session_id": item.session_id, "source_sha256": item.sha256,
            **({"run_id": item.run_id} if item.run_id else {}),
            "ui_observation": request.model_dump(exclude_none=True),
            "ui_observation_trust": "self-reported; not native tab visual acceptance",
        })
        return {
            "workspace": workspace, "document": document,
            "working_view_enabled": working_view_enabled,
            "native_file": {
                **item.model_dump(exclude_none=True),
                "instance_id": request.instance_id, "source_sha256": item.sha256,
            },
        }

    @mcp.tool(annotations=read)
    async def wright_native_tabs_probe_status() -> dict[str, Any]:
        """Read up to 50 bounded native-tab probe receipts; no display claims."""
        _exact_path(str(evidence), exists=False)
        if not evidence.exists():
            return {"observations": [], "native_visual_acceptance": "unverified"}
        if evidence.stat().st_size > 262144:
            raise ValueError("Probe evidence exceeds its bounded size")
        observations = [
            json.loads(line)
            for line in evidence.read_text(encoding="utf-8").splitlines()
        ][-50:]
        return {"observations": observations, "native_visual_acceptance": "unverified"}
