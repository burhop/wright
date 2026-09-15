"""Explicit local Bambu slicing operation; no printer connection capabilities."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
    argv = [str(executable), "--slice", "1", "--debug", "1", "--export-3mf", str(package),
            "--load-settings", f"{machine_resolved};{derived}", "--load-filaments", str(filament_resolved), str(source)]
    completed = subprocess.run(argv, capture_output=True, timeout=480, check=False,
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    (output / "slicer.stdout.log").write_bytes(completed.stdout + b"\n" + completed.stderr)
    if completed.returncode or not package.is_file():
        raise RuntimeError(f"Bambu Studio slice failed with exit {completed.returncode}; inspect slicer.stdout.log")
    with zipfile.ZipFile(package) as archive:
        gcode = archive.read("Metadata/plate_1.gcode").decode("utf-8", errors="replace")
        preview = archive.read("Metadata/plate_1.png")
        if len(preview) < 8 or preview[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Actual sliced package lacks a PNG preview")
        (output / "slice-preview.png").write_bytes(preview)
    moves, support = [], []
    x = y = 0.0
    feature = ""
    extrusion = 0.0
    relative = False
    for line in gcode.splitlines():
        if "FEATURE:" in line or "TYPE:" in line:
            feature = line.lower()
        if line.startswith("M83"):
            relative = True
        elif line.startswith("M82"):
            relative = False
        elif line.startswith("G92 E"):
            extrusion = float(line.split("E",1)[1].split()[0])
        elif re.match(r"G[01]\s", line):
            fields = {k:float(v) for k,v in re.findall(r"([XYE])(-?(?:\d+(?:\.\d*)?|\.\d+))", line.split(";",1)[0])}
            nx, ny = fields.get("X",x), fields.get("Y",y)
            e = fields.get("E", 0 if relative else extrusion)
            if "E" in fields and (e > 0 if relative else e > extrusion) and (nx != x or ny != y):
                segment = (x,y,nx,ny)
                moves.append(segment)
                if "support" in feature:
                    support.append(segment)
            x, y, extrusion = nx, ny, e
    if not moves:
        raise ValueError("Actual slicer package contains no positive-extrusion toolpaths")
    def paths(segments):
        return " ".join(f"M{a:.3f},{256-b:.3f}L{c:.3f},{256-d:.3f}" for a,b,c,d in segments)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 278">'
           '<rect width="256" height="278" fill="white"/>'
           f'<path d="{paths(moves)}" fill="none" stroke="#c5cdd0" stroke-width="0.12"/>'
           f'<path d="{paths(support)}" fill="none" stroke="#d65012" stroke-width="0.3"/>'
           f'<text x="3" y="267" font-size="4">Actual G-code projection: {len(support)} support moves (orange)</text></svg>')
    (output / "support-preview.svg").write_text(svg, encoding="utf-8")
    report = {"operation":"actual_local_bambu_slice", "simulation":False,
              "argv":argv, "exit_code":completed.returncode, "source_sha256":sha(source),
              "executable_sha256":sha(executable), "operation_source_sha256":sha(__file__),
              "configuration_sha256":sha(configuration_path), "package_sha256":sha(package),
              "profile_dependencies":resolved_profile_sources,
              "package_bytes":package.stat().st_size, "extrusion_moves":len(moves),
              "support_moves":len(support), "supports_enabled":True,
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
