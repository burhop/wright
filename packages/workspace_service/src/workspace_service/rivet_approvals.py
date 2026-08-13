"""Exact, one-shot Wright approvals for a pending Rivet child call."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from typing import Callable, Mapping, Protocol, Sequence, Any

from core.rivet_mcp import (
    ApprovalState,
    PendingRivetCallApproval,
    canonical_digest,
)

from .rivet_evidence import safe_argument_summary


class ApprovalRepositoryPort(Protocol):
    def save_approval(self, approval: PendingRivetCallApproval) -> None: ...


class RivetApprovalError(PermissionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class RivetApprovalService:
    def __init__(
        self,
        *,
        repository: ApprovalRepositoryPort | None = None,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: str(uuid.uuid4()))
        self._records: dict[str, PendingRivetCallApproval] = {}
        self._by_request: dict[tuple[str, str], str] = {}
        self._events: dict[str, asyncio.Event] = {}

    def _save(self, approval: PendingRivetCallApproval) -> None:
        self._records[approval.approval_id] = approval
        if self._repository is not None:
            self._repository.save_approval(approval)

    def request(
        self,
        *,
        run_id: str,
        authority_id: str,
        node_id: str,
        binding_digest: str,
        session_id: str,
        server_id: str,
        qualified_tool_name: str,
        request_id: str,
        arguments: Mapping[str, Any],
        required_gates: Sequence[str] | set[str],
        requested_by: str,
        ttl_seconds: float,
    ) -> PendingRivetCallApproval:
        now = self._clock()
        key = (run_id, request_id)
        argument_digest = canonical_digest(arguments)
        summary, _redactions, _truncated = safe_argument_summary(arguments)
        gates = tuple(sorted(set(required_gates)))
        material = {
            "run_id": run_id,
            "authority_id": authority_id,
            "node_id": node_id,
            "binding_digest": binding_digest,
            "session_id": session_id,
            "server_id": server_id,
            "qualified_tool_name": qualified_tool_name,
            "request_id": request_id,
            "argument_digest": argument_digest,
            "required_gates": gates,
            "requested_by": requested_by,
            "created_at": now,
            "expires_at": now + timedelta(seconds=max(1.0, ttl_seconds)),
        }
        approval_digest = canonical_digest(material)
        existing_id = self._by_request.get(key)
        if existing_id is not None:
            existing = self._records[existing_id]
            if existing.approval_digest != approval_digest:
                raise RivetApprovalError(
                    "RIVET_CALL_APPROVAL_CHANGED",
                    "Pending call approval changed",
                )
            return existing
        approval = PendingRivetCallApproval(
            approval_id=self._id_factory(),
            run_id=run_id,
            authority_id=authority_id,
            node_id=node_id,
            binding_digest=binding_digest,
            session_id=session_id,
            server_id=server_id,
            qualified_tool_name=qualified_tool_name,
            request_id=request_id,
            argument_digest=argument_digest,
            argument_summary=summary,
            required_gates=gates,
            state=ApprovalState.PENDING,
            requested_by=requested_by,
            created_at=now,
            expires_at=material["expires_at"],
            approval_digest=approval_digest,
        )
        self._by_request[key] = approval.approval_id
        self._events[approval.approval_id] = asyncio.Event()
        self._save(approval)
        return approval

    def get(self, approval_id: str) -> PendingRivetCallApproval:
        approval = self._records.get(approval_id)
        if approval is None:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_NOT_FOUND", "Call approval was not found"
            )
        return approval

    def list_for_run(self, run_id: str) -> tuple[PendingRivetCallApproval, ...]:
        return tuple(
            sorted(
                (item for item in self._records.values() if item.run_id == run_id),
                key=lambda item: (item.created_at, item.approval_id),
            )
        )

    def decide(
        self,
        approval_id: str,
        *,
        expected_digest: str,
        actor: str,
        approved: bool,
        reason: str | None = None,
    ) -> PendingRivetCallApproval:
        approval = self.get(approval_id)
        now = self._clock()
        if approval.state is not ApprovalState.PENDING:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_NOT_PENDING", "Call approval is not pending"
            )
        if now >= approval.expires_at:
            expired = replace(approval, state=ApprovalState.EXPIRED, decided_at=now)
            self._save(expired)
            self._events[approval_id].set()
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_EXPIRED", "Call approval expired"
            )
        if approval.approval_digest != expected_digest:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_CHANGED", "Call approval changed"
            )
        updated = replace(
            approval,
            state=ApprovalState.APPROVED if approved else ApprovalState.DENIED,
            decided_by=actor.strip(),
            decision_reason=(reason or "")[:512] or None,
            decided_at=now,
        )
        self._save(updated)
        self._events[approval_id].set()
        return updated

    async def wait(self, approval_id: str) -> PendingRivetCallApproval:
        approval = self.get(approval_id)
        remaining = (approval.expires_at - self._clock()).total_seconds()
        if remaining <= 0:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_EXPIRED", "Call approval expired"
            )
        try:
            await asyncio.wait_for(self._events[approval_id].wait(), remaining)
        except TimeoutError as error:
            expired = replace(
                self.get(approval_id),
                state=ApprovalState.EXPIRED,
                decided_at=self._clock(),
            )
            self._save(expired)
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_EXPIRED", "Call approval expired"
            ) from error
        return self.get(approval_id)

    def consume(
        self, approval_id: str, *, argument_digest: str
    ) -> PendingRivetCallApproval:
        approval = self.get(approval_id)
        if approval.state is not ApprovalState.APPROVED:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_NOT_PENDING",
                "Call approval is not pending for consumption",
            )
        if approval.argument_digest != argument_digest:
            raise RivetApprovalError(
                "RIVET_CALL_APPROVAL_CHANGED", "Approved call arguments changed"
            )
        consumed = replace(
            approval, state=ApprovalState.CONSUMED, consumed_at=self._clock()
        )
        self._save(consumed)
        return consumed

    def cancel_run(self, run_id: str) -> int:
        cancelled = 0
        for approval in tuple(self._records.values()):
            if approval.run_id != run_id or approval.state is not ApprovalState.PENDING:
                continue
            updated = replace(
                approval, state=ApprovalState.CANCELLED, decided_at=self._clock()
            )
            self._save(updated)
            self._events[approval.approval_id].set()
            cancelled += 1
        return cancelled


__all__ = ["RivetApprovalError", "RivetApprovalService"]
