"""Read-only native section diagnostic; completion is not model acceptance.
Assumptions: IDs are unique within each collection; plot axes are distinct;
the output parent exists. Manifest sampling controls every display polyline.
No tolerance changes, source serialization, model edits, or physical claims.
"""

import argparse
import hashlib
import io
import json
import math
import platform
import sys
from importlib import metadata
from pathlib import Path
import cadquery as cq
import OCP
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepTools import BRepTools
from OCP.TopTools import TopTools_FormatVersion
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt


def digest(data):
    return hashlib.sha256(data).hexdigest()


def failure(exc):
    return f"{type(exc).__name__}: {exc}"


def finite(values):
    if not all(math.isfinite(v) for v in values):
        raise ValueError("nonfinite computed value")
    return values


def bounds(shape):
    b = shape.BoundingBox()
    return finite([b.xmin, b.ymin, b.zmin, b.xmax, b.ymax, b.zmax])


def validate(m):
    if not isinstance(m, dict):
        raise ValueError("manifest must be an object")
    json.dumps(m, allow_nan=False)
    for key in ("artifacts", "sections"):
        items = m[key]
        if not isinstance(items, list) or not items:
            raise ValueError(f"{key} must be a nonempty list")
        ids = []
        for item in items:
            if (
                not isinstance(item, dict)
                or not isinstance(item.get("id"), str)
                or not item["id"]
            ):
                raise ValueError("each entry needs a nonempty string id")
            ids.append(item["id"])
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate {key} ids")
    n = m["samples_per_edge"]
    if type(n) is not int or not 2 <= n <= 257:
        raise ValueError("samples_per_edge must be an integer in 2..257")
    for a in m["artifacts"]:
        if not isinstance(a["path"], str) or not a["path"]:
            raise ValueError("artifact path must be a nonempty string")
        h = a["sha256"]
        if (
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in h)
        ):
            raise ValueError("sha256 must contain 64 hexadecimal characters")
        if "face_indices" in a and (
            not isinstance(a["face_indices"], list)
            or any(type(i) is not int or i < 0 for i in a["face_indices"])
        ):
            raise ValueError("face_indices must be a list of nonnegative integers")
    for s in m["sections"]:
        for key in ("origin_mm", "normal"):
            v = s[key]
            if (
                not isinstance(v, list)
                or len(v) != 3
                or any(type(x) not in (int, float) or not math.isfinite(x) for x in v)
            ):
                raise ValueError(f"{key} must be a finite numeric three-vector")
        if not any(s["normal"]):
            raise ValueError("normal must be nonzero")
        axes = s["plot_axes"]
        if (
            not isinstance(axes, list)
            or len(axes) != 2
            or any(type(i) is not int or not 0 <= i <= 2 for i in axes)
            or axes[0] == axes[1]
        ):
            raise ValueError(
                "plot_axes must contain two distinct coordinate indices in 0..2"
            )
    return m


