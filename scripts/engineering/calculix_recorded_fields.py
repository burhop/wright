"""Export sealed CalculiX fields and run an explicit output-only RF/FRD expansion.

The caller supplies a recorded run identity, never a deck or command. Original
resources remain unchanged. The second native solve has separate provenance.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess
import time

from mcp.server.fastmcp import FastMCP

IMAGE = "ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778"
ARTIFACTS = {"input.step", "request.json", "mesh.geo", "mesh.inp", "gmsh.log", "job.inp", "ccx.log", "job.dat", "result.json"}
ORIGINAL_TAIL = "*NODE PRINT, NSET=NALL\nU\n*EL PRINT, ELSET=PART\nS\n*END STEP\n"
EXPANDED_TAIL = "*NODE PRINT, NSET=NALL\nU, RF\n*EL PRINT, ELSET=PART\nS\n*NODE FILE\nU, RF\n*EL FILE\nS\n*END STEP\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def confined(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or any(p in (".", "..") for p in path.parts) or "\\" in relative or ":" in relative:
        raise ValueError("Use a canonical workspace-relative path")
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("Path escapes workspace")
    return target


def expand_output_requests(deck):
    if deck.count(ORIGINAL_TAIL) != 1 or deck.count("*STEP\n") != 1:
        raise ValueError("Recorded deck is not the pinned single-static output contract")
    return deck.replace(ORIGINAL_TAIL, EXPANDED_TAIL)


def parse_dat(text):
    result = {"displacement": [], "stress": [], "force": []}
    section = None
    for line in text.splitlines():
        lower = line.lower()
        if "displacements (" in lower:
            section = "displacement"
            continue
        if "stresses (" in lower:
            section = "stress"
            continue
        if "forces (" in lower:
            section = "force"
            continue
        parts = line.split()
        expected = 8 if section == "stress" else 4
        if section and len(parts) == expected:
            try:
                values = [float(p.replace("D", "E")) for p in parts]
            except ValueError:
                continue
            if not all(math.isfinite(v) for v in values):
                raise ValueError("Native field contains nonfinite values")
            result[section].append(values)
    return result


def mesh_nodes_sets(text):
    nodes, sets = {}, {}
    mode, current, generate = None, None, False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("**") or not line:
            continue
        if line.startswith("*"):
            mode = line.split(",")[0].upper()
            current = None
            if mode == "*NSET":
                match = re.search(r"NSET\s*=\s*([A-Za-z0-9_]+)", line, re.I)
                if match:
                    current = match.group(1).upper()
                    sets.setdefault(current, set())
                    generate = "GENERATE" in line.upper()
            continue
        values = [p.strip() for p in line.split(",") if p.strip()]
        if mode == "*NODE" and len(values) == 4:
            nodes[int(values[0])] = tuple(float(v) for v in values[1:])
        elif mode == "*NSET" and current:
            ids = [int(v) for v in values]
            sets[current].update(range(ids[0], ids[1] + 1, ids[2] if len(ids) == 3 else 1) if generate else ids)
    return nodes, sets


def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)


class RecordedFieldOperation:
    def __init__(self, workspace, archive, input_prefix="/inputs", container_prefix="/campaign-workspace"):
        self.workspace, self.archive = Path(workspace).resolve(), Path(archive).resolve()
        self.input_prefix, self.container_prefix = input_prefix.rstrip("/"), container_prefix.rstrip("/")

    def execute(self, run_id, expected_step_sha256, output_directory):
        operation_source_sha256 = sha(Path(__file__).read_bytes())
        if not re.fullmatch(r"r-[0-9a-f-]{36}", run_id) or not re.fullmatch(r"[0-9a-f]{64}", expected_step_sha256):
            raise ValueError("Invalid exact run or STEP identity")
        original_root = self.archive / run_id
        ledger = json.loads((original_root / "ledger.json").read_text())
        if ledger["runId"] != run_id or ledger["state"] != "completed" or {a["name"] for a in ledger["artifacts"]} != ARTIFACTS:
            raise ValueError("Incomplete or unexpected recorded artifact ledger")
        resource_bytes = {}
        for artifact in ledger["artifacts"]:
            data = (original_root / artifact["name"]).read_bytes()
            if len(data) != artifact["bytes"] or sha(data) != artifact["sha256"]:
                raise ValueError("Recorded resource failed its sealed identity: " + artifact["name"])
            resource_bytes[artifact["name"]] = data
        if sha(resource_bytes["input.step"]) != expected_step_sha256:
            raise ValueError("Recorded STEP differs from caller's exact geometry")
        request = json.loads(resource_bytes["request.json"])
        if request["expected_step_sha256"] != expected_step_sha256 or request["request_id"] != ledger["requestId"]:
            raise ValueError("Recorded request/geometry identity mismatch")
        source_path = request["step_path"]
        if not source_path.startswith(self.input_prefix + "/"):
            raise ValueError("Recorded source is outside this operation's configured workspace")
        relative_source = source_path[len(self.input_prefix) + 1:]
        source = confined(self.workspace, relative_source)
        if sha(source.read_bytes()) != expected_step_sha256:
            raise ValueError("Current candidate STEP changed after original solver snapshot")
        output = confined(self.workspace, output_directory)
        parts = PurePosixPath(relative_source).parts
        authority = self.workspace.joinpath(*parts[:parts.index("artifacts") + 1]) if "artifacts" in parts else source.parent
        if not output.is_relative_to(authority) or output == authority:
            raise ValueError("Output must stay inside the original candidate's attempt artifact scope")
        receipt = output / "field-expansion-receipt.json"
        if output.exists():
            if receipt.exists():
                existing = json.loads(receipt.read_text())
                if (existing.get("status") == "completed" and existing.get("original_run_id") == run_id
                        and existing.get("expected_step_sha256") == expected_step_sha256
                        and existing.get("operation_source_sha256") == operation_source_sha256):
                    for item in existing["files"]:
                        if sha((output / item["path"]).read_bytes()) != item["sha256"]:
                            raise ValueError("Previous result changed; no automatic replay")
                    return existing
            raise ValueError("Prior output/claim exists; inspect ambiguous outcome, never blindly re-solve")
        output.mkdir(parents=True)
        receipt.write_text(json.dumps({"status": "claimed", "original_run_id": run_id, "expected_step_sha256": expected_step_sha256, "started_at": time.time()}))
        original = output / "original"
        original.mkdir()
        for name, data in resource_bytes.items():
            (original / name).write_bytes(data)
        (original / "ledger.json").write_text(json.dumps(ledger, indent=2))
        deck = resource_bytes["job.inp"].decode()
        expanded = expand_output_requests(deck)
        replay = output / "native-field-expansion"
        replay.mkdir()
        (replay / "job.inp").write_text(expanded, encoding="utf-8", newline="\n")
        (output / "output-directives.diff").write_text("".join(difflib.unified_diff(deck.splitlines(True), expanded.splitlines(True), fromfile="original/job.inp", tofile="native-field-expansion/job.inp")))
        native_cwd = self.container_prefix + "/" + output_directory + "/native-field-expansion"
        command = ["docker", "exec", "-e", "OMP_NUM_THREADS=2", "-w", native_cwd, "wright-calculix-campaign", "timeout", "120", "ccx", "job"]
        (output / "native-command.json").write_text(json.dumps({"command": command, "image": IMAGE, "input_deck_sha256": sha(expanded.encode()), "status": "dispatching"}, indent=2))
        result = subprocess.run(command, capture_output=True, text=True, timeout=145, check=False)
        (replay / "ccx.stdout.log").write_text(result.stdout)
        (replay / "ccx.stderr.log").write_text(result.stderr)
        if result.returncode:
            raise RuntimeError("Explicit native field expansion failed; output retained, automatic replay disabled")
        native_dat = (replay / "job.dat").read_text()
        original_fields = parse_dat(resource_bytes["job.dat"].decode())
        fields = parse_dat(native_dat)
        if not all(fields.values()) or not original_fields["displacement"] or not original_fields["stress"]:
            raise ValueError("Actual native outputs lack required complete field sections")
        if not (replay / "job.frd").is_file() or not (replay / "job.frd").stat().st_size:
            raise ValueError("Actual native FRD was not created")
        for folder, field in ((original, original_fields), (replay, fields)):
            write_csv(folder / "displacement-field.csv", ["node_id", "ux_mm", "uy_mm", "uz_mm"], field["displacement"])
            write_csv(folder / "stress-field.csv", ["element_id", "integration_point", "sxx_mpa", "syy_mpa", "szz_mpa", "sxy_mpa", "sxz_mpa", "syz_mpa"], field["stress"])
        write_csv(replay / "nodal-force-field.csv", ["node_id", "fx_n", "fy_n", "fz_n"], fields["force"])
        nodes, sets = mesh_nodes_sets(resource_bytes["mesh.inp"].decode())
        displacements = {int(row[0]): row[1:] for row in fields["displacement"]}
        load_points = []
        for load in request["loads"]:
            selection = next(s for s in request["selections"] if s["name"] == load["selection"])
            center = [(a + b) / 2 for a, b in zip(selection["box"]["min"], selection["box"]["max"])]
            candidates = sets[load["selection"].upper()]
            nearest = min(candidates, key=lambda n: sum((a-b)**2 for a, b in zip(nodes[n], center)))
            distance = math.dist(nodes[nearest], center)
            resolved = distance < 1e-6
            load_points.append({"selection": load["selection"], "requested_patch_centroid_mm": center,
                                "exact_mesh_node_at_centroid": resolved,
                                "centroid_displacement_mm": displacements[nearest] if resolved else None,
                                "nearest_node_id": nearest, "nearest_node_distance_mm": distance,
                                "nearest_node_displacement_mm": displacements[nearest],
                                "note": "Require an imprinted CAD vertex at exact load-patch centroid; nearest-node values are not substituted for unresolved centroid response."})
        forces = {int(row[0]): row[1:] for row in fields["force"]}
        fixed_ids = set().union(*(sets[name.upper()] for name in request["fixed"]))
        if not fixed_ids.issubset(forces):
            raise ValueError("Native force output omitted a fixed node")
        reaction = [sum(forces[node][i] for node in fixed_ids) for i in range(3)]
        moment = [0., 0., 0.]
        for node in fixed_ids:
            x, y, z = nodes[node]
            fx, fy, fz = forces[node]
            for i, value in enumerate((y*fz-z*fy, z*fx-x*fz, x*fy-y*fx)):
                moment[i] += value
        reactions = {"source": "separate explicit output-only native solve RF", "fixed_node_count": len(fixed_ids),
                     "reaction_force_n": reaction, "reaction_moment_about_global_origin_nmm": moment,
                     "warning": "Preserve numerical limitations; no safety, joint-compliance or correctness qualification."}
        (output / "reaction-forces.json").write_text(json.dumps(reactions, indent=2))
        files = [{"path": p.relative_to(output).as_posix(), "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
                 for p in sorted(output.rglob("*")) if p.is_file() and p != receipt]
        answer = {"status": "completed", "original_run_id": run_id, "expected_step_sha256": expected_step_sha256,
                  "operation_source_sha256": operation_source_sha256,
                  "original_observations": json.loads(resource_bytes["result.json"]),
                  "load_point_observations": load_points,
                  "original_resources": ledger["artifacts"], "expansion_kind": "explicit_separate_native_solve_output_requests_only",
                  "physics_deck_changed": False, "original_deck_sha256": sha(deck.encode()), "expanded_deck_sha256": sha(expanded.encode()),
                  "native_image": IMAGE, "returncode": result.returncode, "finished_at": time.time(),
                  "nodal_displacement_rows": len(fields["displacement"]), "stress_integration_point_rows": len(fields["stress"]),
                  "reactions": reactions, "files": files,
                  "limitations": ["Equal-node force distribution approximates uniform patch loading; retain it in design/results.",
                                  "Second solve is not the original sealed Casys result; original DAT and full fields remain separate."]}
        receipt.write_text(json.dumps(answer, indent=2))
        return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--archive-root", required=True)
    parser.add_argument("--input-prefix", default="/inputs")
    parser.add_argument("--container-prefix", default="/campaign-workspace")
    args = parser.parse_args()
    operation = RecordedFieldOperation(args.workspace_root, args.archive_root, args.input_prefix, args.container_prefix)
    server = FastMCP("CalculiX recorded field expansion")

    @server.tool()
    def export_recorded_fields_and_reactions(run_id: str, expected_step_sha256: str, output_directory: str) -> dict:
        """Export sealed recorded resources, then explicitly run same static deck with only RF/FRD output additions.

        Writes inside the original candidate's attempt output directory. Accepts
        no arbitrary deck, code, physical value or command. An existing unknown
        outcome is never re-executed. Original and second-run lineage are distinct.
        """
        return operation.execute(run_id, expected_step_sha256, output_directory)

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
