"""Prepare the general native-render revision using existing provider bindings.

This authors accepted source. Wright's existing runtime executes every step.
The preceding v13 source supplies unchanged instruction bodies and CAD policy.
"""

import json
from pathlib import Path
from prepare import h, compile_prompt_workflow, validate_workspace_authoring_shape

HERE = Path(__file__).resolve().parent
RUN = "{{wright.run_id}}"
FILES = "render-proofs/native-chain-001/automatic-transfer-001/" + RUN
VIEWS = "render-proofs/native-chain-001/renders/" + RUN
TOOLS = json.loads((HERE / "native-render-bindings.json").read_bytes())
USER_PROMPT = "Create three ultrarealistic renderings of the design starting with a screen capture of the part in different orientations. Use the actual CAD surfaces, preserve all geometry and include the results in the design review."


def parse(source):
    sections = []
    for line in source.splitlines():
        if not line.strip() or line == "end":
            continue
        if not line.startswith(" "):
            kind, key = line.split(" ", 1)
            sections.append({"kind": kind, "id": key, "fields": {}})
        else:
            key, value = line.strip().split(":", 1)
            sections[-1]["fields"][key] = json.loads(value)
    return sections


def prepare():
    sections = parse(
        (HERE / "prompt-to-reviewed-cad.workflow.wflow").read_text(encoding="utf8")
    )
    remove = {"render_isometric", "render_top", "render_front"}
    sections = [
        s
        for s in sections
        if s["id"] not in remove
        and not (
            s["kind"] == "connection"
            and any(s["fields"][p].split(".")[0] in remove for p in ("from", "to"))
        )
    ]
    for s in sections:
        if s["kind"] == "task":
            settings = s["fields"]["settings"]
            for k in ["output_filename", "expected_files"]:
                if k in settings:
                    settings[k] = settings[k].replace("design-reviews/" + RUN, VIEWS)
            if "expected_file_ports" in settings:
                settings["expected_file_ports"] = {
                    k: v.replace("design-reviews/" + RUN, VIEWS)
                    for k, v in settings["expected_file_ports"].items()
                }
    by_id = {s["id"]: s for s in sections}
    by_id["design_document"]["fields"]["prompt"] += (
        "\nKeep detail proportional to the design: a single simple part normally "
        "needs at most 650 words and compact dimension/requirement tables; complex "
        "assemblies may use the full allowance. Preserve every supplied constraint. "
        "Presentation-only finish/color requirements apply to the three derived "
        "studio renderings. The three original CAD captures are geometric inspection "
        "evidence with provider display colors; do not invent an acceptance test "
        "requiring those captures to have the rendering finish, unless the user "
        "explicitly requires CAD viewport colors. Record that distinction before "
        "construction. This qualified native presentation uses the provider's "
        "isometric convention from (+X,-Y,+Z), top from +Z, and front from -Y. "
        "Do not invent a different camera convention when the user only names "
        "those views; preserve any explicitly requested alternative as a capability "
        "requirement, rather than silently replacing it."
    )
    by_id["test_plan"]["fields"]["prompt"] += (
        "\nUse the connected original design prompt to verify requirement provenance "
        "before construction. Keep a simple single-part plan to about 600 words, "
        "using concise tables while preserving all values, tolerances and methods. "
        "Do not promote a documented presentation choice into a new supplied "
        "requirement. Evaluate presentation-only finish on the three studio renders, "
        "and original CAD captures for geometric view evidence, unless the original "
        "prompt explicitly requires a CAD display finish. Keep supplied geometry "
        "requirements intact; flag any specification conflict explicitly."
    )
    by_id["create_design"]["fields"]["prompt"] += (
        "\nFor a Z-directed through hole in a box that starts at Z=0, anchor Model.hole "
        "to the actual top face of the target body using a STRING selector, for "
        'example on="block.top", not a Python attribute and not the '
        "global XY plane at the bottom. Specify the full known thickness as depth "
        "and verify the returned volume. Use the supplied coordinate convention. "
        "The saved write/edit receipt and successful generate_model response already "
        "provide the current revision, built geometry and feature status. Do not make "
        "a redundant read_design call after generation. Reserve read_design for the "
        "explicit recovery case or revision-safe correction. The selected provider "
        "does not declare repeatability for read_design, so Wright will reject a "
        "duplicate completed call within this task. Do not vary arguments to evade "
        "that guard. Validation independently reads the document in its own stage."
        "\nVerified basic API pattern, with dimensions/locations replaced by this "
        "design's actual specified values:\n"
        'model = Model("part")\n'
        'model.box("stock", length=L, width=W, height=H, at=(0,0,0), centered=False)\n'
        'model.hole("bore", on="stock.top", points=[(x,y)], diameter=d, depth=H, kind="simple")\n'
        "result = model.result()\n"
        "The box method returns None, and Model.feature(...) does not provide a "
        "Python .top attribute. Do not write stock=model.box(...), stock.top or "
        "model.feature(...).top. Selectors such as stock.top are quoted strings. "
        "This is API usage guidance, not additional geometry or a restriction to "
        "blocks. Adapt feature IDs, stock shape and operations to the supplied design."
    )
    by_id["design_review"]["fields"]["inputs"] = [
        p
        for p in by_id["design_review"]["fields"]["inputs"]
        if p["key"] not in {"design_review_" + key for key in remove}
    ]
    by_id["prompt_to_reviewed_cad"]["fields"]["purpose"] = (
        "One prompt to specification, test plan, actual measured CAD, native three-view presentation and illustrated review."
    )

    def edge(source, node, key, kind="engineering_document", file=False):
        target = node["id"] + "_" + key
        node["fields"]["inputs"].append(h.port(target, kind))
        sections.append(
            {
                "kind": "connection",
                "id": "to_" + target,
                "fields": {
                    "type": "item",
                    "from": source,
                    "to": node["id"] + "." + target,
                    "label": key.replace("_", " "),
                    "when": None,
                },
            }
        )
        if file:
            node["fields"]["settings"].setdefault("mcp_file_dependencies", {})[
                target
            ] = {"source": "connected_output"}
        return target

    def order(a, b):
        sections.append(
            {
                "kind": "connection",
                "id": a + "_before_" + b,
                "fields": {
                    "type": "order",
                    "from": a,
                    "to": b,
                    "label": "Declared sequence",
                    "when": None,
                },
            }
        )

    def task(
        key,
        title,
        provider,
        args,
        save=True,
        files=None,
        kind="engineering_document",
        fmt="json",
    ):
        tool = TOOLS[provider]
        settings = {
            "authoring_template": "mcp-tool",
            "mcp_server": tool["server_id"],
            "mcp_tool": tool["name"],
            "mcp_schema_digest": tool["schema_digest"],
            "mcp_arguments": json.dumps(args),
            "output_format": fmt,
            "save_output": save,
            "file_policy": "indexed",
            "run_path_template": "wright.run-path/1",
        }
        if save:
            settings["output_filename"] = (
                FILES + "/" + key + (".txt" if fmt == "text" else ".json")
            )
        outputs = [h.port(key + "_response", kind)]
        if files:
            settings.update(
                expected_files="\n".join(files.values()), expected_file_ports=files
            )
            outputs.extend(h.port(k, "workspace_file") for k in files)
        node = {
            "kind": "task",
            "id": key,
            "fields": {
                "name": title,
                "purpose": title,
                "step_type": "work",
                "performed_by": "configured_tool",
                "group": None,
                "inputs": [],
                "outputs": outputs,
                "prompt": "Execute the declared operation on its connected exact inputs. Preserve failures and uncertainty.",
                "settings": settings,
                "tool": None,
                "reusable_step": None,
            },
        }
        sections.append(node)
        return node

    def stdin(node, source, key="input", kind="engineering_document"):
        port = edge(source, node, key, kind)
        node["fields"]["settings"]["mcp_argument_ports"] = json.dumps({port: "stdin"})

    def whole(node, source):
        port = edge(source, node, "arguments", "workspace_file", file=True)
        node["fields"]["settings"].update(
            mcp_arguments="{}",
            mcp_arguments_source="connection",
            mcp_arguments_input=port,
        )

    edge("design_prompt.prompt", by_id["test_plan"], "supplied_prompt")
    edge("design_prompt.prompt", by_id["design_review"], "supplied_prompt")
    args_filter = 'if (.document_id|test("^[0-9a-f-]{36}$")) and (.revision|type)=="number" and .revision>=1 then {document_id,revision,branch:null,download:["step"],route:false,wait_s:100} else error("Exact created document and revision required") end'
    arguments = task(
        "prepare_export",
        "6. Bind the actual CAD export",
        "transfer",
        {
            "command": ["jq", "-ec", args_filter, ">", "export-arguments.json"],
            "directory": "/outputs/" + RUN,
            "timeout": 15,
        },
        files={"export_arguments": FILES + "/export-arguments.json"},
    )
    stdin(arguments, "create_design.create_design_response")
    order("validate_design", "prepare_export")
    export = task(
        "request_export",
        "6. Export the measured CAD revision",
        "export",
        {},
        save=False,
    )
    whole(export, "prepare_export.export_arguments")
    guard = 'if .document.id==$expected[0].document_id and .document.revision==$expected[0].revision and .model.status=="succeeded" and .model.mode=="full" and .model.metadata.units=="mm" then . else error("Completed requested CAD revision required") end'
    transfer_filter = (
        guard
        + ' | .downloads | if length==1 and .[0].artifact=="step" and .[0].url=="https://stevecad.studio/v1/download" then .[0] else error("Expected documented single STEP transfer") end | "url = " + (.url|@json) + "\\nheader = " + (("X-Download-Ticket: "+.headers["X-Download-Ticket"])|@json)'
    )
    transfer = task(
        "format_transfer",
        "6. Prepare private file transfer",
        "transfer",
        {
            "command": [
                "jq",
                "-er",
                "--slurpfile",
                "expected",
                "export-arguments.json",
                transfer_filter,
            ],
            "directory": "/outputs/" + RUN,
            "timeout": 15,
        },
        save=False,
        kind="text",
        fmt="text",
    )
    stdin(transfer, "request_export.request_export_response")
    edge(
        "prepare_export.export_arguments",
        transfer,
        "expected_revision",
        "workspace_file",
        file=True,
    )
    download = task(
        "download_step",
        "6. Retain the actual STEP file",
        "transfer",
        {
            "command": [
                "curl",
                "--config",
                "-",
                "--proxy",
                "http://transfer-egress:3128",
                "--proto",
                "=https",
                "--max-redirs",
                "0",
                "--disallow-username-in-url",
                "--fail",
                "--silent",
                "--show-error",
                "--remove-on-error",
                "--connect-timeout",
                "15",
                "--max-time",
                "110",
                "--max-filesize",
                "10000000",
                "--output",
                "/outputs/" + RUN + "/design.step",
                "--write-out",
                '{"http_code":%{http_code},"size_download":%{size_download}}',
            ],
            "timeout": 120,
        },
        files={"source_step": FILES + "/design.step"},
    )
    stdin(download, "format_transfer.format_transfer_response", kind="text")
    identity_filter = (
        guard
        + " | {document_id:.document.id,revision:.document.revision,build_id:.model.id,mode:.model.mode,metadata:.model.metadata}"
    )
    identity = task(
        "retain_export_identity",
        "6. Preserve native geometry and appearance",
        "transfer",
        {
            "command": [
                "jq",
                "-ec",
                "--slurpfile",
                "expected",
                "export-arguments.json",
                identity_filter,
                ">",
                "native-identity.json",
            ],
            "directory": "/outputs/" + RUN,
            "timeout": 15,
        },
        files={"native_identity": FILES + "/native-identity.json"},
    )
    stdin(identity, "request_export.request_export_response")
    edge(
        "prepare_export.export_arguments",
        identity,
        "expected_revision",
        "workspace_file",
        file=True,
    )
    mesh = task(
        "export_mesh",
        "6. Validate CAD and export render surfaces",
        "mesh",
        {
            "step_file": "/workspace/automatic-transfer-001/" + RUN + "/design.step",
            "formats": "glb",
            "cwd": "/workspace/automatic-transfer-001/" + RUN,
        },
        files={"renderer_mesh": FILES + "/design.glb"},
    )
    edge("download_step.source_step", mesh, "step", "workspace_file", file=True)
    native_code = (HERE / "native_render_scene.py").read_text(encoding="utf8")
    assert ";" not in native_code and "`" not in native_code
    basis_filter = """$identity[0] as $i | ($i.metadata.modeling) as $m | {document_id:$i.document_id,revision:$i.revision,build_id:$i.build_id,units:$i.metadata.units,solids:$i.metadata.solids,extent_mm:$i.metadata.extent_mm,items:(if $m.design then [$m.design.instances[] as $inst | $inst.bodies|to_entries[] | . as $body | $m.design.components[$inst.component].bodies[$body.key] as $part | {instance:($inst.name+"/"+$body.key),component:$inst.component,extent_mm:$body.value,color:$part.color,material:$part.material,finish:$part.finish}] else [$m.bodies|to_entries[] | {instance:.key,component:.key,extent_mm:.value.extent_mm,color:.value.color,material:.value.material,finish:.value.finish}] end)}"""
    mesh_guard = '.content[0].text|fromjson | if .status=="success" and ._exit_code==0 and .validation.is_valid==true and .mesh_validation.glb.is_valid==true and .validation.layers.structure.solid_count==$identity[0].metadata.solids then . else error("Native CAD and written mesh validation required") end'
    native_filter = (
        mesh_guard
        + " | ("
        + basis_filter
        + ") as $basis | if ($basis.items|length)==$basis.solids and $basis.solids>0 then {code:("
        + json.dumps(native_code)
        + '|split("__WRIGHT_BASIS_JSON_STRING__")|join($basis|tojson|tojson)),user_prompt:'
        + json.dumps(USER_PROMPT)
        + '} else error("One native body per mesh with exact metadata required") end'
    )
    native = task(
        "prepare_native_arguments",
        "6. Bind native bodies to their rendering",
        "transfer",
        {
            "command": [
                "jq",
                "-ec",
                "--slurpfile",
                "identity",
                "native-identity.json",
                native_filter,
                ">",
                "native-arguments.json",
            ],
            "directory": "/outputs/" + RUN,
            "timeout": 15,
        },
        files={"native_arguments": FILES + "/native-arguments.json"},
    )
    stdin(native, "export_mesh.export_mesh_response")
    edge(
        "retain_export_identity.native_identity",
        native,
        "identity",
        "workspace_file",
        file=True,
    )
    importer = task(
        "import_mesh", "6. Match each imported surface to native CAD", "blender", {}
    )
    whole(importer, "prepare_native_arguments.native_arguments")
    edge("export_mesh.renderer_mesh", importer, "mesh", "workspace_file", file=True)
    previous = "import_mesh"
    for view, direction in [
        ("isometric", (1, -1, 1)),
        ("top", (0, 0, 1)),
        ("front", (0, -1, 0)),
    ]:
        key = "render_" + view
        code = f"""import bpy
import json
from mathutils import Vector
scene=bpy.context.scene
assert scene.get('wright_render_run')=='{RUN}'
assert not bpy.app.is_job_running('RENDER')
camera=scene.camera
target=Vector(scene['wright_cad_target'])
direction=Vector({direction}).normalized()
camera.location=target+direction*5
camera.rotation_euler=(0,0,0) if '{view}'=='top' else (-direction).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
screen_right=camera.matrix_world.to_3x3()@Vector((1,0,0))
screen_up=camera.matrix_world.to_3x3()@Vector((0,1,0))
if '{view}'=='top':
    assert (screen_right-Vector((1,0,0))).length<1e-6
    assert (screen_up-Vector((0,1,0))).length<1e-6
corners=[obj.matrix_world@Vector(c) for obj in scene.objects if obj.type=='MESH' and obj.get('wright_cad_body') for c in obj.bound_box]
projected=[camera.matrix_world.inverted()@v for v in corners]
width=max(v.x for v in projected)-min(v.x for v in projected)
height=max(v.y for v in projected)-min(v.y for v in projected)
camera.data.ortho_scale=max(width/.8,height*(scene.render.resolution_x/scene.render.resolution_y)/.8)
scene.render.filepath='/outputs/{RUN}/{key}.png'
result=bpy.ops.render.render(write_still=True)
assert 'FINISHED' in result
print(json.dumps({{'native_operator_result':list(result),'native_render_running':bpy.app.is_job_running('RENDER'),'document_id':scene['wright_cad_document'],'revision':scene['wright_cad_revision'],'build_id':scene['wright_cad_scene_owner'],'run_id':'{RUN}','output_file':scene.render.filepath,'CAD_meshes':scene['wright_native_mesh_count'],'view':'{view}','screen_right_world':list(screen_right),'screen_up_world':list(screen_up),'scope':'Native CAD presentation, not dimensional or physical acceptance'}}))
"""
        render = task(
            key,
            "6. Render " + view,
            "blender",
            {"code": code, "user_prompt": USER_PROMPT},
            files={key + "_image": VIEWS + "/" + key + ".png"},
        )
        edge(
            "validate_design." + view,
            render,
            "cad_capture",
            "workspace_file",
            file=True,
        )
        order(previous, key)
        previous = key
        edge(key + "." + key + "_image", by_id["design_review"], key, "workspace_file")
    review = by_id["design_review"]
    review["fields"]["prompt"] += (
        "\nThe presentation images are native Blender renders of the actual validated STEP mesh, using the three captured orientation conventions. Compare each with its original CAD capture. Cite the exact export revision/build and geometry-matching report. A new full-build ID on the same revision is a separate export identity, not evidence of a geometry change or byte equivalence. Native color metadata is used when available, otherwise a declared neutral matte gray fallback. Retain appearance mismatches if the prompt calls for another finish."
        "\nThe connected original prompt establishes supplied requirements. Keep "
        "original inspection verdicts and any actual specification/test conflict "
        "visible; do not silently waive a failed test. A presentation-only finish "
        "is evaluated on derived studio renders, with original CAD captures kept "
        "as provider-colored geometric evidence unless CAD viewport appearance "
        "was explicitly requested. Compare camera and visible geometry across "
        "each pair. Keep a simple part review concise, with complete requirement "
        "and evidence tables rather than repeated specification prose."
    )
    edge(
        "retain_export_identity.native_identity",
        review,
        "export_identity",
        "workspace_file",
    )
    edge("import_mesh.import_mesh_response", review, "render_geometry_check")
    source = h.render(sections)
    validate_workspace_authoring_shape(source)
    compiled = compile_prompt_workflow(source)
    assert len(compiled.steps) == 16
    return source, {
        "logical_stages": 7,
        "execution_tasks": len(compiled.steps),
        "sha256": h.digest(source.encode()),
        "status": "prepared_not_executed",
        "base": "v13 instruction snapshot preserved",
        "scope": "Native export and rendering replace geometry-changing AI image edits",
    }


if __name__ == "__main__":
    source, summary = prepare()
    (HERE / "prompt-to-reviewed-cad-native.workflow.wflow").write_text(
        source, encoding="utf8"
    )
    print(json.dumps(summary, indent=2))
