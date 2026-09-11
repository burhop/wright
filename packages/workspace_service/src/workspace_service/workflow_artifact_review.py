"""Terminal document review: persist a subject, release execution, record a human decision."""

import asyncio
import base64
import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from data_vault.workflow_artifact_review_repository import (
    WorkflowArtifactReviewRepository,
    ArtifactReviewConflict,
)
from .workspace_path import WorkspacePath
from .workflow_source_execution import WorkflowSourceExecutionError


def _now():
    return datetime.now(timezone.utc).isoformat()


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def snapshot(path, data):
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("A review evidence file exceeds 8 MiB")
    return {
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
        "content_base64": base64.b64encode(data).decode("ascii"),
    }


def _read_bounded(path):
    with path.open("rb") as stream:
        data = stream.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("A review evidence file exceeds 8 MiB")
    return data


class WorkflowArtifactReviewService:
    def __init__(self, db_path):
        self.repository = WorkflowArtifactReviewRepository(db_path)

    @staticmethod
    def _view(row):
        package = json.loads(row["package_json"])
        decision = json.loads(row["decision_json"]) if row["decision_json"] else {}
        return {
            **package["summary"],
            "package_digest": row["package_digest"],
            "state": row["state"],
            "decided_at": decision.get("decided_at"),
            "actor": decision.get("actor"),
            "reason": decision.get("reason"),
            "attribution": "local_workspace_user_not_authenticated",
        }

    @staticmethod
    def _verify(workspace_dir, package):
        paths = WorkspacePath(workspace_dir)
        for saved in package["snapshots"]:
            try:
                data = _read_bounded(paths.resolve(saved["path"], must_exist=True))
                if (
                    len(data) != saved["size_bytes"]
                    or hashlib.sha256(data).hexdigest() != saved["sha256"]
                ):
                    raise ValueError("Content changed")
            except (OSError, ValueError) as error:
                raise WorkflowSourceExecutionError(
                    "WORKFLOW_REVIEW_STALE",
                    f"Review evidence changed or is missing: {saved['path']}",
                    "Create a new run and review its exact outputs; this decision cannot approve changed evidence.",
                ) from error

    async def create(
        self,
        *,
        workspace_id,
        workspace_dir,
        workflow_path,
        run_log_path,
        result,
        request,
    ):
        context = request["context"]
        snapshots = list(context["snapshots"])
        for output in result["outputs"]:
            path = WorkspacePath(workspace_dir).resolve(
                output["output_path"], must_exist=True
            )
            data = await asyncio.to_thread(_read_bounded, path)
            saved = snapshot(output["output_path"], data)
            if (
                saved["sha256"] != output["sha256"]
                or saved["size_bytes"] != output["output_bytes"]
            ):
                raise WorkflowSourceExecutionError(
                    "WORKFLOW_REVIEW_STALE",
                    "An output changed before review.",
                    "Run again to produce a new review draft.",
                )
            snapshots.append(saved)
        if not request["artifacts"]:
            raise ValueError("Review requires a verified output file")
        summary = {
            "review_id": uuid4().hex,
            "run_id": result["run_id"],
            "run_log_path": run_log_path,
            "workflow_path": workflow_path,
            "source_digest": context["source_digest"],
            "task_id": request["task_id"],
            "task_title": request["task_title"],
            "instructions": request["instructions"],
            "artifacts": request["artifacts"],
            "created_at": _now(),
        }
        package = {
            "version": 1,
            "workspace_id": workspace_id,
            "summary": summary,
            "snapshots": snapshots,
            "input_values": context["input_values"],
            "result": result,
        }
        await asyncio.to_thread(self._verify, workspace_dir, package)
        digest = _digest(package)
        await asyncio.to_thread(
            self.repository.create,
            summary["review_id"],
            workspace_id,
            workflow_path,
            digest,
            package,
        )
        return {
            **summary,
            "package_digest": digest,
            "state": "pending",
            "decided_at": None,
            "actor": None,
            "reason": None,
            "attribution": "local_workspace_user_not_authenticated",
        }

    async def _inspect(self, row, workspace_dir):
        view = self._view(row)
        if workspace_dir:
            try:
                await asyncio.to_thread(
                    self._verify, workspace_dir, json.loads(row["package_json"])
                )
                view["evidence_status"] = "current"
            except WorkflowSourceExecutionError as error:
                view.update(evidence_status="stale", evidence_message=str(error))
        return view

    async def get(self, workspace_id, review_id, workspace_dir=None):
        return await self._inspect(
            await asyncio.to_thread(self.repository.get, workspace_id, review_id),
            workspace_dir,
        )

    async def list(self, workspace_id, path, workspace_dir=None):
        return [
            await self._inspect(row, workspace_dir)
            for row in await asyncio.to_thread(self.repository.list, workspace_id, path)
        ]

    async def decide(
        self,
        *,
        workspace_id,
        workspace_dir,
        review_id,
        expected_package_digest,
        decision,
        reason="",
    ):
        if (
            decision not in {"approved", "changes_requested"}
            or not isinstance(reason, str)
            or len(reason) > 2000
        ):
            raise ValueError("Choose approve or request changes with a bounded reason")
        reason = reason.strip()
        if decision == "changes_requested" and not reason:
            raise ValueError(
                "Explain the changes needed before recording this decision"
            )
        row = await asyncio.to_thread(self.repository.get, workspace_id, review_id)
        package = json.loads(row["package_json"])
        if (
            row["package_digest"] != expected_package_digest
            or _digest(package) != row["package_digest"]
        ):
            raise WorkflowSourceExecutionError(
                "WORKFLOW_REVIEW_STALE",
                "The review package identity changed.",
                "Reload the pending review.",
            )
        await asyncio.to_thread(self._verify, workspace_dir, package)
        try:
            row = await asyncio.to_thread(
                self.repository.decide,
                workspace_id,
                review_id,
                expected_package_digest,
                {
                    "state": decision,
                    "reason": reason,
                    "actor": "local-workspace-user",
                    "decided_at": _now(),
                },
            )
        except ArtifactReviewConflict as error:
            raise WorkflowSourceExecutionError(
                "WORKFLOW_REVIEW_CONFLICT",
                str(error),
                "Reload the review to see the recorded decision.",
            ) from error
        return self._view(row)
