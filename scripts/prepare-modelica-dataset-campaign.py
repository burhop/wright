"""Bind uploaded heater CSVs to ordinary canonical native MCP nodes; never dispatch."""
from __future__ import annotations
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import subprocess

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/water-heater-sizing.workflow.wflow"
VALIDATION_COVERAGE = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"
spec = importlib.util.spec_from_file_location("modelica_binding_helpers", ROOT / "scripts/engineering_campaign_binding_helpers.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
renewal_spec = importlib.util.spec_from_file_location(
    "campaign_example_renewal", ROOT / "scripts/campaign_example_renewal.py"
)
renewal = importlib.util.module_from_spec(renewal_spec)
renewal_spec.loader.exec_module(renewal)
ORIGINAL = ["define_requirement", "run_allowed_settings", "verify_selection"]
TOOLS = ["modelica_simulation_manifest_get", "modelica_simulation_request_template_get", "modelica_simulation_submit", "modelica_simulation_request_get", "modelica_export_recorded_result", "modelica_summarize_recorded_study"]
NATIVE_FILES = ["request.json", "resolved-parameters.json", "WrightWaterHeater.mo", "scenario.json", "parameter-schema.json", "run.mos", "omc.log", "result.csv", "evidence.json", "run.json"]
STUDY_FILES = ["temperature-time.csv", "power-comparison.csv", "energy-summary.csv", "temperature-curve.svg", "heater-selection.md", "kit-run-parameters.json"]
STUDY_OUTPUTS = {
    "timeline": "temperature-time.csv",
    "comparison": "power-comparison.csv",
    "energy": "energy-summary.csv",
    "curve": "temperature-curve.svg",
    "report": "heater-selection.md",
    "parameters": "kit-run-parameters.json",
}


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def study_scope(identity):
    """Keep each approved study's requirements out of the other variants."""
    scopes = {
        "water-heater-sizing-01": (
            "This is the single-cup countertop brewer study (water-heater-sizing-01). "
            "Assess only its supplied heat-up, energy-balance and numerical-stability requirements. "
            "The mobile field-brewer power-budget assignment is a different scenario and does not apply here."
        ),
        "water-heater-sizing-02": (
            "This is the mobile field-brewer study (water-heater-sizing-02). "
            "Also account for the inverter efficiency and battery nominal Wh, usable-energy allowance, "
            "continuous-output limit and per-batch constraints supplied in energy-budget.csv and context.md. "
            "Calculate battery-side energy to the first target-temperature crossing from the actual "
            "electrical-energy trajectory divided by the supplied inverter efficiency; "
            "do not substitute full-run energy including the later thermostat holding period for heat-up energy. "
            "Distinguish battery-side input, AC heater input and delivered thermal energy, report usable "
            "batch count and exclusions, and preserve any real failed energy limit."
        ),
        "water-heater-sizing-03": (
            "This is the pilot batch-dispenser study (water-heater-sizing-03). "
            "Retain the complete low/nominal/high loss grid and assess its supplied thermal requirements. "
            "The mobile field-brewer power-budget assignment is a different scenario and does not apply here."
        ),
    }
    try:
        return scopes[identity]
    except KeyError as exc:
        raise ValueError("Unknown approved water-heater study " + identity) from exc


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
    project = workspace / output / "agentcad-project"
    if getattr(args, "initialize_agentcad", False):
        if project.exists():
            raise ValueError("Native init requires a new disposable AgentCAD project")
        project.mkdir(parents=True)
        command = [
            "uv", "run", "--isolated", "--python", "3.12", "--with",
            "agentcad[mcp]==0.6.0", "agentcad", "init", "--name",
            "water-heater-package", "--build-dir", "build",
        ]
        initialized = subprocess.run(
            command, cwd=project, capture_output=True, text=True, timeout=300
        )
        if initialized.returncode:
            raise RuntimeError("Actual AgentCAD project initialization failed")
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
    renewal_contract = renewal.case_contract(data)
    renewal_path = stage(
        "approved-engineering-brief.json",
        (json.dumps(renewal_contract, indent=2) + "\n").encode(),
        role="approved_engineering_brief",
    )
    thermal_source = (ROOT / "scripts/engineering/water_heater_package_skfem.py").read_bytes()
    thermal_source_path = stage(
        "water-heater-package-skfem-" + h.digest(thermal_source)[:12] + ".py",
        thermal_source,
        role="reviewable_thermal_screen_source",
    )
    names = [data["files"]["user_profile"], data["files"]["prompt"], *data["files"]["context"]]
    mapping = {"selected_kit_id": "wright-water-heater-v1", "selected_kit_version": "0.1.0", "upstream_model": "Casys CoffeeMachine, original thermal components retained", "model_source_sha256": baseline["model"]["source"]["sha256"], "parameters_from_human_inputs": parameters, "fixed_control_assumption": "2 K thermostat hysteresis; setpoint equals supplied90degC target; 4180J/(kg.K) fixed water heat capacity", "candidate_electrical_powers_w": candidates, "loss_cases": loss_cases, "time_limit_s": quantities["heat_up_limit"], "baseline_manifest": baseline, "refined_manifest": refined, "approval": "New separately identified campaign kit; upstream original approved kit identity and bounds are unchanged."}
    stage("selected-kit-binding.json", (json.dumps(mapping, indent=2) + "\n").encode(), derived_from=["parameters.csv", "power-candidates.csv", "qualified selected provider manifest"])
    context = "\n\n".join("## Uploaded file: " + name + "\n\n" + (directory / name).read_text(encoding="utf-8") for name in names)
    context += "\n\n## Separately qualified selected kit mapping\n\n" + json.dumps(mapping, indent=2)
    brief = h.add_file_input(sections, suffix, "heater_context", stage("assembled-context-utf8.md", context.encode(), derived_from=names))
    engineering_brief = h.add_file_input(
        sections, suffix, "approved_engineering_brief", renewal_path
    )
    image = h.add_file_input(sections, suffix, "heater_concept", inputs + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"
    review = stages["define_requirement"]
    review["fields"].update(step_type="review", performed_by="engineer", inputs=[], outputs=[], instructions="Review the original uploaded requirements and explicit new selected-kit binding, physical input units, candidate powers, loss variants, control assumptions and independent solver refinement. This local engineering review grants no physical or supplier action.")
    review["fields"]["settings"] = {"authoring_template": "external-action-approval", "action_kind": "local_review", "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": h.digest(b"wright.local_review.v1")}, "approval_destination": {"kind": "local_review", "id": "workspace"}, "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}}
    h.add_reference(sections, brief, review, "uploaded_requirements_and_selected_kit")
    h.add_reference(sections, engineering_brief, review, "approved_engineering_brief")

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
    prompt = f"""{study_scope(identity)}

Use the actual completed baseline request results and original uploaded context to select the lowest electrical power meeting the {quantities['heat_up_limit']:g}s time limit for90degC across every supplied loss case. Never substitute model reasoning for a missing simulation. Every baseline candidate/loss run is required. If none meets the time limit, perform the tighter rerun on the fastest candidate for diagnosis and report no demonstrated setting.

Get modelica_simulation_manifest_get for wright-water-heater-v1 version0.1.0 scenario wright-{horizon}-refined, requiring exact manifest digest {refined['manifest_sha256']}. For each supplied loss case, submit the selected power with every physical parameter unchanged from that case's baseline and only the separate refined scenario changed. Required refined request IDs in loss-case order are {json.dumps(selected_ids)}; loss cases are {json.dumps(loss_cases)}. Use request_template_get if helpful; full parameters and units are in the binding context. The fixed refined scenario uses real DASSL maxStepSize0.25s and tolerance1e-8; output grid remains1s. Submit timeout_ms120000; do not retry with changed values under a reused request ID. Use request_get for an uncertain response.

After each actual successful refined submission, call modelica_export_recorded_result with dataset_id={identity}, attempt_id={args.attempt}, exact refined request_id and expected_manifest_sha256={refined['manifest_sha256']}. Then call modelica_summarize_recorded_study ONCE after every required run with dataset_id,attempt_id, all baseline requests {json.dumps([{k: v for k, v in item.items() if k != 'output'} for item in observed])} plus every refined request/digest, time_limit_s={quantities['heat_up_limit']}, candidate_powers_w={json.dumps(candidates)}, loss_conductances_w_per_k={json.dumps([loss for _, loss in loss_cases])}. This computes independent target crossing, trapezoidal energy, capacity/loss balance and numerical stability from actual sealed CSVs and creates the comparison/energy/plot/report files. It must reject missing candidate/loss evidence.

Write a clear engineering assessment of this scenario's actual outputs and limitations. Do not import requirements from another scenario or claim supplier release. The following process validator determines requirements-compliance credit from the exact current study files. Keep the original engineering requirement review, every baseline run, independent tighter rerun and final study artifacts. Never use the unrelated original kit or an ODE surrogate."""
    verify["fields"].update(step_type="work", performed_by="ai_assisted", tool=None, reusable_step=None, inputs=[], outputs=[h.port(verify["id"] + "_result")], prompt=prompt, instructions=prompt)
    verify["fields"]["settings"] = {"authoring_template": "mcp-task", "mcp_server": args.server_id, "max_tool_calls": 24, "timeout_seconds": 600, "timestep_sensitivity_required": True, "arbitrary_source": False, "task_guidance": "Only the enrolled selected Modelica tools are available. Preserve actual sealed identities and complete all original engineering stages. Exported native evidence is immutable; no physical actions.", "output_format": "markdown", "save_output": True, "output_filename": output + "/workflow-heater-selection.md", "file_policy": "overwrite", "expected_files": "\n".join(output + "/" + name for name in [*STUDY_FILES, *[request_id + "/" + name for request_id in selected_ids for name in NATIVE_FILES]])}
    # The canonical compiler caps each node at16 declared native files. Retain
    # every file by expanding the multi-loss phase into ordinary export nodes.
    final_nodes = []
    if len(loss_cases) > 1:
        refined_prompt = prompt.split("After each actual successful refined submission", 1)[0] + "The next explicit canonical nodes export every refined request and compute the independent time/energy/numerical-stability study. Complete only the selected tighter simulations in this task, then report the actual selected power and exact completed request identities. Retain every loss case. The following process validator determines requirements-compliance credit from the exact current study files."
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
    study_producer = final_nodes[-1] if final_nodes else verify
    study_producer["fields"]["outputs"].extend(
        h.port(role, "workspace_file") for role in STUDY_OUTPUTS
    )
    study_producer["fields"]["settings"]["expected_file_ports"] = {
        role: output + "/" + filename for role, filename in STUDY_OUTPUTS.items()
    }
    agentcad_server = getattr(args, "agentcad_server_id", "agentcad")
    file_server = getattr(args, "workspace_file_server_id", "wright-workspace-files")
    oasis_server = getattr(args, "oasis_server_id", "oasis")
    supplemental = {
        agentcad_server: ("context", "docs", "run"),
        file_server: ("write_text_document", "inspect_file"),
        oasis_server: ("run_simulation",),
    }
    supplemental_tools = []
    for server, names_for_server in supplemental.items():
        for name in names_for_server:
            match = next(
                (
                    tool
                    for tool in tools
                    if tool["server_id"] == server and tool["tool_name"] == name
                ),
                None,
            )
            if not match or not match.get("name") or not match.get("schema_digest"):
                raise ValueError("Missing exact selected package tool " + server + "/" + name)
            supplemental_tools.append(match)

    def package_task(prefix, title, prompt, server, expected=()):
        stage_task = {
            "kind": "task",
            "id": prefix + "_" + suffix,
            "fields": {
                "name": title,
                "purpose": title,
                "group": None,
                "step_type": "work",
                "performed_by": "ai_assisted",
                "tool": None,
                "reusable_step": None,
                "inputs": [],
                "outputs": [h.port(prefix + "_result")],
                "prompt": prompt,
                "settings": {
                    "authoring_template": "mcp-task",
                    "mcp_server": server,
                    "max_tool_calls": 16,
                    "timeout_seconds": 600,
                    "output_format": "json",
                    "save_output": True,
                    "output_filename": output + "/" + prefix + ".json",
                    "file_policy": "overwrite",
                    "expected_files": "\n".join(output + "/" + item for item in expected),
                    "task_guidance": "Use only the connected approved requirements and exact same-attempt outputs. Preserve failures and claim limits; do not substitute prose for a native artifact.",
                },
            },
        }
        sections.append(stage_task)
        return stage_task

    fixed = renewal_contract["approved_engineering_inputs"]["new_fixed_requirements"]
    preflight_cad = package_task(
        "preflight_package_cad",
        "Verify the isolated heater-package CAD project",
        f"Call context(cwd={str(project)!r},build_dir='build') and docs(section='quickstart',cwd={str(project)!r},build_dir='build'). Report the actual initialized project identity. An empty project is expected; do not claim that the heater package exists yet.",
        agentcad_server,
    )
    source_path = output + "/thermal-package-source.py"
    measurements_path = output + "/thermal-package-measurements.json"
    step_path = output + "/thermal-package.step"
    author_cad = package_task(
        "author_package_cad_source",
        "Author the approved vessel, carrier and insulation package",
        "Call write_text_document to create " + source_path + " as actual build123d Python. "
        "Use the approved fixed requirements exactly: " + json.dumps(fixed, sort_keys=True) + ". "
        "Choose only permitted carrier profile/thickness, insulation thickness within its range, shell geometry and stated non-interface styling. "
        "Create a single inspectable digital package containing the vessel wall/base, carrier, insulation and outer shell; preserve the heater contact limit, useful liquid depth/freeboard, mount/keepout interfaces and maximum envelope. "
        f"Use the connected AgentCAD context and quickstart instructions. The script executes inside the CAD project, not the workspace root. Export the exact package to the absolute host path {(workspace / step_path).as_posix()} and write {(workspace / measurements_path).as_posix()} with step_path, step_sha256, envelope_mm [x,y,z], dry_mass_kg, carrier_thickness_mm, insulation_thickness_mm and heater_contact_diameter_mm, all measured or calculated from the authored solids. "
        f"Set the measurements step_path to the exact workspace-relative POSIX reference {step_path!r}; do not put a Windows absolute path or project-relative path in that field. Compute step_sha256 from the exported STEP bytes. "
        "The source must reject a violated fixed requirement and must not claim electrical, food-contact, pressure or physical qualification.",
        file_server,
        ("thermal-package-source.py",),
    )
    author_cad["fields"]["outputs"].append(h.port("thermal_package_source", "workspace_file"))
    author_cad["fields"]["settings"]["expected_file_ports"] = {
        "thermal_package_source": source_path
    }
    build_cad = package_task(
        "build_package_cad",
        "Build and reopen the exact thermal package CAD",
        f"Call run(script={str(workspace / source_path)!r},output='thermal-package',cwd={str(project)!r},build_dir='build',preview=False,view=False,diff=False). Preserve the actual native result and generated STEP. Fail if the measurements or STEP are missing; do not replace them with a report.",
        agentcad_server,
        ("thermal-package.step", "thermal-package-measurements.json"),
    )
    build_cad["fields"]["outputs"].extend(
        (h.port("thermal_package_step", "workspace_file"), h.port("thermal_package_measurements", "workspace_file"))
    )
    build_cad["fields"]["settings"]["expected_file_ports"] = {
        "thermal_package_step": step_path,
        "thermal_package_measurements": measurements_path,
    }
    container_workspace = getattr(args, "container_workspace", "/campaign-workspace").rstrip("/")
    container_output = container_workspace + "/" + output
    screen_config = {
        "workspace_root": container_workspace,
        "output_root": container_output,
        "geometry_step": container_output + "/thermal-package.step",
        "geometry_measurements": container_output + "/thermal-package-measurements.json",
        "power_comparison": container_output + "/power-comparison.csv",
        "approved_engineering_brief": container_workspace + "/" + renewal_path,
        "heater_efficiency": quantities["electrical_to_thermal_efficiency"],
        "target_temperature_c": quantities["target_temperature"],
        "ambient_temperature_c": quantities["ambient_temperature"],
    }
    input_content = "WATER_CONFIG = " + repr(screen_config) + "\nexec(compile(" + repr(thermal_source.decode()) + ", 'water_heater_package_skfem.py', 'exec'))\n"
    oasis_tool = next(
        tool
        for tool in supplemental_tools
        if tool["server_id"] == oasis_server and tool["tool_name"] == "run_simulation"
    )
    thermal_screen = {
        "kind": "task",
        "id": "screen_package_thermal_" + suffix,
        "fields": {
            "name": "Screen the exact CAD package thermally",
            "purpose": "Use the selected Modelica power and exact CAD dimensions in an independent scikit-fem package screen",
            "group": None,
            "step_type": "work",
            "performed_by": "configured_tool",
            "tool": None,
            "reusable_step": None,
            "inputs": [],
            "outputs": [
                h.port("thermal_screen_result"),
                h.port("thermal_package_field", "workspace_file"),
                h.port("thermal_package_verification", "workspace_file"),
            ],
            "prompt": "",
            "instructions": "Execute the immutable scikit-fem package screen once. This is a bounded digital model, not physical qualification.",
            "settings": {
                "authoring_template": "mcp-tool",
                "mcp_server": oasis_server,
                "mcp_tool": oasis_tool["name"],
                "mcp_schema_digest": oasis_tool["schema_digest"],
                "mcp_arguments": json.dumps({"solver": "skfem", "input_content": input_content, "job_name": container_output, "critic_approved": False}),
                "output_format": "json",
                "save_output": True,
                "output_filename": output + "/thermal-screen-execution.json",
                "file_policy": "overwrite",
                "timeout_seconds": 600,
                "expected_files": "\n".join((output + "/thermal-package-field.csv", output + "/thermal-package-verification.json")),
                "expected_file_ports": {
                    "thermal_package_field": output + "/thermal-package-field.csv",
                    "thermal_package_verification": output + "/thermal-package-verification.json",
                },
            },
        },
    }
    sections.append(thermal_screen)
    package_report = package_task(
        "collect_package_verification",
        "Collect the final tested digital heater package",
        f"Call inspect_file(includeText=true) for {output}/thermal-package-measurements.json and {output}/thermal-package-verification.json, and inspect_file(includeText=false) for {output}/thermal-package.step and {output}/thermal-package-field.csv. Produce a concise requirements table with expected, observed, pass/fail/unknown, evidence identity and physical follow-up. A solver run is not itself approval.",
        file_server,
        (),
    )
    package_report["fields"]["settings"]["output_format"] = "markdown"
    package_report["fields"]["settings"]["output_filename"] = output + "/thermal-package-report.md"
    h.add_reference(sections, study_producer["id"] + ".comparison", author_cad, "selected_power_evidence", "workspace_file")
    h.add_reference(sections, engineering_brief, author_cad, "approved_package_requirements")
    h.add_reference(sections, preflight_cad["id"] + ".preflight_package_cad_result", author_cad, "actual_cad_project_context")
    h.add_reference(sections, author_cad["id"] + ".thermal_package_source", build_cad, "authored_package_source", "workspace_file")
    h.add_reference(sections, build_cad["id"] + ".thermal_package_step", package_report, "final_cad", "workspace_file")
    h.add_reference(sections, thermal_screen["id"] + ".thermal_package_field", package_report, "thermal_field", "workspace_file")
    h.add_reference(sections, thermal_screen["id"] + ".thermal_package_verification", package_report, "package_verification", "workspace_file")
    chain.extend([preflight_cad, author_cad, build_cad, thermal_screen, package_report])
    coverage = json.loads(VALIDATION_COVERAGE.read_text(encoding="utf-8"))
    support = next(
        row for row in coverage["scenarios"] if row["scenario_id"] == identity
    )
    profile = support.get("full_profile")
    if not profile:
        raise ValueError("The water-heater full validator profile is unavailable")
    profile_document = json.loads(
        (
            ROOT
            / "packages/workspace_service/src/workspace_service/process_validation/profiles"
            / (profile["profile_resource"] + ".json")
        ).read_text(encoding="utf-8")
    )
    final_review = {
        "kind": "task",
        "id": "review_heater_outputs_" + suffix,
        "fields": {
            "name": "Review exact heater study outputs",
            "purpose": "Review source-backed energy, refinement and release claims",
            "group": None,
            "step_type": "review",
            "performed_by": "engineer",
            "tool": None,
            "reusable_step": None,
            "inputs": [],
            "outputs": [],
            "instructions": "Review the exact energy summary, comparison and engineering report against every frozen review requirement. Approval does not authorize purchasing, construction or operation.",
            "settings": {
                "authoring_template": "external-action-approval",
                "action_kind": "local_review",
                "approval_binding": {
                    "server": "wright",
                    "tool": "review_artifacts",
                    "schema": h.digest(b"wright.local_review.v1"),
                },
                "approval_destination": {"kind": "local_review", "id": "workspace"},
                "approval_settings": {
                    "review_task_id": "review_heater_outputs_" + suffix,
                    "validation_review": {
                        "profile_ref": profile["profile_ref"],
                        "requirement_ids": sorted(
                            requirement["id"]
                            for requirement in profile_document["baseline"]["requirements"]
                            if requirement["review_required"]
                        ),
                    },
                },
                "approval_action": {"kind": "local_review", "mode": "review_only"},
            },
        },
    }
    sections.append(final_review)
    for role in ("energy", "comparison", "report"):
        h.add_reference(
            sections,
            study_producer["id"] + "." + role,
            final_review,
            "review_" + role,
            "workspace_file",
        )
    h.add_reference(sections, build_cad["id"] + ".thermal_package_step", final_review, "final_thermal_package_cad", "workspace_file")
    h.add_reference(sections, thermal_screen["id"] + ".thermal_package_verification", final_review, "thermal_package_verification", "workspace_file")
    h.add_reference(sections, package_report["id"] + ".collect_package_verification_result", final_review, "tested_design_package")
    validation_sources = {
        **{
            role: (study_producer, role)
            for role in STUDY_OUTPUTS
        },
        "package_step": (build_cad, "thermal_package_step"),
        "package_measurements": (build_cad, "thermal_package_measurements"),
        "package_field": (thermal_screen, "thermal_package_field"),
        "package_verification": (
            thermal_screen,
            "thermal_package_verification",
        ),
    }
    validator = {
        "kind": "task",
        "id": "validate_heater_content_" + suffix,
        "fields": {
            "name": "Validate current heater outputs",
            "purpose": "Check the exact study against frozen requirements",
            "group": None,
            "step_type": "work",
            "performed_by": "configured_tool",
            "tool": None,
            "reusable_step": None,
            "inputs": [h.port("validate_" + role, "workspace_file") for role in validation_sources],
            "outputs": [h.port("assessment")],
            "prompt": "",
            "settings": {
                "authoring_template": "process-validator",
                "output_format": "json",
                "max_revisions": 0,
                "validation": {
                    "profile": {
                        "source": "packaged",
                        "name": profile["profile_resource"],
                        "reference": profile["profile_ref"],
                    },
                    "baseline": profile["baseline_ref"],
                    "subjects": {
                        role: "validate_" + role for role in validation_sources
                    },
                },
            },
        },
    }
    sections.append(validator)
    for role, (producer, producer_port) in validation_sources.items():
        sections.append(
            {
                "kind": "connection",
                "id": "bind_" + validator["id"] + "_" + role,
                "fields": {
                    "type": "item",
                    "from": producer["id"] + "." + producer_port,
                    "to": validator["id"] + ".validate_" + role,
                    "label": "current heater output to validate",
                    "when": None,
                },
            }
        )
    chain.extend([final_review, validator])
    for first, last in zip(chain, chain[1:]):
        sections.append({"kind": "connection", "id": "complete_sequence_" + last["id"], "fields": {"type": "order", "from": first["id"], "to": last["id"], "label": "complete native heater engineering chain", "when": None}})
    rendered = h.render_new_draft(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowlist = [selected_tools[name] for name in TOOLS] + supplemental_tools
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    result = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt, "template_id": data["template_id"], "status": "prepared_not_dispatched", "source": str(target), "source_sha256": h.digest(rendered.encode()), "template_source_sha256": h.digest(TEMPLATE.read_bytes()), "workspace_root": str(workspace), "output_root": output, "input_manifest": staged, "required_step_ids": [step.id for step in plan.steps], "preserved_original_stages": [stages[p]["id"] for p in ORIGINAL], "expected_outputs": renewal.expected_outputs(data), "expected_tool_created_files": [path for step in plan.steps for path in step.expected_files], "tool_allowlist": allowlist, "server_id": args.server_id, "package_chain": {"agentcad_server": agentcad_server, "oasis_server": oasis_server, "operation_source": thermal_source_path}, "requires_template_instance_api": not bool(args.instance_source), "selected_kit_identity": "wright-water-heater-v1@0.1.0", "baseline_request_ids": [item["request_id"] for item in observed], "refined_request_ids": selected_ids, "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []}}
    h.publish_input_binding_evidence(result, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return {"scenario_id": identity, "source": str(target), "stages": len(plan.steps), "executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--draft-root", required=True)
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--agentcad-server-id", default="agentcad")
    parser.add_argument("--workspace-file-server-id", default="wright-workspace-files")
    parser.add_argument("--oasis-server-id", default="oasis")
    parser.add_argument("--container-workspace", default="/campaign-workspace")
    parser.add_argument("--initialize-agentcad", action="store_true")
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
