"""Command-line entry points for inspecting, running and continuing native workflows."""

import argparse
import json
import sys
from pathlib import Path

from .definition import parse
from .runner import resume, run
from .source import WorkflowSourceExecutionError


def _read(path):
    return json.loads(path.read_bytes()) if path is not None else {}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="wright-workflow")
    commands = parser.add_subparsers(required=True, dest="command")
    inspect = commands.add_parser("parse")
    inspect.add_argument("source", type=Path)
    execute = commands.add_parser("run")
    execute.add_argument("source", type=Path)
    execute.add_argument("--inputs", type=Path)
    restart = commands.add_parser("resume")
    restart.add_argument("--response", type=Path, required=True)
    for sub in (execute, restart):
        sub.add_argument("--bindings", type=Path)
        sub.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "parse":
            doc = parse(args.source)
            result = {
                "source_digest": doc.source_digest,
                "blocks": doc.graph.ordered,
                "ports": list(doc.graph.ports),
                "required_features": doc.required_features,
                "dependencies": [dep.model_dump() for dep in doc.dependencies],
            }
        elif args.command == "resume":
            result = resume(args.run_dir, _read(args.response), _read(args.bindings))
        else:
            result = run(
                args.source, _read(args.inputs), _read(args.bindings), args.run_dir
            )
    except Exception as error:
        data = {"code": getattr(error, "code", "WORKFLOW_ERROR"), "message": str(error)}
        if isinstance(error, WorkflowSourceExecutionError):
            data.update(correction=error.correction, block=error.block_id)
        print(json.dumps(data, ensure_ascii=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 1 if result.get("status") in {"failed", "outcome_unknown"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
