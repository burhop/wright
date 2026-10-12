"""Publish explicitly selected MCP image bytes through existing result storage."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import PurePosixPath


def validate_image_output_bindings(
    raw, *, agent_task, file_ports, allowed_tools, incompatible=False
):
    from .workflow_source_execution import _invalid

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raise _invalid("MCP image outputs must be a JSON object.") from None
    if raw == {}:
        return {}
    if (
        not isinstance(raw, dict)
        or not 1 <= len(raw) <= 8
        or not agent_task
        or incompatible
    ):
        raise _invalid(
            "MCP image outputs require an ordinary MCP task and 1–8 named image outputs."
        )
    selectors = set()
    paths = set()
    for port, binding in raw.items():
        if (
            port not in file_ports
            or PurePosixPath(file_ports[port]).suffix.lower()
            not in {".png", ".jpg", ".jpeg"}
            or not isinstance(binding, dict)
            or set(binding) != {"tool", "arguments", "image_index"}
            or binding["tool"] not in allowed_tools
            or not isinstance(binding["arguments"], dict)
            or type(binding["image_index"]) is not int
            or not 0 <= binding["image_index"] < 4
        ):
            raise _invalid(
                "Map each MCP image output to a declared PNG/JPEG file, selected tool, argument subset and image index."
            )
        try:
            identity = json.dumps(binding, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError):
            raise _invalid("MCP image selectors must be bounded JSON.") from None
        if (
            len(identity.encode()) > 4096
            or "{{wright." in identity
            or identity in selectors
        ):
            raise _invalid(
                "MCP image selectors must be distinct bounded literal values."
            )
        selectors.add(identity)
        if file_ports[port] in paths:
            raise _invalid("Each MCP image output requires a distinct file path.")
        paths.add(file_ports[port])
    return raw


def _argument_matches(actual, expected):
    # Python equality conflates JSON booleans and numbers, including nested
    # values. Literal selectors must not bind evidence from a different request.
    try:
        return json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(
            expected, sort_keys=True, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError, OverflowError):
        return False


async def publish_image_outputs(service, workspace_dir, step, observations):
    from .workflow_source_execution import _invalid
    from .workflow_mcp_images import _dimensions, MAX_IMAGE_EDGE
    from .workspace_path import WorkspacePath

    prepared = []
    targets = set()
    for port, selector in step.mcp_image_outputs.items():
        matches = [
            item
            for item in observations
            if item["tool_name"] == selector["tool"]
            and all(
                key in item["arguments"]
                and _argument_matches(item["arguments"][key], value)
                for key, value in selector["arguments"].items()
            )
        ]
        if len(matches) != 1:
            raise _invalid(
                f"{step.title}: image output {port} has {len(matches)} matching successful tool responses; exactly one is required."
            )
        observation = matches[0]
        index = selector["image_index"]
        parts = observation["parts"]
        evidence = [
            item
            for item in observation["evidence"]
            if item.get("disposition") == "available_for_model"
        ]
        if index >= len(parts) or index >= len(evidence):
            raise _invalid(
                f"{step.title}: the selected image for {port} was not returned."
            )
        url = parts[index]["image_url"]["url"]
        path = step.expected_file_ports[port]
        mime = (
            "image/png"
            if PurePosixPath(path).suffix.lower() == ".png"
            else "image/jpeg"
        )
        prefix = "data:" + mime + ";base64,"
        if not url.startswith(prefix):
            raise _invalid(
                f"{step.title}: returned image format does not match {port}."
            )
        try:
            raw = base64.b64decode(url[len(prefix) :], validate=True)
            width, height = _dimensions(raw, mime)
        except (ValueError, TypeError):
            raise _invalid(
                f"{step.title}: invalid returned image for {port}."
            ) from None
        digest = hashlib.sha256(raw).hexdigest()
        if (
            not 0 < width <= MAX_IMAGE_EDGE
            or not 0 < height <= MAX_IMAGE_EDGE
            or digest != evidence[index].get("sha256")
            or len(raw) != evidence[index].get("size_bytes")
        ):
            raise _invalid(
                f"{step.title}: returned image differs from its observed evidence."
            )
        target = WorkspacePath(workspace_dir).resolve(path)
        if target in targets:
            raise _invalid(
                f"{step.title}: image output paths resolve to the same destination."
            )
        targets.add(target)
        if target.exists():
            raise _invalid(
                f"{step.title}: image output already exists; inspect the retained run."
            )
        prepared.append(
            (
                path,
                raw,
                {
                    "output_port": port,
                    "output_path": path,
                    "sha256": digest,
                    "size_bytes": len(raw),
                    "tool": observation["tool"],
                    "tool_call_number": observation["tool_call_number"],
                    "content_index": evidence[index]["content_index"],
                },
            )
        )
    receipts = []
    for path, raw, receipt in prepared:
        actual = await service.files.write_generated_bytes(
            workspace_dir, path, raw, "indexed"
        )
        if actual != path:
            raise _invalid(
                f"{step.title}: image output path changed during publication."
            )
        receipts.append(receipt)
    return receipts
