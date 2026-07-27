"""Consumer-owned capability contracts for workspace application use cases."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from .models import WorkspaceRecord, WorkspaceSessionRecord

if TYPE_CHECKING:
    from .models import ProcessResult

T = TypeVar("T")


class WorkspaceRepository(Protocol):
    def get_by_id(self, workspace_id: str) -> WorkspaceRecord | None: ...

    def get_by_session(self, session_id: str) -> WorkspaceRecord | None: ...

    def list_all(self) -> Sequence[WorkspaceRecord]: ...

    def list_recent(self, limit: int) -> Sequence[WorkspaceRecord]: ...

    def list_sessions(self, workspace_id: str) -> Sequence[WorkspaceSessionRecord]: ...


class WorkspaceFiles(Protocol):
    def root(self) -> Path: ...

    def tree(self) -> list[dict[str, Any]]: ...

    def read_text(self, relative_path: str) -> str: ...

    def write_text(self, relative_path: str, content: str) -> None: ...


class WorkspaceGit(Protocol):
    def status(self) -> Mapping[str, Any]: ...

    def diff(self, relative_path: str) -> str: ...

    def history(self, limit: int = 20) -> Sequence[Mapping[str, Any]]: ...


class ProcessRunner(Protocol):
    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: Mapping[str, str] | None = None,
    ) -> "ProcessResult": ...


class AgentContextPort(Protocol):
    def materialize(
        self, *, workspace_id: str, session_id: str, workspace_path: str
    ) -> Any: ...


class WorkspaceNotifier(Protocol):
    def publish(
        self,
        event: str,
        *,
        workspace_id: str | None = None,
        session_id: str | None = None,
    ) -> None: ...


class BlockingExecutor(Protocol):
    async def run(
        self, operation: str, work: Callable[[], T], *, timeout_seconds: float
    ) -> T: ...

    async def close(self) -> None: ...
