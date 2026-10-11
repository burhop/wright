"""Prepare one registered structured output and pinned validation request."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid4

from core.process_validation import (
    ProducerIdentity,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
)
from data_vault.process_validation_repository import ProcessValidationRepository
from workspace_service.process_validation.profiles import load_profile


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--workspace-id", default="validator-example")
    parser.add_argument("--length-mm", type=float, default=100.0)
    parser.add_argument("--part-id", default="demo-plate")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    database = workspace / "validation.sqlite3"
    request_path = workspace / "request.json"
    profile = load_profile("structured-demo")
    run_id = f"validator-example-{uuid4().hex}"
    value = {"part_id": args.part_id, "length_mm": args.length_mm}
    subject = SubjectBinding(
        id=f"output-{canonical_digest([run_id, value])}",
        role="result",
        result_id=f"{run_id}:produce:result",
        producer=ProducerIdentity(
            run_id=run_id,
            step_id="produce",
            attempt=1,
            output_port="result",
        ),
        kind="value",
        value=value,
        sha256=canonical_digest(value),
    )
    repository = ProcessValidationRepository(database)
    repository.register_output(args.workspace_id, subject)
    request = ValidationRequest(
        trace_id=run_id,
        workspace_id=args.workspace_id,
        invocation_id=f"inspect-{run_id}",
        subjects=(subject,),
        profile_ref=profile.reference(),
        baseline_ref=profile.baseline.reference(),
        idempotency_key=f"evaluate-{run_id}",
    )
    request_path.write_text(request.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "workspace": str(workspace),
                "workspace_id": args.workspace_id,
                "database": str(database),
                "request": request_path.name,
                "profile": "structured-demo",
                "expected_release_eligible": (
                    args.part_id == "demo-plate" and 99.8 <= args.length_mm <= 100.2
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
