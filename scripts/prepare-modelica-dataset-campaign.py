"""Bind uploaded heater CSVs to ordinary canonical native MCP nodes; never dispatch."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
from pathlib import Path

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/water-heater-sizing.workflow.wflow"
spec = importlib.util.spec_from_file_location("modelica_binding_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
ORIGINAL = ["define_requirement", "run_allowed_settings", "verify_selection"]
TOOLS = ["modelica_simulation_manifest_get", "modelica_simulation_request_template_get", "modelica_simulation_submit", "modelica_simulation_request_get", "modelica_export_recorded_result", "modelica_summarize_recorded_study"]
NATIVE_FILES = ["request.json", "resolved-parameters.json", "WrightWaterHeater.mo", "scenario.json", "parameter-schema.json", "run.mos", "omc.log", "result.csv", "evidence.json", "run.json"]
STUDY_FILES = ["temperature-time.csv", "power-comparison.csv", "energy-summary.csv", "temperature-curve.svg", "heater-selection.md", "kit-run-parameters.json"]


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def prepare(args, directory):
    data = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    identity = data["scenario_id"]
    suffix = (identity + "_" + args.attempt).replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Prepared attempt exists; inspect it instead of overwriting")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    stages = {prefix: next(s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")) for prefix in ORIGINAL}
    quantities = {row["quantity"]: float(row["value"]) for row in csv_rows(directory / "parameters.csv")}
    if quantities["water_heat_capacity"] != 4180 or quantities["requested_output_interval"] != 1 or quantities["target_temperature"] != 90:
        raise ValueError("Dataset requires a separately qualified fixed-property/scenario extension")
    horizon = int(quantities["requested_stop_time"])
    catalog = json.loads(Path(args.manifest_catalog).read_text(encoding="utf-8"))
    baseline = catalog[f"wright-{horizon}-baseline"]
    refined = catalog[f"wright-{horizon}-refined"]
    tools = json.loads(Path(args.tool_catalog).read_text(encoding="utf-8"))["tools"]
    selected_tools = {}
    for name in TOOLS:
        matches = [tool for tool in tools if tool["server_id"] == args.server_id and tool["tool_name"] == name]
        if len(matches) != 1 or not matches[0].get("schema_digest"):
            raise ValueError("Missing exact selected gateway tool " + name)
        selected_tools[name] = matches[0]
    if any(m["model"]["id"] != "wright-water-heater-v1" for m in [baseline, refined]):
        raise ValueError("Wrong selected kit manifest")
    candidates = [float(row["electrical_power_W"]) for row in csv_rows(directory / "power-candidates.csv")]
    loss_cases = [(row["loss_case"], float(row["linear_loss_coefficient_W_per_K"])) for row in csv_rows(directory / "loss-cases.csv")] if (directory / "loss-cases.csv").exists() else [("nominal", quantities["linear_loss_coefficient"])]
    nominal_loss = quantities.get("linear_loss_coefficient", quantities.get("linear_loss_coefficient_nominal"))
    if nominal_loss is None or next(value for label, value in loss_cases if label == "nominal") != nominal_loss:
        raise ValueError("Missing or inconsistent supplied nominal loss coefficient")
    values = {"initial_water_temperature": quantities["initial_temperature"], "ambient_temperature": quantities["ambient_temperature"], "water_mass": quantities["water_mass"], "boiler_heat_capacity": quantities["vessel_heat_capacity"], "heat_loss_conductance": nominal_loss, "heater_efficiency": quantities["electrical_to_thermal_efficiency"], "setpoint_temperature": quantities["target_temperature"], "hysteresis": 2, "electrical_power": candidates[0]}
    units = {parameter["id"]: parameter["unit"] for parameter in baseline["parameters"]}
    parameters = {key: {"value": value, "unit": units[key]} for key, value in values.items()}
    staged = []

    def stage(name, raw, **metadata):
        relative = inputs + "/" + name
        h.write_once(h.confined(workspace, relative), raw)
        staged.append({"path": relative, "sha256": h.digest(raw), "size_bytes": len(raw), **metadata})
        return relative

    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage(path.name, path.read_bytes(), original=path.relative_to(ROOT).as_posix())
    names = [data["files"]["user_profile"], data["files"]["prompt"], *data["files"]["context"]]
    mapping = {"selected_kit_id": "wright-water-heater-v1", "selected_kit_version": "0.1.0", "upstream_model": "Casys CoffeeMachine, original thermal components retained", "model_source_sha256": baseline["model"]["source"]["sha256"], "parameters_from_human_inputs": parameters, "fixed_control_assumption": "2 K thermostat hysteresis; setpoint equals supplied90degC target; 4180J/(kg.K) fixed water heat capacity", "candidate_electrical_powers_w": candidates, "loss_cases": loss_cases, "time_limit_s": quantities["heat_up_limit"], "baseline_manifest": baseline, "refined_manifest": refined, "approval": "New separately identified campaign kit; upstream original approved kit identity and bounds are unchanged."}
    stage("selected-kit-binding.json", (json.dumps(mapping, indent=2) + "\n").encode(), derived_from=["parameters.csv", "power-candidates.csv", "qualified selected provider manifest"])
    context = "\n\n".join("## Uploaded file: " + name + "\n\n" + (directory / name).read_text(encoding="utf-8") for name in names)
    context += "\n\n## Separately qualified selected kit mapping\n\n" + json.dumps(mapping, indent=2)
    brief = h.add_file_input(sections, suffix, "heater_context", stage("assembled-context-utf8.md", context.encode(), derived_from=names))
    image = h.add_file_input(sections, suffix, "heater_concept", inputs + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"
    review = stages["define_requirement"]
    review["fields"].update(step_type="review", performed_by="engineer", inputs=[], outputs=[], instructions="Review the original uploaded requirements and explicit new selected-kit binding, physical input units, candidate powers, loss variants, control assumptions and independent solver refinement. This local engineering review grants no physical or supplier action.")
    review["fields"]["settings"] = {"authoring_template": "external-action-approval", "action_kind": "local_review", "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": h.digest(b"wright.local_review.v1")}, "approval_destination": {"kind": "local_review", "id": "workspace"}, "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}}
    h.add_reference(sections, brief, review, "uploaded_requirements_and_selected_kit")

    def bind_tool(stage, tool, arguments, expected=()):
        selected = selected_tools[tool]
        stage["fields"].update(step_type="work", performed_by="configured_tool", tool=None, reusable_step=None, inputs=[], outputs=[h.port(stage["id"] + "_result")], prompt="", instructions="Execute only this exact input-bound native selected MCP operation and preserve its immutable response.")
        stage["fields"]["settings"] = {"authoring_template": "mcp-tool", "mcp_server": args.server_id, "mcp_tool": selected["name"], "mcp_schema_digest": selected["schema_digest"], "mcp_arguments": json.dumps(arguments), "output_format": "json", "save_output": True, "output_filename": output + "/records/" + stage["id"] + ".json", "file_policy": "overwrite", "timeout_seconds": 180, "expected_files": "\n".join(output + "/" + name for name in expected)}
        return stage["id"] + "." + stage["id"] + "_result"

    run = stages["run_allowed_settings"]
    bind_tool(run, "modelica_simulation_manifest_get", {"model_id": "wright-water-heater-v1", "model_version": "0.1.0", "scenario_id": f"wright-{horizon}-baseline"})
    chain = [review, run]
    observed = []
    for power in candidates:
        for label, loss in loss_cases:
            request_id = f"{identity}-{args.attempt}-p{power:g}-{label}-baseline"
            applied = {**parameters, "electrical_power": {"value": power, "unit": "W"}, "heat_loss_conductance": {"value": loss, "unit": "W/K"}}
            submission = {"request_id": request_id, "manifest_sha256": baseline["manifest_sha256"], "model_id": "wright-water-heater-v1", "model_version": "0.1.0", "scenario_id": f"wright-{horizon}-baseline", "parameters": applied, "timeout_ms": 120000}
            task = {"kind": "task", "id": f"native_p{power:g}_{label}_".replace(".", "_") + suffix, "fields": {"name": f"Simulate {power:g} W / {label} loss", "purpose": "Run exact uploaded electrical/thermal parameters with the real native model", "group": None}}
            sections.append(task)
            bind_tool(task, "modelica_simulation_submit", submission)
            export = {"kind": "task", "id": "export_" + task["id"], "fields": {"name": f"Preserve {power:g} W / {label} native evidence", "purpose": "Export only sealed successful native CSV and exact provenance", "group": None}}
            sections.append(export)
            bind_tool(export, "modelica_export_recorded_result", {"dataset_id": identity, "attempt_id": args.attempt, "request_id": request_id, "expected_manifest_sha256": baseline["manifest_sha256"]}, [request_id + "/" + name for name in NATIVE_FILES])
            # Bind the complete native evidence file, rather than repeating the
            # full run/kit manifest in the final model prompt. Every native CSV,
            # model, log and run record is still exported and required above.
            evidence_port = export["id"] + "_computed_evidence"
            export["fields"]["outputs"].append(h.port(evidence_port, "workspace_file"))
            export["fields"]["settings"]["expected_file_ports"] = {
                evidence_port: output + "/" + request_id + "/evidence.json"
            }
            chain.extend([task, export])
            observed.append({"request_id": request_id, "expected_manifest_sha256": baseline["manifest_sha256"], "output": export["id"] + "." + evidence_port})
    verify = stages["verify_selection"]
    selected_ids = [f"{identity}-{args.attempt}-selected-{label}-refined" for label, _ in loss_cases]
    prompt = f"""Use the actual completed baseline request results and original uploaded context to select the lowest electrical power meeting the {quantities['heat_up_limit']:g}s time limit for90degC across every supplied loss case. Never substitute model reasoning for a missing simulation. Every baseline candidate/loss run is required. If none meets the time limit, perform the tighter rerun on the fastest candidate for diagnosis and report no demonstrated setting.

