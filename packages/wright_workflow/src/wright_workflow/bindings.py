"""Qualify tool identities without changing the meaning of recorded gateway digests."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator

from .contracts import Contract, Digest, Identifier, canonical_digest
from .source import _invalid


def schema_digest(tool):
    material = {
        "server": tool.server_id,
        "name": tool.name,
        "input": dict(tool.input_schema),
        "output": tool.output_schema,
        "authority": tool.provenance.get("server_revision"),
        "approvals": sorted(tool.required_approvals),
    }
    if tool.upstream_meta.get("wright/operation"):
        material["operation_adapter"] = tool.upstream_meta["wright/operation"]
    if tool.upstream_meta.get("wright/approved-operation"):
        material["approved_operation_adapter"] = tool.upstream_meta[
            "wright/approved-operation"
        ]
    if tool.upstream_meta.get("wright/application"):
        material["application_adapter"] = tool.upstream_meta["wright/application"]
    if tool.upstream_meta.get("wright/terminalOperation"):
        material["terminal_operation"] = tool.upstream_meta["wright/terminalOperation"]
    return hashlib.sha256(
        json.dumps(
            material, sort_keys=True, separators=(",", ":"), default=dict
        ).encode()
    ).hexdigest()


class PortableBinding(Contract):
    version: Literal["wright.mcp-binding/1"]
    provider: Identifier
    build: Identifier
    tool: Identifier
    contract_sha256: Digest


class LocalTool(Contract):
    upstream: Identifier
    contract_sha256: Digest
    required_approvals: tuple[Identifier, ...] = ()


class LocalServer(Contract):
    """This record comes from the caller, independently of the workflow."""

    command: str
    args: tuple[str, ...] = ()
    provider: Identifier
    build: Identifier
    build_files: dict[str, Digest] = Field(min_length=1)
    tools: dict[str, LocalTool] = Field(min_length=1)
    server_revision: str | None = None

    @field_validator("command")
    @classmethod
    def absolute_command(cls, value):
        if not Path(value).is_absolute():
            raise ValueError("Configure an absolute path to the MCP executable.")
        return value

    def verify_build(self):
        for name, expected in self.build_files.items():
            path = Path(name)
            if not path.is_absolute():
                raise ValueError("Configure absolute paths for the reviewed MCP build.")
            with path.open("rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError(f"The reviewed provider build changed at {path}.")
        if Path(self.command) not in {Path(name) for name in self.build_files}:
            raise ValueError("Pin the executable for this local provider.")


@dataclass(frozen=True)
class QualifiedTool:
    server_id: str
    name: str
    input_schema: dict
    output_schema: dict | None
    provenance: dict
    required_approvals: tuple
    upstream_meta: dict
    binding: PortableBinding


def observed_binding(server_info, tool):
    wire = tool.model_dump(mode="json", by_alias=True, exclude_none=True)
    material = {
        key: wire[key]
        for key in (
            "name",
            "inputSchema",
            "outputSchema",
            "annotations",
            "_meta",
            "execution",
        )
        if key in wire
    }
    return PortableBinding(
        version="wright.mcp-binding/1",
        provider=server_info.name,
        build=server_info.version,
        tool=tool.name,
        contract_sha256=canonical_digest(material),
    )


def qualify(step, server, server_info, upstream_tools):
    local = server.tools.get(step.tool_name)
    if local is None or local.upstream not in upstream_tools:
        raise _invalid(
            f"{step.title}: the configured MCP tool is unavailable.", block_id=step.id
        )
    tool = upstream_tools[local.upstream]
    observed = observed_binding(server_info, tool)
    if (server.provider, server.build, local.contract_sha256) != (
        observed.provider,
        observed.build,
        observed.contract_sha256,
    ):
        raise _invalid(
            f"{step.title}: the configured provider build or tool contract has changed.",
            block_id=step.id,
        )
    qualified = QualifiedTool(
        step.server_id,
        step.tool_name,
        tool.inputSchema,
        tool.outputSchema,
        {"server_revision": server.server_revision},
        local.required_approvals,
        tool.meta or {},
        observed,
    )
    if step.portable is not None and observed != step.portable:
        raise _invalid(
            f"{step.title}: the portable binding requires a different provider or tool.",
            block_id=step.id,
        )
    if step.schema_digest and step.schema_digest != schema_digest(qualified):
        raise _invalid(
            f"{step.title}: the historical gateway binding has changed.",
            block_id=step.id,
        )
    if not step.schema_digest and step.portable is None:
        raise _invalid(
            f"{step.title}: an explicit tool revision is required.", block_id=step.id
        )
    if local.required_approvals or any(
        key.startswith("wright/") for key in qualified.upstream_meta
    ):
        raise _invalid(
            f"{step.title}: the declared tool requires a qualified authority or operation handler.",
            block_id=step.id,
        )
    return qualified
