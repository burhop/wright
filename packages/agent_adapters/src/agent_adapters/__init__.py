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
from .hermes_config import HermesApiSettings, resolve_hermes_api_settings
from .registry import (
    AgentApiSettings,
    AgentEngineRegistry,
    AgentRuntimeProvider,
    UnsupportedAgentRuntimeError,
    create_agent_engine,
    default_agent_registry,
    resolve_agent_api_settings,
)
from .gateway import WrightGatewayProfile, build_wright_gateway_args

__all__ = [
    "BaseAgentEngine",
    "AgentStreamEvent",
    "AgentChatRequest",
    "AgentSessionInfo",
    "AgentChatMessage",
    "HermesAdapter",
    "HermesApiSettings",
    "resolve_hermes_api_settings",
    "AgentApiSettings",
    "AgentEngineRegistry",
    "AgentRuntimeProvider",
    "UnsupportedAgentRuntimeError",
    "create_agent_engine",
    "default_agent_registry",
    "resolve_agent_api_settings",
    "WrightGatewayProfile",
    "build_wright_gateway_args",
]
