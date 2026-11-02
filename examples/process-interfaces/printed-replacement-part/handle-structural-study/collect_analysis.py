"""Retain the actual completed native solve for this authored handle study.

Invoke collect_analysis(CONFIG) through the discovered FreeCAD execute_code tool.
The existing provider owns solving; this operation only checks and copies its
reported files and saves the already populated native result document.
"""


def collect_analysis(config):
    import hashlib
    import json
    import math
    from pathlib import Path

    import FreeCAD

    root = Path(config["workspace_root"])
    response_path = Path(config["solver_response"])
    mesh_path = Path(config["prepared_mesh"])
    output = Path(config["output_dir"])
    for path in (root, response_path, mesh_path, output):
        if not path.is_absolute() or path.resolve() != path:
            raise ValueError("Use real absolute paths in the declared workspace")
    if any(not path.is_relative_to(root) for path in (response_path, mesh_path, output)):
        raise ValueError("Study paths must remain in the bound workspace")
    if output == root or output.exists():
        raise ValueError("Preserve prior outputs; use this run's new collection directory")
    response_bytes = response_path.read_bytes()
    response = json.loads(response_bytes)
    texts = [item["text"] for item in response.get("result", []) if item.get("type") == "text"]
    if len(texts) != 1:
        raise ValueError("Expected one structured native solver response")
    solved = json.loads(texts[0])
    if solved.get("success") is not True or solved.get("detailed_results") is not True:
        raise ValueError("Native solver did not report the requested detailed solve")
    work = Path(solved["working_dir"])
    deck = Path(solved["input_file"])
    if (not work.is_absolute() or work.resolve() != work or deck.resolve() != deck
            or deck.parent != work or deck.suffix != ".inp"):
        raise ValueError("Native solver returned an inconsistent input path")
    entries = solved.get("result_files", [])
    if (not entries or len(entries) > 10
            or sum(item["bytes"] for item in entries) > 512 * 1024**2):
        raise ValueError("Unexpected native result inventory")
    paths = {}
    for entry in entries:
        path = Path(entry["path"])
        if (path.parent != work or path.resolve() != path or path.is_symlink()
                or not path.is_file() or path.name in paths):
            raise ValueError("Native result identity is not a unique regular file")
        paths[path.name] = (path, entry)
    for extension in (".inp", ".native.inp", ".dat", ".frd"):
        if deck.with_suffix(extension).name not in paths:
            raise ValueError("Missing native result file: " + extension)

    def nodes(path):
        result = {}
        active = False
        for line in path.read_text().splitlines():
            if line.startswith("**"):
                continue
            if line.startswith("*"):
                active = line.split(",")[0].strip().upper() == "*NODE"
            elif active and line.strip():
                fields = line.split(",")
                key = int(fields[0])
                values = [float(v) for v in fields[1:4]]
                if key in result or len(values) != 3 or not all(map(math.isfinite, values)):
                    raise ValueError("Invalid or duplicate native mesh node")
                result[key] = values
        return result

    prepared_nodes = nodes(mesh_path)
    if not prepared_nodes or prepared_nodes != nodes(deck):
        raise ValueError("Solved mesh does not match this run's prepared native mesh")
    doc = FreeCAD.getDocument(config["document_name"])
    result = doc.getObject(solved["result_object"])
    if result is None or len(result.NodeNumbers) != len(prepared_nodes):
        raise ValueError("Native result does not cover the prepared mesh")
    fields = [obj.Name for obj in doc.Objects if hasattr(obj, "vonMises")]
    if fields != [result.Name]:
        raise ValueError("Expected exactly one native structural result object")

    output.mkdir(parents=True)
    inventory = []
    try:
        for path, entry in paths.values():
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if len(raw) != entry["bytes"] or digest != entry["sha256"]:
                raise ValueError("Native result changed after its solver receipt")
            extension = next(
                (suffix for suffix in (".native.inp", ".stdout.txt", ".stderr.txt", ".execution.json")
                 if path.name.endswith(suffix)), path.suffix
            )
            retained = output / ("solver" + extension)
            with retained.open("xb") as stream:
                stream.write(raw)
            inventory.append({"name": retained.name, "source": str(path),
                              "bytes": len(raw), "sha256": digest})
        native = output / "analysis-results.FCStd"
        doc.saveAs(str(native))
        inventory.append({"name": native.name, "bytes": native.stat().st_size,
                          "sha256": hashlib.sha256(native.read_bytes()).hexdigest()})
        report = {
            "schema_version": "printed02.structural-collection/1",
            "run_id": config["run_id"], "document_name": doc.Name,
            "status": "native_results_retained_checks_pending",
            "engineering_acceptance": False, "physical_acceptance": False,
            "solver_response_sha256": hashlib.sha256(response_bytes).hexdigest(),
            "prepared_mesh_sha256": hashlib.sha256(mesh_path.read_bytes()).hexdigest(),
            "deck_nodes_equal_prepared_mesh": True, "nodes": len(prepared_nodes),
            "native_result_objects": fields, "solver": solved, "files": inventory,
            "geometry_label": config.get("geometry_label", "Original handle"),
            "remaining": ["Force and moment balance", "Integration-point region statistics",
                          "Matched mesh refinement", "Exact geometry checks and human review"],
        }
        (output / "collected-analysis.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "results.md").write_text(
            f"# {report['geometry_label']}: detailed structural output\n\n"
            "Preliminary result; equilibrium, mesh refinement and engineering review pending.\n\n"
            "| Quantity | Value |\n| --- | ---: |\n"
            f"| Maximum displacement | {solved['max_displacement_mm']:.6f} mm |\n"
            f"| Peak nodal von Mises stress | {solved['max_von_mises_MPa']:.6f} MPa |\n"
            f"| Mesh nodes | {len(prepared_nodes):,} |\n"
            f"| Retained files | {len(inventory)} |\n\n"
            + config.get(
                "geometry_note",
                "The original CAD, mounting interface, material assumptions and 40 N pull are unchanged.",
            ) + " "
            "Detailed native output was requested for subsequent assessment. No design improvement "
            "or printed-part strength is established.\n"
        )
        print("Retained native structural files:", json.dumps({
            "nodes": len(prepared_nodes), "files": len(inventory), "output": str(output)}))
        return report
    except Exception as error:
        (output / "collection-failure.json").write_text(json.dumps({
            "error": str(error), "retained_files": inventory,
            "engineering_acceptance": False}, indent=2) + "\n")
        raise
