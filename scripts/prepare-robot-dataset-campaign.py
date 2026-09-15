"""Bind the canonical robot template to real offline bag tools; never execute it."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import urllib.parse
import urllib.request
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape
from workspace_service.workflow_integration_policy import LOCAL_REVIEW_BINDING, LOCAL_REVIEW_DESTINATION

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow"
spec = importlib.util.spec_from_file_location("robot_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


INSPECTION_STAGE_GUIDANCE = (
    "Completion scope: this task performs bounded bag/schema/sample inspection only. "
    "The connected customer prompt, alignment contract and operation source describe the full workflow; their later deliverables are not this task's completion criteria. "
    "After bag_info, all five actual topic schemas and one bounded sample call per topic succeed, compare actual counts with the same-run conversion manifest "
    "and return the task's standard completion envelope with status='completed', JSON inspection evidence as response, and the successful tool-call numbers as evidence. "
    "Complete only when the required bag identity, schemas, counts, samples and manifest comparison are actually observed; missing or inconsistent inspection evidence "
    "or tool errors still block this task. Unequal topic counts can be legitimate retained missing data when they match the conversion manifest; do not fill gaps or require equal counts. "
    "Wright saves this response as bag-inspection.json. Do not generate or verify timeline.csv, trajectory-overlay.svg, tracking-metrics.json or diagnosis.md here. "
    "The absence of calculate_tracking_metrics or file-writing tools from this bag-only server is expected and is not an inspection blocker. "
    "Do not compute full-run metrics from the at-most-two samples, invent artifact values, request more samples, or claim the later analysis has already run. "
)


def prepare(args, directory, available):
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    server_map = getattr(args, "server_map", None) or {}
    if isinstance(server_map, str):
        server_map = json.loads(Path(server_map).read_text(encoding="utf-8"))["server_map"]
    config["bag_server"] = server_map.get(config["bag_server"], config["bag_server"])
    config["operation_server"] = server_map.get(config["operation_server"], config["operation_server"])
    config["allowed_tools"] = {server_map.get(server, server): names for server, names in config["allowed_tools"].items()}
    manifest = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    identity = manifest["scenario_id"]
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace, draft = Path(args.workspace_root).resolve(), Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Attempt already staged; preserve it and choose a fresh attempt")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    originals = [s["id"] for s in sections if s["kind"] == "task"]
    edges = [s.copy() for s in sections if s["kind"] == "connection"]
    stages = {key: next(s for s in sections if s["id"].startswith(key + "_") and s["kind"] == "task")
              for key in ("inspect_bag", "align_and_measure", "evidence_diagnosis")}
    staged = []
    def stage_file(path, data, provenance):
        helpers.write_once(helpers.confined(workspace, path), data)
        staged.append({"path": path, "sha256": helpers.digest(data), "size_bytes": len(data), **provenance})
    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage_file(inputs + "/" + path.name, path.read_bytes(), {"original": path.relative_to(ROOT).as_posix()})
    human = "\n\n".join((directory / name).read_text(encoding="utf-8") for name in ["user-profile.md", "prompt.txt", *manifest["files"]["context"]])
    stage_file(inputs + "/assembled-context.md", human.encode(), {"derived_from": manifest["files"]})
    stage_file(inputs + "/alignment.json", (json.dumps(config["scenarios"][identity], indent=2) + "\n").encode(), {"derived_from": ["context.md", "bag-conversion.md"], "purpose": "Explicit user-supplied survey and clock contract"})
    for name in ("robot_tracking_operations.py", "robot_tracking_mcp.py"):
        stage_file(inputs + "/" + name, (ROOT / "scripts" / name).read_bytes(), {"operation_source": "scripts/" + name})
    context = helpers.add_file_input(sections, suffix, "human_context", inputs + "/assembled-context.md")
    alignment = helpers.add_file_input(sections, suffix, "alignment_contract", inputs + "/alignment.json")
    operation = helpers.add_file_input(sections, suffix, "authored_operation_source", inputs + "/robot_tracking_operations.py")
    image = helpers.add_file_input(sections, suffix, "route_sketch", inputs + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"
    def new_task(key, name):
        value = {"kind": "task", "id": key + "_" + suffix, "fields": {"name": name, "purpose": name, "step_type": "work", "group": None, "performed_by": "ai_assisted", "inputs": [], "outputs": [], "settings": {}, "tool": None, "reusable_step": None}}
        sections.append(value)
        return value
    def bind(task, prompt, server=None, expected=(), filename=None):
        fields = task["fields"]
        old_settings = fields.get("settings", {})
        fields.update(performed_by="ai_assisted", step_type="work", inputs=[], outputs=[helpers.port(task["id"] + "_result")], prompt=prompt)
        fields["settings"] = {**old_settings, "output_format": "markdown" if filename and filename.endswith(".md") else "json", "save_output": True,
                              "output_filename": output + "/" + (filename or task["id"].split("_" + suffix)[0] + ".json"), "file_policy": "overwrite"}
        if server:
            fields["settings"].update(authoring_template="mcp-task", mcp_server=server, max_tool_calls=12, timeout_seconds=300,
                                      expected_files="\n".join(output + "/" + name for name in expected),
                                      task_guidance="Use exact selected offline tool and supplied paths; no physical robot/network actions. Never fabricate output files, source, measurements or tool results.")
        for producer, key in ((context, "human_context"), (alignment, "alignment_contract"), (operation, "operation_source")):
            helpers.add_reference(sections, producer, task, key)
        return task["id"] + "." + task["id"] + "_result"
    normalize = new_task("normalize_csv", "Serialize original CSV uploads into a real ROS2 bag")
    normalized = bind(normalize, f"Call normalize_csv_to_ros2 exactly once with operation_source_document={inputs + '/robot_tracking_operations.py'!r}, input_directory={inputs!r}, output_directory={output + '/converted'!r}. Read the supplied source and mapping. Preserve original CSVs and +150ms header offsets; no frame transform during conversion. Save the actual returned conversion manifest. Never reuse a prior attempt's bag.", config["operation_server"], ["converted/recording/recording.db3", "converted/recording/metadata.yaml", "converted/conversion-manifest.json"])
    inspection_scope = (INSPECTION_STAGE_GUIDANCE
        + f"After this evidence is returned, the connected canonical step {stages['align_and_measure']['id']} on server {config['operation_server']} "
        "calls calculate_tracking_metrics on the complete same-run bag to produce the timeline, overlay and metrics; the later draft_diagnosis step writes diagnosis.md from those actual outputs. "
        "Leave those operations to their declared later stages and retain the subsequent engineer review. ")
    inspection = bind(stages["inspect_bag"], inspection_scope + f"First call bag_info on bag_path='/workspace/{output}/converted/recording', then get_topic_schema for all five topics. Then call get_messages_in_range exactly once per topic with start_time=1767225600,end_time=1767225630.01,max_messages=2. This is a bounded native sample inspection, not full inline extraction. Do not increase max_messages or repeat ranges: the next fixed metrics operation independently reads every actual message from the on-disk bag. Topic names: /wright_test/planned_pose,/wright_test/external_pose,/wright_test/odom,/wright_test/cmd_vel,/wright_test/operator_event. Keep the JSON output below 12000 characters: record actual topic/type/count summaries plus the at-most-two retrieved samples per topic, projecting timestamp, header stamp/frame, position/orientation, velocity and event text as applicable; omit bulky zero covariance arrays while explicitly naming omitted fields. Retain full actual records in the generated bag, referenced by its same-run path and manifest hash. Check actual counts against conversion manifest; report error strings as failures, even when isError is false. Do not infer schemas or invent messages. Inspect before metrics.", config["bag_server"], filename="bag-inspection.json")
    helpers.add_reference(sections, normalized, stages["inspect_bag"], "same_run_conversion")
    # Eleven real inspection calls plus the final report exceeded the original
    # five-minute budget in the recorded run. Keep the observations bounded and
    # the complete inspection intact within the runtime's ten-minute task cap.
    stages["inspect_bag"]["fields"]["settings"]["timeout_seconds"] = 600
    stages["inspect_bag"]["fields"]["settings"]["task_guidance"] += " " + inspection_scope
    measured = bind(stages["align_and_measure"], f"After actual native bag inspection/extraction succeeded, call calculate_tracking_metrics exactly once with operation_source_document={inputs + '/robot_tracking_operations.py'!r}, bag_directory={output + '/converted/recording'!r}, alignment_document={inputs + '/alignment.json'!r}, output_directory={output + '/analysis'!r}. The supplied reusable source applies the explicit transform once and retains the original 1% independent metrics and one-sample event gates. It must preserve the visual occlusion as missing samples, report unaligned/aligned overlays and save actual computed outputs. Read the returned metrics; don't invent or weaken checks.", config["operation_server"], ["analysis/timeline.csv", "analysis/trajectory-overlay.svg", "analysis/tracking-metrics.json"], filename="analysis-report.json")
    helpers.add_reference(sections, inspection, stages["align_and_measure"], "native_bag_evidence")
    diagnosis_task = new_task("draft_diagnosis", "Write the evidence-linked diagnosis for engineer review")
    diagnosis = bind(diagnosis_task, "Write the requested engineering diagnosis from the actual supplied original prompt, route sketch, bag evidence and computed metrics. Cite time ranges, retained counts, frame/time correction, event correlation, missing intervals and uncertainties. Compare raw and aligned interpretations. State measured observations separately from hypotheses; command/odometry disagreement alone is not evidence of wheel slip. Include the requested inexpensive next observation. These are fictional input logs and no real robot commands are authorized.", filename="diagnosis.md")
    helpers.add_reference(sections, measured, diagnosis_task, "actual_metrics")
    helpers.add_reference(sections, inspection, diagnosis_task, "bag_evidence")
    helpers.add_reference(sections, image, diagnosis_task, "route_image", "reference_images")
    # The original combined AI/engineer semantic stage remains the authority gate.
    review = stages["evidence_diagnosis"]
    review["fields"].update(step_type="review", performed_by="engineer", inputs=[], outputs=[], instructions="Review the actual diagnosis, event and metrics evidence. Keep observations separate from candidate causes; do not infer wheel slip from command/odometry disagreement.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review", "causal_overclaiming": False,
                  "approval_binding": LOCAL_REVIEW_BINDING, "approval_destination": LOCAL_REVIEW_DESTINATION,
                  "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}})
    helpers.add_reference(sections, diagnosis, review, "diagnosis_for_review")
    collection = new_task("collect_robot_evidence", "Collect the approved engineering diagnosis and artifact links")
    bind(collection, "Create a compact artifact index referencing the actual same-run bag, conversion manifest, original/analysis source, inspection evidence, timeline, overlay, metrics and approved diagnosis. Do not claim correctness-validation credit; this campaign checks file presence only.", filename="evidence-index.md")
    helpers.add_reference(sections, diagnosis, collection, "approved_diagnosis")
    for start, end in ((normalize["id"], stages["inspect_bag"]["id"]), (diagnosis_task["id"], review["id"]), (review["id"], collection["id"])):
        sections.append({"kind": "connection", "id": "order_" + start + "_" + end, "fields": {"type": "order", "from": start, "to": end, "label": "same canonical execution", "when": None}})
    result = helpers.render(sections)
    validate_workspace_authoring_shape(result)
    plan = compile_prompt_workflow(result)
    if any(edge not in sections for edge in edges):
        raise ValueError("Original robot control edges changed")
    selected = []
    for server, names in config["allowed_tools"].items():
        for name in names:
            matches = [tool for tool in available if tool["server_id"] == server and tool["tool_name"] == name]
            if len(matches) != 1:
                raise ValueError("Required selected workspace tool unavailable: " + server + "/" + name)
            selected.append(matches[0])
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(result, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "template_id": manifest["template_id"], "attempt_id": args.attempt,
              "status": "prepared_not_dispatched", "source": str(target), "source_sha256": helpers.digest(result.encode()),
              "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()),
              "requires_template_instance_api": not bool(args.instance_source), "workspace_root": str(workspace), "output_root": output,
              "input_manifest": staged, "tool_allowlist": selected, "expected_outputs": manifest["expected_outputs"],
              "compiled_stages": [step.id for step in plan.steps], "preserved_original_stages": originals,
              "preserved_original_edges": [s["id"] for s in edges], "expected_tool_created_files": [p for step in plan.steps for p in step.expected_files],
              "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []}}
    helpers.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/robot-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/robot-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--server-map", help="Normal API registration report containing alias-to-UUID server_map")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    with urllib.request.urlopen(args.api + "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session), timeout=30) as response:
        available = json.load(response)["tools"]
    results = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis").iterdir()):
        identity = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))["scenario_id"]
        if not args.scenario or args.scenario == identity:
            results.append(prepare(args, directory, available))
    if not results:
        raise ValueError("No robot scenario matched")
    print(json.dumps({"prepared": results, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