def measure(shape, spec, n, directory, stem):
    r = {"id": spec["id"], "status": "error", "edges": [], "errors": []}
    try:
        origin, normal = spec["origin_mm"], spec["normal"]
        scaled = [v / max(map(abs, normal)) for v in normal]
        unit = [v / math.hypot(*scaled) for v in scaled]
        plane = gp_Pln(gp_Pnt(*origin), gp_Dir(*unit))
        r["normal_unit_used"] = unit
        section = BRepAlgoAPI_Section(shape.wrapped, plane, False)
        section.Build()
        r["native_is_done"] = bool(section.IsDone())
        if not r["native_is_done"]:
            raise RuntimeError("native section Build did not complete")
        raw = cq.Shape.cast(section.Shape())
        r["raw_section_is_valid"] = bool(raw.isValid())
        edges = raw.Edges()
        if not edges:
            r.update(status="empty", empty_meaning="native result contains no edges")
            return r
        if not r["raw_section_is_valid"]:
            r["errors"].append("nonempty native section shape is invalid")
        for i, edge in enumerate(edges):
            e = {"edge_index": i, "samples": [], "errors": []}
            r["edges"].append(e)
            try:
                e.update(
                    geom_type=edge.geomType(),
                    length_mm=finite([edge.Length()])[0],
                    bounds_mm=bounds(edge),
                    orientation=str(edge.wrapped.Orientation()),
                )
            except Exception as exc:
                e["errors"].append(failure(exc))
            try:
                stream = io.BytesIO()
                BRepTools.Write_s(
                    edge.wrapped,
                    stream,
                    False,
                    False,
                    TopTools_FormatVersion.TopTools_FormatVersion_VERSION_1,
                )
                path = directory / f"{stem}_edge_{i}.brep"
                with path.open("xb") as handle:
                    handle.write(stream.getvalue())
                data = path.read_bytes()
                e["brep"] = {
                    "file": path.name,
                    "sha256": digest(data),
                    "bytes": len(data),
                    "format_version": 1,
                    "triangles": False,
                    "normals": False,
                }
            except Exception as exc:
                e["errors"].append(failure(exc))
            for k in range(n):
                t = k / (n - 1)
                p = {"fraction": t, "xyz_mm": None, "plane_residual_mm": None}
                try:
                    p["xyz_mm"] = finite(list(edge.positionAt(t).toTuple()))
                    p["plane_residual_mm"] = finite(
                        [
                            math.fsum(
                                (p["xyz_mm"][j] - origin[j]) * unit[j] for j in range(3)
                            )
                        ]
                    )[0]
                except Exception as exc:
                    p["error"] = failure(exc)
                    e["errors"].append(f"sample {k}: {p['error']}")
                e["samples"].append(p)
            e["status"] = "error" if e["errors"] else "completed"
        r["status"] = (
            "error"
            if r["errors"] or any(e["errors"] for e in r["edges"])
            else "completed"
        )
    except Exception as exc:
        r["errors"].append(failure(exc))
    return r


def plot_section(spec, artifacts, index, directory):
    fig = None
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
        import matplotlib.pyplot as plt
    except Exception as exc:
        return {"status": "unsupported", "error": failure(exc)}
    try:
        fig, ax = plt.subplots()
        u, v = spec["plot_axes"]
        for a in artifacts:
            (line,) = ax.plot([], [], label=a["id"])
            for e in a["sections"][index]["edges"]:
                points = [p["xyz_mm"] for p in e["samples"]]
                ax.plot(
                    [p[u] if p is not None else math.nan for p in points],
                    [p[v] if p is not None else math.nan for p in points],
                    color=line.get_color(),
                )
        ax.set_aspect("equal", adjustable="box")
        ax.legend()
        ax.set_xlabel(f"{'xyz'[u]} (mm)")
        ax.set_ylabel(f"{'xyz'[v]} (mm)")
        ax.set_title("Native section - sampled display; no physical fidelity claim")
        path = directory / f"section_{index}.png"
        with path.open("xb") as handle:
            fig.savefig(handle, format="png", bbox_inches="tight")
        return {
            "status": "completed",
            "file": path.name,
            "sha256": digest(path.read_bytes()),
            "matplotlib_version": matplotlib.__version__,
        }
    except Exception as exc:
        return {"status": "error", "error": failure(exc)}
    finally:
        if fig is not None:
            plt.close(fig)


