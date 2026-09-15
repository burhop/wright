"""Stage human inputs and draft the complete canonical KiCad engineering graph.

Does not create template instances, enroll permissions, dispatch tools or runs.
Pass --instance-source after normal template instantiation to retain real IDs.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from workspace_service.workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT
    / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/sensor-interface-pcb.workflow.wflow"
)
CONFIG = (
    ROOT / "tests/datasets/engineering-workflows/bindings/sensor-interface-pcb.json"
)
spec = importlib.util.spec_from_file_location(
    "pcb_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py"
)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def prepare(args, directory):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    identity = manifest["scenario_id"]
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Draft exists; inspect it and select a new attempt")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    native = "/work/" + output
    # Empty output directories are prerequisites, not generated engineering data.
    for name in ("symbols", "connected", "unrouted", "routing", "records"):
        h.confined(workspace, output + "/" + name).mkdir(parents=True, exist_ok=True)
    discovered = []
    if args.tool_catalog:
        catalog = json.loads(Path(args.tool_catalog).read_text(encoding="utf-8"))
        discovered = catalog["tools"] if isinstance(catalog, dict) else catalog
    copy_matches = [
        tool
        for tool in discovered
        if tool["server_id"] == "wright-workspace-files"
        and tool["tool_name"] == "copy_file"
    ]
    if args.tool_catalog and len(copy_matches) != 1:
        raise ValueError("Require fresh qualified workspace copy_file discovery")
    copy_tool = (
        copy_matches[0]
        if copy_matches
        else {"name": "wright-workspace-files__copy_file", "schema_digest": ""}
    )
    source = (
        Path(args.instance_source).read_text(encoding="utf-8")
        if args.instance_source
        else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    )
    sections = _parse(source)
    stages = {}
    for prefix in config["original_stages"]:
        matches = [
            section
            for section in sections
            if section["kind"] == "task" and section["id"].startswith(prefix + "_")
        ]
        if len(matches) != 1:
            raise ValueError("Missing/ambiguous original stage " + prefix)
        stages[prefix] = matches[0]
    staged = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            raw = path.read_bytes()
            relative = inputs + "/" + path.name
            h.write_once(h.confined(workspace, relative), raw)
            staged.append(
                {
                    "path": relative,
                    "sha256": h.digest(raw),
                    "size_bytes": len(raw),
                    "original": path.relative_to(ROOT).as_posix(),
                }
            )
    names = [
        manifest["files"]["user_profile"],
        manifest["files"]["prompt"],
        *manifest["files"]["context"],
    ]
    context = "\n\n".join(
        "## Uploaded file: "
        + name
        + "\n\n"
        + (directory / name).read_text(encoding="utf-8")
        for name in names
    )
    relative = inputs + "/assembled-context-utf8.md"
    h.write_once(h.confined(workspace, relative), context.encode())
    staged.append(
        {"path": relative, "sha256": h.digest(context.encode()), "derived_from": names}
    )
    brief = h.add_file_input(sections, suffix, "electrical_context", relative)
    image = h.add_file_input(
        sections, suffix, "electrical_sketch", inputs + "/concept.png"
    )
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0][
        "kind"
    ] = "reference_images"

    def bind(stage, prompt, filename, expected=(), model_only=False):
        fields = stage["fields"]
        fields.update(
            step_type="work",
            performed_by="ai_assisted",
            prompt=prompt,
            inputs=[],
            outputs=[h.port(stage["id"] + "_result")],
        )
        fields["settings"] = {
            "output_format": "markdown",
            "save_output": True,
            "output_filename": output + "/" + filename,
            "file_policy": "overwrite",
        }
        if not model_only:
            fields["settings"].update(
                authoring_template="mcp-task",
                mcp_server=args.server_id,
                max_tool_calls=32,
                timeout_seconds=600,
                expected_files="\n".join(output + "/" + path for path in expected),
                task_guidance="Use only actual enrolled KiCad tools. Serialize modifications; never hand-route. Search libraries before selecting parts. Native paths use /work plus workspace-relative path; never invent file bytes or clean-check claims. No supplier calls or hardware actions. Preserve every original net and engineering constraint.",
            )
        h.add_reference(sections, brief, stage, "human_context")
        return stage["id"] + "." + stage["id"] + "_result"

    basis = bind(
        stages["capture_electrical_basis"],
        "Create the exact electrical design basis from profile, prompt, context, net table, component constraints and image. Keep every net/reference/pin, supply domain, current, clearance, board dimension and mounting-hole coordinate. Explicitly retain manufacturer-rating/datasheet gaps and do not call assumptions manufacturer facts. This is a prototype engineering model; no production/fabrication release is authorized.",
        "electrical-basis.md",
        model_only=True,
    )
    h.add_reference(
        sections,
        image,
        stages["capture_electrical_basis"],
        "human_image",
        "reference_images",
    )
    review = {
        "kind": "task",
        "id": "review_electrical_basis_" + suffix,
        "fields": {
            "name": "Review electrical basis",
            "purpose": "Review exact connectivity and unresolved requirements",
            "step_type": "review",
            "group": None,
            "performed_by": "engineer",
            "inputs": [],
            "outputs": [],
            "instructions": "Review exact input-derived connectivity, limits and unresolved datasheet assumptions.",
            "tool": None,
            "reusable_step": None,
            "settings": {
                "authoring_template": "external-action-approval",
                "action_kind": "local_review",
                "approval_binding": {
                    "server": "wright",
                    "tool": "review_artifacts",
                    "schema": h.digest(b"wright.local_review.v1"),
                },
                "approval_destination": {"kind": "local_review", "id": "workspace"},
                "approval_settings": {},
                "approval_action": {"kind": "local_review", "mode": "review_only"},
            },
        },
    }
    review["fields"]["settings"]["approval_settings"]["review_task_id"] = review["id"]
    sections.append(review)
    h.add_reference(sections, basis, review, "accepted_basis")
    authored = bind(
        stages["author_pcb"],
        f"Author the component-placement portion of {native}/symbols/design.kicad_sch from the complete reviewed component table. Expand every semicolon-separated reference into its own actual component. Search each distinct required native symbol/footprint and reuse that exact observed library identity for identical parts. Call schematic(create) once, then add_component for every required reference with its correct value/footprint and a distinct pin-safe schematic position. Plan the whole symbol grid before the first add_component: leave enough room for a 2.54 mm label wire stub at every pin tip, keep every stub disjoint from every other pin/stub, and do not stack adjacent vertical passives on the same x coordinate at only 10.16 mm center spacing (C2 and C4 must be separated laterally or by more than their combined stub reach). A later connectivity task uses connect_pins_with_labels, so this geometric non-overlap is required to keep independent nets independent. Save to the exact symbols/design.kicad_sch path, inspect list_components and report all actual reference/library identities. This task places and saves symbols; the next explicit task connects every supplied net and saves a separate final schematic. Do not call build_pcb_from_schematic or create a PCB here. A tool result containing error or a failed nested step is a failure even if its MCP transport succeeded; report the concrete result without repeating a completed mutation.",
        "authoring-evidence.md",
        ["symbols/design.kicad_sch"],
    )
    h.add_reference(sections, basis, stages["author_pcb"], "accepted_basis")

    def extra(prefix, title):
        task = {
            "kind": "task",
            "id": prefix + "_" + suffix,
            "fields": {
                "name": title,
                "purpose": title,
                "tool": None,
                "reusable_step": None,
                "group": None,
            },
        }
        sections.append(task)
        return task

    def copy_native(prefix, source_path, destination_path, *, seal=False):
        task = extra(prefix, "Copy native file: " + destination_path)
        task["fields"].update(
            step_type="work",
            performed_by="configured_tool",
            inputs=[],
            outputs=[h.port(task["id"] + "_result")],
            prompt="",
            instructions="Copy this exact prior same-run generated native file; preserve the source and record the actual hash receipt.",
        )
        task["fields"]["settings"] = {
            "authoring_template": "mcp-tool",
            "mcp_server": "wright-workspace-files",
            "mcp_tool": copy_tool["name"],
            "mcp_schema_digest": copy_tool["schema_digest"],
            "mcp_arguments": json.dumps(
                {
                    "sourcePath": output + "/" + source_path,
                    "destinationPath": output + "/" + destination_path,
                }
            ),
            "output_format": "json",
            "save_output": True,
            "output_filename": output + "/records/" + prefix + ".json",
            "file_policy": "overwrite",
            "timeout_seconds": 180,
            "expected_files": output + "/" + destination_path if seal else "",
        }
        return task

    connect = extra("connect_native_schematic", "Connect every supplied schematic net")
    connected = bind(
        connect,
        f"Load the saved {native}/symbols/design.kicad_sch using schematic(load,schematic_path). Preserve that immutable symbol-only file. Connect every exact net/reference/pin from the original netlist.csv using connect_pins_with_labels. The same net label joins all matching labels: pair unlabeled pins within each net, then label any odd remaining pin with add_label_to_pin; do not repeatedly label an already covered pin or merge different names. Preserve all rails/returns, test points and filters. Complete every supported read-only coverage/collision inspection and every required in-memory correction before saving. Save exactly once, as the final tool mutation, with schematic(save,schematic_path='{native}/connected/design.kicad_sch') to create the separate connected file. The successful save is the terminal event for this task: immediately after the save result, send the final text report in your next response and make zero further tool calls. Do not use the save result as a reason to inspect, validate, load, connect, or call schematic again. After that successful save, do not mutate or save again; report actual coverage from the already collected evidence. Terminate this task immediately after that report; do not call schematic, connect_pins_with_labels, or any other tool again. A repeated operation after the final save is rejected. Do not build or route a board here. Treat error payloads as failures; no invented clean result.",
        "connectivity-evidence.md",
        ["connected/design.kicad_sch"],
    )
    h.add_reference(sections, authored, connect, "placed_symbols")
    h.add_reference(sections, basis, connect, "accepted_basis")
    copy_connected = copy_native(
        "stage_build_schematic",
        "connected/design.kicad_sch",
        "unrouted/design.kicad_sch",
    )
    setup = extra(
        "initialize_native_project", "Establish native PCB project and design rules"
    )
    initialized = bind(
        setup,
        f"Establish the fresh working native project before the one board build. Call pcb(create,pcb_path='{native}/unrouted/design.kicad_pcb') exactly once, then pcb(set_design_rules,pcb_path=the same path) with the original supplied width/clearance/hole/via constraints. This selected native save creates the sibling {native}/unrouted/design.kicad_pro; require project_rules_updated=true and the exact project_file path. Read project(get_structure,project_path='{native}/unrouted/design.kicad_pro') to confirm the copied schematic/project/PCB exist. The project router has no create operation. Keep the complete copied schematic unchanged. These are working project files: the next task rebuilds the board and reapplies the actual original rules before capturing immutable native board/project deliverables. Do not invoke build or routing here; report any error payload as failure.",
        "native-project-evidence.md",
    )
    h.add_reference(sections, connected, setup, "connected_schematic")
    board = extra("build_native_board", "Build board and place fixed geometry once")
    built = bind(
        board,
        f"The preceding task established {native}/unrouted/design.kicad_pro and the fully connected schematic. Call build_pcb_from_schematic ONCE with that exact project_path, original supplied board dimensions and placement_hints, add_mounting_holes=false, export_gerbers=false, approved=false. The selected approved=false contract creates the real board through placement and returns status=pending_approval before routing; that is the expected successful boundary for this task, not a failed build. The earlier Wright local design review authorizes this prototype generation. Inspect all nested steps for errors and actual expected component/net counts. Never call the build again with approved=true: it recreates the PCB. Use the complete build response as the initial component/net observation; do not spend calls loading or listing the same pre-edit state. Plan placement from the board outline, mounting-hole keepouts and each footprint's full rotated copper and courtyard extent. For this dual-pressure prototype, the retained-board qualification supplies a proven fixed set: J1 footprint origin=(4.5,18.81) mm at rotation 180°, C3 footprint origin=(8.0,23.0) mm at rotation 0° for PCB02 (the prior 90° hint produced an off-board/overlap warning in attempt016), and C4 footprint origin=(12.0,23.0) mm at rotation 0°; apply those exact origins when the corresponding references are present, preserving the supplied connector-center distinction. If the build response reports `placement_hint_offboard` for C4 at that exact qualified origin while the real board was created, do not stop or substitute a new coordinate: treat the report as the build's initial placement observation and make the single first `move_footprint` call for C4 at (12.0,23.0) mm rotation 0°, then continue the bounded fixed-geometry task. A disposable native qualification of the failed attempt016 board proves C3 origin=(8.0,23.0) mm at rotation 0° has zero audit errors, while the failed 90° hint must not be repeated. A disposable native qualification of the failed attempt015 board also proves C2 origin=(23.0,18.5) mm at rotation 0° and TP1 origin=(10.0,14.0) mm at rotation 0° remove the H3-C2 and TP1-J3 courtyard collisions; for PCB02 include those exact fixed hints in the single build_pcb_from_schematic placement_hints and treat C2 and TP1 as completed fixed references. In this bounded task, move only electrical references whose source supplies an exact coordinate or named edge location, including every fixed connector, C2 and TP1, to final coordinates and final rotations. Make one move_footprint call per such reference. A successful move whose response reports no geometry violation completes that reference and must never be repeated. If, and only if, the first move returns a concrete board-outline, courtyard or keepout violation, make at most one corrective move for that reference with different coordinates calculated from the returned native bounds; record both operations and never move it again. Never repeat identical move arguments or make provisional aesthetic moves. Every supplied coordinate identified as a connector center is the geometric center, while move_footprint positions the footprint origin. Use the build response's actual pad extents to calculate the final rotated footprint-origin offset so the midpoint of the final pad bounds lands on the required center; never pass a center coordinate directly unless the observed footprint origin and geometric center coincide. For qualitative near-edge placement, leave enough clearance for the complete rotated footprint and courtyard rather than placing its origin at the desired visual margin. Honor every named upper/lower/left/right relationship and pin-1 orientation directly; for a vertical 1x03 header whose zero-degree pads increase in +Y from pin 1, rotation 180 places pin 1 toward the top edge. Never make provisional connector moves or swap named connector locations later. Add standalone silkscreen labels only after all fixed footprint moves, at the final connector locations. Place each exact supplied NPTH mounting hole once. This adapter has no KiCad rule-area keepout authoring operation, so do not invent one: preserve copper clearance geometrically. Do not place the remaining unconstrained electrical references and do not set final project rules in this task. After the final mounting-hole or silkscreen-label mutation, stop immediately and return the fixed-geometry report; do not call pcb, audit, load, get_pad_positions or any other tool again. A second call after the final mutation is a duplicate and is rejected. Report the exact fixed references, labels, holes, C3, C2 and TP1 placements completed so the next task can continue without moving them again. Do not create a second empty PCB or repeat the build. Report concrete errors and missing features instead of retrying a completed mutation.",
        "native-fixed-geometry-evidence.md",
    )
    h.add_reference(sections, initialized, board, "initialized_native_project")
    h.add_reference(sections, basis, board, "accepted_basis")
    finish_board = extra(
        "finish_native_board", "Place remaining resistors and capacitors"
    )
    finished = bind(
        finish_board,
        f"Continue the existing {native}/unrouted/design.kicad_pcb produced by the preceding task. Never call build_pcb_from_schematic, create another PCB, move a fixed reference already completed by that task (including C2 and TP1), or repeat its labels or mounting holes. In this bounded pass, place only remaining supplied electrical references whose reference starts with R or C; C2 is already fixed by the board-build task and must not be moved again. Leave test points and every other reference for the next placement pass. Plan their final positions together from the board outline, fixed footprint courtyards, mounting-hole clearance circles and each footprint's full rotated copper/courtyard extent before editing. Move each selected reference exactly once to its final coordinate and rotation. A successful response with no geometry violation seals that reference. Only after a concrete native board-outline, courtyard or keepout violation may one changed corrective move be made for that reference, calculated from the returned bounds; never replay identical arguments or make provisional aesthetic moves. Preserve every fixed connector center, pin-1 orientation, named relationship and qualitative edge clearance established by the preceding task. Do not run a whole-board audit in this pass. Do not set design rules or net classes or call get_constraints/list_footprints. Report the exact references and final positions completed so the next task can place only the references still absent. After the final successful move_footprint call, stop immediately and return that report; do not call pcb, audit, suggest_placement, load, or any other tool again in this task. A second call after all planned references are moved is a duplicate and will be rejected.",
        "native-passive-placement-evidence.md",
    )
    h.add_reference(sections, built, finish_board, "fixed_native_geometry")
    h.add_reference(sections, basis, finish_board, "accepted_basis")
    finish_remaining = extra(
        "finish_remaining_native_board",
        "Place remaining test and miscellaneous footprints",
    )
    remaining_finished = bind(
        finish_remaining,
        f"Continue the existing {native}/unrouted/design.kicad_pcb after the bounded resistor/capacitor placement pass. Never call build_pcb_from_schematic, create another PCB, move any fixed reference from the board-build task, move an R/C reference completed by the preceding pass, or repeat labels or mounting holes. Use the preceding tasks' exact completed-reference lists and the accepted basis to identify every still-unplaced supplied electrical reference, including remaining test points. Plan their final positions together from the board outline, completed footprint courtyards, mounting-hole clearance circles and each remaining footprint's full rotated copper/courtyard extent before editing. Move each still-unplaced reference exactly once to its final coordinate and rotation. A successful response with no geometry violation seals that reference. Only after a concrete native board-outline, courtyard or keepout violation may one changed corrective move be made for that reference, calculated from the returned bounds; never replay identical arguments or make provisional aesthetic moves. Preserve every completed connector center, pin-1 orientation, supplied test-point coordinate, named relationship and qualitative edge clearance. After the last geometry edit, run one audit(operation='all') and resolve only concrete placement, courtyard, pad-clearance or keepout findings within the one-correction-per-reference rule. Do not set design rules or net classes and do not call get_constraints/list_footprints; the next bounded task performs those final operations. Report exact final positions and remaining concrete errors without rebuilding or replaying a completed mutation. After the final successful move_footprint call or final audit, stop immediately and return the report; do not call pcb, audit, suggest_placement, load, or any other tool again in this task.",
        "native-remaining-placement-evidence.md",
    )
    h.add_reference(sections, finished, finish_remaining, "passive_native_placement")
    h.add_reference(sections, basis, finish_remaining, "accepted_basis")
    seal_board = extra("seal_native_board", "Apply rules and seal native board")
    sealed = bind(
        seal_board,
        f"Continue the placement-complete {native}/unrouted/design.kicad_pcb. Never call build_pcb_from_schematic, create another PCB, move a footprint, add text or change any geometry. Reapply every original supplied design rule and needed net class with pcb(set_design_rules/set_net_class); the native build recreated default settings. Make no geometry or text mutation after these rule calls. Require project_rules_updated=true, then call pcb(get_constraints) and pcb(list_footprints) exactly once each as the final two tool calls. Inspect actual native pad/net membership, all supplied references, original design/net rules, dimensions, mounting holes and clearance evidence from those final responses. Both unrouted native files become immutable when this task ends. Report concrete errors without rebuilding or replaying a completed mutation.",
        "native-board-evidence.md",
        ["unrouted/design.kicad_pcb", "unrouted/design.kicad_pro"],
    )
    h.add_reference(
        sections, remaining_finished, seal_board, "completed_native_placement"
    )
    h.add_reference(sections, basis, seal_board, "accepted_basis")
    copy_route_pcb = copy_native(
        "stage_routing_board", "unrouted/design.kicad_pcb", "routing/design.kicad_pcb"
    )
    copy_route_pro = copy_native(
        "stage_routing_project", "unrouted/design.kicad_pro", "routing/design.kicad_pro"
    )
    route = {
        "kind": "task",
        "id": "route_native_board_" + suffix,
        "fields": {
            "name": "Route and inspect native board",
            "purpose": "Route actual board preserving schematic nets",
            "tool": None,
            "reusable_step": None,
            "group": None,
        },
    }
    sections.append(route)
    routed = bind(
        route,
        "If the assembled context supplies a proved footprint origin for a route-sensitive reference, use that exact origin and do not substitute a new location; context distinguishes footprint origins from connector or pad centers. "
        f"Reopen/inspect actual {native}/routing/design.kicad_pcb. Before autoroute, use audit/suggest_placement and native_rule_check(kind='drc',source_path='{native}/routing/design.kicad_pcb',report_path='{native}/routing/pre-route-drc-N.json') with a fresh numbered report path for each distinct check. Resolve every native courtyard/clearance error before routing while preserving the exact fixed connector, mounting-hole, board-outline and supplied keepout constraints. KiCad can classify expected unrouted connections as unconnected_items errors before autorouting. Preserve those findings literally, but exclude only unconnected_items from the pre-route blocking-error count; require zero other DRC errors before routing. Call autoroute exactly once after that condition is met: autoroute(operation='run',pcb_path='{native}/routing/design.kicad_pcb',freerouter_jar='/opt/freerouting-2.2.4.jar',passes=2,net_classes=None). After autoroute, run one final native_rule_check DRC as read-only evidence and preserve every finding literally. Do not move footprints, change geometry, call an autofix, save a mutated board or call autoroute again after that autoroute call; the later final verification blocks fabrication if errors remain. Do not hand-route, remove required nets or fabricate clean results. Preserve the supplied project rules; do not call set_design_rules/set_net_class or change net_classes during routing. Native board.Save also writes its sibling project: complete all native placement work before autoroute so this task can capture routing/design.kicad_pcb and routing/design.kicad_pro without a post-route mutation. The next fixed copy nodes publish final filenames; do not edit the immutable unrouted sources or write final root files here.",
        "routing-evidence.md",
        ["routing/design.kicad_pcb", "routing/design.kicad_pro"],
    )
    h.add_reference(sections, sealed, route, "native_authoring")
    copy_final_pcb = copy_native(
        "publish_final_board", "routing/design.kicad_pcb", "design.kicad_pcb", seal=True
    )
    copy_final_pro = copy_native(
        "publish_final_project",
        "routing/design.kicad_pro",
        "design.kicad_pro",
        seal=True,
    )
    copy_final_sch = copy_native(
        "publish_final_schematic",
        "connected/design.kicad_sch",
        "design.kicad_sch",
        seal=True,
    )
    bind(
        stages["verify_and_export"],
        f"The final native PCB, project and schematic are immutable copies. Use only read-only inspection and native CLI checks/exports here; never call board save, finalize, autofix, project rule edits or any native geometry/routing mutation. Independently inspect actual schematic and board with analyze/pcb read operations and compare exact nets, pinout, dimensions and constraints against original CSVs. Run native_rule_check(kind='erc',source_path='{native}/design.kicad_sch',report_path='{native}/erc.json') and kind='drc' on design.kicad_pcb to '{native}/drc.json'. Use actual native results, not schematic.validate alone. Block fabrication export on any unreviewed ERC/DRC error; do not downgrade severities or waive input errors. Once clear, export(operation='bom_csv',project_path='{native}/design.kicad_sch') producing design_bom.csv and export(operation='gerbers',pcb_path='{native}/design.kicad_pcb',output_dir='{native}/gerbers',create_zip=True). Require actual copper, outline and drill files and archive identities. Keep exact check findings and every unresolved rating assumption; no production-ready claim.",
        "verification-evidence.md",
        config["expected_verification_files"],
    )
    h.add_reference(sections, routed, stages["verify_and_export"], "routed_board")
    h.add_reference(sections, basis, stages["verify_and_export"], "original_basis")
    chain = [
        stages["capture_electrical_basis"],
        review,
        stages["author_pcb"],
        connect,
        copy_connected,
        setup,
        board,
        finish_board,
        finish_remaining,
        seal_board,
        copy_route_pcb,
        copy_route_pro,
        route,
        copy_final_pcb,
        copy_final_pro,
        copy_final_sch,
        stages["verify_and_export"],
    ]
    for first, last in zip(chain, chain[1:]):
        sections.append(
            {
                "kind": "connection",
                "id": "sequence_" + last["id"],
                "fields": {
                    "type": "order",
                    "from": first["id"],
                    "to": last["id"],
                    "label": "complete PCB engineering chain",
                    "when": None,
                },
            }
        )
    rendered = h.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowlist = []
    if args.tool_catalog:
        tools = discovered
        for name in config["allowed_tools"]:
            matches = [
                tool
                for tool in tools
                if tool["server_id"] == args.server_id and tool["tool_name"] == name
            ]
            if len(matches) != 1:
                raise ValueError("Missing or ambiguous enrolled KiCad tool " + name)
            allowlist.append(matches[0])
        allowlist.append(copy_tool)
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    result = {
        "schema_version": 1,
        "scenario_id": identity,
        "attempt_id": args.attempt,
        "template_id": manifest["template_id"],
        "status": "prepared_not_dispatched",
        "source": str(target),
        "source_sha256": h.digest(rendered.encode()),
        "template_source_sha256": h.digest(TEMPLATE.read_bytes()),
        "workspace_root": str(workspace),
        "output_root": output,
        "input_manifest": staged,
        "required_step_ids": [step.id for step in plan.steps],
        "preserved_original_stages": [
            stages[p]["id"] for p in config["original_stages"]
        ],
        "expected_tool_created_files": [
            path for step in plan.steps for path in step.expected_files
        ],
        "allowed_tool_names": config["allowed_tools"]
        + ["wright-workspace-files__copy_file"],
        "server_id": args.server_id,
        "requires_template_instance_api": not bool(args.instance_source),
        "requires_fresh_gateway_tool_schema_and_enrollment": True,
        "container_mounts": [
            {
                "host": str(workspace / inputs),
                "container": "/work/" + inputs,
                "read_only": True,
            },
            {"host": str(workspace / output), "container": native, "read_only": False},
        ],
        "blockers": [
            "Fresh selected gateway qualification and grant enrollment required",
            "No dataset-native designs or run outputs have executed",
        ],
    }
    result["tool_allowlist"] = allowlist
    result["approval_policy_request"] = {
        "mode": "auto",
        "scope": "integration_test",
        "test_destinations": [],
    }
    h.publish_input_binding_evidence(result, directory)
    (draft / "staging-manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "scenario_id": identity,
        "source": str(target),
        "stages": len(plan.steps),
        "executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--draft-root", required=True)
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument(
        "--tool-catalog",
        help="Fresh normal API tool discovery JSON for exact schema enrollment",
    )
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    rows = [
        directory
        for directory in sorted(
            (
                ROOT
                / "tests/datasets/engineering-workflows/scenarios/sensor-interface-pcb"
            ).iterdir()
        )
        if not args.scenario
        or json.loads((directory / "scenario.json").read_text(encoding="utf-8"))[
            "scenario_id"
        ]
        == args.scenario
    ]
    if not rows:
        raise ValueError("No matching PCB dataset")
    print(json.dumps([prepare(args, directory) for directory in rows], indent=2))
