#!/usr/bin/env python3
"""Collect development observations independently of committed release evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import uuid
from pathlib import Path
from xml.etree import ElementTree

from tool_registry.development_metrics import (
    DevelopmentMetrics,
    collect_tasks,
    timestamp,
)

PROGRAM = "docs/programs/engineering-process-platform"


def record(store, kind, feature, subject, data, *, at=None, identity=None):
    store.append(
        {
            "id": identity or str(uuid.uuid4()),
            "at": at or timestamp(),
            "kind": kind,
            "feature": feature,
            "subject": subject,
            "data": data,
        }
    )


def import_usage(store, feature, path):
    """Extract counters only from an explicitly selected JSONL session.

    Do not retain prompts, responses, command arguments, or rate-limit percentages.
    Cumulative-counter differences suppress repeated usage notifications.
    """
    previous = None
    known = {event["id"] for event in store.read()["events"]}
    source = hashlib.sha256(str(path.resolve()).encode()).hexdigest()
    with path.open("rb") as stream:
        while True:
            offset = stream.tell()
            line = stream.readline()
            if not line:
                break
            if not line.endswith(b"\n"):
                break  # Writer has not finished this line; retry next poll.
            try:
                row = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            payload = row.get("payload", {})
            if row.get("type") != "event_msg" or payload.get("type") != "token_count":
                continue
            info = payload.get("info") or {}
            total = info.get("total_token_usage") or {}
            current = (total.get("input_tokens"), total.get("output_tokens"))
            if any(type(n) is not int or n < 0 for n in current):
                continue
            if previous is None:
                recent = info.get("last_token_usage") or {}
                delta = (recent.get("input_tokens", 0), recent.get("output_tokens", 0))
            else:
                delta = tuple(n - p for n, p in zip(current, previous))
            previous = current
            if any(type(n) is not int or n < 0 for n in delta) or not any(delta):
                continue
            identity = f"usage:{source}:{offset}"
            if identity in known:
                continue
            record(
                store,
                "usage",
                feature,
                "session-observation",
                {
                    "session": path.stem[-36:],
                    "task": "unassigned",
                    "input_tokens": delta[0],
                    "output_tokens": delta[1],
                },
                at=row["timestamp"],
                identity=identity,
            )


def import_history(store, repository, extra=(), only_tasks=False):
    """Replay task populations on one Git lineage at their actual commit times."""
    registry = json.loads(
        (repository / PROGRAM / "work-registry.json").read_text(encoding="utf-8")
    )
    sources = {row["feature_id"]: row["tasks_path"] for row in registry["task_sources"]}
    if only_tasks:
        sources = {}
    sources.update(dict(item.split("=", 1) for item in extra))
    for path in sources.values():
        if not (repository / path).resolve().is_relative_to(repository.resolve()):
            raise ValueError("Task source must be inside repository")
    known = {event["id"] for event in store.read()["events"]}
    imported = 0
    # Follow each task file through merged development history. Replaying every
    # feature at each branch commit would import unrelated, stale populations.
    for feature, path in sources.items():
        history = subprocess.check_output(
            ["git", "log", "--reverse", "--topo-order", "--format=%H%x09%cI",
             "HEAD", "--", path],
            cwd=repository, text=True, encoding="utf-8",
        )
        for line in history.splitlines():
            commit, at = line.split("\t")
            identity = f"git:{commit}:{feature}"
            if identity in known:
                continue
            blob = subprocess.run(
                ["git", "show", f"{commit}:{path}"],
                cwd=repository,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if blob.returncode:
                # Missing files before a feature existed are not zero progress.
                continue
            tasks = [
                {"task": task, "title": title[:1000], "checked": mark.lower() == "x"}
                for mark, task, title in re.findall(
                    r"^- \[([ xX])\] (T\d+)\b\s*(.*)$", blob.stdout, re.MULTILINE
                )
            ]
            record(
                store,
                "snapshot",
                feature,
                commit,
                {"tasks": tasks},
                at=at,
                identity=identity,
            )
            imported += 1
    return imported


def collect(store, repository, extra, sessions=(), only_tasks=False):
    registry = json.loads(
        (repository / PROGRAM / "work-registry.json").read_text(encoding="utf-8")
    )
    sources = {row["feature_id"]: row["tasks_path"] for row in registry["task_sources"]}
    if only_tasks:
        sources = {}
    sources.update(dict(item.split("=", 1) for item in extra))
    subject = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    history = store.read()["events"]
    latest = {
        event["feature"]: event["data"]
        for event in history
        if event["kind"] == "snapshot"
    }
    for row in collect_tasks(repository, list(sources.items())):
        data = {"tasks": row["tasks"]}
        if latest.get(row["feature"]) != data:
            record(store, "snapshot", row["feature"], subject, data)
    ledger = json.loads(
        (repository / PROGRAM / "test-run-ledger.json").read_text(encoding="utf-8")
    )
    known = {event["id"] for event in history}
    for run in ledger["runs"]:
        identity = "ledger:" + run["run_key"]
        if not run["terminal"] or identity in known:
            continue
        # Suite naming is not a feature binding: leave it explicitly unassigned.
        record(
            store,
            "qa",
            "unassigned",
            run["commit"],
            {
                "suite": run["suite_id"],
                "environment": "ledger-unspecified",
                **{
                    key: run["counts"][key]
                    for key in ("passed", "failed", "skipped", "not_run")
                },
                "evidence": f"{PROGRAM}/test-run-ledger.json#{run['run_id']}",
            },
            at=run["observed_at"],
            identity=identity,
        )
    for item in sessions:
        feature, path = item.split("=", 1)
        import_usage(store, feature, Path(path))
    record(store, "heartbeat", "collector", subject, {"status": "active"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        required=True,
        type=Path,
        help="Wright data directory (parent of program-status)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    watch = commands.add_parser("collect")
    watch.add_argument("--repository", type=Path, default=Path.cwd())
    watch.add_argument("--tasks", action="append", default=[], metavar="FEATURE=PATH")
    watch.add_argument(
        "--session",
        action="append",
        default=[],
        metavar="FEATURE=JSONL",
        help="Opt-in token counters from a specific coding session",
    )
    watch.add_argument("--only-tasks", action="store_true", help="Collect only explicit task sources, preserving historical features from other checkouts")
    watch.add_argument("--watch", action="store_true")
    watch.add_argument("--interval", type=float, default=30)
    history = commands.add_parser(
        "history",
        help="Backfill committed task checkpoints from the current Git lineage",
    )
    history.add_argument("--repository", type=Path, default=Path.cwd())
    history.add_argument("--tasks", action="append", default=[])
    event = commands.add_parser("event")
    event.add_argument(
        "file", type=Path, help="JSON event using the documented closed contract"
    )
    run = commands.add_parser(
        "run", help="Run a command with activity and optional JUnit result capture"
    )
    run.add_argument("--repository", type=Path, default=Path.cwd())
    run.add_argument("--feature", required=True)
    run.add_argument("--task", required=True)
    run.add_argument(
        "--stage",
        choices=["implementation", "testing", "review", "integration"],
        default="testing",
    )
    run.add_argument("--suite", default="command")
    run.add_argument("--environment", required=True)
    run.add_argument("--junit", type=Path)
    run.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    store = DevelopmentMetrics(args.data_root.resolve() / "program-status")
    if args.command == "history":
        print(
            f"Imported {import_history(store, args.repository.resolve(), args.tasks)} committed task snapshots"
        )
        return 0
    if args.command == "event":
        store.append(json.loads(args.file.read_text(encoding="utf-8")))
        return 0
    if args.command == "run":
        command = args.args[1:] if args.args[:1] == ["--"] else args.args
        if not command:
            parser.error("run requires a command after --")
        repository = args.repository.resolve()
        subject = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip()
        # A dirty checkout is explicitly a working-tree observation, not a tested commit claim.
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=repository,
            text=True,
        )
        if dirty:
            subject += ":working-tree"
        junit = (repository / args.junit).resolve() if args.junit else None
        if junit and junit.exists():
            parser.error(
                "Use a new JUnit output path for each run to avoid stale results"
            )
        activity = {
            "task": args.task,
            "stage": args.stage,
            "status": "started",
            "summary": args.suite,
        }
        record(store, "activity", args.feature, subject, activity)
        try:
            code = subprocess.call(command, cwd=repository)
        except (OSError, KeyboardInterrupt):
            record(
                store,
                "activity",
                args.feature,
                subject,
                {**activity, "status": "failed"},
            )
            raise
        record(
            store,
            "activity",
            args.feature,
            subject,
            {**activity, "status": "completed" if code == 0 else "failed"},
        )
        if junit and junit.exists():
            raw = junit.read_bytes()
            if len(raw) > 20 * 1024 * 1024 or b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
                raise ValueError("Invalid or oversized JUnit report")
            cases = ElementTree.fromstring(raw).findall(".//testcase")
            if not cases:
                raise ValueError("JUnit report contains no test cases")
            failed = sum(
                case.find("failure") is not None or case.find("error") is not None
                for case in cases
            )
            skipped = sum(case.find("skipped") is not None for case in cases)
            record(
                store,
                "qa",
                args.feature,
                subject,
                {
                    "suite": args.suite,
                    "environment": args.environment,
                    "passed": len(cases) - failed - skipped,
                    "failed": failed,
                    "skipped": skipped,
                    "not_run": None,
                    "evidence": "junit-sha256:" + hashlib.sha256(raw).hexdigest(),
                },
            )
        elif junit and code == 0:
            raise ValueError("Command succeeded but required JUnit report is missing")
        return code
    if args.interval < 5:
        parser.error("Collection interval must be at least five seconds")
    try:
        import_history(store, args.repository.resolve(), args.tasks, args.only_tasks)
        while True:
            try:
                collect(store, args.repository.resolve(), args.tasks, args.session, args.only_tasks)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                record(store, "heartbeat", "collector", "collector", {"status": "failed"})
                if not args.watch:
                    raise
                print(f"Collection failed ({type(error).__name__}); retrying next interval", flush=True)
            if not args.watch:
                return 0
            time.sleep(args.interval)
    except KeyboardInterrupt:
        record(store, "heartbeat", "collector", "collector", {"status": "stopped"})
        return 0
    except Exception:
        record(store, "heartbeat", "collector", "collector", {"status": "failed"})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
