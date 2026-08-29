"""Build and atomically install a validated program-status bundle.

The implementation is intentionally inactive until the contract tests in T005
define the repository evidence, identity, and failure boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ProgramStatusPublishError(RuntimeError):
    """Typed failure raised when a candidate cannot be safely published."""

    def __init__(self, code: str, message: str, recovery_class: str) -> None:
        super().__init__(message)
        self.code = code
        self.recovery_class = recovery_class


@dataclass(frozen=True, slots=True)
class ProgramStatusPublishRequest:
    """Exact committed subject and stable data-root publication request."""

    repository: Path
    source_commit: str
    data_root: Path


@dataclass(frozen=True, slots=True)
class ProgramStatusPublishResult:
    """Non-secret identity returned after a successful atomic publication."""

    source_commit: str
    source_tree: str
    program_tree: str
    bundle_id: str
    installed_artifact: str
    changed: bool


def publish_program_status(
    request: ProgramStatusPublishRequest,
) -> ProgramStatusPublishResult:
    """Publish one validated committed subject.

    T007-T008 provide the implementation after their failing contract tests.
    """

    del request
    raise NotImplementedError("EPP-F01B publisher implementation begins at T007")
