"""Reader contracts and bounded execution; profiles cannot supply executable code."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Event
from time import monotonic
from typing import Protocol

from core.process_validation import (
    CheckDefinition,
    Measurement,
    ReaderIdentity,
    ResourceBudget,
    SubjectBinding,
)
from core.tracing import traced


class ValidationIssue(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        state="blocked",
        category="missing_evidence",
        action="supply_input",
    ):
        super().__init__(message)
        self.code, self.state, self.category, self.action = (
            code,
            state,
            category,
            action,
        )


@dataclass(frozen=True)
class SubjectSnapshot:
    subject: SubjectBinding
    content: bytes


@dataclass(frozen=True)
class ReaderContext:
    budget: ResourceBudget
    deadline: float
    cancelled: Event
    trace_id: str
    related_snapshots: tuple[SubjectSnapshot, ...] = ()

    @classmethod
    def create(cls, budget, trace_id, cancelled=None):
        return cls(
            budget,
            monotonic() + budget.timeout_seconds,
            cancelled if cancelled is not None else Event(),
            trace_id,
        )

    def checkpoint(self, *, entities=0):
        if self.cancelled.is_set():
            raise ValidationIssue(
                "validation.cancelled",
                "Validation was cancelled.",
                state="error",
                category="validator_error",
                action="retry_validation",
            )
        if monotonic() > self.deadline:
            raise ValidationIssue(
                "reader.timeout",
                "The reader exceeded its time budget.",
                state="error",
                category="validator_error",
                action="retry_validation",
            )
        if entities > self.budget.max_entities:
            raise ValidationIssue(
                "reader.entity_limit",
                "The output exceeds this reader's entity limit.",
                category="capability_unavailable",
                action="restore_capability",
            )


class Reader(Protocol):
    identity: ReaderIdentity

    def measure(
        self, snapshot: SubjectSnapshot, check: CheckDefinition, context: ReaderContext
    ) -> Measurement: ...


class ReaderRegistry:
    def __init__(self):
        self._readers: dict[str, Reader] = {}

    def register(self, reader: Reader):
        if reader.identity.id in self._readers:
            raise ValueError("Reader identity is already registered")
        self._readers[reader.identity.id] = reader

    def capabilities(self) -> tuple[ReaderIdentity, ...]:
        return tuple(reader.identity for _, reader in sorted(self._readers.items()))

    @traced("workspace.process_validation.measure")
    def measure(self, snapshot, check, context):
        context.checkpoint()
        reader = self._readers.get(check.reader)
        if reader is None:
            raise ValidationIssue(
                "reader.unavailable",
                f"Required reader '{check.reader}' is unavailable.",
                category="capability_unavailable",
                action="restore_capability",
            )
        if reader.identity.method != check.evidence_method:
            raise ValidationIssue(
                "reader.evidence_method",
                "Available reader does not supply the required evidence method.",
                category="capability_unavailable",
                action="restore_capability",
            )
        if (
            reader.identity.formats
            and snapshot.subject.format not in reader.identity.formats
        ):
            raise ValidationIssue(
                "reader.format",
                "Reader does not support the bound output format.",
                category="capability_unavailable",
                action="restore_capability",
            )
        measurement = reader.measure(snapshot, check, context)
        context.checkpoint()
        if (
            measurement.subject_id != snapshot.subject.id
            or measurement.subject_sha256 != snapshot.subject.sha256
            or measurement.reader != reader.identity
        ):
            raise ValidationIssue(
                "reader.identity",
                "Reader returned evidence for a different subject or method.",
                state="error",
                category="validator_error",
                action="retry_validation",
            )
        return measurement
