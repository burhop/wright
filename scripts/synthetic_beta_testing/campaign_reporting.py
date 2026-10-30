"""Read-only projections of existing development-metrics observations."""

from collections import defaultdict
from datetime import datetime
from tool_registry.development_metrics import validate_event
from .reports import ReportError
from .journey import CATEGORIES

PHASES = {
    "setup",
    "implementation",
    "focused_validation",
    "customer_validation",
    "diagnosis",
    "review",
    "harness_repair",
    "waiting",
    "reporting",
}
STAGES = {
    "setup": "integration",
    "implementation": "implementation",
    "focused_validation": "testing",
    "customer_validation": "review",
    "diagnosis": "implementation",
    "review": "review",
    "harness_repair": "implementation",
    "waiting": "integration",
    "reporting": "implementation",
}


def observed_at(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def project_activity(snapshot, bindings):
    if snapshot.get("truncated") or snapshot.get("availability") != "available":
        raise ReportError("activity export is incomplete or unavailable")
    pending = {}
    intervals = []
    ids = set()
    for event in sorted(
        snapshot["events"], key=lambda e: (observed_at(e["at"]), e["id"])
    ):
        validate_event(event)
        if event["id"] in ids:
            raise ReportError("duplicate activity event identity")
        ids.add(event["id"])
        if event["kind"] != "activity":
            continue
        task = event["data"]["task"]
        binding = bindings.get(task)
        if (
            not binding
            or not {"phase", "lane"} <= set(binding)
            or set(binding) - {"phase", "lane", "origin", "issue_ids", "categories"}
            or binding["phase"] not in PHASES
        ):
            raise ReportError("activity task lacks an explicit phase/lane binding")
        if binding.get("origin", "unspecified") not in {
            "inside_loop",
            "outside_loop",
            "unspecified",
        }:
            raise ReportError("unknown work origin")
        if not isinstance(binding.get("issue_ids", []), list) or any(
            not isinstance(x, str) or not x for x in binding.get("issue_ids", [])
        ):
            raise ReportError("invalid activity issue links")
        if not isinstance(binding.get("categories", []), list) or any(
            x not in CATEGORIES for x in binding.get("categories", [])
        ):
            raise ReportError("invalid activity issue categories")
        if not isinstance(binding["lane"], str) or not binding["lane"]:
            raise ReportError("invalid activity lane")
        if event["data"]["stage"] != STAGES[binding["phase"]]:
            raise ReportError("phase binding differs from recorded activity stage")
        key = event["feature"], task
        status = event["data"]["status"]
        if status == "started":
            if key in pending or any(
                (x["feature"], x["task"]) == key for x in intervals
            ):
                raise ReportError("activity task has more than one start")
            pending[key] = event
            continue
        start = pending.pop(key, None)
        if (
            start is None
            or start["data"]["stage"] != event["data"]["stage"]
            or start["subject"] != event["subject"]
        ):
            raise ReportError("activity terminal does not bind its start")
        seconds = (
            datetime.fromisoformat(event["at"].replace("Z", "+00:00"))
            - datetime.fromisoformat(start["at"].replace("Z", "+00:00"))
        ).total_seconds()
        if seconds < 0:
            raise ReportError("negative activity interval")
        intervals.append(
            {
                "feature": event["feature"],
                "task": task,
                **binding,
                "started_at": start["at"],
                "finished_at": event["at"],
                "seconds": seconds,
                "status": status,
                "summary": start["data"]["summary"],
                "subject": start["subject"],
            }
        )
    open_windows = [
        {
            "feature": event["feature"],
            "task": event["data"]["task"],
            **bindings[event["data"]["task"]],
            "started_at": event["at"],
            "summary": event["data"]["summary"],
        }
        for event in pending.values()
    ]
    lanes = defaultdict(list)
    for item in intervals + [{**x, "finished_at": None} for x in open_windows]:
        lanes[item["feature"], item["lane"]].append(item)
    for windows in lanes.values():
        windows.sort(key=lambda x: observed_at(x["started_at"]))
        for left, right in zip(windows, windows[1:]):
            if left["finished_at"] is None or datetime.fromisoformat(
                left["finished_at"].replace("Z", "+00:00")
            ) > datetime.fromisoformat(right["started_at"].replace("Z", "+00:00")):
                raise ReportError(
                    "overlapping activity in the same lane; use distinct process lanes"
                )
    totals = defaultdict(float)
    for interval in intervals:
        totals[interval["feature"], interval["lane"], interval["phase"]] += interval[
            "seconds"
        ]
    return {
        "intervals": intervals,
        "open_windows": open_windows,
        "totals": [
            {"feature": feature, "lane": lane, "phase": phase, "seconds": seconds}
            for (feature, lane, phase), seconds in sorted(totals.items())
        ],
        "limits": [
            "Recorded task windows include waits, not human effort or CPU utilization.",
            "Open windows and gaps are uncounted, not zero.",
            "Concurrent lanes are never added into total campaign elapsed time.",
        ],
    }
