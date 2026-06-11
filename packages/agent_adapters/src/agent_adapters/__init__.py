"""Wright Agent Adapters — BaseAgentEngine interface for hot-swappable LLM agents.

Agents (Hermes, openclaw, PI) are integrated via the Adapter Pattern,
never hardcoded into the API.
"""

from .base import (
    BaseAgentEngine,
    AgentStreamEvent,
    AgentChatRequest,
    AgentSessionInfo,
    AgentChatMessage,
)
from .hermes import HermesAdapter

__all__ = [
    "BaseAgentEngine",
    "AgentStreamEvent",
    "AgentChatRequest",
    "AgentSessionInfo",
    "AgentChatMessage",
    "HermesAdapter",
]
