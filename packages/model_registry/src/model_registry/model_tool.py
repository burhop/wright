"""BaseTool implementation for one reviewed engineering-model capability."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from core.tools import BaseTool, ToolContext


ModelExecutor = Callable[[Mapping[str, Any], ToolContext], Awaitable[Mapping[str, Any]]]


class EngineeringModelTool(BaseTool):
    def __init__(
        self,
        *,
        name: str,
        description: str,
        input_schema: Mapping[str, Any],
        output_schema: Mapping[str, Any],
        executor: ModelExecutor,
    ) -> None:
        self._name = name
        self._description = description
        self._input_schema = dict(input_schema)
        self._output_schema = dict(output_schema)
        self._executor = executor
        self.contract()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def input_schema(self) -> Mapping[str, Any]:
        return self._input_schema

    @property
    def output_schema(self) -> Mapping[str, Any]:
        return self._output_schema

    async def execute(
        self, arguments: Mapping[str, Any], *, context: ToolContext
    ) -> Mapping[str, Any]:
        return await self._executor(arguments, context)


__all__ = ["EngineeringModelTool", "ModelExecutor"]
