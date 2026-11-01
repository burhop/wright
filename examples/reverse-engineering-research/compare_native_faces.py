import argparse
import hashlib
import importlib.metadata as metadata
import io
import json
from pathlib import Path
import platform
import re
import sys
import traceback

import cadquery as cq
import OCP
from OCP.BRepTools import BRepTools
from OCP.TopTools import TopTools_FormatVersion_VERSION_1

# Explicit, frozen format choice; no availability probing or fallback.
FORMAT = TopTools_FormatVersion_VERSION_1
FORMAT_NAME = "TopTools_FormatVersion_VERSION_1"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def distribution_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def runtime_info():
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "cadquery_module_version": getattr(cq, "__version__", None),
        "cadquery_distribution_version": distribution_version("cadquery"),
        "OCP_module_version": getattr(OCP, "__version__", None),
        "cadquery_ocp_distribution_version": distribution_version("cadquery-ocp"),
        "occt_build_string": None,
        "occt_build_string_note": "Not exposed by the supplied inspected API; native writer binding/distribution versions are recorded above.",
    }


def serialize_face(face):
    if not isinstance(face, cq.Face) or face.isNull() or not face.isValid():
        raise ValueError("Expected a non-null valid CadQuery face")
    stream = io.BytesIO()
    # Pass the original wrapped face, including location and orientation.
    BRepTools.Write_s(face.wrapped, stream, False, False, FORMAT)
    data = stream.getvalue()
    if not data:
        raise ValueError("Native writer produced an empty serialization")
    return data


def inventory(faces, side, root, evidence):
    folder = root / (side + "_faces")
    folder.mkdir()
    records = []
    for number, face in enumerate(faces, 1):
        face_id = f"{side}_F{number:06d}"
        data = serialize_face(face)  # Exactly one writer invocation per face.
        relative = Path(folder.name) / (face_id + ".brep")
        with (root / relative).open("xb") as target:
            target.write(data)
        record = {
            "id": face_id,
            "sha256": sha256(data),
            "byte_count": len(data),
            "file": relative.as_posix(),
        }
        evidence.append(record)
        records.append({**record, "data": data})
    return records


def compare_records(before, after):
    buckets = {}
    for index, record in enumerate(after):
        buckets.setdefault(record["sha256"], []).append(index)
    used = set()
    matches = []
    unmatched_before = []
    for record in before:
        found = None
        for index in buckets.get(record["sha256"], []):
            # Hashes index candidates; they never establish identity.
            if index not in used and record["data"] == after[index]["data"]:
                found = index
                break
        if found is None:
            unmatched_before.append(record["id"])
        else:
            used.add(found)
            matches.append(
                {
                    "pair_id": f"P{len(matches) + 1:06d}",
                    "before_id": record["id"],
                    "after_id": after[found]["id"],
                    "sha256": record["sha256"],
                    "actual_bytes_equal": True,
                }
            )
    unmatched_after = [r["id"] for i, r in enumerate(after) if i not in used]
    return {
        "counts": {
            "before": len(before),
            "after": len(after),
            "matched": len(matches),
            "unmatched_before": len(unmatched_before),
            "unmatched_after": len(unmatched_after),
        },
        "matches": matches,
        "unmatched_before": unmatched_before,
        "unmatched_after": unmatched_after,
        "before_faces_all_matched": not unmatched_before,
        "multiset_bijection": not unmatched_before and not unmatched_after,
    }


