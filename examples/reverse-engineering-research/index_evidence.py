"""Index an existing local reference package without copying or interpreting media.

This is an authoring utility, not a workflow executor or engineering validator.
Original annotations remain unreviewed imports; hashes establish bytes, not truth.
"""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PureWindowsPath
import re


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def confined(root, name):
    relative = Path(name)
    if relative.is_absolute() or PureWindowsPath(name).drive or ".." in relative.parts:
        raise ValueError("Asset path must be relative and confined")
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Asset escapes input root")
    return path


def image_ids(locator):
    # Decode only explicit IDs/ranges. No inference from component names or pixels.
    found = set()
    for start, end in re.findall(r"I(\d+)(?:\s*-\s*I(\d+))?", locator):
        lower, upper = int(start), int(end or start)
        if upper < lower or upper - lower > 1000:
            raise ValueError("Invalid bounded image range")
        found.update(f"I{i:02d}" for i in range(lower, upper + 1))
    return sorted(found)


def index(root):
    image_path = root / "data/image_manifest.json"
    part_path = root / "data/parts_references.json"
    images = json.loads(image_path.read_text(encoding="utf-8-sig"))
    parts = json.loads(part_path.read_text(encoding="utf-8-sig"))
    components = [
        {
            "id": p["reference_id"],
            "name": p["subsystem"],
            "prior_locator": p["locator"],
            "prior_evidence_status": p["evidence_status"],
            "prior_applicability": p["applicability"],
            "image_ids": image_ids(p["locator"]),
            "missing_information": p["missing_information"],
            "annotation_status": "imported_not_newly_visually_verified",
            "dimensional_readiness": "blocked_no_accepted_metric_basis",
        }
        for p in parts
    ]
    known = {i["image_id"] for i in images}
    observations, issues = [], []
    for component in components:
        absent = set(component["image_ids"]) - known
        if absent:
            issues.append(
                {"component_id": component["id"], "missing_image_ids": sorted(absent)}
            )
    for item in images:
        path = confined(root, item["local_path"])
        actual = digest(path) if path.is_file() else None
        valid = actual is not None and actual == item.get("sha256")
        if not valid:
            reason = (
                "not_downloaded_lead"
                if item.get("download_status") == "not_downloaded"
                else "missing_or_changed_asset"
            )
            issues.append({"image_id": item["image_id"], "reason": reason})
        observations.append(
            {
                "id": item["image_id"],
                "relative_path": item["local_path"],
                "declared_sha256": item.get("sha256"),
                "actual_sha256": actual,
                "byte_identity_verified": valid,
                "dimensions_px": [item.get("width_px"), item.get("height_px")],
                "source_id": item["source_id"],
                "source_uri": item.get("source_page_url"),
                "publication_date": item.get("source_publication_date"),
                "prior_view_annotation": item.get("view_angle"),
                "prior_configuration": item.get("configuration"),
                "prior_provenance": item.get("provenance"),
                "rights": item.get("rights"),
                "component_ids": [
                    c["id"] for c in components if item["image_id"] in c["image_ids"]
                ],
                "capture_group_id": None,
                "publication_group_id": item["source_id"],
                "camera_revision": None,
                "scale_anchor": None,
                "audit_role": "unassigned",
                "annotation_status": "imported_not_newly_visually_verified",
            }
        )
    groups = {}
    for item in observations:
        if item["actual_sha256"]:
            groups.setdefault(item["actual_sha256"], []).append(item["id"])
    return {
        "schema_version": "wright.research-reference-index/1",
        "scope": "local metadata and byte identity only; no new visual observations or dimensional acceptance",
        "input_manifests": {p.name: digest(p) for p in [image_path, part_path]},
        "components": components,
        "observations": observations,
        "duplicate_byte_groups": [ids for ids in groups.values() if len(ids) > 1],
        "unique_asset_hashes": len(groups),
        "issues": issues,
        "unassigned_images": [i["id"] for i in observations if not i["component_ids"]],
        "required_next_inputs": [
            "review component/view links",
            "object state and capture lineage",
            "accepted requirements and uncertainty",
            "independent calibration/scale where metric",
            "frame-level video observations",
            "rights for intended distribution",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = index(args.input_root)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
    print(
        json.dumps(
            {
                "images": len(report["observations"]),
                "components": len(report["components"]),
                "unique_hashes": report["unique_asset_hashes"],
                "issues": len(report["issues"]),
            }
        )
    )
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
