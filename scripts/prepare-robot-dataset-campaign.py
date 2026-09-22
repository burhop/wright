"""Bind the canonical robot template to real offline bag tools; never execute it."""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape
from workspace_service.workflow_integration_policy import LOCAL_REVIEW_BINDING, LOCAL_REVIEW_DESTINATION

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow"
VALIDATION_COVERAGE = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"
spec = importlib.util.spec_from_file_location("robot_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
renewal_spec = importlib.util.spec_from_file_location(
    "campaign_example_renewal", ROOT / "scripts/campaign_example_renewal.py"
)
renewal = importlib.util.module_from_spec(renewal_spec)
renewal_spec.loader.exec_module(renewal)


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
    project = workspace / output / "agentcad-project"
    if getattr(args, "initialize_agentcad", False):
        if project.exists():
            raise ValueError("Native init requires a fresh isolated AgentCAD project")
        project.mkdir(parents=True)
        command = [
            "uv", "run", "--isolated", "--python", "3.12", "--with",
            "agentcad[mcp]==0.6.0", "agentcad", "init", "--name",
            "robot-corrective-hardware", "--build-dir", "build",
        ]
        initialized = subprocess.run(
            command, cwd=project, capture_output=True, text=True, timeout=300
        )
        if initialized.returncode:
            raise RuntimeError("Actual corrective-hardware CAD initialization failed")
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    if identity == "robot-tracking-diagnosis-01":
        next(s for s in sections if s["kind"] == "workflow")["fields"].update(
            name="Investigate cart tracking at a floor seam",
            purpose="Compare the intended route, overhead tracker and wheel-based position estimate around the recorded floor-seam crossing. Separate measured deviations from possible causes and choose the next inexpensive observation. Offline analysis of synthetic logs; no robot control or demonstrated pass/fail tracking limit.",
        )
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
    stage_file(
        inputs + "/approved-engineering-brief.json",
        renewal.contract_bytes(manifest),
        {"role": "approved_engineering_brief"},
    )
    renewal_contract = renewal.case_contract(manifest)
    human = "\n\n".join((directory / name).read_text(encoding="utf-8") for name in ["user-profile.md", "prompt.txt", *manifest["files"]["context"]])
    stage_file(inputs + "/assembled-context.md", human.encode(), {"derived_from": manifest["files"]})
    stage_file(inputs + "/alignment.json", (json.dumps(config["scenarios"][identity], indent=2) + "\n").encode(), {"derived_from": ["context.md", "bag-conversion.md"], "purpose": "Explicit user-supplied survey and clock contract"})
    for name in ("robot_tracking_operations.py", "robot_tracking_mcp.py"):
        stage_file(inputs + "/" + name, (ROOT / "scripts" / name).read_bytes(), {"operation_source": "scripts/" + name})
    context = helpers.add_file_input(sections, suffix, "human_context", inputs + "/assembled-context.md")
    engineering_brief = helpers.add_file_input(
        sections, suffix, "approved_engineering_brief", inputs + "/approved-engineering-brief.json"
    )
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
    normalized = bind(normalize, f"Call normalize_csv_to_ros2 exactly once with operation_source_document={inputs + '/robot_tracking_operations.py'!r}, input_directory={inputs!r}, output_directory={output + '/converted'!r}. Read the supplied source and mapping. Preserve original CSVs and +150ms header offsets; no frame transform during conversion. Save the actual returned conversion manifest. In the completed task response, preserve the tool result's exact topics array with every topic, schema and count, plus omitted_rows, bag_files and operation_sha256; do not replace these values with only a path or hash because the connected bag-inspection task must compare its independently observed counts without file-reader access. Never reuse a prior attempt's bag.", config["operation_server"], ["converted/recording/recording.db3", "converted/recording/metadata.yaml", "converted/conversion-manifest.json"])
    normalize["fields"]["outputs"].append(helpers.port("conversion_manifest", "workspace_file"))
    normalize["fields"]["settings"]["expected_file_ports"] = {
        "conversion_manifest": output + "/converted/conversion-manifest.json"
    }
    inspection_scope = (INSPECTION_STAGE_GUIDANCE
        + f"After this evidence is returned, the connected canonical step {stages['align_and_measure']['id']} on server {config['operation_server']} "
        "calls calculate_tracking_metrics on the complete same-run bag to produce the timeline, overlay and metrics; the later draft_diagnosis step writes diagnosis.md from those actual outputs. "
        "Leave those operations to their declared later stages and retain the subsequent engineer review. ")
    inspection = bind(stages["inspect_bag"], inspection_scope + f"Use the connected same_run_conversion response's exact topics array as the conversion-manifest count evidence; this bag-only server is not expected to read conversion-manifest.json. First call bag_info on bag_path='/workspace/{output}/converted/recording', then get_topic_schema for all five topics. Then call get_messages_in_range exactly once per topic with start_time=1767225600,end_time=1767225630.01,max_messages=2. This is a bounded native sample inspection, not full inline extraction. Do not increase max_messages or repeat ranges: the next fixed metrics operation independently reads every actual message from the on-disk bag. Topic names: /wright_test/planned_pose,/wright_test/external_pose,/wright_test/odom,/wright_test/cmd_vel,/wright_test/operator_event. Keep the JSON output below 12000 characters: record actual topic/type/count summaries plus the at-most-two retrieved samples per topic, projecting timestamp, header stamp/frame, position/orientation, velocity and event text as applicable; omit bulky zero covariance arrays while explicitly naming omitted fields. Retain full actual records in the generated bag, referenced by its same-run path and manifest hash. Check each independently observed bag count against the connected manifest topic count; report the comparison and any mismatch explicitly; report error strings as failures, even when isError is false. Do not infer schemas or invent messages. Inspect before metrics.", config["bag_server"], filename="bag-inspection.json")
    helpers.add_reference(sections, normalized, stages["inspect_bag"], "same_run_conversion")
    # Eleven real inspection calls plus the final report exceeded the original
    # five-minute budget in the recorded run. Keep the observations bounded and
    # the complete inspection intact within the runtime's ten-minute task cap.
    stages["inspect_bag"]["fields"]["settings"]["timeout_seconds"] = 600
    stages["inspect_bag"]["fields"]["settings"]["task_guidance"] += " " + inspection_scope
    measured = bind(stages["align_and_measure"], f"After actual native bag inspection/extraction succeeded, call calculate_tracking_metrics exactly once with operation_source_document={inputs + '/robot_tracking_operations.py'!r}, bag_directory={output + '/converted/recording'!r}, alignment_document={inputs + '/alignment.json'!r}, output_directory={output + '/analysis'!r}. The supplied reusable source applies the explicit transform once and retains the original 1% independent metrics and one-sample event gates. It must preserve the visual occlusion as missing samples, report unaligned/aligned overlays and save actual computed outputs. The main plot compares the intended route, external position measurements and wheel-based estimates, with time-linked sideways error in millimetres. Keep the separate alignment comparison and plot reading guide available for review. Read the returned metrics; don't invent or weaken checks.", config["operation_server"], ["analysis/timeline.csv", "analysis/trajectory-overlay.svg", "analysis/tracking-metrics.json", "analysis/alignment-comparison.svg", "analysis/plot-guide.md"], filename="analysis-report.json")
    measurement_files = {
        "timeline": output + "/analysis/timeline.csv",
        "plot": output + "/analysis/trajectory-overlay.svg",
        "metrics": output + "/analysis/tracking-metrics.json",
        "alignment_plot": output + "/analysis/alignment-comparison.svg",
        "plot_guide": output + "/analysis/plot-guide.md",
    }
    stages["align_and_measure"]["fields"]["outputs"].extend(
        helpers.port(role, "workspace_file") for role in measurement_files
    )
    stages["align_and_measure"]["fields"]["settings"]["expected_file_ports"] = measurement_files
    helpers.add_reference(sections, inspection, stages["align_and_measure"], "native_bag_evidence")
    diagnosis_task = new_task("draft_diagnosis", "Write the evidence-linked diagnosis for engineer review")
    diagnosis = bind(diagnosis_task, "Write the requested engineering diagnosis from the actual supplied original prompt, route sketch, bag evidence and computed metrics. Cite time ranges, retained counts, frame/time correction, event correlation, missing intervals and uncertainties. Compare raw and aligned interpretations. Link the actual path/error plot, separate alignment comparison and plot reading guide from the measurement output. Explain what each plot shows in engineering language, including the independent axis scales and the difference between external measurement and wheel-based estimate. State measured observations separately from hypotheses; command/odometry disagreement alone is not evidence of wheel slip. Include the requested inexpensive next observation. These are fictional input logs and no real robot commands are authorized.", filename="diagnosis.md")
    helpers.add_reference(
        sections, engineering_brief, diagnosis_task, "approved_engineering_brief"
    )
    diagnosis_task["fields"]["prompt"] += (
        " Organize the report under: Why this analysis matters; What the plots show; "
        "Measured findings; What remains unknown; Next inexpensive test. "
        "Start with a short decision-oriented summary, not file hashes or tool details. "
        "Use actual relative Markdown links: [Path and sideways error](analysis/trajectory-overlay.svg), "
        "[Before and after alignment](analysis/alignment-comparison.svg), and "
        "[How to read the plots](analysis/plot-guide.md). "
        "Do not invent a tracking acceptance limit or imply that the seam caused the deviation."
    )
    helpers.add_reference(sections, measured, diagnosis_task, "actual_metrics")
    helpers.add_reference(sections, inspection, diagnosis_task, "bag_evidence")
    helpers.add_reference(sections, image, diagnosis_task, "route_image", "reference_images")
    # The original combined AI/engineer semantic stage remains the authority gate.
    review = stages["evidence_diagnosis"]
    review["fields"].update(name="Review findings and choose the next test", step_type="review", performed_by="engineer", inputs=[], outputs=[], instructions="Review the actual diagnosis, event and metrics evidence. Keep observations separate from candidate causes; do not infer wheel slip from command/odometry disagreement.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review", "causal_overclaiming": False,
                  "approval_binding": LOCAL_REVIEW_BINDING, "approval_destination": LOCAL_REVIEW_DESTINATION,
                  "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}})
    helpers.add_reference(sections, diagnosis, review, "diagnosis_for_review")
    agentcad_server = getattr(args, "agentcad_server_id", "agentcad")
    file_server = getattr(args, "workspace_file_server_id", "wright-workspace-files")
    solver_server = getattr(args, "solver_server_id", "calculix")
    field_server = getattr(args, "field_server_id", "calculix-fields")
    fixed = renewal_contract["approved_engineering_inputs"]["new_fixed_requirements"]
    preflight_cad = new_task(
        "preflight_corrective_cad", "Verify isolated corrective-hardware CAD project"
    )
    bind(
        preflight_cad,
        f"Call context(cwd={str(project)!r},build_dir='build') and docs(section='quickstart',cwd={str(project)!r},build_dir='build'). Report the actual project identity. An empty project is expected; do not claim corrective hardware exists yet.",
        agentcad_server,
    )
    author_cad = new_task(
        "author_corrective_cad_source", "Author corrective hardware from independent site requirements"
    )
    source_path = output + "/corrective-hardware-source.py"
    step_path = output + "/corrective-hardware.step"
    measurements_path = output + "/corrective-hardware-measurements.json"
    request_path = output + "/corrective-fea-request.json"
    bind(
        author_cad,
        "Call write_text_document to create " + source_path + " as actual build123d Python for this approved corrective-hardware job. "
        "Use these independently approved site/interface/material/load requirements exactly: " + json.dumps(fixed, sort_keys=True) + ". "
        "The tracking diagnosis is context only and does not prove a cause or authorize changing these fixed requirements. Choose only the explicitly permitted topology/mechanism details. "
        f"Export one connected final part or assembly envelope to {step_path}. Reopen it and write {measurements_path} with step_path, step_sha256, envelope_mm, mass_kg and every fixed interface/load-location measurement. "
        f"Write {request_path} with coarse and fine CalculiX requests bound to the exact STEP SHA-256, E=69000 MPa, nu=0.33, density=2700 kg/m3, the approved load and support interfaces, and the approved stress/deflection limits. "
        "Reject missing load/support geometry or a violated fixed requirement. Do not claim installation, causal proof, trip-risk acceptance, visibility performance or physical robot testing.",
        file_server,
        ("corrective-hardware-source.py",),
    )
    author_cad["fields"]["outputs"].append(
        helpers.port("corrective_hardware_source", "workspace_file")
    )
    author_cad["fields"]["settings"]["expected_file_ports"] = {
        "corrective_hardware_source": source_path
    }
    build_cad = new_task(
        "build_corrective_hardware", "Build and reopen the corrective hardware CAD"
    )
    bind(
        build_cad,
        f"Call run(script={str(workspace / source_path)!r},output='corrective-hardware',cwd={str(project)!r},build_dir='build',preview=False,view=False,diff=False). Preserve actual native execution and generated files. Fail if the STEP, measurements or closed FEA request are missing.",
        agentcad_server,
        ("corrective-hardware.step", "corrective-hardware-measurements.json", "corrective-fea-request.json"),
    )
    build_outputs = {
        "corrective_step": step_path,
        "corrective_measurements": measurements_path,
        "corrective_request": request_path,
    }
    build_cad["fields"]["outputs"].extend(
        helpers.port(role, "workspace_file") for role in build_outputs
    )
    build_cad["fields"]["settings"]["expected_file_ports"] = build_outputs
    helpers.add_reference(
        sections,
        author_cad["id"] + ".corrective_hardware_source",
        build_cad,
        "authored_corrective_source",
        "workspace_file",
    )
    solve = new_task(
        "solve_corrective_hardware", "Run coarse and fine corrective-hardware CalculiX checks"
    )
    solved = bind(
        solve,
        "Read the exact connected corrective-fea-request. For both coarse and fine records, call calculix_mesh_preflight with only its closed supported arguments, require nonempty supports and load selections, then call calculix_solve_static_recorded with the unchanged request. Preserve actual run IDs, STEP hashes, mesh counts, solver results and errors. Do not enlarge supports/loads, add gravity, change limits, or infer correctness from solver completion.",
        solver_server,
        filename="corrective-solver-runs.json",
    )
    helpers.add_reference(
        sections,
        build_cad["id"] + ".corrective_request",
        solve,
        "closed_corrective_fea_request",
        "workspace_file",
    )
    expand = new_task(
        "export_corrective_fields", "Export displacement, stress and reactions for both meshes"
    )
    field_expected = tuple(
        f"corrective-fea/{mesh}/{name}"
        for mesh in ("coarse", "fine")
        for name in (
            "field-expansion-receipt.json",
            "native-field-expansion/displacement-field.csv",
            "native-field-expansion/stress-field.csv",
            "reaction-forces.json",
        )
    )
    fields_result = bind(
        expand,
        f"For each exact coarse/fine run in the connected solver result, call export_recorded_fields_and_reactions(run_id=<actual>,expected_step_sha256=<actual>,output_directory='{output}/corrective-fea/<mesh>'). Preserve original and output-only solve lineage, complete displacement/stress fields and reactions. Never fabricate a successful field export.",
        field_server,
        field_expected,
        filename="corrective-field-exports.json",
    )
    helpers.add_reference(sections, solved, expand, "actual_corrective_solver_runs")
    expand_outputs = {}
    for mesh in ("coarse", "fine"):
        for short, name in (
            ("receipt", "field-expansion-receipt.json"),
            ("displacement", "native-field-expansion/displacement-field.csv"),
            ("stress", "native-field-expansion/stress-field.csv"),
            ("reaction", "reaction-forces.json"),
        ):
            role = f"corrective_{mesh}_{short}"
            expand_outputs[role] = output + f"/corrective-fea/{mesh}/{name}"
    expand["fields"]["outputs"].extend(
        helpers.port(role, "workspace_file") for role in expand_outputs
    )
    expand["fields"]["settings"]["expected_file_ports"] = expand_outputs
    fea_report = new_task(
        "verify_corrective_design", "Verify the exact corrective design against its fixed requirements"
    )
    verified_design = bind(
        fea_report,
        f"Call inspect_file(includeText=true) for {measurements_path}, {request_path}, both corrective displacement/stress CSVs, both reaction JSONs and both expansion receipts. Call inspect_file(includeText=false) for {step_path}. Produce an evidence-linked JSON document at {output}/corrective-fea.json with schema='wright-robot-corrective-fea-v1', status='pass' only when every approved digital check passes, step_sha256, requirements[] entries containing expected/observed/status/evidence, coarse/fine sensitivity, force equilibrium, maximum displacement, evaluated stress and mass. Preserve raw stress peaks and limitations. A solver run or tracking correlation is not causal proof or physical qualification.",
        file_server,
        ("corrective-fea.json",),
        filename="corrective-fea.json",
    )
    fea_report["fields"]["outputs"].append(
        helpers.port("corrective_fea", "workspace_file")
    )
    fea_report["fields"]["settings"]["expected_file_ports"] = {
        "corrective_fea": output + "/corrective-fea.json"
    }
    helpers.add_reference(sections, fields_result, fea_report, "actual_field_exports")
    helpers.add_reference(
        sections, build_cad["id"] + ".corrective_step", fea_report, "exact_corrective_cad", "workspace_file"
    )
    commissioning = new_task(
        "write_commissioning_package", "Write the bounded installation and commissioning package"
    )
    bind(
        commissioning,
        "Write a concise engineering commissioning package from the approved independent site requirements, reviewed non-causal diagnosis, exact CAD and FEA verification. Include installation prerequisites, inspection dimensions, torque/anchor items that remain for engineer approval, and a measurement plan that would test the original tracking issue after installation. Clearly mark installation, physical proof, causal attribution and robot testing as not performed.",
        filename="commissioning-package.md",
    )
    helpers.add_reference(sections, verified_design, commissioning, "corrective_design_verification")
    helpers.add_reference(sections, diagnosis, commissioning, "reviewed_noncausal_diagnosis")
    coverage = json.loads(VALIDATION_COVERAGE.read_text(encoding="utf-8"))
    support = next(row for row in coverage["scenarios"] if row["scenario_id"] == identity)
    profile = support.get("full_profile")
    if not profile:
        raise ValueError("The robot tracking full validator profile is unavailable")
    profile_document = json.loads(
        (
            ROOT
            / "packages/workspace_service/src/workspace_service/process_validation/profiles"
            / (profile["profile_resource"] + ".json")
        ).read_text(encoding="utf-8")
    )
    review_requirement_ids = sorted(
        requirement["id"]
        for requirement in profile_document["baseline"]["requirements"]
        if requirement["review_required"]
    )
    review["fields"]["settings"]["approval_settings"]["validation_review"] = {
        "profile_ref": profile["profile_ref"],
        "requirement_ids": review_requirement_ids,
    }
    validator = new_task("validate_robot_content", "Validate current robot tracking outputs")
    validation_sources = {
        "conversion_manifest": (normalize, "conversion_manifest", "workspace_file"),
        "timeline": (stages["align_and_measure"], "timeline", "workspace_file"),
        "metrics": (stages["align_and_measure"], "metrics", "workspace_file"),
        "plot": (stages["align_and_measure"], "plot", "workspace_file"),
        "diagnosis": (
            diagnosis_task,
            diagnosis_task["fields"]["outputs"][0]["key"],
            "engineering_document",
        ),
        "corrective_step": (build_cad, "corrective_step", "workspace_file"),
        "corrective_measurements": (
            build_cad,
            "corrective_measurements",
            "workspace_file",
        ),
        "corrective_fea": (fea_report, "corrective_fea", "workspace_file"),
        "commissioning": (
            commissioning,
            commissioning["fields"]["outputs"][0]["key"],
            "engineering_document",
        ),
    }
    validator["fields"].update(
        performed_by="configured_tool",
        inputs=[
            helpers.port("validate_" + role, kind)
            for role, (_, _, kind) in validation_sources.items()
        ],
        outputs=[helpers.port("assessment")],
        prompt="",
        settings={
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
    )
    for role, (producer, producer_port, _) in validation_sources.items():
        sections.append({
            "kind": "connection",
            "id": "bind_" + validator["id"] + "_" + role,
            "fields": {
                "type": "item",
                "from": producer["id"] + "." + producer_port,
                "to": validator["id"] + ".validate_" + role,
                "label": "current robot output to validate",
                "when": None,
            },
        })
    collection = new_task("collect_robot_evidence", "Collect the approved engineering diagnosis and artifact links")
    bind(collection, "Create a compact artifact index referencing the actual same-run bag, conversion manifest, original/analysis source, inspection evidence, timeline, overlay, metrics, approved diagnosis and current process-validation assessment. State only the scope and verdict supported by that assessment.", filename="evidence-index.md")
    helpers.add_reference(sections, diagnosis, collection, "approved_diagnosis")
    helpers.add_reference(
        sections,
        validator["id"] + ".assessment",
        collection,
        "process_validation_assessment",
    )
    for start, end in (
        (normalize["id"], stages["inspect_bag"]["id"]),
        (diagnosis_task["id"], review["id"]),
        (review["id"], preflight_cad["id"]),
        (preflight_cad["id"], author_cad["id"]),
        (author_cad["id"], build_cad["id"]),
        (build_cad["id"], solve["id"]),
        (solve["id"], expand["id"]),
        (expand["id"], fea_report["id"]),
        (fea_report["id"], commissioning["id"]),
        (commissioning["id"], validator["id"]),
    ):
        sections.append({"kind": "connection", "id": "order_" + start + "_" + end, "fields": {"type": "order", "from": start, "to": end, "label": "same canonical execution", "when": None}})
    sections.append({
        "kind": "connection",
        "id": "release_" + validator["id"],
        "fields": {
            "type": "approval",
            "from": validator["id"],
            "to": collection["id"],
            "label": "release current validated outputs",
            "when": "pass",
        },
    })
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
    for server, names in {
        agentcad_server: ("context", "docs", "run"),
        file_server: ("write_text_document", "inspect_file"),
        solver_server: (
            "calculix_mesh_preflight",
            "calculix_solve_static_recorded",
            "calculix_run_get",
        ),
        field_server: ("export_recorded_fields_and_reactions",),
    }.items():
        for name in names:
            matches = [
                tool
                for tool in available
                if tool["server_id"] == server and tool["tool_name"] == name
            ]
            if len(matches) != 1:
                raise ValueError(
                    "Required corrective-design tool unavailable: " + server + "/" + name
                )
            selected.append(matches[0])
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(result, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "template_id": manifest["template_id"], "attempt_id": args.attempt,
              "status": "prepared_not_dispatched", "source": str(target), "source_sha256": helpers.digest(result.encode()),
              "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()),
              "requires_template_instance_api": not bool(args.instance_source), "workspace_root": str(workspace), "output_root": output,
              "input_manifest": staged, "tool_allowlist": selected,
              "expected_outputs": renewal.expected_outputs(manifest),
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
    parser.add_argument("--agentcad-server-id", default="agentcad")
    parser.add_argument("--workspace-file-server-id", default="wright-workspace-files")
    parser.add_argument("--solver-server-id", default="calculix")
    parser.add_argument("--field-server-id", default="calculix-fields")
    parser.add_argument("--initialize-agentcad", action="store_true")
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