def parser():
    result = argparse.ArgumentParser(
        description="Exact native-face multiset audit; no geometric tolerance."
    )
    result.add_argument("--before", required=True, type=Path)
    result.add_argument("--before-sha", required=True)
    result.add_argument("--after", required=True, type=Path)
    result.add_argument("--after-sha", required=True)
    result.add_argument("--output", required=True, type=Path)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    root = args.output.absolute()
    try:
        # Atomic exclusivity check; never reuse, clean, or overwrite a directory.
        root.mkdir()
    except OSError as exc:
        print(f"Output refused: {exc}", file=sys.stderr)
        return 2

    sources = {"before": args.before.absolute(), "after": args.after.absolute()}
    expected = {"before": args.before_sha, "after": args.after_sha}
    report = {
        "schema": "native-face-audit/1",
        "audit_status": "error",
        "preservation_claim": "NOT_PROVEN",
        "before_faces_fully_preserved": None,
        "scope": "Faces() of each exact STEP snapshot imported with cq.importers.importStep(...).val(); equality is complete native serialization equality in this reader/kernel/writer.",
        "writer": {
            "api": "OCP.BRepTools.BRepTools.Write_s",
            "format": FORMAT_NAME,
            "with_triangles": False,
            "with_normals": False,
            "location_and_orientation": "Original wrapped face passed unchanged",
            "identity": "Actual byte equality; SHA256 used only for indexing",
        },
        "runtime": None,
        "audit_source_sha256": None,
        "inputs": {},
        "faces": {"before": [], "after": []},
        "comparison": None,
        "errors": [],
    }
    for side, source in sources.items():
        report["inputs"][side] = {
            "path": str(source),
            "expected_sha256": expected[side],
            "pre_import_sha256": None,
            "post_audit_sha256": None,
            "snapshot": side + ".step",
            "snapshot_post_audit_sha256": None,
        }

    try:
        report["runtime"] = runtime_info()
        report["audit_source_sha256"] = sha256(Path(__file__).read_bytes())
        # Preserve both exact input byte streams before validating or importing.
        for side, source in sources.items():
            data = source.read_bytes()
            item = report["inputs"][side]
            item["pre_import_sha256"] = sha256(data)
            with (root / item["snapshot"]).open("xb") as target:
                target.write(data)
        for side, item in report["inputs"].items():
            supplied = item["expected_sha256"]
            if re.fullmatch("[0-9a-fA-F]{64}", supplied) is None:
                raise ValueError(
                    f"{side}: expected SHA256 must be 64 hexadecimal digits"
                )
            if item["pre_import_sha256"] != supplied.lower():
                raise ValueError(f"{side}: input SHA256 mismatch")

        records = {}
        for side in sources:
            snapshot = root / report["inputs"][side]["snapshot"]
            shape = cq.importers.importStep(str(snapshot)).val()
            if not isinstance(shape, cq.Shape) or shape.isNull() or not shape.isValid():
                raise ValueError(f"{side}: imported shape is null or invalid")
            records[side] = inventory(shape.Faces(), side, root, report["faces"][side])
        report["comparison"] = compare_records(records["before"], records["after"])
    except Exception as exc:
        report["errors"].append(
            {
                "stage": "audit",
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )

    # Final input and snapshot hashes are attempted even after audit failure.
    for side, source in sources.items():
        item = report["inputs"][side]
        checks = [
            ("original", source, "post_audit_sha256"),
            ("snapshot", root / item["snapshot"], "snapshot_post_audit_sha256"),
        ]
        for kind, path, field in checks:
            try:
                digest = sha256(path.read_bytes())
                item[field] = digest
                if (
                    item["pre_import_sha256"] is not None
                    and digest != item["pre_import_sha256"]
                ):
                    raise ValueError(f"{side}: {kind} bytes changed during audit")
            except Exception as exc:
                report["errors"].append(
                    {
                        "stage": "final_hash",
                        "side": side,
                        "kind": kind,
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }
                )

    if not report["errors"] and report["comparison"] is not None:
        preserved = report["comparison"]["before_faces_all_matched"]
        report["audit_status"] = "completed"
        report["before_faces_fully_preserved"] = preserved
        report["preservation_claim"] = (
            "PROVEN_IN_SERIALIZATION_SCOPE" if preserved else "NOT_PROVEN"
        )
        code = 0 if preserved else 1
    else:
        code = 2
    try:
        with (root / "report.json").open("x", encoding="utf-8") as target:
            json.dump(report, target, indent=2, sort_keys=True, allow_nan=False)
    except Exception as exc:
        # Existing snapshots and native face files are deliberately retained.
        print(
            f"Report write failed; evidence retained in {root}: {exc}", file=sys.stderr
        )
        return 2
    print(str(root / "report.json"))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
