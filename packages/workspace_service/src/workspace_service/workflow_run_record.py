"""Durable run diagnostics, written through the existing workspace file service."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import PurePosixPath
from uuid import uuid4
import socket
import hashlib
import logging

import anyio

_FINAL_CHECKPOINT_SECONDS = 5
_logger = logging.getLogger(__name__)


def _execution_snapshot(record, state):
    """Fold durable events, never infer execution from graph position or elapsed time.

    Polling exposes artifact metadata, not model responses or native tool payloads.
    Detailed immutable evidence remains available at the existing run-log path.
    """
    truncated = False

    def fields(value, names):
        nonlocal truncated
        if not isinstance(value, dict):
            return {}
        out = {}
        for key in names:
            item = value.get(key)
            if isinstance(item, str) and len(item) > 4096:
                truncated = True
                continue  # Never turn a truncated path/identity into a valid link.
            if item is None or isinstance(item, (str, int, float, bool)):
                if key in value:
                    out[key] = item
        return out

    def artifact(value, depth=0):
        nonlocal truncated
        out = fields(value, ("schema_version", "id", "kind", "name"))
        if not out.get("id") or not out.get("kind") or not out.get("name"):
            truncated = True
            return None
        out["provenance"] = fields(
            value.get("provenance"), ("run_id", "task_id", "output_port")
        )
        revisions = value.get("provenance", {}).get("input_revisions", [])
        out["provenance"]["input_revisions"] = (
            [
                list(pair)
                for pair in revisions[:64]
                if isinstance(pair, (list, tuple))
                and len(pair) == 2
                and isinstance(pair[0], str)
                and len(pair[0]) <= 4096
                and (
                    pair[1] is None or isinstance(pair[1], str) and len(pair[1]) <= 4096
                )
            ]
            if isinstance(revisions, (list, tuple))
            else []
        )
        truncated |= not isinstance(revisions, (list, tuple)) or len(revisions) > 64
        reps = value.get("representations", [])
        if not isinstance(reps, list):
            truncated = True
            return None
        out["representations"] = [
            fields(
                r,
                (
                    "kind",
                    "location",
                    "format",
                    "provider_id",
                    "resource_id",
                    "revision",
                    "durability",
                    "sha256",
                    "size_bytes",
                ),
            )
            for r in reps[:64]
            if isinstance(r, dict)
        ]
        out["representations"] = [
            r for r in out["representations"] if r.get("location") and r.get("kind")
        ]
        exports = value.get("exports", [])
        if not isinstance(exports, list):
            exports = []
            truncated = True
        out["exports"] = (
            [
                a
                for item in exports[:16]
                if isinstance(item, dict)
                if (a := artifact(item, depth + 1))
            ]
            if depth < 2
            else []
        )
        truncated |= (
            len(reps) > 64 or len(exports) > 16 or (depth >= 2 and bool(exports))
        )
        return out if out["representations"] else None

    completed = {}
    active = None
    execution_kinds = {}
    current_results = {}
    outputs = {}
    tools = tool_ends = model_calls = revisions = 0
    progress = None
    events = record.get("events", [])
    output_fields = (
        "task_id",
        "task_title",
        "output_path",
        "output_bytes",
        "output_format",
        "sha256",
        "cad_role",
        "artifact_role",
    )
    event_fields = (
        "kind",
        "at",
        "task_id",
        "task_title",
        "execution_kind",
        "message",
        "status",
        "tool",
        "revision",
    )

    def invalidate(ids):
        for task_id in ids:
            completed.pop(task_id, None)
        for key, result in list(current_results.items()):
            if result.get("provenance", {}).get("task_id") in ids:
                del current_results[key]
        for key, output in list(outputs.items()):
            if output.get("task_id") in ids:
                del outputs[key]

    for event in events:
        kind = event.get("kind")
        task_id = event.get("task_id")
        if not isinstance(task_id, str) or not task_id or len(task_id) > 4096:
            task_id = None
        if kind == "step_started" and task_id:
            invalidate({task_id})
            active = task_id
            execution_kinds[task_id] = event.get("execution_kind")
            model_calls += event.get("execution_kind") == "ai"
            tools += event.get("execution_kind") == "mcp"
        elif kind == "step_completed" and task_id:
            completed[task_id] = None
            tool_ends += execution_kinds.get(task_id) == "mcp"
            if active == task_id:
                active = None
        elif kind == "design_revision":
            ids = event.get("invalidated_task_ids", [])
            invalidate(
                {i for i in ids if isinstance(i, str)}
                if isinstance(ids, list)
                else set()
            )
            active = None  # The restart is active only after its step_started event.
            revisions += 1
        elif kind == "tool_started":
            tools += 1
        elif (
            kind == "task_progress"
            and execution_kinds.get(task_id) == "mcp_task"
            and isinstance(event.get("available_tools"), list)
            and type(event.get("tool_calls")) is int
        ):
            # The agent loop persists this immediately before each model decision.
            # A task can have many decisions; never equate one MCP task to one call.
            # CAD export/integrity messages share task_progress but have no decision
            # catalog/call-count metadata and must not inflate model usage.
            model_calls += 1
        elif kind == "tool_completed":
            tool_ends += 1
        elif kind == "result_ready":
            result = event.get("engineering_result")
            if isinstance(result, dict) and isinstance(result.get("id"), str):
                current_results[result["id"]] = result
        elif kind == "output_saved":
            if isinstance(event.get("output_path"), str):
                outputs[event["output_path"]] = fields(event, output_fields)
        if kind in {
            "run_started",
            "step_started",
            "step_completed",
            "task_progress",
            "operation_progress",
            "tool_started",
            "tool_completed",
            "design_check",
            "design_revision",
            "review_requested",
        }:
            progress = fields(event, event_fields)

    result = record.get("result") or {}
    if isinstance(result.get("results"), list):
        current_results = {
            r["id"]: r
            for r in result["results"]
            if isinstance(r, dict) and isinstance(r.get("id"), str)
        }
    elif not events:
        current_results = record.get("partial_results", {})
    if isinstance(result.get("outputs"), list):
        outputs = {
            o["output_path"]: fields(o, output_fields)
            for o in result["outputs"]
            if isinstance(o, dict) and isinstance(o.get("output_path"), str)
        }
    compact_results = [
        a for r in current_results.values() if isinstance(r, dict) if (a := artifact(r))
    ]
    run_id = result.get("run_id")
    if not isinstance(run_id, str):
        ids = {r.get("provenance", {}).get("run_id") for r in compact_results}
        ids.discard(None)
        run_id = next(iter(ids)) if len(ids) == 1 else None
    if isinstance(run_id, str) and len(run_id) > 4096:
        run_id = None
        truncated = True
    snapshot = {
        "active_task_id": active if state == "running" else None,
        "completed_task_ids": list(completed),
        "event_count": len(events),
        "model_call_count": model_calls,
        "tool_call_count": tools,
        "tool_completed_count": tool_ends,
        "revision_count": revisions,
        "outputs": list(outputs.values()),
        "last_progress": progress,
        "truncated": truncated,
    }
    # Bound the complete artifact/event projection, even for unusually wide graphs.
    while (
        len(json.dumps([snapshot, compact_results], ensure_ascii=True).encode())
        > 64 * 1024
    ):
        snapshot["truncated"] = True
        if compact_results:
            compact_results.pop()
        elif snapshot["outputs"]:
            snapshot["outputs"].pop()
        elif snapshot["completed_task_ids"]:
            snapshot["completed_task_ids"].pop()
        else:
            snapshot["last_progress"] = None
            break
    return snapshot, compact_results, run_id


async def record_workflow_run(
    *,
    service,
    workspace_dir,
    source_path,
    source_digest,
    execute,
    on_event=None,
    workspace_id=None,
):
    from .workflow_resource_lease import ApplicationLease

    identity = "workflow-run:" + uuid4().hex
    async with ApplicationLease(identity):
        return await _record_run(
            service=service,
            workspace_dir=workspace_dir,
            source_path=source_path,
            source_digest=source_digest,
            execute=execute,
            on_event=on_event,
            identity=identity,
            workspace_id=workspace_id,
        )


async def _record_run(
    *,
    service,
    workspace_dir,
    source_path,
    source_digest,
    execute,
    on_event,
    identity,
    workspace_id,
):
    started = datetime.now(timezone.utc)
    slug = PurePosixPath(source_path).name.removesuffix(".workflow.wflow")
    filename = (
        f"runs/{slug}/{started.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:12]}.json"
    )
    record = {
        "workflow_path": source_path,
        "source_digest": source_digest,
        "owner": {"host": socket.gethostname(), "lease": identity},
        "started_at": started.isoformat(),
        "status": "running",
        "events": [],
    }
    # Publish before execution, then atomically checkpoint this run's own file.
    # A host crash leaves a nonterminal record with the last known operation;
    # reopening it must not imply that a submitted mutation is safe to repeat.
    filename = await service.files.write_generated(
        workspace_dir,
        filename,
        json.dumps(record, ensure_ascii=False, indent=2),
        "indexed",
    )

    async def checkpoint():
        await service.files.write_generated(
            workspace_dir,
            filename,
            json.dumps(record, ensure_ascii=False, indent=2),
            "overwrite",
        )

    async def emit(event):
        record["events"].append(dict(event))
        if event.get("kind") == "result_ready":
            result = event["engineering_result"]
            record.setdefault("partial_results", {})[result["id"]] = result
        if event.get("kind") == "design_revision":
            invalidated = set(event.get("invalidated_task_ids", []))
            record["partial_results"] = {
                key: result
                for key, result in record.get("partial_results", {}).items()
                if result.get("provenance", {}).get("task_id") not in invalidated
            }
        await checkpoint()
        if on_event:
            await on_event(event)

    try:
        await emit(
            {
                "kind": "run_started",
                "at": started.isoformat(),
                "task_id": "",
                "task_title": slug,
                "run_log_path": filename,
            }
        )
        result = await execute(emit)
        review_request = result.pop("_review_request", None)
        if review_request:
            if not workspace_id:
                raise ValueError("Engineer review requires a workspace identity")
            review = await service.workflow_artifact_reviews.create(
                workspace_id=workspace_id,
                workspace_dir=workspace_dir,
                workflow_path=source_path,
                run_log_path=filename,
                result=result,
                request=review_request,
            )
            result.update(status="pending_review", review=review)
            record.update(status="pending_review", result=result, review=review)
            await emit(
                {
                    "kind": "review_requested",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "task_id": review["task_id"],
                    "task_title": review["task_title"],
                    "review": review,
                }
            )
        else:
            result["status"] = "completed"
            record.update(status="completed", result=result)
    except asyncio.CancelledError:
        record.update(
            status="cancelled", error="Cancelled; completed tool operations remain."
        )
        raise
    except Exception as error:
        record.update(
            status="failed",
            error=str(error),
            code=getattr(error, "code", "EXECUTION_FAILED"),
        )
        raise
    finally:
        record["execution_ended_at"] = datetime.now(timezone.utc).isoformat()
        if record["status"] != "pending_review":
            record["completed_at"] = record["execution_ended_at"]
        # Indexed publication never replaces another run. Logs survive reloads and
        # remain accessible through the existing workspace file browser/viewer.
        # Starlette disconnects cancel an AnyIO scope repeatedly at every await.
        # Shield only this bounded final evidence write, never execution or a tool.
        try:
            with anyio.move_on_after(_FINAL_CHECKPOINT_SECONDS, shield=True) as cleanup:
                await checkpoint()
            if cleanup.cancel_called:
                raise TimeoutError(
                    "Final workflow checkpoint exceeded its cleanup deadline"
                )
        except Exception:
            if record["status"] not in {"cancelled", "failed"}:
                raise
            # Preserve the original cancellation/failure. If storage cannot finish,
            # the read-only lease probe still reports interrupted/unknown, not live.
            _logger.exception(
                "Unable to persist final workflow checkpoint: %s", filename
            )
    return {**result, "run_log_path": filename}


def recent_workflow_runs(workspace_dir, source_path, *, limit=10, latest_only=False):
    """Bounded, read-only history. Never resubmit or mutate a recovered operation."""
    from .workspace_path import WorkspacePath
    from .workflow_resource_lease import lease_is_active

    paths = WorkspacePath(workspace_dir)
    source_file = paths.resolve(source_path, must_exist=True)
    current_digest = None
    if latest_only:
        with source_file.open("rb") as stream:
            current_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    slug = PurePosixPath(source_path).name.removesuffix(".workflow.wflow")
    folder = paths.resolve(f"runs/{slug}")
    if not folder.is_dir():
        return []
    # Bound directory work as well as JSON reads. Report only this exact source.
    candidates = []
    for index, entry in enumerate(folder.iterdir()):
        if index >= 10000:
            break
        if entry.suffix == ".json":
            candidates.append(entry.name)
    results = []
    latest_group = None
    for name in sorted(candidates, reverse=True)[:100]:
        # Same-second run names have random suffixes. Read that small timestamp
        # group before selecting by actual start time, rather than UUID ordering.
        if latest_only and results and name.split("-", 1)[0] != latest_group:
            break
        relative = f"runs/{slug}/{name}"
        try:
            path = paths.resolve(relative, must_exist=True)
            with path.open("rb") as stream:
                data = stream.read(16 * 1024 * 1024 + 1)
            if len(data) > 16 * 1024 * 1024:
                continue
            record = json.loads(data)
            if not isinstance(record, dict):
                continue
            if record.get("workflow_path") != source_path:
                continue
            events = record.get("events", [])
            if not isinstance(events, list) or any(
                not isinstance(e, dict) for e in events
            ):
                continue
            state = record.get("status", "unknown")
            if not isinstance(state, str) or state not in {
                "running",
                "completed",
                "pending_review",
                "failed",
                "cancelled",
                "interrupted",
                "unknown",
            }:
                continue
            if any(
                record.get(key) is not None
                and (not isinstance(record[key], str) or len(record[key]) > 128)
                for key in (
                    "started_at",
                    "completed_at",
                    "execution_ended_at",
                    "source_digest",
                )
            ):
                continue
            if record.get("error") is not None and not isinstance(record["error"], str):
                continue
            if state == "running":
                owner = record.get("owner", {})
                try:
                    active = (
                        lease_is_active(owner["lease"])
                        if owner.get("host") == socket.gethostname()
                        and isinstance(owner.get("lease"), str)
                        else None
                    )
                except OSError:
                    active = (
                        None  # An unreadable ownership probe cannot prove interruption.
                    )
                state = (
                    "running"
                    if active is True
                    else "interrupted"
                    if active is False
                    else "unknown"
                )
            result = record.get("result") or {}
            if not isinstance(result, dict) or not isinstance(
                record.get("partial_results", {}), dict
            ):
                continue
            if result.get("results") is not None and not isinstance(
                result["results"], list
            ):
                continue
            summary = {
                "path": relative,
                "status": state,
                "started_at": record.get("started_at"),
                "completed_at": record.get("completed_at"),
                "source_digest": record.get("source_digest"),
                "error": record.get("error"),
                "results": result.get("results")
                or list(record.get("partial_results", {}).values()),
                "last_event": events[-1] if events else None,
            }
            if latest_only:
                snapshot, artifacts, run_id = _execution_snapshot(record, state)
                summary.update(
                    execution=snapshot,
                    results=artifacts,
                    run_id=run_id,
                    execution_ended_at=record.get("execution_ended_at"),
                    source_matches_current=record.get("source_digest")
                    == current_digest,
                    last_event=snapshot["last_progress"],
                )
                if isinstance(summary.get("error"), str):
                    summary["error"] = summary["error"][:4096]
                latest_group = name.split("-", 1)[0]
            results.append(summary)
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue
        if not latest_only and len(results) >= min(20, max(1, limit)):
            break
    return (
        sorted(
            results, key=lambda r: (r.get("started_at") or "", r["path"]), reverse=True
        )[:1]
        if latest_only
        else results
    )
