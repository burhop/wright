"""Installed/offline entry point for the same validation application service."""

import argparse
import asyncio
from contextlib import redirect_stdout
from pathlib import Path
import sys

from core.process_validation import ValidationRequest, canonical_json
from core.tools import ToolContext
from .process_validation.application import ValidationApplication
from .process_validation.profiles import load_profile
from .process_validation_tools import ProcessValidationTool
from .workflow_sources import WorkspaceWorkflowSourceStore


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inspect process output and retain validation evidence"
    )
    parser.add_argument(
        "operation", choices=("evaluate", "read", "get", "export", "profile")
    )
    parser.add_argument("--profile", default="structured-demo")
    parser.add_argument(
        "--profile-source", choices=("packaged", "workspace"), default="packaged"
    )
    parser.add_argument("--workspace")
    parser.add_argument("--workspace-id", default="standalone")
    parser.add_argument("--db")
    parser.add_argument("--request", help="Workspace-relative validation request JSON")
    parser.add_argument("--assessment")
    parser.add_argument("--cursor", type=int, default=0)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--format", choices=("json", "markdown", "csv"), default="json")
    args = parser.parse_args(argv)
    try:
        if args.operation == "profile":
            if args.profile_source == "workspace" and not args.workspace:
                parser.error("Workspace profiles require --workspace")
            profile = load_profile(
                args.profile,
                workspace_root=args.workspace
                if args.profile_source == "workspace"
                else None,
            )
            result = {
                "profile": profile.model_dump(mode="json"),
                "profile_ref": profile.reference().model_dump(),
                "baseline_ref": profile.baseline.reference().model_dump(),
            }
        else:
            if not args.workspace or not args.db:
                parser.error("Evaluation/read requires --workspace and --db")
            root = Path(args.workspace).resolve(strict=True)
            application = ValidationApplication(args.db, args.workspace_id, str(root))
            if args.operation == "evaluate":
                if not args.request:
                    parser.error("Evaluation requires --request")
                raw = WorkspaceWorkflowSourceStore(str(root)).read_artifact_bytes(
                    args.request, max_bytes=16 * 1024 * 1024
                )
                request = ValidationRequest.model_validate_json(raw)
                arguments = {
                    "request": request.model_dump(mode="json"),
                    "profile": {
                        "source": args.profile_source,
                        "name": args.profile,
                        "reference": request.profile_ref.model_dump(),
                    },
                }
                context_id = request.invocation_id
            elif args.operation == "read":
                if not args.assessment:
                    parser.error("Read requires --assessment")
                arguments, context_id = (
                    {
                        "assessment_id": args.assessment,
                        "cursor": args.cursor,
                        "limit": args.limit,
                    },
                    "cli-read",
                )
            else:
                if not args.assessment:
                    parser.error(f"{args.operation.title()} requires --assessment")
                arguments, context_id = {"assessment_id": args.assessment}, "cli-read"
                if args.operation == "export":
                    arguments["format"] = args.format
            with redirect_stdout(sys.stderr):
                result = asyncio.run(
                    ProcessValidationTool(application, args.operation).execute(
                        arguments,
                        context=ToolContext(
                            principal_id="local-cli",
                            workspace_id=args.workspace_id,
                            trace_id=context_id,
                            request_id=context_id,
                        ),
                    )
                )
        if args.operation == "export":
            print(result["content"], end="")
        else:
            print(canonical_json(result))
        return (
            2 if args.operation == "evaluate" and not result["release_eligible"] else 0
        )
    except (ValueError, KeyError, PermissionError, OSError) as exc:
        print(canonical_json({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
