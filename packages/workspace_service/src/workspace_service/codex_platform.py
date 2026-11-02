"""Host composition supplies storage to the provider-neutral adapter boundary."""

from agent_adapters.codex import create_codex_engine
from data_vault.agent_platform_repository import AgentPlatformRepository


def create_codex_chat_engine(db_path):
    return create_codex_engine(db_path, repository=AgentPlatformRepository(db_path))