def run(input_path, output_path):
    directory = Path(output_path)
    directory.mkdir(exist_ok=False)
    r = {
        "status": "incomplete",
        "model_acceptance": "not assessed",
        "artifacts": [],
        "sections": [],
        "errors": [],
        "versions": {
            "python": platform.python_version(),
            "python_build": sys.version,
            "cadquery": cq.__version__,
            "ocp": getattr(OCP, "__version__", None),
        },
    }
    try:
        r["versions"]["cadquery_ocp_distribution"] = metadata.version("cadquery-ocp")
    except metadata.PackageNotFoundError:
        r["versions"]["cadquery_ocp_distribution"] = None
    r["interpretation"] = {
        "coordinates": "reader mm",
        "source_units": "unverified",
        "intersection": "native kernel plane intersection, not triangle intersection",
        "sampling": "edge.positionAt(t), default arc-length mode; endpoints included",
        "bounds": "CadQuery BoundingBox of actual native shapes; not certified extrema",
        "identity": "source byte hashes and per-edge serialized representations; no global geometric equivalence claim",
        "assumptions": "IDs unique per collection; distinct plot axes; existing output parent; manifest sampling count; BRep V1 without triangulation/normals",
    }
    try:
        manifest_path = Path(input_path).resolve()
        data = manifest_path.read_bytes()
        r["input"] = {
            "path": str(manifest_path),
            "sha256": digest(data),
            "bytes": len(data),
        }
        m = validate(json.loads(data))
        r["settings"] = m
        for ai, item in enumerate(m["artifacts"]):
            a = {
                "id": item["id"],
                "requested_path": item["path"],
                "expected_sha256": item["sha256"],
                "errors": [],
                "sections": [
                    {
                        "id": s["id"],
                        "status": "error",
                        "edges": [],
                        "errors": ["artifact unavailable"],
                    }
                    for s in m["sections"]
                ],
            }
            r["artifacts"].append(a)
            path = None
            try:
                path = (manifest_path.parent / item["path"]).resolve()
                a["resolved_path"] = str(path)
                a["sha256_before"] = digest(path.read_bytes())
                if a["sha256_before"] != item["sha256"].lower():
                    raise ValueError(
                        "artifact SHA-256 mismatch before import; import refused"
                    )
                shape = cq.importers.importStep(str(path)).val()
                a["input_shape_is_valid"] = not shape.wrapped.IsNull() and bool(
                    shape.isValid()
                )
                if not a["input_shape_is_valid"]:
                    raise ValueError("invalid or null input shape; measurement refused")
                faces = shape.Faces()
                indices = item.get("face_indices", list(range(len(faces))))
                if any(i >= len(faces) for i in indices):
                    raise ValueError("face index out of range")
                a.update(
                    face_count=len(faces),
                    actual_face_indices=indices,
                    selection="faces" if "face_indices" in item else "whole shape",
                    input_bounds_mm=bounds(shape),
                )
                selected = (
                    cq.Compound.makeCompound([faces[i] for i in indices])
                    if "face_indices" in item
                    else shape
                )
                if selected.wrapped.IsNull() or not selected.isValid():
                    raise ValueError("invalid selected shape; measurement refused")
                a["selected_bounds_mm"] = (
                    bounds(selected) if selected.Vertices() else None
                )
                for si, spec in enumerate(m["sections"]):
                    a["sections"][si] = measure(
                        selected,
                        spec,
                        m["samples_per_edge"],
                        directory,
                        f"artifact_{ai}_section_{si}",
                    )
            except Exception as exc:
                a["errors"].append(failure(exc))
            finally:
                try:
                    a["sha256_after"] = (
                        digest(path.read_bytes()) if path is not None else None
                    )
                    a["integrity_verified"] = (
                        a.get("sha256_before")
                        == a["sha256_after"]
                        == item["sha256"].lower()
                    )
                    if not a["integrity_verified"]:
                        a["errors"].append(
                            "artifact byte integrity not verified across diagnostic interval"
                        )
                except Exception as exc:
                    a["integrity_verified"] = False
                    a["errors"].append(failure(exc))
            a["status"] = (
                "error"
                if a["errors"] or any(s["status"] == "error" for s in a["sections"])
                else (
                    "empty"
                    if all(s["status"] == "empty" for s in a["sections"])
                    else "completed"
                )
            )
        for si, spec in enumerate(m["sections"]):
            plot = plot_section(spec, r["artifacts"], si, directory)
            bad = plot["status"] != "completed" or any(
                not a["integrity_verified"] or a["sections"][si]["status"] == "error"
                for a in r["artifacts"]
            )
            r["sections"].append(
                {
                    "id": spec["id"],
                    "plot": plot,
                    "status": "error"
                    if bad
                    else (
                        "empty"
                        if all(
                            a["sections"][si]["status"] == "empty"
                            for a in r["artifacts"]
                        )
                        else "completed"
                    ),
                }
            )
    except Exception as exc:
        r["errors"].append(failure(exc))
    r["diagnostics_completed"] = (
        not r["errors"]
        and all(a["status"] != "error" for a in r["artifacts"])
        and all(s["status"] != "error" for s in r["sections"])
    )
    r["status"] = "completed" if r["diagnostics_completed"] else "incomplete"
    with (directory / "report.json").open("x", encoding="utf-8") as handle:
        json.dump(r, handle, indent=2, allow_nan=False)
    return r


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        return 0 if run(args.input, args.output)["diagnostics_completed"] else 1
    except Exception as exc:
        print(failure(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
