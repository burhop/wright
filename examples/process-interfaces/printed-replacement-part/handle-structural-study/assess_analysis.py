"""Measure this study's retained native static C3D10 fields through FreeCAD MCP.

Invoke assess_analysis(CONFIG) as a declared workflow operation. This is a passive
engineering calculation, not a solver, process executor or review authority.
CalculiX 2.21 gauss.f / printoutint.f / printoutelem.f establish the native point
order and quadrature convention. The quadratic barycentric basis below computes
physical weights, checked against every native COORD and EVOL record.
"""


def assess_analysis(config):
    import csv
    import hashlib
    import json
    import math
    import time
    from pathlib import Path

    import numpy as np
    import Part
    import FreeCAD

    began = time.monotonic()
    root = Path(config["workspace_root"])

    def path(key):
        p = Path(config[key])
        if not p.is_absolute() or p.resolve() != p or not p.is_relative_to(root):
            raise ValueError("Use real paths within the declared workspace: " + key)
        return p

    if not root.is_absolute() or root.resolve() != root:
        raise ValueError("Invalid workspace root")
    output = path("output_dir")
    if output == root or output.exists():
        raise ValueError("Preserve prior assessment outputs")
    output.mkdir(parents=True)
    report = {"schema_version": "printed02.structural-assessment/1",
              "run_id": config["run_id"], "source_run_id": config["source_run_id"],
              "geometry_label": config.get("geometry_label", "Original handle"),
              "engineering_acceptance": False, "physical_acceptance": False,
              "checks": [], "remaining": ["Matched mesh refinement", "Peak nodal stress location", "Native solver warning review", "Engineering review",
                                               "Exact geometry and downstream deliverable checks"]}

    def verified(key, expected):
        p = path(key)
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError("Changed input: " + key)
        return p

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    try:
        collection_path = verified("collection", config["collection_sha256"])
        prepared_path = verified("prepared", config["prepared_sha256"])
        partition = verified("partition", config["partition_sha256"])
        collection = json.loads(collection_path.read_text())
        prepared = json.loads(prepared_path.read_text())
        require(collection["run_id"] == config["source_run_id"], "Collection run differs")
        require(prepared["study_revision"] == "printed02-structural-S1-L1-r1", "Unsupported study")
        require(collection["deck_nodes_equal_prepared_mesh"] is True, "Unmatched prepared mesh")
        report["inputs"] = {key: config[key] for key in (
            "collection_sha256", "prepared_sha256", "partition_sha256")}
        report["original_brep_sha256"] = prepared["input_brep_sha256"]
        files = {}
        for item in collection["files"]:
            p = collection_path.parent / item["name"]
            require(p.resolve() == p and p.parent == collection_path.parent, "Invalid retained path")
            require(p.stat().st_size == item["bytes"] and
                    hashlib.sha256(p.read_bytes()).hexdigest() == item["sha256"], "Changed native file")
            files[item["name"]] = p

        nodes, elements, sets, loads, bounds = {}, {}, {}, {}, []
        mode = ""
        material, steps, statics = [], 0, 0
        for raw in files["solver.inp"].read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                fields = [s.strip().upper() for s in line.split(",")]
                mode = fields[0]
                require(mode not in {"*EQUATION", "*MPC", "*TRANSFORM", "*DLOAD", "*CFLUX",
                                     "*TEMPERATURE", "*ORIENTATION"}, "Unsupported load/material/constraint")
                if mode == "*ELEMENT":
                    require("TYPE=C3D10" in fields, "Only native C3D10 is supported")
                if mode == "*NSET":
                    require("GENERATE" not in fields, "Generated node sets unsupported")
                    name = next(s.split("=", 1)[1] for s in fields if s.startswith("NSET="))
                    sets.setdefault(name, [])
                if mode == "*STEP":
                    steps += 1
                    require(not any("NLGEOM" in s for s in fields), "Nonlinear geometry unsupported")
                statics += mode == "*STATIC"
                continue
            fields = [s.strip() for s in line.split(",") if s.strip()]
            if mode == "*NODE":
                key = int(fields[0]); require(key not in nodes and len(fields) == 4, "Invalid node")
                nodes[key] = list(map(float, fields[1:]))
            elif mode == "*ELEMENT":
                key = int(fields[0]); require(key not in elements and len(fields) == 11, "Invalid element")
                elements[key] = list(map(int, fields[1:]))
            elif mode == "*NSET":
                sets[name].extend(map(int, fields))
            elif mode == "*BOUNDARY":
                bounds.append(fields)
            elif mode == "*CLOAD":
                node, dof, value = int(fields[0]), int(fields[1]), float(fields[2])
                require(dof in (1, 2, 3), "Unsupported loaded degree of freedom")
                loads.setdefault(node, [0., 0., 0.])[dof - 1] += value
            elif mode == "*ELASTIC":
                material.append(list(map(float, fields)))
        require(steps == statics == 1 and material == [[2000., .38]], "Study physics differs")
        require(bounds == [["FixedBoreBarrels", str(i)] for i in (1, 2, 3)], "Study support differs")
        support = set(sets["FIXEDBOREBARRELS"])
        require(nodes and elements and support and loads and not (support & set(loads)), "Empty/overlapping sets")
        require(len(nodes) == collection["nodes"], "Mesh node coverage differs")

        # Require one complete static frame for every expected native field.
        definitions = {
            "displacements (vx,vy,vz) for set NALL ": ("displacements", 1, 3),
            "forces (fx,fy,fz) for set NALL ": ("forces", 1, 3),
            "stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set EALL ": ("stresses", 2, 6),
            "global coordinates (elem, integ.pnt.,x,y,z) for set EALL ": ("coordinates", 2, 3),
            "volume (element, volume) for set EALL ": ("volumes", 1, 1),
        }
        data, active, started, frame_times = {}, None, False, []
        for raw in files["solver.dat"].open():
            line = raw.strip()
            selected = next((spec for prefix, spec in definitions.items() if line.startswith(prefix)), None)
            if selected:
                key, ids, width = selected
                require(key not in data, "Repeated native result frame")
                data[key] = {}; active = selected; started = False
                frame_times.append(float(line.rsplit(" ", 1)[-1])); continue
            if not active:
                continue
            if not line:
                if started:
                    active = None
                continue
            key, ids, width = active; fields = line.split()
            require(len(fields) == ids + width, "Unexpected native field shape")
            identity = tuple(map(int, fields[:ids])) if ids == 2 else int(fields[0])
            values = list(map(float, fields[ids:]))
            require(identity not in data[key] and all(map(math.isfinite, values)), "Invalid native field")
            data[key][identity] = values; started = True
        require(set(data) == {v[0] for v in definitions.values()} and set(frame_times) == {1.}, "Incomplete frame")
        require(set(data["forces"]) == set(data["displacements"]) == set(nodes), "Incomplete nodal field")
        expected = {(e, i) for e in elements for i in range(1, 5)}
        require(set(data["stresses"]) == set(data["coordinates"]) == expected and
                set(data["volumes"]) == set(elements), "Incomplete integration field")

        element_ids = sorted(elements)
        xyz = np.asarray([[nodes[n] for n in elements[e]] for e in element_ids])
        require(np.isfinite(xyz).all(), "Non-finite mesh")
        a, b = (5 + 3 * math.sqrt(5)) / 20, (5 - math.sqrt(5)) / 20
        barycentric = np.full((4, 4), b); np.fill_diagonal(barycentric, a)
        gradients = np.array([[-1., -1., -1.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
        edges = [(0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)]
        basis = np.empty((4, 10)); derivative = np.empty((4, 10, 3))
        for p, lam in enumerate(barycentric):
            basis[p, :4] = lam * (2 * lam - 1)
            derivative[p, :4] = (4 * lam - 1)[:, None] * gradients
            for k, (i, j) in enumerate(edges, 4):
                basis[p, k] = 4 * lam[i] * lam[j]
                derivative[p, k] = 4 * (lam[i] * gradients[j] + lam[j] * gradients[i])
        coordinates = np.einsum("pn,enx->epx", basis, xyz)
        determinants = np.linalg.det(np.einsum("enx,pnq->epxq", xyz, derivative))
        require(np.isfinite(determinants).all() and (determinants > 0).all(), "Invalid/inverted integration Jacobian")
        weights = determinants / 24
        keys = [(e, i) for e in element_ids for i in range(1, 5)]
        native_coordinates = np.asarray([data["coordinates"][key] for key in keys]).reshape((-1, 4, 3))
        native_volumes = np.asarray([data["volumes"][e][0] for e in element_ids])
        # Native DAT writes seven significant decimal digits (E13.6).
        coord_error = np.abs(coordinates - native_coordinates)
        volume_error = np.abs(weights.sum(axis=1) - native_volumes)
        require((coord_error <= 5.1e-7 * np.maximum(1, np.abs(native_coordinates))).all(), "Native point coordinates differ")
        require((volume_error <= np.maximum(1e-10, 5.1e-7 * np.abs(native_volumes))).all(), "Native element volumes differ")
        points, weights = coordinates.reshape((-1, 3)), weights.reshape(-1)
        stress = np.asarray([data["stresses"][key] for key in keys])
        xx, yy, zz, xy, xz, yz = stress.T
        vm = np.sqrt(.5 * ((xx - yy)**2 + (yy - zz)**2 + (zz - xx)**2) + 3 * (xy**2 + xz**2 + yz**2))
        tensor = np.empty((len(keys), 3, 3))
        tensor[:, 0, 0], tensor[:, 1, 1], tensor[:, 2, 2] = xx, yy, zz
        tensor[:, 0, 1] = tensor[:, 1, 0] = xy
        tensor[:, 0, 2] = tensor[:, 2, 0] = xz
        tensor[:, 1, 2] = tensor[:, 2, 1] = yz
        principal = np.linalg.eigvalsh(tensor)[:, -1]
        require(np.isfinite(principal).all() and np.isfinite(vm).all(), "Invalid stress measures")

        def sum_vectors(rows):
            return np.asarray([math.fsum(v[i] for v in rows) for i in range(3)])

        applied = sum_vectors(list(loads.values()))
        reaction = sum_vectors([data["forces"][n] for n in support])
        applied_moment = sum_vectors([np.cross(nodes[n], f) for n, f in loads.items()])
        reaction_moment = sum_vectors([np.cross(nodes[n], data["forces"][n]) for n in support])
        require(all(f[:2] == [0., 0.] for f in loads.values()) and applied[2] > 0, "Load direction differs")
        compliance = math.fsum(f * u for n, load in loads.items() for f, u in zip(load, data["displacements"][n]))
        displacement_node = max(nodes, key=lambda n: math.hypot(*data["displacements"][n]))
        report["equilibrium"] = {"applied_N": applied.tolist(), "reaction_N": reaction.tolist(),
                                 "applied_moment_Nmm": applied_moment.tolist(), "reaction_moment_Nmm": reaction_moment.tolist()}
        for name, value, limit, unit in (
            ("Force balance", float(np.linalg.norm(applied + reaction)), .4, "N"),
            ("Moment balance", float(np.linalg.norm(applied_moment + reaction_moment)), max(.01 * np.linalg.norm(applied_moment), .4), "N mm"),
            ("Load resultant", float(np.linalg.norm(applied - [0, 0, 40])), .4, "N"),
        ):
            report["checks"].append({"name": name, "value": value, "limit": float(limit), "unit": unit, "passed": bool(value <= limit)})

        # Native BREP distances; axis-aligned bounds only reject impossible candidates.
        shape = Part.Shape(); shape.read(str(partition))
        boundary = next(s for s in prepared["steps"] if s["name"] == "native_material_and_boundary_objects")
        require(shape.isValid(), "Invalid retained CAD")
        fixed_faces = [shape.Faces[int(name[4:]) - 1] for name in boundary["fixed_faces"]]
        load_faces = [shape.Faces[int(name[4:]) - 1] for name in boundary["load_faces"]]

        def near_shapes(shapes):
            mask = np.zeros(len(points), dtype=bool)
            for surface in shapes:
                box = surface.optimalBoundingBox(False, False)
                low = np.array([box.XMin, box.YMin, box.ZMin]) - 2
                high = np.array([box.XMax, box.YMax, box.ZMax]) + 2
                candidates = np.flatnonzero(((points >= low) & (points <= high)).all(axis=1) & ~mask)
                for i in candidates:
                    distance = Part.Vertex(FreeCAD.Vector(*points[i])).distToShape(surface)[0]
                    require(math.isfinite(distance) and distance >= 0, "Invalid boundary distance")
                    mask[i] = distance <= 2
            return mask

        near_support = near_shapes(fixed_faces)
        near_load = near_shapes([edge for face in load_faces for edge in face.Edges])
        x, y, z = points.T
        regions = {"Left root": (x <= 15.5) & (z >= 5) & (z <= 12),
                   "Right root": (x >= 80.5) & (z >= 5) & (z <= 12),
                   "Central grip": (x >= 15.5) & (x <= 80.5) & (z >= 25),
                   "Pads": (z >= 0) & (z <= 5)}

        def quantile(values, selected_weights):
            order = np.argsort(values, kind="stable")
            i = np.searchsorted(np.cumsum(selected_weights[order]), .95 * math.fsum(selected_weights), side="left")
            return float(values[order[min(i, len(order) - 1)]])

        def statistics(mask):
            if not mask.any():
                return {"points": 0, "volume_mm3": 0., "status": "empty"}
            return {"points": int(mask.sum()), "volume_mm3": math.fsum(weights[mask]),
                    "vm_p95_MPa": quantile(vm[mask], weights[mask]),
                    "principal_p95_MPa": quantile(principal[mask], weights[mask]),
                    "principal_peak_MPa": float(principal[mask].max()),
                    "vm_peak_MPa": float(vm[mask].max())}

        peak = int(vm.argmax())
        report.update(status="native_fields_assessed_comparison_pending",
                      mesh={"nodes": len(nodes), "elements": len(elements), "integration_points": len(keys),
                            "volume_mm3": math.fsum(weights), "min_jacobian_mm3": float(determinants.min()),
                            "native_coordinate_error_max_mm": float(coord_error.max()),
                            "native_volume_error_max_mm3": float(volume_error.max())},
                      displacement={"maximum_mm": math.hypot(*data["displacements"][displacement_node]),
                                    "peak_node": displacement_node, "peak_location_mm": nodes[displacement_node],
                                    "load_weighted_mean_Uz_mm": compliance / applied[2], "compliance_Nmm": compliance},
                      stress={"integration_point_peak_MPa": float(vm[peak]), "peak_location_mm": points[peak].tolist(),
                              "element": keys[peak][0], "point": keys[peak][1],
                              "prior_nodal_peak_MPa": collection["solver"]["max_von_mises_MPa"],
                              "nodal_peak_location": "Not read by this integration-point assessment"},
                      regions={name: {"full": statistics(mask), "within_2mm_support": statistics(mask & near_support),
                                      "within_2mm_load_perimeter": statistics(mask & near_load)} for name, mask in regions.items()},
                      boundary_zones={"within_2mm_support": statistics(near_support), "within_2mm_load_perimeter": statistics(near_load)},
                      method="Native integration-point stresses; quadratic barycentric geometry; positive Jacobian / 24 volume weights; native COORD/EVOL reconciliation; first cumulative volume >=95%; native BREP boundary distances")
        require(all(value["full"]["points"] for value in report["regions"].values()), "Empty study region")
        with (output / "integration-points.csv").open("x", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Element", "Point", "X (mm)", "Y (mm)", "Z (mm)", "Volume weight (mm3)",
                             "Von Mises (MPa)", "Max principal (MPa)", "Within 2 mm support", "Within 2 mm load perimeter"])
            for i, key in enumerate(keys):
                writer.writerow([*key, *points[i], weights[i], vm[i], principal[i], bool(near_support[i]), bool(near_load[i])])
        report["elapsed_seconds"] = time.monotonic() - began
        (output / "assessment.json").write_text(json.dumps(report, indent=2) + "\n")
        lines = [f"# {report['geometry_label']}: structural assessment", "", "Mesh comparison and engineering review remain pending.", "",
                 "| Quantity | Value |", "| --- | ---: |",
                 f"| Mesh nodes | {len(nodes):,} |",
                 f"| Quadratic tetrahedra | {len(elements):,} |",
                 f"| Maximum displacement | {report['displacement']['maximum_mm']:.4f} mm |",
                 f"| Load-weighted mean displacement | {compliance / applied[2]:.4f} mm |",
                 f"| Compliance | {compliance:.4f} N·mm |",
                 f"| Peak integration-point von Mises | {vm[peak]:.3f} MPa |", "",
                 "| Region | Volume (mm³) | Volume-weighted P95 von Mises (MPa) | P95 maximum principal (MPa) |",
                 "| --- | ---: | ---: | ---: |"]
        for name, item in report["regions"].items():
            full = item["full"]
            lines.append(f"| {name} | {full['volume_mm3']:.2f} | {full['vm_p95_MPa']:.3f} | {full['principal_p95_MPa']:.3f} |")
        lines += ["", "| Numerical check | Measured | Limit | Result |", "| --- | ---: | ---: | --- |"]
        for check in report["checks"]:
            lines.append(f"| {check['name']} | {check['value']:.6g} {check['unit']} | {check['limit']:.6g} {check['unit']} | {'Within limit' if check['passed'] else 'Outside limit'} |")
        lines += ["", "| Boundary diagnostic | Volume (mm³) | P95 von Mises (MPa) |", "| --- | ---: | ---: |"]
        for label, key in [("Within 2 mm of fixed bores", "within_2mm_support"), ("Within 2 mm of load perimeter", "within_2mm_load_perimeter")]:
            item = report["boundary_zones"][key]
            value = f"{item['vm_p95_MPa']:.3f}" if item["points"] else "No samples"
            lines.append(f"| {label} | {item['volume_mm3']:.2f} | {value} |")
        lines += ["", "Full regions include their boundary zones. All native fields and integration samples are retained.", "",
                  "These are measurements of the documented homogeneous-solid model under a 40 N pull. They do not establish printed-part strength, engineering approval or a design improvement.", ""]
        (output / "assessment.md").write_text("\n".join(lines))
        print("Structural field assessment retained:", str(output))
        return {"status": report["status"], "output_dir": str(output), "integration_points": len(keys),
                "numerical_checks_within_limits": all(c["passed"] for c in report["checks"]),
                "engineering_acceptance": False, "elapsed_seconds": report["elapsed_seconds"]}
    except Exception as error:
        report.update(status="assessment_failed", error=str(error), elapsed_seconds=time.monotonic() - began)
        (output / "assessment-failure.json").write_text(json.dumps(report, indent=2) + "\n")
        raise
