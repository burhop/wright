"""Continuous observed/declared customer activity, separate from product status."""

ACTIVITY_STATES = {
    "preparing_environment": "Preparing environment",
    "reviewing_deciding": "Reviewing / deciding next action",
    "reading": "Reading",
    "screen_capture": "Capturing the screen",
    "considering_alternative": "Considering another approach",
    "navigating": "Navigating",
    "typing": "Entering information",
    "waiting_wright": "Waiting for Wright",
    "waiting_external": "Waiting for external service",
    "recovering": "Recovering from a problem",
    "feedback": "Giving feedback",
    "recording_observation": "Recording observation",
    "native_pause": "AI tester pause",
}


def project_diary(marks, elapsed, stage_rows, finished):
    if not marks:
        return {"available": False, "reason": "Activity states were not recorded in this earlier session."}
    stage_intervals = sorted(
        ({**span, "stage_id": stage["id"], "stage_label": stage["label"]}
         for stage in stage_rows for span in stage["intervals"]),
        key=lambda span: span["start_seconds"],
    )
    intervals = []
    for index, mark in enumerate(marks):
        end = marks[index + 1]["elapsed_seconds"] if index + 1 < len(marks) else elapsed
        # Split at stage changes so each instant has both dimensions.
        for stage in stage_intervals:
            begin = max(mark["elapsed_seconds"], stage["start_seconds"])
            stop = min(end, stage["end_seconds"])
            if stop <= begin:
                continue
            state = mark["state"]
            # v1 controller called screenshot capture "reading"; a declared
            # reading interval is separate. Preserve raw marks, clarify the view.
            if state == "reading" and mark["source"] == "controller":
                state = "screen_capture"
            intervals.append({
                "start_seconds": begin, "end_seconds": stop, "seconds": stop - begin,
                "stage_id": stage["stage_id"], "stage_label": stage["stage_label"],
                "state": state, "label": ACTIVITY_STATES[state],
                "summary": mark["summary"], "source": mark["source"],
                "evidence_refs": mark.get("evidence_refs", []),
                "clock_sequence": mark["sequence"],
            })
    total = sum(row["seconds"] for row in intervals)
    return {
        "available": True, "version": "continuous-customer-activity-v1",
        "intervals": intervals, "accounted_seconds": total,
        "coverage_complete": abs(total - elapsed) < 0.000001,
        "finished": finished,
        "basis": "Controller-timed activity boundaries and brief customer declarations. Reviewing/deciding includes model/transport/controller delay; no private reasoning or human-equivalent pace inferred.",
    }
