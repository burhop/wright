from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from .db import get_server
from .validation_executor import (
    DockerCleanContainerExecutor,
    MockValidationExecutor,
    ValidationExecutionUnavailable,
    skipped_evidence_from_unavailable,
)
from .validation_plan import build_validation_plan
from .validation_writer import write_validation_evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tool_registry.validation_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "validate"):
        command = subparsers.add_parser(name)
        command.add_argument("server_id")
        command.add_argument(
            "--db-path", default=os.getenv("DATABASE_PATH", "wright.db")
        )
        command.add_argument("--container", default="ubuntu-x64")
        command.add_argument("--evidence-dir", default="docs/mcp-catalog/evidence")
        command.add_argument("--executor", choices=["mock", "docker"], default="docker")
    return parser


async def _run(args: argparse.Namespace) -> int:
    server = get_server(args.db_path, args.server_id)
    if not server:
        raise SystemExit(f"MCP server '{args.server_id}' not found in {args.db_path}")

    plan = build_validation_plan(server)
    if args.command == "plan":
        print(plan.model_dump_json(indent=2))
        return 0

    executor = (
        MockValidationExecutor()
        if args.executor == "mock"
        else DockerCleanContainerExecutor(args.container)
    )
    try:
        evidence = await executor.execute(plan)
        exit_code = 0 if evidence.status == "passed" else 2
    except ValidationExecutionUnavailable as exc:
        evidence = skipped_evidence_from_unavailable(plan, args.container, exc)
        exit_code = 2
    json_path, markdown_path = write_validation_evidence(
        evidence, Path(args.evidence_dir)
    )
    print(
        json.dumps(
            {
                "server_id": args.server_id,
                "status": evidence.status,
                "json": str(json_path),
                "markdown": str(markdown_path),
            },
            indent=2,
        )
    )
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
