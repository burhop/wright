from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Mapping

from .base import BaseAgentEngine


class UnsupportedAgentRuntimeError(ValueError):
    """Raised when a requested agent runtime cannot be selected."""


AgentEngineFactory = Callable[[str | None], BaseAgentEngine]


@dataclass(frozen=True)
class AgentApiSettings:
    provider_name: str
    base_url: str
    api_key: str
    source: str


@dataclass(frozen=True)
class AgentRuntimeProvider:
    name: str
    display_name: str
    description: str
    supported: bool
    is_default: bool = False
    factory: AgentEngineFactory | None = None

    def create_engine(self, db_path: str | None = None) -> BaseAgentEngine:
        if not self.supported or self.factory is None:
            raise UnsupportedAgentRuntimeError(
                f"Agent runtime '{self.name}' is known but not implemented."
            )
        return self.factory(db_path)


class AgentEngineRegistry:
    """Registry/factory for selectable Wright agent runtimes."""

    def __init__(self, providers: list[AgentRuntimeProvider]):
        if not providers:
            raise ValueError("At least one agent runtime provider is required.")

        normalized: dict[str, AgentRuntimeProvider] = {}
        for provider in providers:
            name = provider.name.strip().lower()
            if not name:
                raise ValueError("Agent runtime provider names cannot be blank.")
            if name in normalized:
                raise ValueError(f"Duplicate agent runtime provider: {name}")
            normalized[name] = AgentRuntimeProvider(
                name=name,
                display_name=provider.display_name,
                description=provider.description,
                supported=provider.supported,
                is_default=provider.is_default,
                factory=provider.factory,
            )

        defaults = [provider for provider in normalized.values() if provider.is_default]
        if len(defaults) != 1:
            raise ValueError("Exactly one default agent runtime provider is required.")
        if not defaults[0].supported:
            raise ValueError("Default agent runtime provider must be supported.")

        self._providers = normalized
        self._default_provider = defaults[0]

    def default_provider(self) -> AgentRuntimeProvider:
        return self._default_provider

    def known_names(self) -> list[str]:
        return sorted(self._providers)

    def supported_names(self) -> list[str]:
        return sorted(
            name for name, provider in self._providers.items() if provider.supported
        )

    def resolve_provider(self, name: str | None) -> AgentRuntimeProvider:
        normalized = (name or "").strip().lower()
        if not normalized:
            return self._default_provider

        provider = self._providers.get(normalized)
        if provider is None:
            raise UnsupportedAgentRuntimeError(
                f"Unsupported agent runtime: {normalized}"
            )
        if not provider.supported:
            raise UnsupportedAgentRuntimeError(
                f"Agent runtime '{normalized}' is known but not implemented."
            )
        return provider

    def create_engine(
        self, name: str | None = None, db_path: str | None = None
    ) -> BaseAgentEngine:
        return self.resolve_provider(name).create_engine(db_path)


def _create_hermes_engine(db_path: str | None = None) -> BaseAgentEngine:
    from .hermes import HermesAdapter

    settings = resolve_agent_api_settings("hermes")
    return HermesAdapter(settings.base_url, settings.api_key, db_path)


@lru_cache(maxsize=1)
def default_agent_registry() -> AgentEngineRegistry:
    return AgentEngineRegistry(
        [
            AgentRuntimeProvider(
                name="hermes",
                display_name="Hermes",
                description="Default Wright workspace agent runtime.",
                supported=True,
                is_default=True,
                factory=_create_hermes_engine,
            ),
            AgentRuntimeProvider(
                name="openclaw",
                display_name="OpenClaw",
                description="Future Wright agent runtime using the Wright gateway.",
                supported=False,
            ),
            AgentRuntimeProvider(
                name="pi",
                display_name="Pi",
                description="Future lightweight local agent runtime.",
                supported=False,
            ),
        ]
    )


def create_agent_engine(
    name: str | None = None,
    db_path: str | None = None,
    registry: AgentEngineRegistry | None = None,
) -> BaseAgentEngine:
    active_registry = registry or default_agent_registry()
    return active_registry.create_engine(name, db_path)


def resolve_agent_api_settings(
    name: str | None = None,
    env: Mapping[str, str] | None = None,
    registry: AgentEngineRegistry | None = None,
) -> AgentApiSettings:
    active_registry = registry or default_agent_registry()
    provider = active_registry.resolve_provider(name)
    if provider.name == "hermes":
        from .hermes_config import resolve_hermes_api_settings

        settings = resolve_hermes_api_settings(env)
        return AgentApiSettings(
            provider_name=provider.name,
            base_url=settings.base_url,
            api_key=settings.api_key,
            source=settings.source,
        )

    raise UnsupportedAgentRuntimeError(
        f"Agent runtime '{provider.name}' does not expose API settings."
    )
