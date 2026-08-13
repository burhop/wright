"""Provider-neutral contract for every engineering tool exposed to an agent."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from .rivet_mcp import reject_secret_material

_TOOL_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_MAX_SCHEMA_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class ToolContext:
    principal_id: str
    workspace_id: str
    trace_id: str
    request_id: str

    def __post_init__(self) -> None:
        for value in (
            self.principal_id,
            self.workspace_id,
            self.trace_id,
            self.request_id,
        ):
            if not value or len(value) > 128:
                raise ValueError("Tool context identity is invalid")


class BaseTool(ABC):
    """Strict typed boundary for an engineering capability offered to an LLM."""

    name: ClassVar[str]
    description: ClassVar[str]
    input_schema: ClassVar[Mapping[str, Any]]
    output_schema: ClassVar[Mapping[str, Any]]

    @property
    @abstractmethod
    def name(self) -> str:  # type: ignore[no-redef]
        """Stable provider-local name."""

    @property
    @abstractmethod
    def description(self) -> str:  # type: ignore[no-redef]
        """Bounded, non-marketing description."""

    @property
    @abstractmethod
    def input_schema(self) -> Mapping[str, Any]:  # type: ignore[no-redef]
        """Closed JSON input schema."""

    @property
    @abstractmethod
    def output_schema(self) -> Mapping[str, Any]:  # type: ignore[no-redef]
        """Bounded JSON output schema."""

    def contract(self) -> dict[str, Any]:
        name = str(self.name)
        description = str(self.description)
        if not _TOOL_NAME.fullmatch(name):
            raise ValueError("Tool name is invalid")
        if not description or len(description) > 1_000:
            raise ValueError("Tool description is invalid")
        value = {
            "name": name,
            "description": description,
            "input_schema": dict(self.input_schema),
            "output_schema": dict(self.output_schema),
        }
        reject_secret_material(value)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        if len(encoded) > _MAX_SCHEMA_BYTES:
            raise ValueError("Tool contract exceeds the 64 KiB limit")
        for label in ("input_schema", "output_schema"):
            schema = value[label]
            if schema.get("type") != "object":
                raise ValueError(f"Tool {label} must describe an object")
        return value

    @abstractmethod
    async def execute(
        self, arguments: Mapping[str, Any], *, context: ToolContext
    ) -> Mapping[str, Any]:
        """Execute through the owning Wright policy and lifecycle boundary."""
