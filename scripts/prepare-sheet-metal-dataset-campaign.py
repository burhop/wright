"""Prepare three original sheet-metal graphs without executing CAD or handoffs.

Use --instance-source after normal template creation to retain immutable origin.
All six original task identities and their existing revision/approval edges are
preserved. The two-part case adds a separately bound lid, never an assembly DXF.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import urllib.parse
import urllib.request

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape
from workspace_service.workflow_integration_policy import LOCAL_REVIEW_BINDING, LOCAL_REVIEW_DESTINATION, TEST_HANDOFF_BINDING

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/sheet-metal-supplier-handoff.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sheet-metal-supplier-handoff.workflow.wflow"
SERVER = "solid-edge-mcp-burhop"
MATERIAL_PAGES = {
    "sheet-metal-supplier-handoff-01": "https://sendcutsend.com/materials/5052-aluminum/",
    "sheet-metal-supplier-handoff-02": "https://sendcutsend.com/materials/mild-steel/",
    "sheet-metal-supplier-handoff-03": "https://sendcutsend.com/materials/5052-aluminum/",
}
_spec = importlib.util.spec_from_file_location("sheet_campaign_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def prepare(args, directory, available):
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    manifest = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    if "cad-design-choices-revision-r3.md" not in manifest["files"]["context"]:
        raise ValueError("Publish the explicit R3 CAD design-choice input revision before preparing a fresh sheet-metal attempt")
    scenario = manifest["scenario_id"]
    scenario_config = config["scenarios"][scenario]
    company_capabilities = "company-fabrication-capabilities-r4.md" in manifest["files"]["context"]
    # Keep the seven specific process references and the original eight-page
    # output contract; material identity needs its own primary supplier page.
    supplier_sources = [MATERIAL_PAGES[scenario], *config["supplier_sources"][1:]]
    suffix = scenario.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / scenario / args.attempt
    if draft.exists():
        raise ValueError("Draft attempt exists; preserve it and select a new attempt.")
    inputs_root = f"campaign/{scenario}/{args.attempt}/inputs"
    output_root = f"campaign/{scenario}/{args.attempt}/artifacts"
    evidence_server = getattr(args, "evidence_server_id", "wright-engineering-evidence")
    original = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(original)
    original_tasks = [s["id"] for s in sections if s["kind"] == "task"]
    original_edges = [s for s in sections if s["kind"] == "connection"]
    def stage(prefix):
        matches = [s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")]
        if len(matches) != 1:
            raise ValueError("Original sheet-metal stage is missing/ambiguous: " + prefix)
        return matches[0]
    intent, cad, check, export, preview, handoff = [stage(prefix) for prefix in (
        "intent_document", "solid_edge_cad", "measured_design_check", "export_and_verify", "supplier_preview_approval", "cart_quote_handoff")]
    staged = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            relative = inputs_root + "/" + path.name
            data = path.read_bytes()
            helpers.write_once(helpers.confined(workspace, relative), data)
            staged.append({"path": relative, "sha256": helpers.digest(data), "size_bytes": len(data),
                           "original": path.relative_to(ROOT).as_posix()})
    human_files = [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]]
    # Include every human table exactly, even when authored outside files.context.
    human_files += [p.name for p in directory.glob("*.csv") if p.name not in human_files]
    context = "\n\n".join("## Original upload: " + name + "\n\n" + (directory / name).read_text(encoding="utf-8") for name in human_files)
    context_path = inputs_root + "/assembled-context.md"
    helpers.write_once(helpers.confined(workspace, context_path), context.encode())
    staged.append({"path": context_path, "sha256": helpers.digest(context.encode()), "size_bytes": len(context.encode()),
                   "derived_from": [inputs_root + "/" + name for name in human_files]})
    brief = helpers.add_file_input(sections, suffix, "human_context", context_path)
    operation_source = ROOT / "scripts/engineering_evidence_mcp.py"
    operation_path = inputs_root + "/engineering-evidence-operation.py"
    helpers.write_once(helpers.confined(workspace, operation_path), operation_source.read_bytes())
    staged.append({"path": operation_path, "sha256": helpers.digest(operation_source.read_bytes()),
                   "size_bytes": operation_source.stat().st_size, "original": operation_source.relative_to(ROOT).as_posix()})
    operation_ref = helpers.add_file_input(sections, suffix, "evidence_operation_source", operation_path)
    image = helpers.add_file_input(sections, suffix, "human_concept", inputs_root + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"

    def new_task(prefix, name):
        task = {"kind": "task", "id": prefix + "_" + suffix, "fields": {
            "name": name, "purpose": name, "step_type": "work", "group": None,
            "performed_by": "ai_assisted", "inputs": [], "outputs": [], "settings": {},
            "tool": None, "reusable_step": None,
        }}
        sections.append(task)
        return task
    def order(before, after, label):
        sections.append({"kind": "connection", "id": "campaign_order_" + before["id"] + "_" + after["id"], "fields": {
            "type": "order", "from": before["id"], "to": after["id"], "label": label, "when": None,
        }})
    def bind(task, prompt, name, server=None, expected=(), fmt="json"):
        fields = task["fields"]
        fields.update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[],
                      outputs=[helpers.port(task["id"] + "_report")])
        fields["settings"] = {"output_format": fmt, "save_output": True, "file_policy": "indexed",
                              "output_filename": output_root + "/" + name}
        if server:
            fields["settings"].update(authoring_template="mcp-task", mcp_server=server,
                expected_files="\n".join(output_root + "/" + p for p in expected), max_tool_calls=24, timeout_seconds=600,
                task_guidance="Use only enrolled tools; do not target unrelated open documents. Preserve original requirements, exact called recipe/source and observed readbacks in run evidence. Never fabricate a successful tool call or claim an unresolved fact is verified.")
        helpers.add_reference(sections, brief, task, "human_inputs")
        return task["id"] + "." + task["id"] + "_report"
    research = new_task("supplier_research", "Retrieve current supplier capability evidence")
    source_files = [f"supplier-source-{i + 1}.{extension}" for i in range(len(supplier_sources)) for extension in ("html", "txt")]
    research_ref = bind(research,
        "Retrieve these exact official supplier pages without logging in, uploading, communicating, or changing a cart: " + json.dumps(supplier_sources) + ". "
        f"Call retrieve_public_references(operation_source_document={operation_path!r}, output_root={output_root!r}, urls={supplier_sources!r}). "
        "The selected operation verifies its exact staged source and saves complete actual HTML/text, URLs, retrieval times and hashes; retrieval returns compact metadata and short previews. "
        f"Use read_reference_text(operation_source_document={operation_path!r}, output_root={output_root!r}, source_index=<returned index>, expected_evidence_sha256=<returned evidence_sha256>, query=<literal relevant term>, offset=0, max_chars=2000) for relevant stock/radii/clearance/finish excerpts. Follow next_offset only for directly relevant continuation and retain source index, offsets and evidence hash in findings. Search the actual requested alloy, thickness and manufacturing terms; do not read or concatenate whole pages. "
        "Report attributed findings and unresolved items concisely. A bounded excerpt is not the full page; no-match or insufficient context remains unresolved. No cached fixture acceptance or invented numeric offering. Proposed 1.5 mm thickness and 2 mm radius are customer requests, not established supplier offerings.",
        "supplier-research-report.json", evidence_server, source_files)
    helpers.add_reference(sections, operation_ref, research, "executed_operation_source")
    research["fields"]["prompt"] += (
        " Read the dedicated relief page for minimum width/depth and measurement reference, the channel page for applicable thin-sheet exceptions, "
        "the deformation page for feature-to-bend distances, and the processing-size page for applicable press/part limits. "
        "Do not label these rules unknown merely because the general overview omits them. Evaluate conditions and distinguish recommendation, hard minimum and conditional supplier review. "
        "Read the ordinary channel ratio before its optional thin-sheet exceptions. Check the applicable base-to-flange ratio using actual dimensional frames; "
        "exceeding a flange-height limit on an optional 1:1 exception does not itself fail an otherwise applicable ordinary 2:1 rule. "
        "A passing channel ratio alone does not verify full box-forming tool access. "
        "Read the scenario's material page to establish the selected stock's alloy/class and offered thickness; a generic material label alone is insufficient identity evidence. "
        "On the calculator page, locate the actual material table and retain its column header plus the complete matching thickness row with original units. "
        "The first material-name match may be an introduction, not the table. Repeat the literal material query from the returned next_offset to reach later matching occurrences; "
        "page directly relevant table continuations until the header and full matching row are retained. Do not repeatedly reset offset to zero after an introductory match. "
        "Use the exact displayed thickness spelling as the literal query (for example, .059 rather than 0.059 when the page displays .059); this example is not a stock selection. "
        "Do not declare K factor, bend deduction, radius, die width or relief values absent based on introductory text, a differently spelled no-match, or a truncated row. "
        "If bounded reads still cannot establish the complete row, disclose the precise unread or missing evidence and keep selection unresolved. "
        "Return only the exact selected stock row and relevant bounded rule excerpts/citations, not whole pages or every material row. "
        "Keep the report below 12000 characters, including source index, evidence hash and excerpt offsets for each decision."
    )
    materials = new_task("installed_materials", "Read installed Solid Edge material identities")
    material_ref = bind(materials,
        "Call cad.get_status and cad.list_materials using query " + json.dumps(scenario_config["material_query"]) + ". "
        "If connection is needed, cad.connect may start the licensed local host; do not create or modify a document here. Retain actual native spelling, library and returned properties. Follow hasMore/nextOffset or use a narrower query when the required entry is not on the returned page; an incomplete page is not a complete inventory. A 5052 label does not prove H32. "
        "Distinguish requested alloy/class from supplier temper and native metadata: do not promote a sourced temper to a customer requirement. "
        "Apply any explicit uploaded native-label mapping only when the unique fresh inventory supports it. Missing density/strength/temper metadata is not a geometry blocker when the human revision explicitly allows the mapping and no property-dependent analysis was requested; do not claim those properties. "
        "Missing or ambiguous required alloy/class remains an unresolved design decision; never invent a library entry.",
        "installed-materials.json", SERVER)
    order(research, intent, "current supplier facts precede intent")
    order(materials, intent, "installed material evidence precedes intent")
    intent_ref = bind(intent,
        "Create the complete sheet-metal manufacturing intent document from the original human uploads/image, supplier research and installed CAD material evidence. "
        + scenario_config["specific_decisions"] + " "
        "Preserve dimensional frames, quantity and styling. Read stock-selection-revision-r1.md and any later declared human revision in order: select actual sourced stock and its complete bend rule within those bounds, record old versus new thickness/radius and recalculate offsets while retaining protected folded geometry. "
        "Use exact source attribution: distinguish original customer requirements, later human revision choices, retrieved supplier offerings and observed native metadata. The original 5052 request does not specify H32; never invent that temper as a customer requirement. "
        "Missing material properties that are neither requested nor needed for geometry are disclosed unknowns, not invented mandatory CAD prerequisites when an explicit human native-label mapping permits geometry. Missing required identity or unsupported supplier hard constraints still block. "
        "Produce a criterion-by-criterion verification table with measurable nominal dimensions and explicitly supplied tolerances; do not invent tolerances or certification. "
        "Cite the exact selected supplier row, original units, evidence identity/offsets, K factor, radius, relief and applicable flange/feature/press limits; do not transpose values between stocks. If no complete eligible row is established, report needs_input rather than inventing a compatible rule. "
        "State unresolved supplier differences separately; auto review confirms the test's chosen bounded revision, not manufacturability or supplier acceptance. A release HOLD does not waive any mandatory DFM/geometry requirement. "
        "Name each required part with the runtime part labels and its separate PSM/STEP/developed DXF outputs; runtime-supplied indexed paths are authoritative. Retain manufacturing_release=HOLD and supplier_acceptance=unverified.",
        "manufacturing-intent.md", fmt="markdown")
    nominal_outputs = {part: {extension: output_root + "/" + part + "." + extension
                             for extension in ("psm", "step", "dxf", "jpg")}
                       for part in scenario_config["parts"]}
    intent["fields"]["prompt"] += (
        " Explicit runtime output contract (nominal paths, indexed when the owning CAD task executes): "
        + json.dumps(nominal_outputs) + ". Quantity per part: " + str(scenario_config["quantity_per_part"]) + ". "
        "Final indexed allocation is a later runtime responsibility, not an unresolved human choice or a prerequisite for drafting this intent. "
        "Apply cad-design-choices-revision-r3.md after R1/R2. Populate a complete native-rule table before approval: actual stock thickness T, inside radius R, "
        "sourced K, controlling bendCalculationMethod, exact native materialDesignation, evaluated bendReliefWidth and bendReliefDepth with units, "
        "square bend relief, corner construction, and all nine explicit flatPatternSettings. Attribute company choices separately from source rules. "
        "The supplied K-factor priority resolves which native development method controls; retain any listed bend-deduction discrepancy as disclosed supplier confirmation, "
        "without silently changing K or claiming both agree. Resolve outside virtual-sharp datum definitions, all panel/slot/vent/fastener coordinates, "
        "bend directions/order and through-cut details from R3. Do not mark an explicitly supplied human choice unknown. "
        "Distinguish complete CAD inputs from unperformed downstream measurements, indexed allocation, physical fit and supplier acceptance. "
        "Honor the existing R1/R3 permission for bare-sheet CAD: unresolved finish availability, color, coating thickness, hole allowance and coated fit "
        "remain disclosed downstream uncertainties, not prerequisites for bare-sheet CAD. Do not claim a finish is available or that coated fit has passed without evidence. "
        "This permission does not waive material identity or mandatory forming constraints. Evaluate the actual complete forming sequence "
        "for this part against the sourced conditions; do not impose another scenario's four-bend sequence on a two-station split-lip dock. "
        "A thin-sheet exception alone does not establish full sequence support. Unsupported or unresolved mandatory tooling remains a CAD blocker "
        "unless a later explicit company upload supplies the missing prototype criteria and defines which supplier confirmations remain downstream. "
        "Do not claim later measurements passed; actual unsupported or conflicting mandatory geometry/DFM requirements still block."
    )
    if company_capabilities:
        intent["fields"]["prompt"] += (
            " Apply the explicitly uploaded company-fabrication-capabilities-r4.md after R3. Separate company prototype criteria, "
            "fresh supplier DFM and observed native geometry into distinct assessment columns. The fictional company equipment, "
            "part-specific forming sequence, pocket/end clearances and thickness-dependent cut/web minima are human prototype inputs, never supplier facts. "
            "Evaluate all company inequalities numerically using the selected T and sourced die opening. Record tool-end access and the ordinary channel ratio "
            "before considering supplier exceptions. Complete company criteria may support exact-reviewed CAD for geometry verification while missing "
            "supplier-specific cut limits or machine acceptance remain explicitly unverified, as the actual R4 upload authorizes. "
            "Use only permissions supplied in that document; do not transfer another company's exceptions or machine setup. Known supplier hard-limit conflicts still block; "
            "company limits cannot override them or establish supplier-compatible holes/webs. Missing or failed company inputs also block. "
            "Native developed distances, outlines, relief intersections and topology are pending post-CAD verification, not missing human inputs before a model exists. "
            "Keep their measurable criteria and mandatory downstream gates; no unobserved check passes. Preserve the sourced stock/rule and all original geometry. "
            "Where the upload explicitly addresses interrupted bends, assess its full split-lip sequence and the actual unsupported-bend/relief provisions "
            "alongside die-width cautions; retain every caution and do not invent an exception or waive a known hard limit. "
            "An explicitly selected K-based company method is one nominal development basis; a separately published deduction difference remains "
            "a disclosed supplier confirmation issue when the upload permits that timing, not agreement between sources or a new dimensional tolerance. "
            "Carry every supplier uncertainty into both simulated approvals and final handoff with manufacturing_release=HOLD, "
            "supplier_acceptance=unverified and physical_fabrication=not_performed."
        )
    helpers.add_reference(sections, research_ref, intent, "supplier_research")
    helpers.add_reference(sections, material_ref, intent, "native_materials")
    helpers.add_reference(sections, image, intent, "original_concept", "reference_images")
    review = new_task("approve_intent", "Review exact manufacturing intent before CAD")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review exact human inputs, sourced capability gaps and manufacturing intent for this local integration attempt.", outputs=[],
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review",
                  "approval_binding": LOCAL_REVIEW_BINDING, "approval_destination": LOCAL_REVIEW_DESTINATION,
                  "approval_settings": {"review_task_id": review["id"]},
                  "approval_action": {"kind": "local_review", "mode": "review_only"}})
    order(intent, review, "intent exact file review")
    order(review, cad, "approved intent before native mutation")

    def bind_part(create, inspect, export_task, part_name, revision_limit):
        model_key = create["id"] + "_model"
        native_key = create["id"] + "_native"
        create_ref = bind(create,
            "Build the " + part_name + " only from the approved manufacturing intent and original uploads. "
            "Use native cad.create_sheet_metal_from_recipe, not a solid-body substitute. Read exact installed material and retain explicit source/recipe. "
            "The runtime supplies the authoritative creation path and retains indexed revisions. Use commit mode, closeAfterSave=false and visible=false. "
            "Create a genuine native flat pattern with explicit flatPatternSettings. Respect profile-relative flange edges, native pre-flange sketch spans, full-thickness flange surface offsets, and measured coordinate frames documented in the live schema. "
            "Do not omit customer cutouts, return flanges, corner reliefs or lid features to obtain a passing file. Record requested versus actual material and geometry; fail on unsupported native feature rather than substituting a fixture.",
            part_name + "-creation.json", SERVER)
        if company_capabilities:
            create["fields"]["prompt"] += (
                " Apply only the exact-reviewed R4 prototype scope in the approved intent. An explicit ready_for_geometry_verification status "
                "permits creating the first native model with complete company inputs while supplier-only acceptance is disclosed unverified. "
                "Do not promote that status to a DFM pass or override an explicit needs_input or known mandatory conflict. "
                "Pending native developed measurements belong to the following measured-design/export gates; preserve every such check."
            )
        create["fields"]["outputs"].extend([helpers.port(model_key, "cad_model"), helpers.port(native_key, "workspace_file")])
        create["fields"]["settings"]["cad"] = json.dumps({"source": "new", "native_path": output_root + "/" + part_name + ".psm",
            "native_port": native_key, "save_native": True, "policy": "indexed", "exports": []})
        helpers.add_reference(sections, intent_ref, create, "approved_intent")
        helpers.add_reference(sections, material_ref, create, "installed_materials")
        helpers.add_reference(sections, image, create, "original_concept", "reference_images")
        model_ref = create["id"] + "." + model_key
        inspect_ref = bind(inspect,
            "Inspect the exact upstream " + part_name + " without changing, rebuilding, saving or exporting it. "
            "Use cad.verify_inspection_requirements and native measurement/feature readbacks against the approved criterion table; retain all unavailable observations explicitly. "
            "Return the existing design-check JSON contract: verdict pass/revise/needs_input; checks with requirement, expected, observed, status and 1-based evidence call indices; corrections list. "
            "Pass requires actual supported observed evidence, not recipe values or prose. Preserve the existing runtime inspection gate; this is not campaign content-validity qualification.",
            part_name + "-measured-check.json", SERVER)
        if company_capabilities:
            inspect["fields"]["prompt"] += (
                " Preserve the exact-reviewed R4 assessment scope. Measure all applicable CAD geometry, topology, relief, flat-development "
                "and company setup criteria; missing observations cannot pass. Record physical tooling trials, springback and supplier acceptance "
                "separately as unverified, not as measured CAD facts. Only a distinction explicitly supplied by the uploaded policy may affect "
                "verification timing; it cannot excuse a failed or unknown applicable CAD criterion or a known supplier hard-limit conflict. "
                "Carry any selected-development discrepancy and die-width cautions into the report even when nominal CAD criteria pass."
            )
        inspect_key = inspect["id"] + "_checked_model"
        inspect["fields"]["outputs"].append(helpers.port(inspect_key, "cad_model"))
        helpers.add_reference(sections, model_ref, inspect, "model", "cad_model")
        helpers.add_reference(sections, intent_ref, inspect, "criteria")
        inspect["fields"]["settings"].update(design_check=True, max_revisions=revision_limit,
            cad=json.dumps({"source": "upstream", "from_port": inspect["id"] + "_model", "save_native": False, "exports": [], "edit_mode": "in_place"}))
        bind(export_task,
            "Read the exact accepted upstream native " + part_name + " identity and existing flat-pattern state without modifying geometry. "
            "Confirm its readback using native measurement tools. Wright will export folded STEP, persisted flat DXF and a labeled model screenshot from this same document after the task finishes. "
            "Never replace a failed flat DXF with a folded projection, STEP file, drawing, or copied input. Preserve existing native DXF integrity checks. The JPEG is only an inspection view, not a dimensioned manufacturing drawing.",
            part_name + "-export.json", SERVER)
        helpers.add_reference(sections, inspect["id"] + "." + inspect_key, export_task, "model", "cad_model")
        helpers.add_reference(sections, inspect_ref, export_task, "observed_checks")
        exports = []
        for fmt, extension in (("step", "step"), ("flat_dxf", "dxf"), ("screenshot_jpeg", "jpg")):
            key = export_task["id"] + "_" + extension
            export_task["fields"]["outputs"].append(helpers.port(key, "workspace_file"))
            exports.append({"format": fmt, "path": output_root + "/" + part_name + "." + extension, "port": key, "policy": "indexed"})
        export_task["fields"]["settings"]["cad"] = json.dumps({"source": "upstream", "from_port": export_task["id"] + "_model",
            "save_native": False, "edit_mode": "in_place", "exports": exports})
        return create_ref

    bind_part(cad, check, export, scenario_config["parts"][0], 2)
    if len(scenario_config["parts"]) == 2:
        lid = new_task("create_lid", "Create separate native removable lid")
        lid_check = new_task("inspect_lid", "Independently inspect the separate lid")
        lid_export = new_task("export_lid", "Export separate accepted lid representations")
        bind_part(lid, lid_check, lid_export, scenario_config["parts"][1], 0)
        order(export, lid, "base exported before separate lid construction")
        order(lid, lid_check, "separate lid identity")
        order(lid_check, lid_export, "checked lid before export")
        order(lid_export, preview, "both parts before supplier preview")
    destination = f"test://{args.campaign_id}/supplier/{scenario}"
    for task, kind, filename in ((preview, "supplier_upload_preview", "supplier-preview.json"), (handoff, "cart_quote_handoff", "cart-quote-handoff.json")):
        task["fields"]["settings"] = {"authoring_template": "external-action-approval", "action_kind": kind,
            "approval_binding": TEST_HANDOFF_BINDING, "approval_destination": {"kind": "integration_test", "id": destination},
            "approval_settings": {"receipt_path": output_root + "/" + filename,
                "quantity_per_part": scenario_config["quantity_per_part"], "parts": scenario_config["parts"],
                "supplier": "SendCutSend", "simulation": True, "price": "not_quoted", "delivery": "not_quoted",
                "manufacturing_release": "HOLD", "supplier_acceptance": "unverified"},
            "approval_action": {"kind": kind, "mode": "preview_only" if kind == "supplier_upload_preview" else "reviewed_handoff",
                                "order": False, "payment": False, "simulation": True}}
    final = new_task("collect_handoff", "Collect both approval receipts and final engineering handoff")
    bind(final, "Create the final engineering handoff after both exact simulated supplier gates have completed. "
         "Summarize every original requirement, unresolved issue, explicit part quantity, indexed CAD attempt, measured check and exported file. "
         "Supplier preview/cart receipts are labeled simulations, no live quotation, order or acceptance. Retain manufacturing_release=HOLD and supplier_acceptance=unverified, the actual selected stock/rule/source evidence, exact native identity and all old-versus-new input decisions. A HOLD never waives a failed or unknown mandatory DFM gate. Do not claim content correctness qualification or certification. "
         f"Call collect_artifact_manifest(operation_source_document={operation_path!r}, output_root={output_root!r}, files=[...]). "
         "Each entry has path (workspace-relative) and role (including part label). Include both actual supplier receipt JSONs, manufacturing intent and every required native PSM, STEP, DXF and inspection view using the exact indexed paths from upstream outputs. "
         f"Also include {output_root}/supplier-evidence.json and all sixteen supplier-source HTML/text files; their exact names/hashes come from the source-bound research evidence. "
         f"The source-bound operation saves actual byte counts/SHA256/role labels to {output_root}/final-artifact-manifest.json. "
         "Do not copy source inputs into engineering outputs or invent missing file entries.",
         "engineering-handoff.md", evidence_server, ("final-artifact-manifest.json",), fmt="markdown")
    helpers.add_reference(sections, operation_ref, final, "executed_operation_source")
    helpers.add_reference(sections, intent_ref, final, "approved_intent")
    helpers.add_reference(sections, export["id"] + "." + export["id"] + "_report", final, "base_exports")
    if len(scenario_config["parts"]) == 2:
        helpers.add_reference(sections, lid_export["id"] + "." + lid_export["id"] + "_report", final, "lid_exports")
    order(handoff, final, "final report only after second handoff checkpoint")
    result = helpers.render(sections)
    validate_workspace_authoring_shape(result)
    plan = compile_prompt_workflow(result)
    if any(identity not in [step.id for step in plan.steps] for identity in original_tasks):
        raise ValueError("A preserved original canonical task was lost.")
    if any(edge not in sections for edge in original_edges):
        raise ValueError("A preserved canonical revision or approval edge was changed.")
    selected = []
    for server, names in config["allowed_tools"].items():
        if server == "wright-engineering-evidence":
            server = evidence_server
        for name in names:
            tool = next((t for t in available if t["server_id"] == server and t["tool_name"] == name), None)
            if not tool:
                raise ValueError("Required workspace tool unavailable: " + server + "/" + name)
            selected.append(tool)
    expected = list(manifest["expected_outputs"])
    # The complex case must produce both parts; broad glob matching is not enough.
    for name in scenario_config["parts"]:
        for role, extension in (("native_sheet_metal", "psm"), ("folded_neutral_model", "step"), ("developed_flat_pattern", "dxf")):
            expected.append({"role": name + "_" + role, "patterns": ["**/" + name + "." + extension, "**/" + name + "-*." + extension]})
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(result, encoding="utf-8", newline="")
    report = {"schema_version": 1, "scenario_id": scenario, "attempt_id": args.attempt, "template_id": manifest["template_id"],
              "status": "prepared_not_dispatched", "source": str(target), "source_sha256": helpers.digest(result.encode()),
              "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()), "workspace_root": str(workspace), "output_root": output_root,
              "requires_template_instance_api": not bool(args.instance_source), "preserved_original_stages": original_tasks,
              "compiled_stages": [step.id for step in plan.steps], "preserved_original_edges": [s["id"] for s in original_edges],
              "input_manifest": staged, "tool_allowlist": selected, "expected_outputs": expected,
              "expected_tool_created_files": [p for s in plan.steps for p in s.expected_files],
              "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": [destination]},
              "blockers": ["Solid Edge must connect on the licensed Windows desktop; read-only probe found MK_E_UNAVAILABLE before connection",
                           "Native status response omits nullable fields required by its advertised output schema when disconnected",
                           "Exact workspace output root must be allowed by the SolidEdge server",
                           "Installed material and requested native feature/flat-pattern support require actual preflight",
                           "No native dimensioned drawing tool is exposed; JPEG views are not drawings",
                           "Selected source-bound public-reference and file-manifest tools require actual backend/gateway prerequisite evidence",
                           "Draft preparation is not engineering qualification or evidence of a completed workflow"]}
    helpers.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return {"scenario_id": scenario, "draft": str(target), "stages": len(plan.steps), "files": len(staged), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/sheet-metal-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/sheet-metal-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--campaign-id", default="081-engineering-datasets-v1")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--evidence-server-id", default="wright-engineering-evidence")
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    uri = args.api + "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session)
    with urllib.request.urlopen(uri, timeout=30) as response:
        available = json.load(response)["tools"]
    rows = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/sheet-metal-supplier-handoff").iterdir()):
        scenario = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))["scenario_id"]
        if not args.scenario or scenario == args.scenario:
            rows.append(prepare(args, directory, available))
    if not rows:
        raise ValueError("No sheet-metal scenario matched.")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
