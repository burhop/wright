"""Read-only historical links over the existing canonical run recorder.

This adapter discovers one recorded identity at an exact workspace locator. It
does not prepare, resume, dispatch, poll a provider or reinterpret old results
as current engineering acceptance.
"""

import json
from pathlib import PurePosixPath

from ..workspace_path import WorkspacePath
from ..workflow_run_record import read_workflow_run, WorkflowRunReadError

MAX_LEGACY_IDENTITY_BYTES = 16 * 1024 * 1024


def read_legacy_result(workspace_dir: str, workflow_path: str, run_log_path: str):
    paths = WorkspacePath(workspace_dir)
    try:
        source_parts = paths._validate_relative(workflow_path)
        source = "/".join(source_parts)
        parts = paths._validate_relative(run_log_path)
        relative = "/".join(parts)
        slug = PurePosixPath(source).name.removesuffix(".workflow.wflow")
        if PurePosixPath(
            relative
        ).parent.as_posix() != f"runs/{slug}" or not relative.endswith(".json"):
            raise ValueError("Choose the exact recorded workflow result")
        with paths.resolve(relative, must_exist=True).open("rb") as stream:
            raw = stream.read(MAX_LEGACY_IDENTITY_BYTES + 1)
        if len(raw) > MAX_LEGACY_IDENTITY_BYTES:
            raise ValueError("The historical identity record exceeds its read bound")
        record = json.loads(raw)
        if not isinstance(record, dict) or record.get("workflow_path") != source:
            raise ValueError("The historical result belongs to another workflow")
        run_id = record.get("run_id") or (record.get("result") or {}).get("run_id")
        if not isinstance(run_id, str) or not run_id or len(run_id) > 4096:
            raise ValueError("The historical result has no recorded run identity")
    except (OSError, ValueError, TypeError, AttributeError) as error:
        raise WorkflowRunReadError(
            "invalid", "The exact historical result could not be verified"
        ) from error
    run = read_workflow_run(workspace_dir, source, run_id, run_log_path=relative)
    return {
        "schema_version": "wright.historical-result/1",
        "read_only": True,
        "workflow_path": source,
        "run_log_path": relative,
        "run": run,
        "permitted_actions": [],
    }
