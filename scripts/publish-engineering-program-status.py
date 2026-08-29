#!/usr/bin/env python3
"""CLI entry point for deterministic engineering program-status publication."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from pathlib import Path

from program_status.publisher import (
    ProgramStatusPublishError,
    ProgramStatusPublishRequest,
    publish_program_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="publish-engineering-program-status",
        description="Publish one validated committed EPP status bundle.",
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--data-root", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        result = publish_program_status(
            ProgramStatusPublishRequest(
                repository=Path(args.repository),
                source_commit=args.source,
                data_root=Path(args.data_root),
            )
        )
    except ProgramStatusPublishError as exc:
        print(
            json.dumps(
                {
                    "status": "rejected",
                    "code": exc.code,
                    "message": str(exc),
                    "recovery_class": exc.recovery_class,
                },
                sort_keys=True,
            )
        )
        return 2
    print(
        json.dumps(
            {
                "status": "published",
                "source_commit": result.source_commit,
                "source_tree": result.source_tree,
                "program_tree": result.program_tree,
                "bundle_id": result.bundle_id,
                "installed_artifact": result.installed_artifact,
                "changed": result.changed,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
