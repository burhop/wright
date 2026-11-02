"""Authored FreeCAD MCP operation for the actual Printed02 structural study.

Append prepare_analysis(CONFIG) to these bytes in a declared execute_code call.
This prepares native CAD/mesh/constraints; the provider's run_fem_analysis owns
its subsequent native solve. No workflow execution or approval lives here.
"""


def prepare_analysis(config):
    import hashlib
    import json
    import math
    from pathlib import Path
    import time
    import traceback

    import FreeCAD
    import ObjectsFem
    import Part
    from FreeCAD import Vector
    from femmesh.gmshtools import GmshTools

    started = time.monotonic()
    root = Path(config["workspace_root"])
    source_path = Path(config["input_brep"])
    output = Path(config["output_dir"])
    for path in (root, source_path, output):
        if not path.is_absolute() or path.resolve() != path:
            raise ValueError("Bind real absolute paths in the declared workspace")
    if not source_path.is_relative_to(root) or not output.is_relative_to(root):
        raise ValueError("Study paths must stay in the bound workspace")
    if output == root or output.exists():
        raise ValueError("Preserve existing work; use a distinct study revision output")
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    if source_hash != config["input_brep_sha256"]:
        raise ValueError("Declared CAD input identity changed")
    name = config["document_name"]
    if (not name or len(name) > 63 or not name[0].isalpha()
            or not name.isascii() or not name.replace("_", "").isalnum()):
        raise ValueError("Use a bounded explicit native document identity")
    minimum, maximum = float(config["mesh_min_mm"]), float(config["mesh_max_mm"])
    if not (math.isfinite(minimum) and math.isfinite(maximum)
            and 0 < minimum <= maximum):
        raise ValueError("Bind finite positive ordered mesh sizes in millimetres")
    if name in FreeCAD.listDocuments():
        raise ValueError("Native document already exists; reconcile before retrying")
    output.mkdir(parents=True)
    report = {
        "schema_version": "printed02.structural-preparation/1",
        "status": "preparing",
        "study_revision": config["study_revision"],
        "input_brep_sha256": source_hash,
        "document_name": name,
        "analysis_name": "HandleAnalysis",
        "engineering_acceptance": False,
        "physical_acceptance": False,
        "face_bounds_method": "optimalBoundingBox(useTriangulation=False,useShapeTolerance=False)",
        "steps": [],
    }

    def save(label, values):
        report["steps"].append({"name": label, **values})
        report["elapsed_seconds"] = time.monotonic() - started
        (output / "preparation-progress.json").write_text(json.dumps(report, indent=2))

    def sound_solid(shape):
        if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
            raise ValueError("Study requires one valid positive-volume native solid")
        shape.check(True)

    def measured_properties(shape, *, volume=False):
        # Use the binding supplied with this native FreeCAD installation. Its
        # ordinary Area/Volume properties use non-adaptive integration, which
        # is not accurate enough to compare differently trimmed spline faces.
        from OCC.Core.BRepGProp import brepgprop
        from OCC.Core.GProp import GProp_GProps

        native = Part.__toPythonOCC__(shape)
        area_props = GProp_GProps()
        epsilon = 1e-11
        area_error = brepgprop.SurfaceProperties(native, area_props, epsilon, False)
        center = area_props.CentreOfMass()
        result = {
            "area_mm2": area_props.Mass(),
            "area_relative_error_estimate": area_error,
            "area_centroid_mm": [center.X(), center.Y(), center.Z()],
            "requested_relative_error": epsilon,
        }
        if volume:
            volume_props = GProp_GProps()
            volume_error = brepgprop.VolumeProperties(
                native, volume_props, epsilon, True, False)
            result.update(volume_mm3=volume_props.Mass(),
                          volume_relative_error_estimate=volume_error)
        for key, value in result.items():
            values = value if isinstance(value, list) else [value]
            if not all(math.isfinite(number) for number in values):
                raise ValueError("Native integration returned a nonfinite property")
            if key.endswith("error_estimate") and not 0 <= value <= epsilon:
                raise ValueError("Native integration did not reach the requested accuracy")
        return result

    try:
        source = Part.Shape()
        source.read(str(source_path))
        sound_solid(source)
        save("read_exact_native_cad", {
            "volume_mm3": source.Volume, "area_mm2": source.Area,
            "faces": len(source.Faces), "native_version": FreeCAD.Version(),
        })

        # Partition the existing central external faces only. This leaves a single
        # continuum and adds a selectable rear-half surface; no convenient point
        # load or new geometry is substituted for the declared distributed patch.
        central = []
        for index, face in enumerate(source.Faces):
            # Spline control-net bounds can extend beyond the actual trimmed
            # surface. Classify the native surface without relying on a display
            # tessellation; keep the declared geometric thresholds unchanged.
            box = face.optimalBoundingBox(False, False)
            if (box.XMin >= 15.5 - 1e-6 and box.XMax <= 80.5 + 1e-6
                    and box.XLength > 1e-3 and box.ZMin >= 25 - 5e-5):
                central.append(index)
        if not central:
            raise ValueError("Could not identify the actual central grip surface")
        central_bounds = [source.Faces[i].optimalBoundingBox(False, False)
                          for i in central]
        intervals = sorted((box.XMin, box.XMax) for box in central_bounds)
        covered = 15.5
        for lower, upper in intervals:
            if lower > covered + 1e-6:
                raise ValueError("Central surface selection has an axial gap")
            covered = max(covered, upper)
        if covered < 80.5 - 1e-6:
            raise ValueError("Central surface selection misses the required span")
        faces = []
        rear_area = 0.0
        partitions = []
        for index, face in enumerate(source.Faces):
            if index not in central:
                faces.append(face)
                continue
            # This original grip uses U=0..2pi around its oval and V along X.
            # Trim its existing surface directly. Boolean cutting of this seam
            # produced a wrapped front face and inflated tolerance when sewn.
            surface = face.Surface
            u0, u1, v0, v1 = face.ParameterRange
            if (type(surface).__name__ != "BSplineSurface"
                    or abs(u0) > 1e-12 or abs(u1 - 2 * math.pi) > 1e-12
                    or abs(v0 - face.optimalBoundingBox(False, False).XMin) > 1e-6
                    or abs(v1 - face.optimalBoundingBox(False, False).XMax) > 1e-6):
                raise ValueError("Grip surface does not match the declared native parameterization")
            front = Part.RectangularTrimmedSurface(surface, u0, math.pi, v0, v1).toShape()
            rear = Part.RectangularTrimmedSurface(surface, math.pi, u1, v0, v1).toShape()
            for patch in (front, rear):
                if patch.Orientation != face.Orientation:
                    patch.reverse()
                if not patch.isValid():
                    raise ValueError("Native grip patch is invalid")
            if (rear.optimalBoundingBox(False, False).ZMax > 29.5 + 1e-6
                    or front.optimalBoundingBox(False, False).ZMin < 29.5 - 1e-6):
                raise ValueError("Native grip patches do not match the declared load plane")
            rear_area += measured_properties(rear)["area_mm2"]
            partitions.append({"source_face_index_zero_based": index,
                               "original_parameter_range": [u0, u1, v0, v1],
                               "front_parameter_range": list(front.ParameterRange),
                               "rear_parameter_range": list(rear.ParameterRange)})
            faces.extend([front, rear])
        shell = Part.makeShell(faces)
        shell.sewShape()
        if len(shell.Shells) != 1:
            raise ValueError("Partition did not preserve one closed native shell")
        study_shape = Part.makeSolid(shell.Shells[0])
        sound_solid(study_shape)
        original_properties = measured_properties(source, volume=True)
        partition_properties = measured_properties(study_shape, volume=True)
        volume_error = abs(partition_properties["volume_mm3"] - original_properties["volume_mm3"])
        area_error = abs(partition_properties["area_mm2"] - original_properties["area_mm2"])
        cuts = [source.cut(study_shape), study_shape.cut(source)]
        difference = sum(shape.Volume for shape in cuts)
        # Keep the earlier numerical limits; improve measurement, not tolerance.
        volume_limit = max(1e-7, source.Volume * 1e-8)
        area_limit = max(1e-7, source.Area * 1e-8)
        original_tolerance = source.getTolerance(1)
        partition_tolerance = study_shape.getTolerance(1)
        passed = (volume_error <= volume_limit and area_error <= area_limit
                  and difference <= volume_limit
                  and not any(shape.Faces or shape.Solids for shape in cuts)
                  and partition_tolerance <= original_tolerance + 1e-9)
        # Retain the actual failing quantities before enforcing the gate.
        save("partition_correspondence", {
            "passed": passed,
            "method": "Native parameter-space trim; BRepGProp adaptive integration",
            "original_properties": original_properties,
            "partition_properties": partition_properties,
            "original_max_tolerance_mm": original_tolerance,
            "partition_max_tolerance_mm": partition_tolerance,
            "partition_ranges": partitions,
            "source_face_indices_zero_based": central,
            "volume_difference_mm3": volume_error,
            "volume_difference_limit_mm3": volume_limit,
            "area_difference_mm2": area_error,
            "area_difference_limit_mm2": area_limit,
            "symmetric_difference_volume_mm3": difference,
            "rear_surface_area_mm2": rear_area,
        })
        if not passed:
            raise ValueError("Analysis partition does not preserve the declared CAD solid")
        study_shape.exportBrep(str(output / "analysis-partition.brep"))

        supports = []
        for bolt_x in (0.0, 96.0):
            matches = []
            for i, face in enumerate(study_shape.Faces, 1):
                surface = face.Surface
                if type(surface).__name__ != "Cylinder":
                    continue
                axis, center, radius = surface.Axis, surface.Center, surface.Radius
                box = face.optimalBoundingBox(False, False)
                if (abs(abs(axis.z) - 1) <= 1e-8
                        and abs(center.x - bolt_x) <= 1e-6
                        and abs(center.y) <= 1e-6 and 2.25 <= radius <= 2.2515
                        and abs(box.ZMin - 1.02) <= 1e-5
                        and abs(box.ZMax - 3.98) <= 1e-5):
                    matches.append(f"Face{i}")
            if len(matches) != 1:
                raise ValueError(f"Expected one exact bore barrel at X={bolt_x}")
            supports.extend(matches)
        loaded = []
        for i, face in enumerate(study_shape.Faces, 1):
            box = face.optimalBoundingBox(False, False)
            if (box.XMin >= 15.5 - 1e-6 and box.XMax <= 80.5 + 1e-6
                    and box.XLength > 1e-3 and box.ZMin >= 25 - 5e-5
                    and box.ZMax <= 29.5 + 1e-6):
                loaded.append(i)
        load_properties = [measured_properties(study_shape.Faces[i - 1]) for i in loaded]
        area = sum(item["area_mm2"] for item in load_properties)
        if not loaded or area <= 0 or abs(area - rear_area) > max(1e-7, area * 1e-7):
            raise ValueError("Final native load faces differ from the rear-half patch")
        centroid = sum((Vector(*item["area_centroid_mm"]) * item["area_mm2"]
                        for item in load_properties), Vector()) / area

        doc = FreeCAD.newDocument(name)
        body = doc.addObject("Part::Feature", "AnalysisBody")
        body.Shape = study_shape
        analysis = ObjectsFem.makeAnalysis(doc, "HandleAnalysis")
        material = ObjectsFem.makeMaterialSolid(doc, "IllustrativeMaterial")
        material.Material = {
            "Name": "Illustrative homogeneous elastic assumption; not calibrated PETG",
            "YoungsModulus": "2000 MPa", "PoissonRatio": "0.38",
        }
        analysis.addObject(material)
        fixed = ObjectsFem.makeConstraintFixed(doc, "FixedBoreBarrels")
        fixed.References = [(body, supports)]
        analysis.addObject(fixed)
        axis_object = doc.addObject("Part::Feature", "PositiveZLoadDirection")
        axis_object.Shape = Part.makeLine(Vector(0, 0, 0), Vector(0, 0, 1))
        load = ObjectsFem.makeConstraintForce(doc, "DistributedGripPull")
        load.References = [(body, [f"Face{i}" for i in loaded])]
        load.Direction = (axis_object, ["Edge1"])
        load.Reversed = False
        load.Force = "40 N"
        analysis.addObject(load)
        doc.recompute()
        direction = load.DirectionVector
        if (abs(direction.x) > 1e-8 or abs(direction.y) > 1e-8
                or abs(direction.z - 1) > 1e-8):
            raise ValueError("Native force direction is not the declared positive Z")
        axis_object.ViewObject.Visibility = False
        save("native_material_and_boundary_objects", {
            "fixed_faces": supports,
            "load_faces": [f"Face{i}" for i in loaded],
            "load_area_mm2": area,
            "load_area_centroid_mm": [centroid.x, centroid.y, centroid.z],
            "expected_total_force_N": [0, 0, 40],
            "expected_load_moment_about_origin_N_mm": [40 * centroid.y, -40 * centroid.x, 0],
            "material_assumptions": {"E_MPa": 2000, "nu": 0.38},
            "native_deck_resultant_and_reactions": "not yet observed; required after solve",
        })

        mesh = ObjectsFem.makeMeshGmsh(doc, "HandleMesh")
        geometry_property = "Shape" if hasattr(mesh, "Shape") else "Part"
        setattr(mesh, geometry_property, body)
        mesh.CharacteristicLengthMax = float(config["mesh_max_mm"])
        mesh.CharacteristicLengthMin = float(config["mesh_min_mm"])
        mesh.ElementOrder = "2nd"
        analysis.addObject(mesh)
        doc.recompute()
        error = GmshTools(mesh).create_mesh()
        if error:
            raise ValueError(f"Native Gmsh reported a failure: {error}")
        native_mesh = mesh.FemMesh
        volumes = list(native_mesh.Volumes)
        if not native_mesh.NodeCount or not volumes:
            raise ValueError("Native mesher did not create a volume mesh")
        counts = {len(native_mesh.getElementNodes(i)) for i in volumes}
        if counts != {10}:
            raise ValueError("Expected only second-order tetrahedral volume elements")
        for point in native_mesh.Nodes.values():
            if not all(math.isfinite(v) for v in (point.x, point.y, point.z)):
                raise ValueError("Native mesh has a nonfinite node")
        native_mesh.write(str(output / "mesh.inp"))
        doc.saveAs(str(output / "prepared-analysis.FCStd"))
        save("actual_native_mesh", {
            "nodes": native_mesh.NodeCount, "volume_elements": len(volumes),
            "nodes_per_volume_element": sorted(counts),
            "requested_global_max_mm": float(config["mesh_max_mm"]),
            "requested_global_min_mm": float(config["mesh_min_mm"]),
            "quality_and_refinement": "not established by mesh settings; inspect native solve and matched refinements",
        })
        report["status"] = "native_analysis_prepared_not_solved"
        report["remaining"] = [
            "Call discovered run_fem_analysis for this exact native document/analysis",
            "Retain actual INP/FRD/DAT/logs before timeout recovery or another call",
            "Verify deck selections, force/moment balance, fields and mesh sensitivity",
            "Existing exact geometry checks, declared human reviews and downstream deliverable gates",
        ]
        report["elapsed_seconds"] = time.monotonic() - started
        with (output / "prepared-analysis.json").open("x") as stream:
            json.dump(report, stream, indent=2)
        print("PRINTED02_ANALYSIS_PREPARATION", json.dumps(report, sort_keys=True))
        return report
    except Exception as exc:
        report.update(status="failed", failure_type=type(exc).__name__,
                      failure=str(exc), traceback=traceback.format_exc(),
                      elapsed_seconds=time.monotonic() - started)
        with (output / "failed-preparation.json").open("x") as stream:
            json.dump(report, stream, indent=2)
        raise
