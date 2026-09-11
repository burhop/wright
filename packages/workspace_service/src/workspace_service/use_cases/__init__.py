"""Focused workspace application use cases."""

from .files import FileReadResult, WorkspaceFileUseCases
from .git import GitMergeConflict, WorkspaceGitUseCases
from .context import WorkspaceContextUseCases
from .lifecycle import WorkspaceLifecycleUseCases
from .tools import WorkspaceToolUseCases
from .workflows import WorkspaceWorkflowUseCases
from ..workflow_sources import WorkspaceWorkflowSourceUseCases

__all__ = [
    "FileReadResult",
    "GitMergeConflict",
    "WorkspaceFileUseCases",
    "WorkspaceGitUseCases",
    "WorkspaceContextUseCases",
    "WorkspaceLifecycleUseCases",
    "WorkspaceToolUseCases",
    "WorkspaceWorkflowUseCases",
    "WorkspaceWorkflowSourceUseCases",
]