Get modelica_simulation_manifest_get for wright-water-heater-v1 version0.1.0 scenario wright-{horizon}-refined, requiring exact manifest digest {refined['manifest_sha256']}. For each supplied loss case, submit the selected power with every physical parameter unchanged from that case's baseline and only the separate refined scenario changed. Required refined request IDs in loss-case order are {json.dumps(selected_ids)}; loss cases are {json.dumps(loss_cases)}. Use request_template_get if helpful; full parameters and units are in the binding context. The fixed refined scenario uses real DASSL maxStepSize0.25s and tolerance1e-8; output grid remains1s. Submit timeout_ms120000; do not retry with changed values under a reused request ID. Use request_get for an uncertain response.

After each actual successful refined submission, call modelica_export_recorded_result with dataset_id={identity}, attempt_id={args.attempt}, exact refined request_id and expected_manifest_sha256={refined['manifest_sha256']}. Then call modelica_summarize_recorded_study ONCE after every required run with dataset_id,attempt_id, all baseline requests {json.dumps([{k: v for k, v in item.items() if k != 'output'} for item in observed])} plus every refined request/digest, time_limit_s={quantities['heat_up_limit']}, candidate_powers_w={json.dumps(candidates)}, loss_conductances_w_per_k={json.dumps([loss for _, loss in loss_cases])}. This computes independent target crossing, trapezoidal energy, capacity/loss balance and numerical stability from actual sealed CSVs and creates the comparison/energy/plot/report files. It must reject missing candidate/loss evidence.

