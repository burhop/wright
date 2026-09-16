"""Fixed CAD-region to OpenFOAM10 compiler; no arbitrary script/dictionary input.

STEP solids, region identities and physical numbers are explicit design inputs.
Gmsh/OCC derives the actual conformal mesh; OpenFOAM performs the actual solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


MAX_CLOSED_SOLIDS_PER_REGION = 64
MAX_IMPORTED_SOLIDS = 128


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def name(value):
    if not isinstance(value, str) or not re.fullmatch("[a-z][a-z0-9_]{0,39}", value):
        raise ValueError("Region and boundary names require lowercase safe identifiers")
    return value


def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError("Physical number is absent, nonfinite or outside the supported range")
    return float(value)


def _validate_cad_evidence(evidence):
    """Validate optional bounded CAD inspection provenance.

    Evidence is descriptive lineage emitted by the CAD authoring step.  It is
    never interpreted as physics, a boundary selector, or executable input.
    Keeping the shape closed prevents this provenance field from becoming a
    dictionary/source injection channel.
    """
    if evidence is None:
        return
    if not isinstance(evidence, dict):
        raise ValueError("CAD evidence must be an object")
    allowed = {"fluid_step_sha256", "fluid_domain_observed_bounds_mm", "fan_inlet_face", "outlet_face"}
    if set(evidence) - allowed:
        raise ValueError("Unsupported CAD evidence field")
    digest = evidence.get("fluid_step_sha256")
    if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)):
        raise ValueError("CAD evidence fluid STEP digest is invalid")
    bounds = evidence.get("fluid_domain_observed_bounds_mm")
    if bounds is not None:
        if not isinstance(bounds, dict) or set(bounds) != {"x_min", "x_max", "y_min", "y_max", "z_min", "z_max"}:
            raise ValueError("CAD evidence domain bounds are invalid")
        for value in bounds.values():
            number(value, -100000, 100000)
    for key in ("fan_inlet_face", "outlet_face"):
        face = evidence.get(key)
        if face is None:
            continue
        if not isinstance(face, dict) or set(face) != {"inspection_method", "matching_face_count", "selected_face_index", "observed_bounds_mm", "observed_area_mm2"}:
            raise ValueError("CAD evidence face record is invalid")
        if not isinstance(face["inspection_method"], str) or not face["inspection_method"] or len(face["inspection_method"]) > 256:
            raise ValueError("CAD evidence inspection method is invalid")
        if isinstance(face["matching_face_count"], bool) or not isinstance(face["matching_face_count"], int) or not 0 <= face["matching_face_count"] <= 10000:
            raise ValueError("CAD evidence matching face count is invalid")
        if isinstance(face["selected_face_index"], bool) or not isinstance(face["selected_face_index"], int) or not 0 <= face["selected_face_index"] <= 1000000:
            raise ValueError("CAD evidence selected face index is invalid")
        face_bounds = face["observed_bounds_mm"]
        if not isinstance(face_bounds, dict) or set(face_bounds) != {"x_min", "x_max", "y_min", "y_max", "z_min", "z_max"}:
            raise ValueError("CAD evidence face bounds are invalid")
        for value in face_bounds.values():
            number(value, -100000, 100000)
        number(face["observed_area_mm2"], 0, 1e12)


def numerical_profile(contract):
    """Keep legacy transient inputs; require an explicit versioned steady profile."""
    if contract.get("schema_version") == 1:
        return {"mode": "transient", "end": number(contract["duration_s"], .001, 3600),
                "delta": number(contract["delta_t_s"], .00001, 1), "write_interval": 1}
    profile = contract.get("numerics")
    if not isinstance(profile, dict) or set(profile) != {"mode", "iterations", "write_interval"} or profile["mode"] != "steady":
        raise ValueError("Version 2 requires an explicit steady numerical profile")
    for key, high in (("iterations", 5000), ("write_interval", profile["iterations"])):
        value = profile[key]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= high:
            raise ValueError("Steady iterations and write interval must be bounded positive integers")
    if profile["iterations"] % profile["write_interval"]:
        raise ValueError("The final declared iteration must write its actual fields")
    return {"mode": "steady", "end": profile["iterations"], "delta": 1,
            "write_interval": profile["write_interval"]}


def path_under(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("Use relative POSIX paths")
    path = Path(relative)
    if path.is_absolute() or any(part.startswith(".") for part in path.parts):
        raise ValueError("Absolute, hidden and parent paths are forbidden")
    result = (root/path).resolve()
    if not result.is_relative_to(root):
        raise ValueError("Path escapes attempt")
    return result


def validate(contract, root):
    allowed = {"schema_version", "units", "ambient_k", "gravity_m_s2", "mesh_size_mm", "duration_s", "delta_t_s", "regions", "boundaries", "assumptions", "fan_curve", "evidence"}
    if contract.get("schema_version") == 2:
        allowed = (allowed-{"duration_s", "delta_t_s"}) | {"numerics", "mesh_grading"}
    if set(contract)-allowed or contract.get("schema_version") not in {1, 2} or contract.get("units") != "mm":
        raise ValueError("Unsupported declarative contract; source and dictionary injection are forbidden")
    number(contract["ambient_k"], 250, 400)
    number(contract["mesh_size_mm"], .2, 20)
    numerical_profile(contract)
    _validate_cad_evidence(contract.get("evidence"))
    if contract.get("schema_version") == 2:
        grading = contract.get("mesh_grading")
        if not isinstance(grading, dict) or set(grading) != {"far_size_mm", "distance_min_mm", "distance_max_mm"}:
            raise ValueError("Version 2 requires an explicit CAD-surface mesh grading profile")
        number(grading["far_size_mm"], contract["mesh_size_mm"], 30)
        number(grading["distance_min_mm"], 0, 20)
        number(grading["distance_max_mm"], grading["distance_min_mm"]+.01, 100)
    if len(contract["gravity_m_s2"]) != 3:
        raise ValueError("Gravity requires three explicit components")
    for value in contract["gravity_m_s2"]:
        number(value, -10, 10)
    regions = contract["regions"]
    if not 2 <= len(regions) <= 12 or sum(r["kind"] == "fluid" for r in regions) != 1:
        raise ValueError("One air region and one to eleven solid regions required")
    identities = set()
    for region in regions:
        if set(region)-{"name", "kind", "step", "sha256", "material", "heat_w"}:
            raise ValueError("Unsupported region field")
        identity = name(region["name"])
        if identity in identities or region["kind"] not in {"fluid", "solid"}:
            raise ValueError("Duplicate or unsupported region identity")
        identities.add(identity)
        path = path_under(root, region["step"])
        if path.suffix.lower() not in {".step", ".stp"} or sha(path) != region["sha256"]:
            raise ValueError("Actual CAD STEP bytes do not match declared lineage")
        number(region.get("heat_w", 0), 0, 100)
        material = region["material"]
        if set(material) != {"rho", "cp", "kappa"}:
            raise ValueError("Explicit density, heat capacity and conductivity required")
        for key in material:
            number(material[key], 0.0001, 100000)
    boundaries = contract["boundaries"]
    if not isinstance(boundaries, list) or len(boundaries) > 16:
        raise ValueError("A bounded explicit exterior-face selection is required")
    seen = set()
    for boundary in boundaries:
        if set(boundary) != {"name", "region", "axis", "coordinate_mm", "tolerance_mm", "role"}:
            raise ValueError("Boundary requires an exact CAD plane selector and role")
        label = name(boundary["name"])
        if label in seen or boundary["region"] not in identities or boundary["axis"] not in (0, 1, 2):
            raise ValueError("Boundary identity is duplicate or invalid")
        seen.add(label)
        if boundary["role"] not in {"ambient", "inlet", "outlet", "fan"}:
            raise ValueError("Unsupported boundary condition role")
        number(boundary["coordinate_mm"], -10000, 10000)
        number(boundary["tolerance_mm"], .000001, .1)
    fan = contract.get("fan_curve")
    if fan is not None:
        if set(fan) != {"points", "provenance"} or fan["provenance"] != "synthetic_customer_curve":
            raise ValueError("Fan curve requires explicit synthetic customer provenance")
        points = fan["points"]
        if not 2 <= len(points) <= 30:
            raise ValueError("Bounded tabulated fan curve required")
        for point in points:
            if len(point) != 2:
                raise ValueError("Fan curve is volume flow and pressure")
            number(point[0], 0, .1)
            number(point[1], 0, 1000)
        if any(b[0] <= a[0] or b[1] > a[1] for a, b in zip(points, points[1:])):
            raise ValueError("Fan curve must increase in flow and decrease in pressure")
        if sum(boundary["role"] == "fan" for boundary in boundaries) != 1:
            raise ValueError("One actual fan face must be identified")
    elif any(boundary["role"] == "fan" for boundary in boundaries):
        raise ValueError("Fan boundary lacks explicit curve")
    if not contract.get("assumptions"):
        raise ValueError("Explicit engineering assumptions required")
    return regions


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def header(object_name, cls="dictionary"):
    return f"FoamFile {{ version 2.0; format ascii; class {cls}; object {object_name}; }}\n"


def foam_command(case, command):
    if command[0] not in {"gmshToFoam", "splitMeshRegions", "checkMesh", "chtMultiRegionFoam", "foamToVTK"}:
        raise ValueError("Only fixed OpenFOAM applications are available")
    logfile = case/("log."+"_".join(command).replace("/", "_").replace("-", ""))
    # Stream to durable disk so a timeout or host restart cannot discard the log.
    started = time.monotonic()
    with logfile.open("x", encoding="utf-8") as stream:
        try:
            result = subprocess.run(["bash", "-c", '. /opt/openfoam10/etc/bashrc; exec "$@"', "--", *command], cwd=case,
                                    stdout=stream, stderr=subprocess.STDOUT, text=True, timeout=540)
        except subprocess.TimeoutExpired:
            write(logfile.with_suffix(logfile.suffix+".receipt.json"), json.dumps({"command": command, "status": "timed_out", "duration_seconds": time.monotonic()-started}))
            raise
    write(logfile.with_suffix(logfile.suffix+".receipt.json"), json.dumps({"command": command, "exit_code": result.returncode, "duration_seconds": time.monotonic()-started}))
    if result.returncode or "FOAM FATAL" in logfile.read_text():
        raise ValueError("Actual OpenFOAM application failed: "+str(logfile))
    return logfile


def classify_fragment_owners(imported_owners, mappings):
    """Group OCC fragments by material region and expose cross-region overlap."""
    if len(imported_owners) != len(mappings) or any(not mapping for mapping in mappings):
        raise ValueError("CAD region fragmentation lost an imported volume")
    fragment_owners = {}
    for owner, mapping in zip(imported_owners, mappings):
        for _, fragment in mapping:
            fragment_owners.setdefault(fragment, []).append(owner)
    cross_region = {
        fragment: sorted(set(owners))
        for fragment, owners in fragment_owners.items()
        if len(set(owners)) > 1
    }
    by_owner = {}
    for fragment, owners in fragment_owners.items():
        if fragment not in cross_region:
            by_owner.setdefault(owners[0], set()).add(fragment)
    return {owner: sorted(fragments) for owner, fragments in by_owner.items()}, cross_region, fragment_owners


def record_mesh_progress(case, stages, started, stage):
    entry = {"stage": stage, "elapsed_seconds": round(time.monotonic()-started, 3)}
    stages.append(entry)
    write(case/"mesh-progress.json", json.dumps({"stages": stages}, indent=2))
    # MCP stdio reserves stdout for JSON-RPC frames.
    print(json.dumps(entry), file=sys.stderr, flush=True)
    return entry


def mesh(root, contract, case):
    import gmsh
    regions = validate(contract, root)
    gmsh.initialize(interruptible=False)
    # Native Gmsh output would corrupt the MCP JSON-RPC stdout stream.
    gmsh.option.setNumber("General.Terminal", 0)
    started = time.monotonic()
    stages = []
    def progress(stage):
        record_mesh_progress(case, stages, started, stage)
    try:
        progress("import_started")
        gmsh.model.add("explicit_cad_regions")
        imported = []
        imported_owners = []
        import_summary = []
        for region in regions:
            entities = gmsh.model.occ.importShapes(str(path_under(root, region["step"])))
            volumes = [entity for entity in entities if entity[0] == 3]
            import_summary.append({
                "region": region["name"],
                "step": region["step"],
                "closed_solid_count": len(volumes),
            })
            imported_total = len(imported) + len(volumes)
            if (
                not 1 <= len(volumes) <= MAX_CLOSED_SOLIDS_PER_REGION
                or imported_total > MAX_IMPORTED_SOLIDS
            ):
                diagnostic = {
                    "kind": "cad_region_import",
                    "regions": import_summary,
                    "failed_region": region["name"],
                    "allowed_closed_solids_per_region": {
                        "minimum": 1,
                        "maximum": MAX_CLOSED_SOLIDS_PER_REGION,
                    },
                    "allowed_closed_solids_per_variant": MAX_IMPORTED_SOLIDS,
                    "imported_closed_solids_through_failure": imported_total,
                    "geometry_modified": False,
                }
                write(case/"region-import-diagnostic.json", json.dumps(diagnostic, indent=2))
                raise ValueError(
                    f"CAD region {region['name']!r} imported {len(volumes)} closed solids; "
                    f"at most {MAX_CLOSED_SOLIDS_PER_REGION} are allowed per region "
                    f"and {MAX_IMPORTED_SOLIDS} per variant"
                )
            imported.extend(volumes)
            imported_owners.extend([region["name"]]*len(volumes))
        progress("fragment_started")
        _, mappings = gmsh.model.occ.fragment([imported[0]], imported[1:])
        gmsh.model.occ.synchronize()
        actual = [[entity for entity in mapping if entity[0] == 3] for mapping in mappings]
        owner_fragments, cross_region, fragment_owners = classify_fragment_owners(imported_owners, actual)
        if cross_region:
            diagnostic = {
                "kind": "cad_region_fragment_mapping",
                "source_mapping": [{"region": owner, "imported_volume": entity[1],
                                    "result_volumes": [fragment[1] for fragment in mapping]}
                                   for owner, entity, mapping in zip(imported_owners, imported, actual)],
                "shared_fragments": [{"volume": fragment, "regions": sorted(set(owners)),
                                      "volume_mm3": gmsh.model.occ.getMass(3, fragment)}
                                     for fragment, owners in fragment_owners.items() if fragment in cross_region],
                "geometry_modified": False,
            }
            write(case/"region-mapping-diagnostic.json", json.dumps(diagnostic, indent=2))
            raise ValueError("CAD regions overlap or fragment ambiguously; do not infer region identity")
        progress("region_mapping_passed")
        owners = {}
        volumes = {}
        solid_surfaces = set()
        for region in regions:
            region_volumes = owner_fragments[region["name"]]
            tag = gmsh.model.addPhysicalGroup(3, region_volumes)
            gmsh.model.setPhysicalName(3, tag, region["name"])
            volumes[region["name"]] = sum(gmsh.model.occ.getMass(3, volume) for volume in region_volumes)*1e-9
            for _, surface in gmsh.model.getBoundary([(3, volume) for volume in region_volumes], oriented=False, combined=True):
                owners.setdefault(surface, []).append(region["name"])
                if region["kind"] == "solid":
                    solid_surfaces.add(surface)
        exterior = {}
        for surface, region_names in owners.items():
            if len(region_names) == 2:
                continue
            if len(region_names) != 1:
                raise ValueError("Nonmanifold CAD region interface")
            bounds = gmsh.model.getBoundingBox(2, surface)
            matches = []
            for boundary in contract["boundaries"]:
                axis = boundary["axis"]
                if boundary["region"] == region_names[0] and all(abs(bounds[index]-boundary["coordinate_mm"]) <= boundary["tolerance_mm"] for index in (axis, axis+3)):
                    matches.append(boundary["name"])
            if len(matches) > 1:
                raise ValueError("Ambiguous CAD boundary selector")
            label = matches[0] if matches else "outer_"+region_names[0]
            exterior.setdefault(label, []).append(surface)
        if any(boundary["name"] not in exterior for boundary in contract["boundaries"]):
            raise ValueError("Named inlet/outlet/fan boundary matches no actual CAD face")
        for label, surfaces in exterior.items():
            tag = gmsh.model.addPhysicalGroup(2, surfaces)
            gmsh.model.setPhysicalName(2, tag, label)
        gmsh.option.setNumber("Mesh.MeshSizeMin", contract["mesh_size_mm"])
        gmsh.option.setNumber("Mesh.MeshSizeMax", contract["mesh_size_mm"])
        if contract.get("mesh_grading"):
            grading = contract["mesh_grading"]
            distance = gmsh.model.mesh.field.add("Distance")
            gmsh.model.mesh.field.setNumbers(distance, "SurfacesList", sorted(solid_surfaces))
            gmsh.model.mesh.field.setNumber(distance, "Sampling", 20)
            threshold = gmsh.model.mesh.field.add("Threshold")
            for key, value in {"InField": distance, "SizeMin": contract["mesh_size_mm"], "SizeMax": grading["far_size_mm"],
                               "DistMin": grading["distance_min_mm"], "DistMax": grading["distance_max_mm"]}.items():
                gmsh.model.mesh.field.setNumber(threshold, key, value)
            gmsh.model.mesh.field.setAsBackgroundMesh(threshold)
            gmsh.option.setNumber("Mesh.MeshSizeMax", grading["far_size_mm"])
            gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
            gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
        gmsh.option.setNumber("Mesh.ScalingFactor", .001)
        for dimension in (1, 2, 3):
            progress(f"mesh_{dimension}d_started")
            gmsh.model.mesh.generate(dimension)
        progress("mesh_generated")
        # Gmsh's many small writes are prohibitively slow across Windows/9P.
        # Serialize on native local storage, then transfer the exact bytes in bulk.
        with tempfile.TemporaryDirectory(prefix="wright-cfd-mesh-") as scratch:
            local_mesh = Path(scratch)/"cad-regions.msh"
            gmsh.write(str(local_mesh))
            progress("mesh_serialized")
            shutil.copyfile(local_mesh, case/"cad-regions.msh")
            if sha(local_mesh) != sha(case/"cad-regions.msh"):
                raise ValueError("Native mesh bulk transfer changed its bytes")
        progress("mesh_transferred")
        return {"volumes_m3": volumes, "exterior_face_ids": exterior, "gmsh_version": gmsh.__version__, "unit_scale": .001,
                "mesh_seconds": round(time.monotonic()-started, 3), "refined_solid_surface_ids": sorted(solid_surfaces),
                "mesh_grading": contract.get("mesh_grading")}
    finally:
        gmsh.finalize()


def field(case, region, key, dimensions, initial, boundary_values):
    cls = "volVectorField" if key == "U" else "volScalarField"
    write(case/"0"/region/key, header(key, cls)+f"dimensions [{dimensions}];\ninternalField uniform {initial};\nboundaryField\n{{\n"+boundary_values+"\n}\n")


def validate_split_regions(case, contract):
    """Require splitMeshRegions to preserve the declared material identities."""
    expected = {region["name"] for region in contract["regions"]}
    actual = {
        path.name
        for path in (case/"constant").iterdir()
        if path.is_dir() and (path/"polyMesh/boundary").is_file()
    }
    sampled = set()
    for identity in actual:
        boundary = (case/"constant"/identity/"polyMesh/boundary").read_text()
        sampled.update(re.findall(r"\bsampleRegion\s+([a-zA-Z][a-zA-Z0-9_]*)\s*;", boundary))
    if actual != expected or not sampled.issubset(expected):
        diagnostic = {
            "expected_regions": sorted(expected),
            "actual_regions": sorted(actual),
            "sampled_regions": sorted(sampled),
        }
        write(case/"split-region-diagnostic.json", json.dumps(diagnostic, indent=2))
        raise ValueError("OpenFOAM split regions do not match declared CAD material identities")
    return {"actual_regions": sorted(actual), "sampled_regions": sorted(sampled)}


def steady_solution_controls(text, is_fluid):
    """Apply reviewed OpenFOAM steady buoyant-flow relaxation controls."""
    if not is_fluid:
        return text + "\nrelaxationFactors\n{\n    equations\n    {\n" + (
            "        e               0.1;\n    }\n}\n"
        )
    text, pressure_count = re.subn(
        r"solver\s+GAMG;\s*smoother\s+symGaussSeidel;\s*"
        r"tolerance\s+1e-7;",
        "solver           PCG;\n        preconditioner   DIC;\n"
        "        tolerance        1e-8;",
        text,
        count=1,
    )
    text = text.replace("h               1;", "h               0.1;")
    text = text.replace("U               1;", "U               0.2;")
    marker = "relaxationFactors\n{\n"
    if pressure_count != 1 or marker not in text:
        raise ValueError("Pinned fluid solution lacks the reviewed steady controls")
    return text.replace(
        marker,
        marker + "    fields\n    {\n        p_rgh           0.7;\n    }\n\n",
        1,
    )


def dictionaries(case, contract, observation):
    ambient = contract["ambient_k"]
    regions = contract["regions"]
    fluid = next(region["name"] for region in regions if region["kind"] == "fluid")
    solids = [region["name"] for region in regions if region["kind"] == "solid"]
    profile = numerical_profile(contract)
    observation["numerical_profile"] = profile
    write(case/"constant/regionProperties", header("regionProperties")+f"regions (fluid ({fluid}) solid ({' '.join(solids)}));\n")
    write(case/"system/controlDict", header("controlDict")+f"application chtMultiRegionFoam; startFrom startTime; startTime 0; stopAt endTime; endTime {profile['end']}; deltaT {profile['delta']}; writeControl timeStep; writeInterval {profile['write_interval']}; writeFormat ascii; writePrecision 10; runTimeModifiable false; adjustTimeStep no;\n")
    if contract.get("fan_curve"):
        library = Path("/workspace/pi-boundary-build/lib/libwrightPiFan.so")
        built_source = library.parent.parent/"wrightPrghFanPressure.C"
        authored_source = Path(__file__).parent/"pi_foam_boundary/wrightPrghFanPressure.C"
        if not library.exists() or sha(built_source) != sha(authored_source):
            raise ValueError("Qualified fixed fan adapter is absent or its source changed")
        (case/"lib").mkdir()
        shutil.copyfile(library, case/"lib/libwrightPiFan.so")
        observation["fan_adapter"] = {"source_sha256": sha(authored_source), "library_sha256": sha(library), "law": "Native OpenFOAM fanPressure wrapped by native PrghPressure"}
        with (case/"system/controlDict").open("a") as stream:
            stream.write('libs ("$FOAM_CASE/lib/libwrightPiFan.so");\n')
        write(case/"constant/pressure-vs-q.csv", "volume_flow_m3_s,pressure_pa\n"+"\n".join(f"{flow},{pressure}" for flow, pressure in contract["fan_curve"]["points"])+"\n")
    write(case/"system/fvSchemes", header("fvSchemes"))
    write(case/"system/fvSolution", header("fvSolution")+f"PIMPLE {{ nOuterCorrectors {1 if profile['mode'] == 'steady' else 2}; }}")
    roles = {boundary["name"]: boundary["role"] for boundary in contract["boundaries"]}
    for region in regions:
        identity = region["name"]
        is_fluid = region["kind"] == "fluid"
        material = region["material"]
        mixture = f"specie {{ molWeight 28.9; }} equationOfState {{ rho {material['rho']}; }} thermodynamics {{ {'Cp' if is_fluid else 'Cv'} {material['cp']}; Hf 0; }} "
        if is_fluid:
            physical = "thermoType { type heRhoThermo; mixture pureMixture; transport const; thermo hConst; equationOfState perfectGas; specie specie; energy sensibleEnthalpy; }\n"
            mixture += f"transport {{ mu 1.85e-5; Pr {1.85e-5*material['cp']/material['kappa']}; }}"
            write(case/"constant"/identity/"momentumTransport", header("momentumTransport")+"simulationType laminar;")
            gravity = " ".join(str(value) for value in contract["gravity_m_s2"])
            write(case/"constant"/identity/"g", header("g", "uniformDimensionedVectorField")+f"dimensions [0 1 -2 0 0 0 0]; value ({gravity});")
        else:
            physical = "thermoType { type heSolidThermo; mixture pureMixture; transport constIsoSolid; thermo eConst; equationOfState rhoConst; specie specie; energy sensibleInternalEnergy; }\n"
            mixture += f"transport {{ kappa {material['kappa']}; }}"
            if region.get("heat_w", 0):
                write(case/"constant"/identity/"fvModels", header("fvModels")+f"source {{ type heatSource; selectionMode all; Q {region['heat_w']}; }}")
        write(case/"constant"/identity/"physicalProperties", header("physicalProperties")+physical+"mixture {"+mixture+"}\n")
        template_root = Path("/opt/openfoam10/tutorials/heatTransfer/chtMultiRegionFoam/heatedDuct/system")/("fluid" if is_fluid else "heater")
        for filename in ("fvSchemes", "fvSolution"):
            text = (template_root/filename).read_text()
            if profile["mode"] == "steady" and filename == "fvSchemes":
                text, count = re.subn(r"ddtSchemes\s*\{[^}]*\}", "ddtSchemes { default steadyState; }", text, count=1)
                if count != 1:
                    raise ValueError("Pinned native region scheme has no unambiguous ddtSchemes")
            if profile["mode"] == "steady" and filename == "fvSolution":
                # OpenFOAM's steady buoyant-room example uses strong
                # under-relaxation for pressure, velocity and energy. The
                # transient heated-duct template leaves U/h at 1, which is
                # unstable for the first natural-convection iteration on the
                # imported enclosure mesh.
                text = steady_solution_controls(text, is_fluid)
            write(case/"system"/identity/filename, text)
        boundary_text = (case/"constant"/identity/"polyMesh/boundary").read_text()
        patches = re.findall(r"\n\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\n\s*\{([^}]+)\}", boundary_text)
        if not patches:
            raise ValueError("Actual split-region boundary file contains no patches")
        values = {key: [] for key in ("T", "U", "p", "p_rgh")}
        for patch, body in patches:
            coupled = "sampleRegion" in body
            role = roles.get(patch, "wall")
            if coupled:
                temperature = f"type compressible::turbulentTemperatureCoupledBaffleMixed; Tnbr T; value uniform {ambient};"
            elif contract["schema_version"] == 2 and role in {"ambient", "inlet", "outlet", "fan"}:
                temperature = f"type inletOutlet; inletValue uniform {ambient}; value uniform {ambient};"
            else:
                temperature = f"type fixedValue; value uniform {ambient};"
            values["T"].append(f"{patch} {{{temperature}}}")
            velocity = "type pressureInletOutletVelocity; value uniform (0 0 0);" if role in {"ambient", "inlet", "outlet", "fan"} else "type noSlip;"
            pressure = "type fixedFluxPressure; value uniform 0;"
            if role in {"ambient", "inlet", "outlet", "fan"}:
                pressure = "type prghPressure; rho rho; p uniform 101325; value uniform 101325;"
            if role == "fan":
                pressure = 'type wrightPrghFanPressure; fanCurve table; fanCurveCoeffs { file "$FOAM_CASE/constant/pressure-vs-q.csv"; format csv; nHeaderLine 1; refColumn 0; componentColumns 1(1); separator ","; mergeSeparators no; outOfBounds clamp; interpolationScheme linear; } direction in; p0 uniform 101325; value uniform 101325;'
            values["U"].append(f"{patch} {{{velocity}}}")
            values["p"].append(f"{patch} {{type calculated; value uniform 101325;}}")
            values["p_rgh"].append(f"{patch} {{{pressure}}}")
        field(case, identity, "T", "0 0 0 1 0 0 0", ambient, "\n".join(values["T"]))
        if is_fluid:
            field(case, identity, "U", "0 1 -1 0 0 0 0", "(0 0 0)", "\n".join(values["U"]))
            field(case, identity, "p", "1 -1 -2 0 0 0 0", 101325, "\n".join(values["p"]))
            field(case, identity, "p_rgh", "1 -1 -2 0 0 0 0", 101325, "\n".join(values["p_rgh"]))


def prepare(root, contract_document, output_directory):
    root = Path(root).resolve()
    contract_path = path_under(root, contract_document)
    contract = json.loads(contract_path.read_text())
    validate(contract, root)
    case = path_under(root, output_directory)
    if case.exists():
        raise ValueError("Case exists; preserve prior attempt")
    case.mkdir(parents=True)
    write(case/"contract.json", json.dumps(contract, indent=2))
    shutil.copyfile(__file__, case/"compiler-provenance.py")
    write(case/"system/controlDict", header("controlDict")+"application chtMultiRegionFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 1; deltaT .001; writeControl timeStep; writeInterval 1;")
    observation = mesh(root, contract, case)
    foam_command(case, ["gmshToFoam", "cad-regions.msh"])
    # A declared material region may contain multiple disconnected solids (for
    # example, four inserts). Walking across faces creates anonymous region1,
    # region2, ... meshes for those solids. Cell-zone-only splitting keeps every
    # disconnected component under its declared material identity.
    foam_command(case, ["splitMeshRegions", "-cellZonesOnly", "-overwrite"])
    observation["split_regions"] = validate_split_regions(case, contract)
    dictionaries(case, contract, observation)
    for region in contract["regions"]:
        foam_command(case, ["checkMesh", "-region", region["name"]])
    observation.update(compiler_sha256=sha(__file__), contract_sha256=sha(contract_path), source_geometry=[{"name": r["name"], "path": r["step"], "sha256": r["sha256"]} for r in contract["regions"]], solver_executed=False)
    write(case/"preparation.json", json.dumps(observation, indent=2))
    return observation


def solve_and_extract(case):
    case = Path(case).resolve()
    claim = case/"solver-dispatch.json"
    dispatch_identity = {"compiler_sha256": sha(__file__), "contract_sha256": sha(case/"contract.json")}
    if claim.exists():
        prior = json.loads(claim.read_text())
        if prior.get("status") != "completed" or any(prior.get(key) != value for key, value in dispatch_identity.items()):
            raise ValueError("Prior solver dispatch is unresolved or source changed; do not replay")
        saved = case/"results/computed-fields.json"
        if sha(saved) != prior["result_sha256"]:
            raise ValueError("Completed solver result changed")
        result = json.loads(saved.read_text())
        if any(sha(case/"results"/row["field"]) != row["sha256"] for row in [*result["actual_regions"], *result.get("actual_boundaries", [])]):
            raise ValueError("Completed solver field changed")
        return result
    with claim.open("x") as stream:
        json.dump({**dispatch_identity, "status": "dispatched"}, stream)
    foam_command(case, ["chtMultiRegionFoam"])
    contract = json.loads((case/"contract.json").read_text())
    import pyvista as pv
    records = []
    boundary_records = []
    results = case/"results"
    results.mkdir()
    for region in contract["regions"]:
        identity = region["name"]
        foam_command(case, ["foamToVTK", "-region", identity, "-latestTime"])
        candidates = list((case/"VTK"/identity).rglob("*.vtu")) + list((case/"VTK"/identity).rglob("*.vtk"))
        internal = [path for path in candidates if "internal" in path.name or path.parent.name == identity]
        if not internal:
            raise ValueError("No actual VTK internal field exported for "+identity)
        mesh_path = max(internal, key=lambda path: path.stat().st_size)
        grid = pv.read(mesh_path)
        if "T" not in grid.array_names or not grid.n_cells:
            raise ValueError("Actual computed cell temperature is missing")
        temperature = grid["T"]
        target = results/(identity+mesh_path.suffix)
        shutil.copyfile(mesh_path, target)
        records.append({"region": identity, "cells": grid.n_cells, "minimum_k": float(temperature.min()), "maximum_k": float(temperature.max()), "field": target.name, "sha256": sha(target)})
        for boundary in [item for item in contract["boundaries"] if item["region"] == identity]:
            paths = list((case/"VTK"/identity/boundary["name"]).glob("*.vtk"))
            if len(paths) != 1:
                raise ValueError("Expected one actual latest-time boundary field")
            surface = pv.read(paths[0]).compute_normals(cell_normals=True, point_normals=False, consistent_normals=False)
            areas = surface.compute_cell_sizes()["Area"]
            velocity = surface.cell_data["U"]
            pressure = surface.cell_data["p"]
            density = surface.cell_data["rho"]
            outward = (velocity*surface.cell_data["Normals"]).sum(axis=1)
            area = float(areas.sum())
            target = results/(identity+"-"+boundary["name"]+".vtk")
            shutil.copyfile(paths[0], target)
            boundary_records.append({"region": identity, "boundary": boundary["name"], "role": boundary["role"], "area_m2": area,
                                     "net_outward_volume_flux_m3_s": float((outward*areas).sum()),
                                     "area_mean_static_pressure_pa": float((pressure*areas).sum()/area),
                                     "area_mean_total_pressure_pa": float(((pressure+.5*density*(velocity**2).sum(axis=1))*areas).sum()/area),
                                     "field": target.name, "sha256": sha(target), "normals": "Actual VTK boundary polygon winding"})
    result = {"actual_regions": records, "actual_boundaries": boundary_records, "contract_sha256": sha(case/"contract.json"), "compiler_sha256": sha(__file__), "solver": "chtMultiRegionFoam OpenFOAM10", "numerical_profile": numerical_profile(contract), "engineering_validation_complete": False, "steady_state_convergence_claimed": False}
    write(results/"computed-fields.json", json.dumps(result, indent=2))
    write(claim, json.dumps({**dispatch_identity, "status": "completed", "result_sha256": sha(results/"computed-fields.json")}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["prepare", "solve"])
    parser.add_argument("--root", required=True)
    parser.add_argument("--contract")
    parser.add_argument("--case", required=True)
    args = parser.parse_args()
    result = prepare(args.root, args.contract, args.case) if args.operation == "prepare" else solve_and_extract(path_under(Path(args.root).resolve(), args.case))
    print(json.dumps(result, indent=2))
