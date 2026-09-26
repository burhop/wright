"""Explicit local Bambu slicing operation; no printer connection capabilities."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _oriented_stl(source, destination, axes):
    """Rotate a binary STL by an axis permutation and put its lowest vertex at Z=0."""
    data = source.read_bytes()
    if len(data) < 84 or len(data) != 84 + struct.unpack_from("<I", data, 80)[0] * 50:
        raise ValueError("Orientation search requires the repaired binary STL")
    triangles = struct.unpack_from("<I", data, 80)[0]
    vertices = []
    for index in range(triangles):
        base = 84 + index * 50
        vertices.extend(struct.unpack_from("<3f", data, base + offset) for offset in (12, 24, 36))
    def rotate(point):
        return tuple(sign * point[axis] for axis, sign in axes)
    rotated = [rotate(point) for point in vertices]
    minima = [min(point[axis] for point in rotated) for axis in range(3)]
    maxima = [max(point[axis] for point in rotated) for axis in range(3)]
    spans = [maxima[axis] - minima[axis] for axis in range(3)]
    if any(span > 256.000001 for span in spans):
        return None
    contact = 0.0
    for index in range(triangles):
        a, b, c = rotated[index * 3:index * 3 + 3]
        if max(abs(point[2] - minima[2]) for point in (a, b, c)) <= 0.02:
            contact += abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])) / 2
    if contact < max(25.0, spans[0] * spans[1] * 0.05):
        return None
    result = bytearray(data)
    for index in range(triangles):
        base = 84 + index * 50
        normal = rotate(struct.unpack_from("<3f", data, base))
        struct.pack_into("<3f", result, base, *normal)
        for corner in range(3):
            point = rotated[index * 3 + corner]
            struct.pack_into("<3f", result, base + 12 + corner * 12,
                             point[0], point[1], point[2] - minima[2])
    destination.write_bytes(result)
    return {"contact_area_mm2": round(contact, 3), "dimensions_mm": [round(v, 3) for v in spans]}


def _slice_metrics(gcode):
    def header(pattern):
        match = re.search(pattern, gcode[:3000], re.MULTILINE)
        if not match:
            raise ValueError("Bambu slice lacks expected time or filament estimate")
        return match.group(1)
    def seconds(value):
        return sum(int(number) * {"h": 3600, "m": 60, "s": 1}[unit]
                   for number, unit in re.findall(r"(\d+)([hms])", value))
    return {
        "estimated_seconds": seconds(header(r"total estimated time: ([^\r\n]+)")),
        "filament_g": float(header(r"total filament weight \[g\] : ([\d.]+)")),
    }


def _toolpath_layers(gcode):
    layers = {}
    x = y = 0.0
    feature = ""
    extrusion = 0.0
    relative = False
    current_layer = None
    for line in gcode.splitlines():
        match = re.match(r";\s*Z_HEIGHT:\s*([-\d.]+)", line)
        if match:
            current_layer = 1 if current_layer is None else current_layer + 1
            layers.setdefault(current_layer, {"z": float(match.group(1)), "model": [], "support": []})
        if "FEATURE:" in line or "TYPE:" in line:
            feature = line.lower()
        if line.startswith("M83"):
            relative = True
        elif line.startswith("M82"):
            relative = False
        elif line.startswith("G92 E"):
            extrusion = float(line.split("E", 1)[1].split()[0])
        elif re.match(r"G[0123]\s", line):
            command = line.split(" ", 1)[0]
            fields = {k: float(v) for k, v in re.findall(r"([XYEIJ])(-?(?:\d+(?:\.\d*)?|\.\d+))", line.split(";", 1)[0])}
            nx, ny = fields.get("X", x), fields.get("Y", y)
            e = fields.get("E", 0 if relative else extrusion)
            if current_layer is not None and "E" in fields and (e > 0 if relative else e > extrusion) and ((nx != x or ny != y) or (command in ("G2", "G3") and "I" in fields and "J" in fields)):
                bucket = layers[current_layer]["support" if "support" in feature else "model"]
                if command in ("G2", "G3") and "I" in fields and "J" in fields:
                    cx, cy = x + fields["I"], y + fields["J"]
                    radius = math.hypot(x - cx, y - cy)
                    start = math.atan2(y - cy, x - cx)
                    end = math.atan2(ny - cy, nx - cx)
                    sweep = (end - start) % (2 * math.pi) if command == "G3" else -((start - end) % (2 * math.pi))
                    if abs(sweep) < 1e-8:
                        sweep = 2 * math.pi if command == "G3" else -2 * math.pi
                    steps = max(1, min(256, math.ceil(abs(sweep * radius) / 0.5)))
                    px, py = x, y
                    for index in range(1, steps + 1):
                        angle = start + sweep * index / steps
                        qx, qy = (nx, ny) if index == steps else (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
                        bucket.append((px, py, qx, qy))
                        px, py = qx, qy
                else:
                    bucket.append((x, y, nx, ny))
            x, y, extrusion = nx, ny, e
    return layers


def run(configuration_path):
    config = json.loads(Path(configuration_path).read_text(encoding="utf-8"))
    root = Path(config["workspace_root"]).resolve()
    def scoped(value):
        path = (root / value).resolve()
        if not path.is_relative_to(root):
            raise ValueError("Output/input path escapes campaign workspace")
        return path
    source = scoped(config["source"])
    output = scoped(config["output_root"])
    if not source.is_file() or source.stat().st_size < 84:
        raise ValueError("The actual repaired STL is missing")
    output.mkdir(parents=True, exist_ok=True)
    profiles = Path(config["profiles_root"]).resolve()
    def profile(value):
        path = (profiles / value).resolve()
        if not path.is_relative_to(profiles) or not path.is_file():
            raise ValueError("Unknown profile")
        return path
    machine, filament = profile(config["machine"]), profile(config["filament"])
    process_base = profile(config["process"]["base"])
    material = json.loads(filament.read_text(encoding="utf-8"))
    if "PETG" not in material["name"] or "Bambu Lab P1S 0.4 nozzle" not in material["compatible_printers"]:
        raise ValueError("Require explicit compatible P1S PETG profile")
    profile_index = {}
    for candidate in profiles.rglob("*.json"):
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError):
            continue
        if isinstance(value, dict):
            profile_index[value.get("name", candidate.stem)] = (candidate, value)
            profile_index.setdefault(candidate.stem, (candidate, value))
    resolved_profile_sources = {}
    def resolve_profile(path, chain=()):
        data = json.loads(path.read_text(encoding="utf-8"))
        identity = str(path)
        if identity in chain:
            raise ValueError("Cyclic profile inheritance")
        result = {}
        references = []
        if data.get("inherits"):
            references.append(data["inherits"])
        references.extend(data.get("include", []))
        for name in references:
            if name not in profile_index:
                raise ValueError(f"Missing profile dependency {name}")
            result.update(resolve_profile(profile_index[name][0], (*chain, identity)))
        result.update({k:v for k,v in data.items() if k not in {"inherits", "include"}})
        resolved_profile_sources[identity] = sha(path)
        return result
    process = resolve_profile(process_base)
    process.update({k:v for k,v in config["process"].items() if k != "base"})
    if process.get("enable_support") != "1":
        raise ValueError("This operation requires support generation enabled")
    derived = output / "process-profile.json"
    process["curr_bed_type"] = "Textured PEI Plate"
    derived.write_text(json.dumps(process, indent=2) + "\n", encoding="utf-8")
    machine_resolved = output / "machine-profile.json"
    machine_values = resolve_profile(machine)
    machine_values["default_filament_profile"] = [material["name"]]
    machine_resolved.write_text(json.dumps(machine_values, indent=2) + "\n", encoding="utf-8")
    filament_resolved = output / "filament-profile.json"
    filament_resolved.write_text(json.dumps(resolve_profile(filament), indent=2) + "\n", encoding="utf-8")
    package = output / "slice_package.gcode.3mf"
    if package.exists():
        raise ValueError("A slice package already exists; reconcile instead of replaying")
    executable = Path(config["slicer"]).resolve()
    candidates = []
    optimize = bool(config.get("optimize_orientation", False))
    orientations = [("as_authored", ((0, 1), (1, 1), (2, 1)))]
    if optimize:
        orientations.extend([
            ("x_plus_90", ((0, 1), (2, -1), (1, 1))),
            ("x_minus_90", ((0, 1), (2, 1), (1, -1))),
            ("x_180", ((0, 1), (1, -1), (2, -1))),
            ("y_plus_90", ((2, 1), (1, 1), (0, -1))),
            ("y_minus_90", ((2, -1), (1, 1), (0, 1))),
        ])
    candidate_dir = output / "orientation-candidates"
    if optimize:
        candidate_dir.mkdir(exist_ok=True)
    for name, axes in orientations:
        candidate_stl = candidate_dir / f"{name}.stl" if optimize else source
        geometry = _oriented_stl(source, candidate_stl, axes) if optimize else {
            "contact_area_mm2": 0.0, "dimensions_mm": [],
        }
        if geometry is None:
            candidates.append({"name": name, "rejected": "insufficient bed contact or outside P1S envelope"})
            continue
        candidate_package = candidate_dir / f"{name}.gcode.3mf" if optimize else package
        argv = [str(executable), "--slice", "1", "--debug", "1", "--export-3mf", str(candidate_package),
                "--load-settings", f"{machine_resolved};{derived}", "--load-filaments", str(filament_resolved), str(candidate_stl)]
        completed = subprocess.run(argv, capture_output=True, timeout=480, check=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        log = candidate_dir / f"{name}.log" if optimize else output / "slicer.stdout.log"
        log.write_bytes(completed.stdout + b"\n" + completed.stderr)
        if completed.returncode or not candidate_package.is_file():
            candidates.append({"name": name, "rejected": f"Bambu Studio slice exit {completed.returncode}", **geometry})
            continue
        with zipfile.ZipFile(candidate_package) as archive:
            candidate_gcode = archive.read("Metadata/plate_1.gcode").decode("utf-8", errors="replace")
        layers = _toolpath_layers(candidate_gcode)
        support_count = sum(len(layer["support"]) for layer in layers.values())
        candidates.append({"name": name, "axes": axes, **geometry, **_slice_metrics(candidate_gcode),
                           "support_moves": support_count, "stl_sha256": sha(candidate_stl),
                           "package_sha256": sha(candidate_package)})
    viable = [item for item in candidates if "rejected" not in item]
    if not viable:
        raise RuntimeError("No stable orientation sliced successfully; inspect orientation-candidates logs")
    authored = next((item for item in viable if item["name"] == "as_authored"), None)
    non_regressing = [item for item in viable if authored is None or (
        item["estimated_seconds"] <= authored["estimated_seconds"]
        and item["filament_g"] <= authored["filament_g"]
        and item["support_moves"] <= authored["support_moves"]
    )]
    selected = min(non_regressing, key=lambda item: (item["support_moves"] > 0,
                                             item["estimated_seconds"], item["filament_g"],
                                             -item["contact_area_mm2"]))
    chosen = selected["name"]
    selected_package = candidate_dir / f"{chosen}.gcode.3mf" if optimize else package
    selected_stl = candidate_dir / f"{chosen}.stl" if optimize else source
    selected_argv = [str(executable), "--slice", "1", "--debug", "1", "--export-3mf",
                     str(selected_package), "--load-settings",
                     f"{machine_resolved};{derived}", "--load-filaments", str(filament_resolved),
                     str(selected_stl)]
    oriented = output / "oriented_mesh.stl"
    shutil.copyfile(selected_stl, oriented)
    if optimize:
        shutil.copyfile(selected_package, package)
        shutil.copyfile(candidate_dir / f"{chosen}.log", output / "slicer.stdout.log")
    with zipfile.ZipFile(package) as archive:
        gcode = archive.read("Metadata/plate_1.gcode").decode("utf-8", errors="replace")
        preview = archive.read("Metadata/plate_1.png")
        if len(preview) < 8 or preview[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Actual sliced package lacks a PNG preview")
        (output / "slice-preview.png").write_bytes(preview)
    layers = _toolpath_layers(gcode)
    if not layers:
        raise ValueError("Actual slicer package contains no positive-extrusion toolpaths")
    toolpaths = {"format": "wright.gcode.toolpaths.v1", "package_sha256": sha(package),
                 "layers": [{"index": number, "z": layer["z"],
                             "model": [[round(value, 3) for value in segment] for segment in layer["model"]],
                             "support": [[round(value, 3) for value in segment] for segment in layer["support"]]}
                            for number, layer in sorted(layers.items())]}
    (output / "toolpaths.json").write_text(json.dumps(toolpaths, separators=(",", ":")), encoding="utf-8")
    layer_number = max(layers, key=lambda number: len(layers[number]["support"])) if selected["support_moves"] else sorted(layers)[len(layers)//2]
    model = layers[layer_number]["model"]
    support = layers[layer_number]["support"]
    moves = model + support
    xs = [v for a, b, c, d in moves for v in (a, c)]
    ys = [v for a, b, c, d in moves for v in (b, d)]
    left, right = min(xs)-3, max(xs)+3
    top, bottom = 256-max(ys)-3, 256-min(ys)+3
    def paths(segments):
        return " ".join(f"M{a:.3f},{256-b:.3f}L{c:.3f},{256-d:.3f}" for a,b,c,d in segments)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left:.2f} {top-8:.2f} {right-left:.2f} {bottom-top+8:.2f}">'
           f'<rect x="{left:.2f}" y="{top-8:.2f}" width="{right-left:.2f}" height="{bottom-top+8:.2f}" fill="white"/>'
           f'<text x="{left+1:.2f}" y="{top-2:.2f}" font-size="3">Sliced layer {layer_number} of {max(layers)}; {len(support)} support moves</text>'
           f'<path d="{paths(model)}" fill="none" stroke="#344b5a" stroke-width="0.25"/>'
           f'<path d="{paths(support)}" fill="none" stroke="#d65012" stroke-width="0.35"/></svg>')
    (output / "support-preview.svg").write_text(svg, encoding="utf-8")
    report = {"operation":"actual_local_bambu_slice", "simulation":False,
              "argv":selected_argv, "exit_code":0, "source_sha256":sha(source),
              "executable_sha256":sha(executable), "operation_source_sha256":sha(__file__),
              "configuration_sha256":sha(configuration_path), "package_sha256":sha(package),
              "profile_dependencies":resolved_profile_sources,
              "package_bytes":package.stat().st_size, "extrusion_moves":sum(len(layer["model"])+len(layer["support"]) for layer in layers.values()),
              "support_moves":selected["support_moves"], "supports_enabled":True,
              "orientation_selected":chosen, "orientation_candidates":candidates,
              "orientation_selection_policy":"stable_contact_then_no_regression_vs_authored_in_time_filament_and_support_then_fewest_supports_and_fastest_time",
              "oriented_stl_sha256":sha(oriented), "preview_layer":layer_number,
              "estimated_seconds":selected["estimated_seconds"], "filament_g":selected["filament_g"],
              "machine":{"path":str(machine),"sha256":sha(machine)},
              "filament":{"name":material["name"],"path":str(filament),"sha256":sha(filament)},
              "process":{"base":str(process_base),"base_sha256":sha(process_base),"derived_sha256":sha(derived)},
              "content_validated":False, "printer_connected":False}
    (output / "slice-evidence.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    return report


if "configuration_path" in globals():
    print(json.dumps(run(globals()["configuration_path"])))
elif __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuration_path")
    print(json.dumps(run(parser.parse_args().configuration_path)))