Write a clear engineering assessment of the actual outputs and limitations. For the mobile brewer, additionally account for the supplied inverter efficiency and battery Wh/usable-energy/per-batch constraints using actual electrical energy; distinguish battery input from delivered thermal energy. Do not claim supplier release or engineering content validation. Keep the original engineering requirement review, every baseline run, independent tighter rerun and final study artifacts. Never use the unrelated original kit or an ODE surrogate."""
    verify["fields"].update(step_type="work", performed_by="ai_assisted", tool=None, reusable_step=None, inputs=[], outputs=[h.port(verify["id"] + "_result")], prompt=prompt, instructions=prompt)
    verify["fields"]["settings"] = {"authoring_template": "mcp-task", "mcp_server": args.server_id, "max_tool_calls": 24, "timeout_seconds": 600, "timestep_sensitivity_required": True, "arbitrary_source": False, "task_guidance": "Only the enrolled selected Modelica tools are available. Preserve actual sealed identities and complete all original engineering stages. Exported native evidence is immutable; no physical actions.", "output_format": "markdown", "save_output": True, "output_filename": output + "/workflow-heater-selection.md", "file_policy": "overwrite", "expected_files": "\n".join(output + "/" + name for name in [*STUDY_FILES, *[request_id + "/" + name for request_id in selected_ids for name in NATIVE_FILES]])}
    # The canonical compiler caps each node at16 declared native files. Retain
    # every file by expanding the multi-loss phase into ordinary export nodes.
    final_nodes = []
    if len(loss_cases) > 1:
        refined_prompt = prompt.split("After each actual successful refined submission", 1)[0] + "The next explicit canonical nodes export every refined request and compute the independent time/energy/numerical-stability study. Complete only the selected tighter simulations in this task, then report the actual selected power and exact completed request identities. Retain every loss case."
        verify["fields"].update(prompt=refined_prompt, instructions=refined_prompt)
        verify["fields"]["settings"]["expected_files"] = ""
        for request_id, (label, _) in zip(selected_ids, loss_cases):
            task = {"kind": "task", "id": "export_selected_" + label + "_" + suffix, "fields": {"name": "Preserve selected refined " + label + " evidence", "purpose": "Preserve every actual refined simulation artifact", "group": None}}
            sections.append(task)
            bind_tool(task, "modelica_export_recorded_result", {"dataset_id": identity, "attempt_id": args.attempt, "request_id": request_id, "expected_manifest_sha256": refined["manifest_sha256"]}, [request_id + "/" + name for name in NATIVE_FILES])
            final_nodes.append(task)
        summary = {"kind": "task", "id": "compare_sealed_study_" + suffix, "fields": {"name": "Compare time, energy and independent numerical stability", "purpose": "Compute the complete engineering comparison from every sealed candidate and refined result", "group": None}}
        sections.append(summary)
        bind_tool(summary, "modelica_summarize_recorded_study", {"dataset_id": identity, "attempt_id": args.attempt, "requests": [{k: v for k, v in item.items() if k != "output"} for item in observed] + [{"request_id": request_id, "expected_manifest_sha256": refined["manifest_sha256"]} for request_id in selected_ids], "time_limit_s": quantities["heat_up_limit"], "candidate_powers_w": candidates, "loss_conductances_w_per_k": [loss for _, loss in loss_cases]}, STUDY_FILES)
        final_nodes.append(summary)
    h.add_reference(sections, brief, verify, "original_requirements_and_binding")
    h.add_reference(sections, image, verify, "original_concept", "reference_images")
    for index, item in enumerate(observed):
        h.add_reference(sections, item["output"], verify, "native_baseline_" + str(index), "workspace_file")
    chain.append(verify)
    chain.extend(final_nodes)
    for first, last in zip(chain, chain[1:]):
        sections.append({"kind": "connection", "id": "complete_sequence_" + last["id"], "fields": {"type": "order", "from": first["id"], "to": last["id"], "label": "complete native heater engineering chain", "when": None}})
    rendered = h.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowlist = [selected_tools[name] for name in TOOLS]
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    result = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt, "template_id": data["template_id"], "status": "prepared_not_dispatched", "source": str(target), "source_sha256": h.digest(rendered.encode()), "template_source_sha256": h.digest(TEMPLATE.read_bytes()), "workspace_root": str(workspace), "output_root": output, "input_manifest": staged, "required_step_ids": [step.id for step in plan.steps], "preserved_original_stages": [stages[p]["id"] for p in ORIGINAL], "expected_tool_created_files": [path for step in plan.steps for path in step.expected_files], "tool_allowlist": allowlist, "server_id": args.server_id, "requires_template_instance_api": not bool(args.instance_source), "selected_kit_identity": "wright-water-heater-v1@0.1.0", "baseline_request_ids": [item["request_id"] for item in observed], "refined_request_ids": selected_ids, "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []}}
    h.publish_input_binding_evidence(result, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"scenario_id": identity, "source": str(target), "stages": len(plan.steps), "executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--draft-root", required=True)
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--manifest-catalog", default=".local-run/feature-081-live/modelica-prerequisite/manifest-catalog.json")
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--tool-catalog", required=True)
    args = parser.parse_args()
    rows = [directory for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/water-heater-sizing").iterdir()) if not args.scenario or json.loads((directory / "scenario.json").read_text(encoding="utf-8"))["scenario_id"] == args.scenario]
    if not rows or (args.instance_source and not args.scenario):
        raise ValueError("Select exactly one scenario for an actual instance source")
    print(json.dumps([prepare(args, directory) for directory in rows], indent=2))
