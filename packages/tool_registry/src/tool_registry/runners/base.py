from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable, Mapping
from typing import List, Dict, Any


ProgressCallback = Callable[[Mapping[str, Any]], Awaitable[None] | None]


class BaseRunner(ABC):
    """Abstract base class for all Model Context Protocol (MCP) server runners (stdio, sse)."""

    @abstractmethod
    async def start(self) -> None:
        """Start the MCP server or connection."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the MCP server or connection and clean up resources."""
        pass

    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """Query the MCP server for available tools.

        Returns:
            A list of tools, where each tool is a dictionary containing at least:
            - name: str
            - description: Optional[str]
            - inputSchema: dict
        """
        pass

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        *,
        progress_callback: ProgressCallback | None = None,
    ) -> Dict[str, Any]:
        """Invoke a tool exposed by the MCP server.

        Returns:
            A dictionary containing the response payload from the MCP server.
        """
        pass

    async def list_resources(self, cursor: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError("Child runner does not support resources/list")

    async def list_resource_templates(
        self, cursor: str | None = None
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "Child runner does not support resources/templates/list"
        )

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        raise NotImplementedError("Child runner does not support resources/read")

    async def subscribe_resource(self, uri: str) -> None:
        raise NotImplementedError("Child runner does not support resources/subscribe")

    async def unsubscribe_resource(self, uri: str) -> None:
        raise NotImplementedError(
            "Child runner does not support resources/unsubscribe"
        )

    @abstractmethod
    def is_running(self) -> bool:
        """Return True if the runner is currently connected/active."""
        pass
