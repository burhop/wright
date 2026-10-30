"""Stable reporting stages over immutable, scenario-specific action clocks.

One continuous attention clock changes owner at each recorded action start.
Completion marks record outcomes; they do not stop elapsed-time accounting.
This projection changes neither observations nor completion authority.
"""

from pathlib import Path
import json

from .reports import ReportError
from .activity_diary import project_diary

TAXONOMY_PATH = Path(__file__).parent / "assets/journey-stages-v1.json"
TAXONOMY = json.loads(TAXONOMY_PATH.read_text())
STAGE_IDS = {stage["id"] for stage in TAXONOMY["stages"]}
LEGACY = {
    step_id: stage["id"]
    for stage in TAXONOMY["stages"]
    for step_id in stage["legacy_step_ids"]
}


def stage_for(step):
    explicit = step.get("stage_id")
    if explicit is not None:
        if explicit not in STAGE_IDS:
            raise ReportError("Unknown shared journey stage: " + str(explicit))
        return explicit
    # Exact documented historical IDs only: never guess from labels or position.
    return LEGACY.get(step["id"], "unmapped")


def project_stages(journey):
    available = journey.get("available", False)
    steps = journey.get("steps", []) if available else []
    grouped = {stage_id: [] for stage_id in STAGE_IDS | {"unmapped"}}
    visits = []
    for step in steps:
        stage_id = stage_for(step)
        grouped[stage_id].append(step)
        for visit in step.get("visits", []):
            visits.append((visit["start_seconds"], stage_id, step["id"], visit))
    visits.sort(key=lambda row: row[0])
    intervals = {stage_id: [] for stage_id in grouped}
    for index, (start, stage_id, action_id, visit) in enumerate(visits):
        # The first declared action owns preparation from the already-started
        # whole-journey clock. Every subsequent start transfers ownership.
        begin = 0 if index == 0 else start
        end = visits[index + 1][0] if index + 1 < len(visits) else journey["elapsed_seconds"]
        intervals[stage_id].append({
            "action_id": action_id,
            "start_seconds": begin,
            "end_seconds": end,
            "seconds": end - begin,
            "outcome_mark_seconds": visit.get("end_seconds"),
            "status": visit["status"],
            "actor": visit["actor"],
        })
    rows = []
    definitions = TAXONOMY["stages"] + (
        [TAXONOMY["unmapped"]] if grouped["unmapped"] else []
    )
    for definition in definitions:
        stage_id = definition["id"]
        actions = grouped[stage_id]
        states = {action["status"] for action in actions}
        if not available:
            status = "not_measured"
        elif not actions:
            status = "not_in_journey"
        else:
            status = next(
                (s for s in ("blocked", "failed", "interrupted", "in_progress", "abandoned") if s in states),
                "completed" if states == {"completed"} else "partial_progress" if "completed" in states else "not_attempted",
            )
        spans = intervals[stage_id]
        rows.append({
            "id": stage_id,
            "label": definition["label"],
            "color": definition["color"],
            "seconds": sum(span["seconds"] for span in spans) if spans else None,
            "status": status,
            "action_ids": [a["id"] for a in actions],
            "visits": len(spans),
            "timing_complete": bool(spans) and journey.get("finished", False),
            "intervals": spans,
        })
    accounted = sum(row["seconds"] or 0 for row in rows)
    complete = available and bool(visits) and abs(accounted - journey["elapsed_seconds"]) < 0.000001
    return {
        "taxonomy_id": TAXONOMY["id"],
        "accounting_policy": "continuous_action_start_boundaries_v1",
        "available": available,
        "stages": rows,
        "accounted_seconds": accounted,
        "coverage_complete": complete,
        "activity_diary": project_diary(journey.get("activity_marks", []), journey.get("elapsed_seconds", 0), rows, journey.get("finished", False)),
        "basis": "From clock start to stop; each action owns elapsed time until the next action starts. Outcome marks do not stop timing. Includes waits and tester/controller time; not isolated product latency.",
    }
