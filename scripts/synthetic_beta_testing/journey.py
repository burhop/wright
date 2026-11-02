"""Append-only observational clocks. No product execution or success authority."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time

from .reports import ReportError
from .activity_diary import ACTIVITY_STATES

CATEGORIES = {
    "slow": "Takes too long",
    "unclear_instructions": "Instructions are unclear",
    "broken_behavior": "Something fails or behaves incorrectly",
    "unclear_progress": "Cannot tell what Wright is doing",
    "hard_to_find": "Cannot find the next action",
    "setup_access": "Setup or access gets in the way",
    "hard_to_recover": "Cannot recover or keep my work",
    "unhelpful_result": "Result is missing, wrong or not useful",
    "unexpected_effort": "Too much repeated work or unexpected cost",
    "unclassified": "Needs classification",
}
STATES = {"started", "completed", "blocked", "abandoned"}


def validate_plan(plan):
    if plan.get("schema_version") != 1 or not plan.get("id") or not plan.get("label"):
        raise ReportError("journey plan needs version, identity and label")
    steps = plan.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 50:
        raise ReportError("journey plan needs 1–50 steps")
    ids = set()
    for step in steps:
        if (
            not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", step.get("id", ""))
            or step["id"] in ids
        ):
            raise ReportError("journey steps need unique safe identities")
        ids.add(step["id"])
        if not isinstance(step.get("label"), str) or not 1 <= len(step["label"]) <= 160:
            raise ReportError("journey step needs a bounded label")
    for item in [plan, *steps]:
        target = item.get("target_seconds")
        if target is not None and (
            type(target) not in (int, float) or not math.isfinite(target) or target <= 0
        ):
            raise ReportError("journey target must be positive or omitted")
    return plan


def read_events(root):
    return [
        json.loads(line)
        for line in (Path(root) / "journey-clock.jsonl").read_text().splitlines()
    ]


def project(plan, events):
    """Account for serial attention, revisits and gaps without guessing product time."""
    validate_plan(plan)
    if not events or events[0].get("kind") != "begin":
        raise ReportError("journey clock has no beginning")
    plan_digest = hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest()
    if events[0].get("plan_sha256") != plan_digest:
        raise ReportError("journey clock differs from frozen plan")
    steps = {
        s["id"]: {
            **s,
            "status": "not_attempted",
            "seconds": None,
            "visits": [],
            "categories": [],
            "note": "",
        }
        for s in plan["steps"]
    }
    active = None
    previous = 0.0
    ended = False
    issues = []
    activity_marks = []
    if events[0].get("activity_diary_version") == 1:
        activity_marks.append({"sequence": 0, "elapsed_seconds": 0,
                               "state": "preparing_environment",
                               "summary": "Starting the declared environment and preparing session access",
                               "source": "operator", "evidence_refs": []})
    session_id = events[0]["session_id"]
    for n, event in enumerate(events):
        elapsed = event.get("elapsed_seconds")
        if event.get("sequence") != n or event.get("session_id") != session_id:
            raise ReportError("journey event identity/order mismatch")
        if (
            type(elapsed) not in (int, float)
            or not math.isfinite(elapsed)
            or elapsed < previous
            or (n == 0 and elapsed != 0)
        ):
            raise ReportError("invalid journey clock")
        if datetime.fromisoformat(event["at"].replace("Z", "+00:00")).tzinfo is None:
            raise ReportError("journey event requires timezone")
        if ended:
            raise ReportError("journey event follows its end")
        previous = elapsed
        kind = event["kind"]
        if kind == "begin":
            if n:
                raise ReportError("duplicate journey beginning")
            continue
        if kind == "end":
            ended = True
            if active:
                active.update(
                    end_seconds=elapsed,
                    seconds=elapsed - active["start_seconds"],
                    status="interrupted",
                )
                steps[active["step_id"]]["status"] = "interrupted"
                active = None
            continue
        if kind == "activity":
            if not activity_marks:
                raise ReportError("Activity marks require a declared activity diary")
            if (event.get("state") not in ACTIVITY_STATES
                    or event.get("source") not in {"operator", "controller", "customer_declaration"}
                    or not isinstance(event.get("summary"), str)
                    or not 1 <= len(event["summary"]) <= 500
                    or not isinstance(event.get("evidence_refs", []), list)):
                raise ReportError("Invalid customer activity boundary")
            activity_marks.append(event)
            continue
        if (
            kind != "step"
            or event.get("step_id") not in steps
            or event.get("status") not in STATES
        ):
            raise ReportError("unknown journey step or status")
        if event.get("actor") not in {"customer", "operator"}:
            raise ReportError("invalid journey actor")
        categories = event.get("categories", [])
        if not isinstance(categories, list) or any(
            c not in CATEGORIES for c in categories
        ):
            raise ReportError("unknown customer issue category")
        step = steps[event["step_id"]]
        if event["status"] == "started":
            if active:
                raise ReportError("finish current journey step before starting another")
            active = {
                "step_id": event["step_id"],
                "start_seconds": elapsed,
                "end_seconds": None,
                "seconds": None,
                "status": "in_progress",
                "actor": event["actor"],
            }
            step["visits"].append(active)
            step["status"] = "in_progress"
        else:
            if not active or active["step_id"] != event["step_id"]:
                raise ReportError("journey finish does not match active step")
            if active["actor"] != event["actor"]:
                raise ReportError("journey step cannot change recorder actor")
            active.update(
                end_seconds=elapsed,
                seconds=elapsed - active["start_seconds"],
                status=event["status"],
            )
            active = None
            step["status"] = event["status"]
        step["note"] = event.get("note", "")
        step["categories"] = sorted(set(step["categories"] + categories))
        if categories:
            issues.append(
                {
                    "step_id": step["id"],
                    "categories": categories,
                    "note": event.get("note", ""),
                    "evidence_refs": event.get("evidence_refs", []),
                    "sequence": n,
                    "basis": "customer report"
                    if event["actor"] == "customer"
                    else "operator report",
                }
            )
    accounted = 0
    for step in steps.values():
        visits = step["visits"]
        closed = [v["seconds"] for v in visits if v["seconds"] is not None]
        step["seconds"] = sum(closed) if closed else None
        step["timing_complete"] = bool(visits) and len(closed) == len(visits)
        step["retry_count"] = max(0, len(visits) - 1)
        step["over_target"] = (
            step["seconds"] is not None
            and step.get("target_seconds") is not None
            and step["seconds"] > step["target_seconds"]
        )
        accounted += sum(closed)
    return {
        "available": True,
        "plan_id": plan["id"],
        "label": plan["label"],
        "session_id": session_id,
        "boundary": events[0]["boundary"],
        "started_at": events[0]["at"],
        "finished_at": events[-1]["at"] if ended else None,
        "elapsed_seconds": previous,
        "finished": ended,
        "target_seconds": plan.get("target_seconds"),
        "steps": list(steps.values()),
        "unassigned_seconds": max(0, previous - accounted),
        "issues": issues,
        "activity_marks": activity_marks,
        "basis": "Controller-timed, self-reported step boundaries; completion needs independent result evidence.",
    }


class JourneyRecorder:
    def __init__(self, root):
        self.root = Path(root)
        self.path = self.root / "journey-clock.jsonl"
        self.plan = json.loads((self.root / "journey-plan.json").read_text())
        if self.path.is_symlink() or (self.root / "journey-plan.json").is_symlink():
            raise ReportError("journey records cannot be symlinks")

    @classmethod
    def begin(cls, root, plan, boundary="whole_journey"):
        root = Path(root)
        validate_plan(plan)
        from .journey_stages import stage_for
        if any(stage_for(step) == "unmapped" for step in plan["steps"]):
            raise ReportError("New journey actions require a shared stage_id before observation")
        if boundary not in {"whole_journey", "customer_session_only"}:
            raise ReportError("unknown journey boundary")
        if (root / "journey-plan.json").exists() or (
            root / "journey-clock.jsonl"
        ).exists():
            raise ReportError("retain existing journey; use a fresh session")
        with (root / "journey-plan.json").open("x") as f:
            json.dump(plan, f, indent=2)
        event = {
            "kind": "begin",
            "session_id": root.name,
            "sequence": 0,
            "at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": 0,
            "monotonic_start": time.monotonic(),
            "boundary": boundary,
            "activity_diary_version": 1,
            "plan_sha256": hashlib.sha256(
                json.dumps(plan, sort_keys=True).encode()
            ).hexdigest(),
        }
        with (root / "journey-clock.jsonl").open("x") as f:
            f.write(json.dumps(event) + "\n")
        return cls(root)

    def append(self, kind, **fields):
        events = read_events(self.root)
        event = {
            **fields,
            "kind": kind,
            "session_id": self.root.name,
            "sequence": len(events),
            "at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.monotonic() - events[0]["monotonic_start"],
        }
        project(
            self.plan, events + [event]
        )  # Reject overlap, unknown IDs, replay or clock reset before writing.
        with self.path.open("a") as f:
            f.write(json.dumps(event) + "\n")
        return event

    def step(
        self,
        step_id,
        status,
        note="",
        categories=None,
        evidence_refs=None,
        actor="operator",
    ):
        if (
            actor not in {"operator", "customer"}
            or not isinstance(note, str)
            or len(note) > 3000
        ):
            raise ReportError("invalid journey observation")
        return self.append(
            "step",
            step_id=step_id,
            status=status,
            note=note,
            categories=categories or [],
            evidence_refs=evidence_refs or [],
            actor=actor,
        )

    def finish(self):
        return self.append("end")

    def activity(self, state, summary, *, source="controller", evidence_refs=None):
        return self.append("activity", state=state, summary=summary, source=source,
                           evidence_refs=evidence_refs or [])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-root", required=True, type=Path)
    sub = parser.add_subparsers(dest="command", required=True)
    begin = sub.add_parser("begin")
    begin.add_argument("--plan", required=True, type=Path)
    step = sub.add_parser("step")
    step.add_argument("--id", required=True)
    step.add_argument("--status", required=True, choices=sorted(STATES))
    step.add_argument("--note", default="")
    step.add_argument(
        "--category", action="append", choices=sorted(CATEGORIES), default=[]
    )
    sub.add_parser("finish")
    sub.add_parser("show")
    args = parser.parse_args()
    if args.command == "begin":
        JourneyRecorder.begin(args.session_root, json.loads(args.plan.read_text()))
    else:
        recorder = JourneyRecorder(args.session_root)
        if args.command == "step":
            recorder.step(args.id, args.status, args.note, args.category)
        elif args.command == "finish":
            recorder.finish()
    print(
        json.dumps(
            project(
                json.loads((args.session_root / "journey-plan.json").read_text()),
                read_events(args.session_root),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
