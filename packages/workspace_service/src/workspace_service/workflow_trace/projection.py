"""Bounded read projection over pinned workflow trace records."""

from __future__ import annotations

from data_vault import WorkflowTraceRepository

from .evidence import ingest_external_evidence


class WorkflowTraceProjection:
    def __init__(self, repository: WorkflowTraceRepository) -> None:
        self.repository = repository

    def summary(self, *, workspace_id: str, run_id: str) -> dict:
        run = self.repository.get_run(run_id)
        if run is None or run.workspace_id != workspace_id:
            raise KeyError(run_id)
        occurrences = self.repository.occurrences(run_id, limit=100)
        evidence = self.repository.evidence(run_id, limit=100)
        return {
            "schema_version": 1,
            "run": run.model_dump(mode="json"),
            "occurrences": [item.model_dump(mode="json") for item in occurrences],
            "evidence": [item.model_dump(mode="json") for item in evidence],
            "bounded": len(occurrences) == 100 or len(evidence) == 100,
            "mutations_allowed": False,
        }

    def ingest_evidence(
        self, *, workspace_id: str, run_id: str, envelope: dict
    ) -> dict:
        run = self.repository.get_run(run_id)
        if run is None or run.workspace_id != workspace_id:
            raise KeyError(run_id)
        record = ingest_external_evidence(envelope)
        if record.run_id != run_id:
            raise ValueError("workflow trace evidence run subject does not match")
        self.repository.put_evidence(record)
        return record.model_dump(mode="json")

    def evidence_page(
        self,
        *,
        workspace_id: str,
        run_id: str,
        after_id: str = "",
        limit: int = 100,
    ) -> dict:
        run = self.repository.get_run(run_id)
        if run is None or run.workspace_id != workspace_id:
            raise KeyError(run_id)
        bounded = max(1, min(int(limit), 200))
        records = self.repository.evidence(run_id, after_id=after_id, limit=bounded + 1)
        has_more = len(records) > bounded
        page = records[:bounded]
        return {
            "records": [item.model_dump(mode="json") for item in page],
            "next_after": page[-1].evidence_id if has_more and page else None,
        }
