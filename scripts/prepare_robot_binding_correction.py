"""Qualify and enroll Robot 010 after the named-file runtime repair; never dispatch.

Preserves Robot 009, uses the existing preparer/enroller, and starts a linked,
bounded correction episode. A saved uncertain write request is never replayed.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import urllib.parse
import xml.etree.ElementTree as ET

from prepare_robot_plot_correction import (
    ROOT,
    BASE,
    MODEL,
    SCENARIO,
    load,
    save_once,
    sha,
)

RUNTIME = (
    ROOT
    / "packages/workspace_service/src/workspace_service/workflow_source_execution.py"
)
TEST = ROOT / "packages/workspace_service/tests/test_workflow_ai_named_files.py"
ATTEMPT = "attempt-010"
PREDECESSOR = "attempt-009"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a"
    )
    parser.add_argument("--restart-proof", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace_root.resolve(strict=True)
    campaign = BASE / "campaign-execution/validator-campaign-082"
    local = campaign / SCENARIO / ATTEMPT
    source_path = f"workflows/validator-082-{SCENARIO}-{ATTEMPT}.workflow.wflow"
    if (
        local.exists()
        or (workspace / "campaign" / SCENARIO / ATTEMPT).exists()
        or (workspace / source_path).exists()
    ):
        raise ValueError(
            "Successor exists; reconcile it instead of repeating enrollment"
        )
    restart = json.loads(args.restart_proof.read_text(encoding="utf-8"))
    pin = restart["code_provenance"]["module_origins"][
        "workspace_service.workflow_source_execution"
    ]
    if not restart["source_unchanged"] or pin["sha256"] != sha(RUNTIME):
        raise ValueError("API restart is not proven for this repaired runtime")
    enroller = load("binding_enroller", "enroll_engineering_dataset_case.py")
    preparer = load("binding_preparer", "prepare-robot-dataset-campaign.py")
    bindings = load("binding_inputs", "engineering_dataset_input_bindings.py")

    def api(method, route, body=None):
        return enroller.api_request(args.api, method, route, body)

    if api("GET", "/api/agent/models").get("current_value") != MODEL:
        raise ValueError("The configured campaign inference model changed")
    previous = workspace / "campaign" / SCENARIO / PREDECESSOR
    before = {
        p.relative_to(previous).as_posix(): sha(p)
        for p in previous.rglob("*")
        if p.is_file()
    }
    if not before:
        raise ValueError("Predecessor files are unavailable")
    query = urllib.parse.urlencode(
        {
            "session_id": args.session,
            "path": f"workflows/validator-082-{SCENARIO}-{PREDECESSOR}.workflow.wflow",
            "latest_only": "true",
        }
    )
    prior = api("GET", "/api/workspace/workflow-sources/runs?" + query)["runs"][0]
    if (
        prior["run_id"] != "f0059a04d5964fa8866ccf4c4faa0f12"
        or prior["status"] != "awaiting_approval"
        or prior["approval"]["state"] != "pending"
        or prior["approval"]["actor"] is not None
    ):
        raise ValueError("Predecessor decision changed; reconcile before proceeding")
    predecessor = {
        "attempt_id": PREDECESSOR,
        "run_id": prior["run_id"],
        "source_digest": prior["source_digest"],
        "checkpoint_id": prior["approval"]["checkpoint_id"],
        "subject_digest": prior["approval"]["subject_digest"],
        "state": prior["approval"]["state"],
        "actor": prior["approval"]["actor"],
        "files": before,
    }
    save_once(local / "predecessor.json", predecessor)
    identity = {"runtime_sha256": sha(RUNTIME), "test_sha256": sha(TEST)}
    proof = local / "isolated-file-binding-tests.xml"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(TEST.relative_to(ROOT)),
            "-q",
            "-p",
            "no:cacheprovider",
            f"--basetemp={local / 'isolated-tests'}",
            f"--junitxml={proof}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    (local / "isolated-file-binding-tests.log").write_text(
        completed.stdout + completed.stderr, encoding="utf-8"
    )
    if completed.returncode or identity != {
        "runtime_sha256": sha(RUNTIME),
        "test_sha256": sha(TEST),
    }:
        raise ValueError("Isolated repair qualification failed or code changed")
    suites = ET.parse(proof).getroot().findall("testsuite")
    if sum(int(s.get("tests", "0")) for s in suites) < 7 or any(
        int(s.get(k, "0")) for s in suites for k in ("failures", "errors", "skipped")
    ):
        raise ValueError("Repair tests are incomplete")
    evidence = (
        ROOT
        / "artifacts/engineering-workflow-datasets/diagnostics/robot01-named-output-binding-r1.json"
    )
    save_once(
        evidence,
        {
            "schema_version": 1,
            "observed_at": datetime.now(UTC).isoformat(),
            "status": "qualified_for_bounded_correction",
            "reason": "Verified AI-created files now bind to their exact authored output ports and survive review continuation.",
            "predecessor": predecessor,
            "successor_attempt": ATTEMPT,
            "repair": identity,
            "qualification": {
                "method": "isolated canonical executor tests with simulated tool/model and actual files, repository, validator and durable continuation",
                "tests": 7,
                "path": str(proof),
                "sha256": sha(proof),
            },
            "restart_proof": {
                "path": str(args.restart_proof),
                "sha256": sha(args.restart_proof),
            },
            "requirements_changed": False,
            "engineering_approval_recorded": False,
            "dispatched": False,
        },
    )

    metadata = api(
        "GET", "/api/workspace/workflow-source-templates/robot-tracking-diagnosis"
    )["template"]
    request = {
        "session_id": args.session,
        "template_version": metadata["version"],
        "expected_source_digest": metadata["source_digest"],
        "workflow_path": source_path,
        "request_id": f"validator-082-{SCENARIO}-{ATTEMPT}",
    }
    save_once(local / "instance-request.json", request)
    instance = api(
        "POST",
        "/api/workspace/workflow-source-templates/robot-tracking-diagnosis/instances",
        request,
    )
    save_once(local / "template-instance.json", instance)
    original = local / "original.workflow.wflow"
    original.write_text(instance["source"], encoding="utf-8", newline="")
    tools = api(
        "GET",
        "/api/workspace/workflow-sources/tools?"
        + urllib.parse.urlencode({"session_id": args.session}),
    )["tools"]
    preparer.prepare(
        SimpleNamespace(
            workspace_root=str(workspace),
            draft_root=str(local / "prepared"),
            attempt=ATTEMPT,
            instance_source=str(original),
            server_map={
                "wright-campaign-rosbag": "413c3100-cd94-4436-b34a-5fa0373985a9",
                "wright-campaign-robot-operations": "c7279493-594a-4e17-b38e-673395a5f987",
            },
        ),
        ROOT
        / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis/01-aisle-floor-seam",
        tools,
    )
    report_path = local / "prepared" / SCENARIO / ATTEMPT / "staging-manifest.json"
    execution_path = local / "execution.json"
    enroller.enroll(
        SimpleNamespace(
            prepared=str(report_path),
            campaign_state=str(
                ROOT / "artifacts/engineering-workflow-datasets/status.json"
            ),
            database=str(BASE / "data/wright.db"),
            session=args.session,
            source_path=source_path,
            output=str(execution_path),
            api=args.api,
        )
    )
    case = json.loads(execution_path.read_text(encoding="utf-8"))
    if not bindings.validate_case(case)["complete"]:
        raise ValueError("Successor input bindings are incomplete")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if any((workspace / p).exists() for p in report["expected_tool_created_files"]):
        raise ValueError("Successor already has outputs; no reuse is permitted")
    after = {
        p.relative_to(previous).as_posix(): sha(p)
        for p in previous.rglob("*")
        if p.is_file()
    }
    current = api("GET", "/api/workspace/workflow-sources/runs?" + query)["runs"][0]
    if (
        before != after
        or current["approval"] != prior["approval"]
        or current["source_digest"] != prior["source_digest"]
    ):
        raise ValueError("Predecessor evidence or review changed")
    case["retry_episode"] = {
        "episode_id": "robot01-named-output-binding",
        "failure_key": "runtime:ai-task-named-files",
        "boundary": f"{SCENARIO}:validator-file-subjects",
        "max_corrections": 2,
        "baseline_attempt_ids": [PREDECESSOR],
        "correction": {
            "id": "named-file-ports-r1",
            "evidence": [
                {
                    "id": "robot01-named-output-binding-r1",
                    "path": evidence.relative_to(
                        ROOT / "artifacts/engineering-workflow-datasets"
                    ).as_posix(),
                    "sha256": sha(evidence),
                }
            ],
        },
    }
    manifest = campaign / "pilot-robot01-attempt010-binding-correction.json"
    save_once(manifest, {"schema_version": 1, "cases": [case]})
    summary = {
        "status": "enrolled_not_dispatched",
        "manifest": str(manifest),
        "manifest_sha256": sha(manifest),
        "source_path": source_path,
        "source_digest": case["source_digest"],
        "predecessor_unchanged": True,
    }
    save_once(local / "staging-verification.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
