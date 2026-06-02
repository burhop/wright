from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

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
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a tool exposed by the MCP server.
        
        Returns:
            A dictionary containing the response payload from the MCP server.
        """
        pass

    @abstractmethod
    def is_running(self) -> bool:
        """Return True if the runner is currently connected/active."""
        pass
