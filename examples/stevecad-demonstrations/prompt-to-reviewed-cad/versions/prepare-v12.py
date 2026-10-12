"""Prepare one reusable source; the runtime executes it with per-run prompt values."""

from pathlib import Path
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
for package in (ROOT / "packages").iterdir():
    if (package / "src").is_dir():
        sys.path.insert(0, str(package / "src"))
spec = importlib.util.spec_from_file_location(
    "bindings", ROOT / "scripts/engineering_campaign_binding_helpers.py"
)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
from agent_adapters.workflow_instructions import load_default_workflow_instructions  # noqa: E402
from workspace_service.workflow_instruction_settings import (  # noqa: E402
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_source_execution import (  # noqa: E402
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)

HERE = Path(__file__).resolve().parent
OUT = "design-reviews/{{wright.run_id}}"


def prepare():
    sections = [
        {
            "kind": "workflow",
            "id": "prompt_to_reviewed_cad",
            "fields": {
                "name": "Prompt to reviewed CAD",
                "purpose": "Specify, test, build, inspect and present a design in one reusable process.",
                "discipline": "mechanical",
                "reviewed_ai_suggestions": True,
            },
        }
    ]
    sections.append(
        {
            "kind": "input",
            "id": "design_prompt",
            "fields": {
                "name": "1. What should we build?",
                "purpose": "Change this prompt between runs.",
                "step_type": "work",
                "provided_by": "engineer",
                "group": None,
                "inputs": [],
                "outputs": [h.port("prompt")],
                "instructions": "Describe the design and requirements.",
                "settings": {
                    "input_mode": "text",
                    "input_text": (HERE / "prompts/01-drilled-block.txt").read_text(),
                },
                "tool": None,
                "reusable_step": None,
            },
        }
    )

    def task(key, title, prompt, fmt="markdown", **settings):
        settings = {
            "authoring_template": "ai-prompt",
            "output_format": fmt,
            "save_output": True,
            "output_filename": OUT
            + "/"
            + key
            + {"markdown": ".md", "json": ".json", "html": ".html", "text": ".txt"}[
                fmt
            ],
            "file_policy": "indexed",
            "run_path_template": "wright.run-path/1",
            **settings,
        }
        node = {
            "kind": "task",
            "id": key,
            "fields": {
                "name": title,
                "purpose": title,
                "step_type": "work",
                "performed_by": "ai_assisted",
                "group": None,
                "inputs": [],
                "outputs": [h.port(key + "_response")],
                "prompt": prompt,
                "settings": settings,
                "tool": None,
                "reusable_step": None,
            },
        }
        sections.append(node)
        return node

    def connect(source, node, key, kind="engineering_document"):
        producer, port = source.split(".")
        if port in {"response", "image"}:
            source = producer + "." + producer + "_" + port
        key = node["id"] + "_" + key
        node["fields"]["inputs"].append(h.port(key, kind))
        sections.append(
            {
                "kind": "connection",
                "id": "to_" + node["id"] + "_" + key,
                "fields": {
                    "type": "item",
                    "from": source,
                    "to": node["id"] + "." + key,
                    "label": key.replace("_", " "),
                    "when": None,
                },
            }
        )

    design = task(
        "design_document",
        "2. Specify the engineering design",
        "Write a complete, concise engineering design document in at most 2600 words from the connected user prompt. "
        "Keep all supplied numerical constraints. Use stable requirement IDs R01, R02, etc. "
        "Specify geometry, dimensions, units, coordinate frame, feature locations, part/assembly structure, "
        "appearance, interfaces and acceptance tolerances. Distinguish supplied requirements from any "
        "reasonable explicitly recorded design choices. Name the exact component, interface or assembly subset "
        "for each bound or count, and distinguish local coordinates from assembled world coordinates. "
        "A stationary footprint is measured on the stationary group, not the arm's complete reach envelope. "
        "Assign each requirement its responsible stage: "
        "CAD creation, geometric validation, presentation rendering, or final review. Presentation-only "
        "appearance belongs to rendering; do not require a physical CAD material assignment for it. "
        "Do not turn a scope exclusion (for example no mechanical-property claim) into a new requirement "
        "to prove zero material assignments. Only supplied requirements are mandatory; other choices must "
        "remain identified assumptions. Presentation fidelity means visual agreement in visible features, "
        "camera and appearance, not identical pixels or a new numerical geometry tolerance for an image. "
        "Include a dimension/feature table and analytical "
        "checks where applicable. This is a specification before construction: never claim the CAD or tests "
        "already exist. Treat supplied modeling hints as implementation guidance rather than mandatory "
        "construction-history acceptance tests. For assemblies include a BOM, assembly sequence, joint "
        "ranges, printing assumptions and export requirements when requested. Scope claims to the "
        "requested digital work. Output Markdown, not a code fence.",
    )
    connect("design_prompt.prompt", design, "design_prompt")
    plan = task(
        "test_plan",
        "3. Define the tests before building",
        "Create a compact test plan in at most 2200 words for the connected design document. Do not repeat its prose. For every requirement ID give the "
        "expected value, units, tolerance, numerical comparison and actual geometric observation needed. "
        "Preserve each test's exact named subject, subset, coordinate frame and count; do not apply a subset "
        "bound to the whole assembly or invent extra supports/fasteners beyond the specification. "
        "Include dimensions, solid/component counts, feature counts/positions/axes/depths and volume "
        "where specified; add interfaces/clearances/motion checks when the design requires them. "
        "Do not invent inspection capabilities or accept source code as proof of generated geometry. "
        "Missing evidence must be UNVERIFIED, measured noncompliance FAIL. Include a traceability table "
        "and required isometric/top/front captures. Assign each test its evaluation stage. The CAD inspection "
        "checks geometry and captures only. Rendering/appearance and final-document tests are deferred to "
        "the final review, after those outputs exist; they are not failures during CAD inspection. "
        "A final visual comparison can check visible feature count, silhouette, orientation and appearance; "
        "it must not claim metrical verification from pixels. This plan precedes CAD creation and cannot be weakened "
        "later to obtain a pass. Output Markdown.",
    )
    connect("design_document.response", plan, "design_document")
    build_tools = [
        "list_skills",
        "read_skill",
        "api_reference",
        "list_designs",
        "read_design",
        "write_design",
        "generate_model",
        "create_component",
        "link_design",
        "edit_design",
    ]
    build = task(
        "create_design",
        "4. Build the design in SteveCAD",
        "Use the engineering design document to create a NEW editable SteveCAD document for this run. "
        "If the supplied prompt explicitly identifies a previously created document/revision/build for "
        "this exercise's recovery, reconcile that exact document instead of creating a duplicate: read its "
        "source/current revision, compare with the supplied design, then generate or inspect the existing "
        "revision. Report its original identity honestly. At most one correction to this explicitly "
        "identified exercise document is permitted after a confirmed feature error or measured mismatch. "
        "Your deliverable is the generated geometry and exact document receipt. Geometric validation, "
        "CAD screenshots, presentation rendering and the review are separate downstream tasks. "
        "Do not treat those later tasks as prerequisites for completing this CAD receipt. Do not call "
        "Model.material by inventing a physical material just to tint a body. When the design document "
        "declares a material or a labeled reference-material assumption, read the discovered materials "
        "skill and assign it with the specified native finish/color before returning the component. "
        "Record unknown material IDs and do not claim physical mass or properties from an envelope. "
        "Use the name Wright reviewed design {{wright.run_id}}. Call api_reference without a name, then "
        "read the exact method references needed before writing source; avoid fetching an entire class "
        "when a few method signatures suffice. Single-part modeling "
        "does not require a named skill. For an assembly or specialized capability, call list_skills and "
        "read only exact skill names actually returned. Do not invent skill names or edit an existing user document. "
        "Use the documented Model/Component/Design API and named editable features; prefer Model.hole "
        "for holes so native geometric inspection can identify them. Use valid lowercase feature IDs, "
        "separate from requirement IDs. Do not assume a face's sketch origin is its centroid; use the "
        "documented or supplied coordinate convention. Use as few calls as practical; "
        "batch the initial source in write_design. Generate the saved exact revision. You may correct "
        "your own new document at most once after an explicit failed build or measured mismatch: read its "
        "current source/revision and use one uniquely matching full fragment in edit_design, or one "
        "revision-checked write_design batch for the explicitly identified owned multi-file document. "
        "A batch preserves all unaffected files and records every corrected file; it is one correction, "
        "not authority for an unbounded rewrite loop. Then generate "
        "the new revision. A timeout or "
        "queued build is not a completed design. The saved reconciliation contract permits at most four "
        "same-argument observations of generate_model while its exact receipt is queued/running; this "
        "joins the documented existing build and never authorizes another document or revision. "
        "On every generate_model request include document_id, revision, branch=null, download=null "
        "and route=false explicitly so the observation matches the accepted contract. "
        "Inspect component feature errors as well as the top-level build status. For an assembly, verify "
        "every required moving instance belongs to the correct connected rigid/joint group; do not leave "
        "motor housings, horns or retaining hardware independently grounded. Declare and execute "
        "required fit/animation checks in the source; a named animation with check=False is not a "
        "performed collision test. An open semicircular groove is not a closed through pivot bore. "
        "Preserve its document/build identities and report the "
        "actual condition without creating duplicate designs or replaying uncertain mutations. "
        "Do not request one-time download credentials. On success return a JSON object containing "
        "document_id, revision, build_id, document_url, source_code, document_kind, generated_measurements "
        "and the names of the created features/components. Include source_files for a multi-file design "
        "and actual kinematics/fit/print metadata when available. Preserve supplied requirements.",
        "json",
        authoring_template="mcp-task",
        mcp_server="stevecad-mcp",
        mcp_task_tools=build_tools,
        max_tool_calls=32,
        timeout_seconds=600,
        mcp_context_budget_bytes=400_000,
        mcp_reconciliation_contracts=json.dumps(
            {
                "generate_model": {
                    "pending_status_path": ["model", "status"],
                    "pending_status_values": ["queued", "running"],
                    "terminal_status_values": ["succeeded", "failed", "cancelled"],
                    "receipt_path": ["model", "id"],
                    "argument_bindings": {
                        "document_id": ["document", "id"],
                        "revision": ["document", "revision"],
                    },
                    "fixed_arguments": {
                        "branch": None,
                        "download": None,
                        "route": False,
                    },
                    "max_polls": 4,
                }
            }
        ),
    )
    connect("design_document.response", build, "design_document")
    sections.append(
        {
            "kind": "connection",
            "id": "plan_before_build",
            "fields": {
                "type": "order",
                "from": "test_plan",
                "to": "create_design",
                "label": "Plan tests before CAD creation",
                "when": None,
            },
        }
    )
    inspection_tools = [
        "read_design",
        "inspect_model",
        "api_reference",
        "list_skills",
        "read_skill",
    ]
    check = task(
        "validate_design",
        "5. Validate the actual CAD and capture three views",
        "Inspect only the exact document/revision/build from the connected creation result. "
        "Read the document to confirm its revision. Apply the connected pre-existing test plan without "
        "changing requirements. Separate observations from presentation captures. First call inspect_model "
        'with view=null and checks=["machining"] to obtain actual B-rep holes/round faces and positions. '
        "Then capture view=isometric, top and front, exactly once each, with checks=[]. "
        "Use actual numeric bounds, solids, volumes, hole/round-face diameter, "
        "axis, at_mm and length_mm to evaluate the relevant requirements. Do not infer dimensions from "
        "pixels or treat written source as measured geometry. Record every measured value, tolerance, "
        "comparison and evidence location. Mark missing evidence UNVERIFIED, not PASS. "
        "Evaluate only requirements assigned to CAD geometry and CAD captures in this stage. Return "
        "presentation/rendering and final-review requirements separately in deferred_tests with their "
        "planned evaluation stage; they must not make the CAD overall_status FAIL or UNVERIFIED simply "
        "because downstream work has not run. Do not judge studio appearance from CAD colors. "
        "For assemblies or printing, discover and read the exact relevant skills and inspect the "
        "declared fit/interference, joint/animation or dfam checks. Read exact-revision built kinematics "
        "and fit/animation results from read_design before requesting another computation. Reuse those "
        "actual results when they already cover the declared tests, citing their bounded sampling; "
        "do not infer continuous collision freedom. These additional numeric checks "
        "use view=null so each named capture still has one unambiguous response. Never edit the design "
        "here. Report unfinished checks and scope gaps honestly. "
        "The runtime saves declared returned images; you need not create local files. "
        "Return JSON with document_id, revision, build_id, observations (complete numerical measurement "
        "objects), tests [{requirement_id,expected,actual,tolerance,status,evidence}], "
        "overall_status, deferred_tests and unresolved_findings. No human acceptance or certification is implied.",
        "json",
        authoring_template="mcp-task",
        mcp_server="stevecad-mcp",
        mcp_task_tools=inspection_tools,
        max_tool_calls=16,
        timeout_seconds=600,
        mcp_context_budget_bytes=400_000,
    )
    connect("design_document.response", check, "design_document")
    connect("test_plan.response", check, "test_plan")
    connect("create_design.response", check, "created_design")
    paths = {
        view: OUT + "/cad-" + view + ".png" for view in ("isometric", "top", "front")
    }
    check["fields"]["outputs"] += [h.port(view, "workspace_file") for view in paths]
    check["fields"]["settings"].update(
        expected_files="\n".join(paths.values()),
        expected_file_ports=paths,
        mcp_image_outputs=json.dumps(
            {
                view: {
                    "tool": "inspect_model",
                    "arguments": {"view": view},
                    "image_index": 0,
                }
                for view in paths
            }
        ),
    )
    renders = []
    for view in paths:
        key = "render_" + view
        image_path = OUT + "/" + key + ".png"
        node = task(
            key,
            "6. Render " + view,
            "Create an ultrarealistic studio product rendering by editing the connected ACTUAL CAD "
            + view
            + " "
            "capture. Preserve its camera orientation, silhouette, proportions, hole count, positions and "
            "all visible geometry exactly. Use the appearance in the engineering design document, a neutral "
            "studio background, physically plausible lighting and contact shadows. Remove CAD UI/grid/axes "
            "from the presentation. Do not add features, hardware, labels, dimensions or branding. "
            "Apply colors only to the existing surfaces. Keep reference envelopes as their existing simple "
            "geometry; do not turn an exposed board into a covered housing or invent detailed purchased hardware. "
            "This is a presentation image, not measurement evidence. Output one PNG.",
            "text",
            save_output=False,
            expected_files=image_path,
            expected_file_ports={key + "_image": image_path},
            image_output=json.dumps(
                {"format": "png", "path": image_path, "port": key + "_image"}
            ),
        )
        node["fields"]["outputs"] = [h.port(key + "_image", "workspace_file")]
        connect("validate_design." + view, node, "cad_capture", "workspace_file")
        connect("design_document.response", node, "design_document")
        renders.append((key, view))
    report = task(
        "design_review",
        "7. Produce the illustrated design review",
        "Produce a compact self-contained HTML design review in at most 1500 words for the connected exact design and test "
        "results. Include design intent, dimensions and feature table, complete requirement-by-requirement "
        "test results, actual measured values, unresolved findings and links to the editable SteveCAD "
        "document/revision. Include the three actual CAD captures and the three realistic renderings "
        "in clearly captioned separate sections. Use img src filenames cad-isometric.png, cad-top.png, "
        "cad-front.png, render_isometric.png, render_top.png and render_front.png, which are siblings of "
        "this document. Show all three captured views and all three presentation views. Preserve actual "
        "CAD FAIL and UNVERIFIED findings prominently. Now evaluate the deferred presentation tests "
        "using the supplied image pairs: record specific visual observations of feature count, silhouette, "
        "camera orientation and requested appearance. Evaluate final-document completeness against the "
        "actual outputs. Do not carry a merely deferred earlier-stage test as a failure after evaluating "
        "its now-available evidence. Do not claim exact dimensional or pixel identity from visual inspection. "
        "If an image is unavailable for visual inspection, mark that check UNVERIFIED. A rendered image "
        "never proves a geometric requirement. Distinguish measured geometry from qualitative image checks. "
        "State that the report records a digital design review and does not record human acceptance. "
        "Use clean engineering typography and compact tables, no JavaScript or external assets. "
        "Keep long IDs and evidence paths wrapped (overflow-wrap:anywhere); constrain tables and "
        "images to the page width. Do not add an exact B-rep equivalence requirement for presentation "
        "images when the test plan specifies qualitative visible-feature comparison. "
        "Return complete HTML beginning with <!doctype html>.",
        "html",
    )
    for key in ("design_document", "test_plan", "create_design", "validate_design"):
        connect(key + ".response", report, key)
    for view in paths:
        connect("validate_design." + view, report, "cad_" + view, "workspace_file")
    for key, view in renders:
        connect(key + ".image", report, key, "workspace_file")
    for section in sections:
        if section["kind"] == "task" and not section["fields"]["settings"].get(
            "image_output"
        ):
            outputs = [port["key"] for port in section["fields"]["outputs"]]
            section["fields"]["prompt"] += (
                "\nEnvelope identifiers: if you record a new assumption, affected_outputs must use "
                "these declared output IDs: "
                + ", ".join(outputs)
                + ". Requirement IDs such as R01 "
                "belong in the document and test table, not affected_outputs. Preserve upstream "
                "assumptions as cited design choices; do not reissue them as new assumptions for this step."
            )
    profile = load_default_workflow_instructions().model_copy(deep=True)
    profile = profile.model_copy(
        update={
            "policy": profile.policy.model_copy(
                update={"assumption_policy": "document_reasonable"}
            )
        }
    )
    source = materialize_new_workflow_instructions(h.render(sections), profile)
    validate_workspace_authoring_shape(source)
    compiled = compile_prompt_workflow(source)
    return source, {
        "logical_stages": 7,
        "execution_tasks": len(compiled.steps),
        "input_id": "design_prompt",
        "sha256": h.digest(source.encode()),
        "status": "prepared_not_executed",
    }


if __name__ == "__main__":
    source, summary = prepare()
    destination = HERE / "prompt-to-reviewed-cad.workflow.wflow"
    destination.write_text(source, encoding="utf-8")
    print(json.dumps(summary, indent=2))
