"""Compose an optional two-orientation study into the existing wheel example.

These are accepted workflow declarations, not a runner. Native geometry is made
by the current run; Wright checks its exact dependency before the independent
inspection/slicer providers consume it. The final engineering review is retained.
"""

from copy import copy
import json
from pathlib import Path
from core.process_validation import ValidationProfile


def add(parent, definition, bindings, create, construction):
    if "source_mesh" not in construction["outputs"]:
        raise ValueError(
            "Orientation comparison requires the current native mesh producer"
        )
    flow = copy(parent)
    flow.suffix = parent.suffix + "_orientation"
    flow.output = parent.output + "/orientation"
    flow.input_root = parent.input_root + "/orientation"
    first_section = len(flow.sections)
    repo = definition.REPO
    ws = flow.workspace
    source_ref = create["id"] + ".source_mesh"
    source_rel = parent.output + "/" + construction["outputs"]["source_mesh"]
    basis = """# Focus-wheel orientation study basis

    Compare socket-down and socket-up from the same current-run native STL, in mm.
    Socket-up is a 180 degree X rotation translated onto the build plane. No geometry
    features, dimensions, material or original requirements change. Preserve PETG,
    P1S 0.4 mm, 0.20 mm layer height, four walls, 35% infill and enabled supports.

    Before slicing, each transformed mesh must pass the original five repaired-mesh
    checks. Rigid float32 export area/volume relative error must remain <=0.00001;
    height is18mm within0.0001mm. These are numerical conversion limits, not production
    tolerances. The original full engineering profile remains an attached requirement.

    Compare actual support paths in the nominal D cavity first, then external support
    contact/removal, coplanar bed contact and slicer-reported material/time. The cavity
    screen uses support-segment midpoints and the symmetric model path envelope; it
    is not a bead-width/contact simulation and leaves unclassified paths explicit.
    No automatic orientation selection or release occurs. Keep the final review
    pending. Fit, torque, creep, adhesion, removal and glove comfort require separate
    physical tests under the retained inspection plan. Geometry-only contact and
    downward-area screens do not establish adhesion or support requirements.
    """
    basis_ref = flow.input_bytes(
        "orientation-basis.md",
        basis.encode(),
        kind="workspace_file",
        title="Orientation comparison basis",
    )
    context_dir = (
        repo
        / "tests/datasets/engineering-workflows/scenarios/printed-replacement-part/01-observatory-focus-wheel"
    )
    original_refs = {
        name: flow.input_bytes(
            "original-" + name,
            (context_dir / name).read_bytes(),
            kind="workspace_file",
            original=str(context_dir / name),
        )
        for name in ("context.md", "prompt.txt", "user-profile.md")
    }
    profiles = {
        role: flow.input_bytes(
            role + "-profile.json",
            Path(ref["path"]).read_bytes(),
            kind="workspace_file",
            original=ref["path"],
        )
        for role, ref in bindings["profiles"].items()
    }
    profile_hashes = {role: ref["sha256"] for role, ref in bindings["profiles"].items()}
    assert all(
        definition.sha(Path(bindings["profiles"][role]["path"]).read_bytes()) == value
        for role, value in profile_hashes.items()
    )
    assets = {
        "orientation-study.py": repo
        / "examples/process-interfaces/printed-replacement-part/orientation-study.py",
        "passive-representations.py": repo
        / "packages/workspace_service/src/workspace_service/process_interfaces/representations.py",
        "inspect_manufacturing_package.py": repo
        / "scripts/engineering/inspect_manufacturing_package.py",
    }
    asset_refs = {
        name: flow.input_bytes(
            name, path.read_bytes(), kind="workspace_file", original=str(path)
        )
        for name, path in assets.items()
    }
    config = {
        "workspace_root": "/workspace",
        "source_mesh": source_rel,
        "output_root": flow.output,
        "profile_sha256": profile_hashes,
        "gcode_entry": "Metadata/plate_1.gcode",
        "reported_usage_prefixes": {
            "filament length (mm)": "; total filament length [mm] :",
            "filament mass (g)": "; total filament weight [g] :",
            "time estimate": "; model printing time:",
        },
    }

    def load_asset(name, namespace):
        return f"raw=Path({('/workspace/' + flow.input_root + '/' + name)!r}).read_bytes()\nassert hashlib.sha256(raw).hexdigest()=={definition.sha(assets[name].read_bytes())!r}\n{namespace}={{'__name__':'accepted_study'}}\nexec(compile(raw,{name!r},'exec'),{namespace})\n"

    def python_stage(identity, title, code, outputs, dependencies):
        stage = flow.stage(identity, title)
        args = {
            "solver": bindings["inspection_backend"],
            "input_content": code,
            "job_name": flow.output + "/" + identity,
            "critic_approved": False,
        }
        args_ref = flow.input_bytes(
            identity + "-arguments.json",
            (json.dumps(args, indent=2) + "\n").encode(),
            run_paths=True,
        )
        port = flow.reference(args_ref, stage, "exact_arguments")
        flow.exact_mcp(
            stage,
            flow.select(bindings["inspection_server"], "run_simulation"),
            port,
            tuple(outputs.values()),
            identity + "-provider-response.json",
        )
        stage["fields"]["settings"]["mcp_file_dependencies"] = {
            flow.reference(ref, stage, key, "workspace_file"): path
            for key, (ref, path) in dependencies.items()
        }
        flow.file_outputs(
            stage, {key: flow.output + "/" + path for key, path in outputs.items()}
        )
        return stage

    prefix = "import hashlib\nfrom pathlib import Path\n"
    config_code = f"config={config!r}\nconfig['source_sha256']=hashlib.sha256(Path({('/workspace/' + source_rel)!r}).read_bytes()).hexdigest()\n"
    mesh = python_stage(
        "orient_geometry",
        "Orient the exact wheel in two build directions",
        prefix
        + load_asset("orientation-study.py", "study")
        + config_code
        + "print(study['prepare'](config))\n",
        {
            "source_mesh": "source_mesh.stl",
            "socket_down_mesh": "socket_down/oriented.stl",
            "socket_up_mesh": "socket_up/oriented.stl",
            "geometry": "orientation-geometry.json",
        },
        {
            "source_mesh": (source_ref, source_rel),
            "basis": (basis_ref, flow.input_root + "/orientation-basis.md"),
            "operation": (
                asset_refs["orientation-study.py"],
                flow.input_root + "/orientation-study.py",
            ),
        },
    )
    chain = [mesh]
    original = json.loads(
        (
            repo
            / "packages/workspace_service/src/workspace_service/process_validation/profiles/printed-replacement-part-01.json"
        ).read_bytes()
    )
    original_ref = flow.input_bytes(
        "original-full-profile.json",
        json.dumps(original, indent=2).encode(),
        kind="workspace_file",
    )
    mesh_checks = [
        item for item in original["checks"] if item["subject_role"] == "repaired_mesh"
    ]
    assert len(mesh_checks) == 5
    ids = {i for check in mesh_checks for i in check["requirement_ids"]}
    mesh_profile = ValidationProfile.model_validate(
        {
            "id": "focus-wheel-orientation-mesh-gate",
            "version": "1",
            "baseline": {
                **original["baseline"],
                "id": "focus-wheel-orientation-mesh-basis",
                "requirements": [
                    r for r in original["baseline"]["requirements"] if r["id"] in ids
                ],
            },
            "checks": mesh_checks,
            "supported_kinds": ["file"],
            "limitations": [
                "Original mesh checks only. Orientation/contact decisions and complete engineering acceptance remain separate."
            ],
        }
    )
    declared_profiles = []

    def validator(identity, title, profile, subjects):
        name = identity + "-profile.json"
        ref = flow.input_bytes(
            name, profile.model_dump_json(indent=2).encode(), kind="workspace_file"
        )
        stage = flow.stage(identity, title)
        stage["fields"]["prompt"] = ""
        stage["fields"]["outputs"] = [definition.port("assessment")]
        stage["fields"]["settings"] = {
            "authoring_template": "process-validator",
            "max_revisions": 0,
            "validation": {
                "profile": {
                    "source": "workspace",
                    "name": flow.input_root + "/" + name,
                    "reference": profile.reference().model_dump(),
                },
                "baseline": profile.baseline.reference().model_dump(),
                "subjects": {
                    key: flow.reference(value, stage, key, "workspace_file")
                    for key, value in subjects.items()
                },
            },
        }
        declared_profiles.append((identity, ref))
        return stage, ref

    readers = {}
    for name in ("socket_down", "socket_up"):
        gate, _ = validator(
            "validate_" + name,
            "Check " + name.replace("_", " ") + " mesh before slicing",
            mesh_profile,
            {
                "source_mesh": mesh["id"] + ".source_mesh",
                "repaired_mesh": mesh["id"] + "." + name + "_mesh",
            },
        )
        chain.append(gate)
        slicer = flow.stage(
            "slice_" + name,
            "Slice " + name.replace("_", " ") + " with the retained PETG profile",
        )
        args = {
            "source": str(ws / flow.output / name / "oriented.stl"),
            "plate": 1,
            "output": str(ws / flow.output / name / "package.gcode.3mf"),
            "orient": False,
            "arrange": True,
            "confirm": True,
        }
        args_ref = flow.input_bytes(
            "slice-" + name + ".json",
            json.dumps(args, indent=2).encode(),
            run_paths=True,
        )
        port = flow.reference(args_ref, slicer, "exact_arguments")
        flow.exact_mcp(
            slicer,
            flow.select(bindings["slicer_server"], "slice_model_file"),
            port,
            (name + "/package.gcode.3mf",),
            "slice-" + name + "-response.json",
        )
        deps = {
            flow.reference(
                mesh["id"] + "." + name + "_mesh",
                slicer,
                "oriented_geometry",
                "workspace_file",
            ): flow.output + "/" + name + "/oriented.stl"
        }
        deps.update(
            {
                flow.reference(
                    ref, slicer, role + "_profile", "workspace_file"
                ): flow.input_root + "/" + role + "-profile.json"
                for role, ref in profiles.items()
            }
        )
        slicer["fields"]["settings"]["mcp_file_dependencies"] = deps
        slicer["fields"]["settings"]["timeout_seconds"] = 300
        flow.file_outputs(
            slicer, {"package": flow.output + "/" + name + "/package.gcode.3mf"}
        )
        retain = flow.stage(
            "retain_" + name,
            "Retain actual " + name.replace("_", " ") + " slicer observations",
        )
        port = flow.reference(
            slicer["id"] + "." + slicer["id"] + "_result", retain, "actual_response"
        )
        flow.exact_mcp(
            retain,
            flow.select(bindings["files_server"], "write_text_document"),
            port,
            (name + "/provider-response.json",),
            "retain-" + name + "-receipt.json",
        )
        retain["fields"]["settings"].update(
            mcp_arguments_source="fields",
            mcp_argument_ports=json.dumps({port: "content"}),
            mcp_arguments=json.dumps(
                {
                    "relativePath": flow.output
                    + "/"
                    + name
                    + "/provider-response.json",
                    "mediaType": "application/json",
                    "overwrite": False,
                }
            ),
        )
        flow.file_outputs(
            retain, {"response": flow.output + "/" + name + "/provider-response.json"}
        )
        cfg = {
            "workspace_root": "/workspace",
            "source_mesh": flow.output + "/" + name + "/oriented.stl",
            "slice_package": flow.output + "/" + name + "/package.gcode.3mf",
            "provider_response": flow.output + "/" + name + "/provider-response.json",
            "output_root": flow.output + "/" + name,
            "profiles": {
                role: flow.input_root + "/" + role + "-profile.json"
                for role in profiles
            },
            "gcode_entry": "Metadata/plate_1.gcode",
            "nominal_layer_section": bindings["nominal_layer_section"],
            "success_field": "ok",
            "expected_response_fields": {
                key: args[key] for key in ("source", "output", "plate")
            },
            "success_contract": bindings["slice_success_contract"],
            "operation_label": "actual_local_bambu_slice",
        }
        code = (
            prefix
            + load_asset("passive-representations.py", "reader")
            + load_asset("inspect_manufacturing_package.py", "inspector")
            + f"print(inspector['run']({cfg!r},reader['read_3mf_toolpaths']))\n"
        )
        dependencies = {
            "mesh": (
                mesh["id"] + "." + name + "_mesh",
                flow.output + "/" + name + "/oriented.stl",
            ),
            "package": (
                slicer["id"] + ".package",
                flow.output + "/" + name + "/package.gcode.3mf",
            ),
            "response": (
                retain["id"] + ".response",
                flow.output + "/" + name + "/provider-response.json",
            ),
        }
        dependencies.update(
            {
                key: (ref, flow.input_root + "/" + key)
                for key, ref in asset_refs.items()
                if key != "orientation-study.py"
            }
        )
        dependencies.update(
            {
                role: (ref, flow.input_root + "/" + role + "-profile.json")
                for role, ref in profiles.items()
            }
        )
        outputs = {
            key: name + "/" + filename
            for key, filename in {
                "evidence": "slice-evidence.json",
                "paths": "support-preview.json",
                "summary": "toolpath-summary.json",
                "machine": "machine-profile.json",
                "process": "process-profile.json",
                "filament": "filament-profile.json",
            }.items()
        }
        inspect = python_stage(
            "inspect_" + name,
            "Read " + name.replace("_", " ") + " package and nominal support paths",
            code,
            outputs,
            dependencies,
        )
        readers[name] = inspect
        chain.extend([slicer, retain, inspect])
    deps = {
        "source_mesh": (source_ref, source_rel),
        "source_copy": (mesh["id"] + ".source_mesh", flow.output + "/source_mesh.stl"),
        "geometry": (
            mesh["id"] + ".geometry",
            flow.output + "/orientation-geometry.json",
        ),
        "operation": (
            asset_refs["orientation-study.py"],
            flow.input_root + "/orientation-study.py",
        ),
    }
    for name, stage in readers.items():
        for key, path in stage["fields"]["settings"]["expected_file_ports"].items():
            deps[name + "_" + key] = (stage["id"] + "." + key, path)
        slicer = next(
            s for s in chain if s["id"] == "slice_" + name + "_" + flow.suffix
        )
        deps[name + "_package"] = (
            slicer["id"] + ".package",
            flow.output + "/" + name + "/package.gcode.3mf",
        )
    comparison = python_stage(
        "compare_orientations",
        "Compare measured supports, contact and material use",
        prefix
        + load_asset("orientation-study.py", "study")
        + config_code
        + "print(study['compare'](config))\n",
        {
            "comparison": "orientation-comparison.json",
            "report": "orientation-review.md",
        },
        deps,
    )
    chain.append(comparison)
    checks = []

    def check(identity, selector, operator, expected):
        checks.append(
            {
                "id": identity,
                "version": "1",
                "requirement_ids": ["ORIENTATION-DIGITAL-CORRESPONDENCE"],
                "subject_role": "comparison",
                "reader": "structured",
                "selector": selector,
                "unit": ("1" if operator in ("lte", "gte") else None),
                "constraint": (
                    {"operator": "range", "minimum": 0, "maximum": expected}
                    if operator == "lte"
                    else {"operator": "range", "minimum": expected}
                    if operator == "gte"
                    else {"operator": operator, "expected": expected}
                ),
                "evidence_method": "structured_value",
                "parameters": {},
            }
        )

    check("unchanged-profiles", "/same_profiles", "equals", True)
    check("source-identity", "/source_matches_dependency", "equals", True)
    for name in readers:
        check(
            name + "-volume",
            "/cases/" + name + "/volume_relative_error",
            "lte",
            0.00001,
        )
        check(name + "-area", "/cases/" + name + "/area_relative_error", "lte", 0.00001)
        checks.append(
            {
                "id": name + "-height",
                "version": "1",
                "requirement_ids": ["ORIENTATION-DIGITAL-CORRESPONDENCE"],
                "subject_role": "comparison",
                "reader": "structured",
                "selector": "/cases/" + name + "/height_mm",
                "constraint": {"operator": "within", "target": 18, "tolerance": 0.0001},
                "unit": "mm",
                "evidence_method": "structured_value",
                "parameters": {},
            }
        )
        check(
            name + "-classification",
            "/cases/" + name + "/classification_known",
            "equals",
            True,
        )
        check(name + "-layers", "/cases/" + name + "/layer_count", "gte", 1)
    profile = ValidationProfile.model_validate(
        {
            "id": "focus-wheel-orientation-correspondence",
            "version": "1",
            "baseline": {
                "id": "focus-wheel-orientation-basis",
                "version": "1",
                "requirements": [
                    {
                        "id": "ORIENTATION-DIGITAL-CORRESPONDENCE",
                        "text": "Compare rigid orientation candidates with unchanged geometry, exact retained profiles and actual classified layer paths. This contributes digital evidence; original engineering acceptance remains mandatory.",
                        "scope": "design",
                        "sources": [
                            {
                                "artifact_ref": flow.input_root
                                + "/orientation-basis.md",
                                "sha256": definition.sha(basis.encode()),
                                "locator": "Entire declared study basis",
                            }
                        ],
                        "mandatory": True,
                        "review_required": False,
                    }
                ],
            },
            "checks": checks,
            "supported_kinds": ["file"],
            "limitations": [
                "No automatic orientation acceptance, support-removal proof, physical print or fit/strength certification."
            ],
        }
    )
    gate, profile_ref = validator(
        "validate_comparison",
        "Check exact orientation comparison evidence",
        profile,
        {"comparison": comparison["id"] + ".comparison"},
    )

    chain.append(gate)
    review_refs = [
        (comparison["id"] + ".report", "orientation_report", "workspace_file"),
        (comparison["id"] + ".comparison", "orientation_comparison", "workspace_file"),
        (basis_ref, "orientation_basis", "workspace_file"),
        (original_ref, "orientation_original_requirements", "workspace_file"),
        (gate["id"] + ".assessment", "orientation_assessment", "engineering_document"),
    ]
    review_refs.extend(
        (ref, "orientation_original_" + name, "workspace_file")
        for name, ref in original_refs.items()
    )
    review_refs.extend(
        (stage["id"] + ".paths", name + "_paths", "workspace_file")
        for name, stage in readers.items()
    )
    review_refs.extend(
        (ref, "orientation_criteria_" + identity, "workspace_file")
        for identity, ref in declared_profiles
    )
    # Only this added subgraph is namespaced. Existing accepted stage identities stay intact.
    renamed = {}
    for section in flow.sections[first_section:]:
        if section["kind"] != "task":
            continue
        fields = section["fields"]
        keys = {p["key"]: section["id"] + "__" + p["key"] for p in fields["outputs"]}
        renamed.update(
            {
                section["id"] + "." + old: section["id"] + "." + new
                for old, new in keys.items()
            }
        )
        for p in fields["outputs"]:
            p["key"] = keys[p["key"]]
        if "expected_file_ports" in fields["settings"]:
            fields["settings"]["expected_file_ports"] = {
                keys[key]: path
                for key, path in fields["settings"]["expected_file_ports"].items()
            }
    for section in flow.sections[first_section:]:
        if section["kind"] == "connection" and section["fields"]["type"] == "item":
            fields = section["fields"]
            fields["from"] = renamed.get(fields["from"], fields["from"])
    return chain, [
        (renamed.get(ref, ref), role, kind) for ref, role, kind in review_refs
    ]
