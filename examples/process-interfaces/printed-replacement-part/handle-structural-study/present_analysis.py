"""Fit and export existing native result views through the independent FreeCAD MCP.

This changes presentation only. It does not solve, alter CAD/fields, approve a
result, or interpret a provider protocol. Keep the original native input intact.
"""


def present_analysis(config):
    import hashlib
    import json
    import math
    from pathlib import Path

    import FreeCAD
    import FreeCADGui
    from PySide import QtGui

    root = Path(config["workspace_root"])
    collection_path = Path(config["collection"])
    native = Path(config["native_result"])
    output = Path(config["output_dir"])
    for path in (root, collection_path, native, output):
        if not path.is_absolute() or path.resolve() != path:
            raise ValueError("Use real paths in the declared workspace")
    if any(not path.is_relative_to(root) for path in (collection_path, native, output)):
        raise ValueError("Presentation paths must remain in the workspace")
    if output == root or output.exists():
        raise ValueError("Preserve existing views; use a new presentation output")
    collection = json.loads(collection_path.read_text())
    if collection["run_id"] != config["source_run_id"]:
        raise ValueError("The collection belongs to another solve")
    expected = next(item for item in collection["files"] if item["name"] == native.name)
    original_hash = hashlib.sha256(native.read_bytes()).hexdigest()
    if original_hash != expected["sha256"] or native.stat().st_size != expected["bytes"]:
        raise ValueError("The original native result changed")
    doc = FreeCAD.getDocument(config["document_name"])
    if doc.Name != collection["document_name"]:
        raise ValueError("The open native document belongs to another study")
    result = doc.getObject(collection["solver"]["result_object"])
    if result is None or len(result.NodeNumbers) != collection["nodes"]:
        raise ValueError("The open result does not cover the retained study")
    displacement = max(result.DisplacementLengths)
    stress = max(result.vonMises)
    for actual, key in [(displacement, "max_displacement_mm"), (stress, "max_von_mises_MPa")]:
        if not math.isclose(actual, collection["solver"][key], rel_tol=1e-9, abs_tol=1e-12):
            raise ValueError("The open fields differ from the retained solver response")
    pipeline = doc.getObject("Pipeline_" + result.Name)
    if pipeline is None or "Field" not in pipeline.ViewObject.PropertiesList:
        raise ValueError("The native result pipeline is unavailable; inspect its actual view contract")
    if result.Name != "CCX_Results" or pipeline.Name != "Pipeline_CCX_Results":
        raise ValueError("Qualify the legend units of this different native result pipeline first")
    output.mkdir(parents=True)
    for obj in doc.Objects:
        if obj.ViewObject:
            obj.ViewObject.Visibility = False
    FreeCAD.setActiveDocument(doc.Name)
    pipeline.ViewObject.Visibility = True
    pipeline.ViewObject.DisplayMode = "Surface"
    view = FreeCADGui.activeDocument().activeView()
    view.viewAxonometric()
    images = []
    for field, filename, unit in [
        ("von Mises Stress", "candidate-nodal-stress.png", "Pa"),
        ("Displacement Magnitude", "candidate-displacement.png", "m"),
    ]:
        pipeline.ViewObject.Field = field
        QtGui.QApplication.processEvents()
        view.fitAll()
        QtGui.QApplication.processEvents()
        path = output / filename
        view.saveImage(str(path), 1400, 900, "White")
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("The native result view was not exported")
        images.append({"field": field, "unit": unit, "path": str(path),
                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                       "scale": "Native automatic scale for this field; not a paired baseline color scale"})
    fitted = output / "fitted-candidate-results.FCStd"
    doc.saveAs(str(fitted))
    if hashlib.sha256(native.read_bytes()).hexdigest() != original_hash:
        raise ValueError("The original native result changed during presentation")
    report = {
        "schema_version": "printed02.structural-presentation/1",
        "run_id": config["run_id"], "source_run_id": config["source_run_id"],
        "geometry_label": config["geometry_label"], "original_native_sha256": original_hash,
        "original_native_unchanged": True, "nodes": collection["nodes"],
        "max_displacement_mm": displacement, "max_nodal_von_mises_MPa": stress,
        "images": images, "fitted_native_path": str(fitted),
        "fitted_native_sha256": hashlib.sha256(fitted.read_bytes()).hexdigest(),
        "engineering_acceptance": False, "physical_acceptance": False,
    }
    (output / "presentation.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "presentation.md").write_text(
        "# Fitted views of the handle candidate\n\n"
        "These are actual native finer-mesh result views for the R3.15 root-blend candidate. "
        "The original result is unchanged. Only visibility, selected field and camera were adjusted; "
        "no CAD change or solver run occurred.\n\n"
        "| Field | Native color-bar unit | Report unit |\n|---|---|---|\n"
        "| Nodal von Mises stress | Pa | MPa: divide by 1,000,000 |\n"
        "| Displacement magnitude | m | mm: multiply by 1,000 |\n\n"
        "This qualified legacy CCX pipeline uses SI color-bar units, unlike its result object's mm/MPa values. "
        "See [FreeCAD's native postprocessing guide](https://blog.freecad.org/2025/09/16/getting-started-with-fem/).\n\n"
        "Each view uses its native automatic color scale. The raw restrained-bore peak remains a "
        "mesh-sensitive diagnostic. These images do not establish design improvement, engineering "
        "approval or printed PETG strength. Open the numerical assessment and comparison for context.\n"
    )
    print("Retained fitted native result views:", json.dumps(report))
    return report
