"""Observed raw/normalized/canonical input lineage, separate from run outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from workspace_service.workflow_source_execution import _parse
from workspace_service.workspace_path import WorkspacePath

ROOT = Path(__file__).resolve().parents[1]
LINEAGE = ROOT / ".local-run/feature-081-live/image-normalization-lineage"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def declared(manifest):
    files = manifest["files"]
    return [files["user_profile"], files["prompt"], *files["context"], *files["images"]]


def consumers(source):
    sections = _parse(source)
    result = {}
    for section in sections:
        if section["kind"] != "input":
            continue
        path = section["fields"].get("settings", {}).get("workspace_file")
        if not path:
            continue
        bindings = []
        for edge in sections:
            fields = edge["fields"]
            if edge["kind"] != "connection" or fields.get("type") != "item":
                continue
            producer = fields.get("from", "").split(".", 1)
            if producer[0] != section["id"]:
                continue
            target = fields["to"].split(".", 1)
            bindings.append(
                {
                    "input_block": section["id"],
                    "output_port": producer[1] if len(producer) > 1 else None,
                    "consumer_block": target[0],
                    "consumer_port": target[1] if len(target) > 1 else None,
                    "connection": edge["id"],
                }
            )
        result.setdefault(path, []).extend(bindings)
    return result


def _receipt(manifest, name, raw_hash, png_hash, lineage_root):
    path = (
        Path(lineage_root)
        / manifest["scenario_id"]
        / (raw_hash + "-" + png_hash + ".json")
    )
    if not path.is_file():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        value.get("operation") != "wright.svg-rasterization.v1"
        or value.get("scenario_id") != manifest["scenario_id"]
        or value.get("source") != name
        or value.get("output") != str(Path(name).with_suffix(".png"))
        or value.get("source_sha256") != raw_hash
        or value.get("output_sha256") != png_hash
        or value.get("reproduced_sha256") != png_hash
        or value.get("matches") is not True
        or value.get("historical_execution_claim") is not False
        or value.get("observation_kind")
        not in {"reproduced_now_compared_existing", "rendered_now"}
        or value.get("operation_sha256")
        != digest((ROOT / "scripts/render-engineering-dataset-images.mjs").read_bytes())
        or not value.get("observed_at")
        or value.get("renderer", {}).get("network") != "http_https_blocked"
    ):
        raise ValueError("Invalid image normalization lineage: " + name)
    return value


def build_bindings(report, *, manifest, raw_directory=None, lineage_root=LINEAGE):
    """Read-only observation of actual bytes; unresolved mappings remain explicit."""
    workspace = WorkspacePath(report["workspace_root"])
    # Preparers/API save use UTF-8 logical source with LF; a Windows draft may
    # contain CRLF. The execution validator separately pins actual saved bytes.
    source_bytes = Path(report["source"]).read_text(encoding="utf-8").encode("utf-8")
    if digest(source_bytes) != report["source_sha256"]:
        raise ValueError("Canonical source identity changed")
    source = source_bytes.decode("utf-8")
    canonical = consumers(source)
    staged = {}
    for item in report["input_manifest"]:
        payload = workspace.resolve(item["path"], must_exist=True).read_bytes()
        if digest(payload) != item["sha256"]:
            raise ValueError("Staged input identity changed: " + item["path"])
        staged[item["path"]] = payload
    for path in canonical:
        if path not in staged:
            raise ValueError(
                "Canonical input is missing from staged identity inventory: " + path
            )
    originals = {}
    raw_hashes = {}
    for name in declared(manifest):
        matches = [path for path in staged if path.rsplit("/", 1)[-1] == name]
        if len(matches) != 1:
            raise ValueError("Original file needs one exact staged identity: " + name)
        relative = matches[0]
        payload = staged[relative]
        if (
            raw_directory is not None
            and WorkspacePath(raw_directory).resolve(name, must_exist=True).read_bytes()
            != payload
        ):
            raise ValueError("Original uploaded bytes were changed: " + name)
        originals[name] = relative
        raw_hashes[name] = digest(payload)
    bindings = []
    for name, relative in originals.items():
        raw = staged[relative]
        entry = {
            "raw_file": name,
            "raw_sha256": raw_hashes[name],
            "staged_path": relative,
            "staged_sha256": digest(raw),
            "relationships": [],
        }
        for path, targets in canonical.items():
            if not targets:
                continue
            if path == relative:
                entry["relationships"].append(
                    {
                        "kind": "unchanged_upload",
                        "normalized_path": path,
                        "normalized_sha256": digest(staged[path]),
                        "consumers": targets,
                    }
                )
                continue
            if Path(name).suffix.lower() not in {
                ".txt",
                ".md",
                ".csv",
                ".json",
                ".yaml",
                ".yml",
            }:
                continue
            try:
                text = (
                    raw.decode("utf-8")
                    .replace("\r\n", "\n")
                    .replace("\r", "\n")
                    .encode("utf-8")
                )
                normalized = staged[path].decode("utf-8").encode("utf-8")
            except UnicodeError:
                continue
            start = normalized.find(text)
            if text and start >= 0:
                entry["relationships"].append(
                    {
                        "kind": "utf8_text_embedding",
                        "normalization": "utf8-lf-v1",
                        "normalized_path": path,
                        "normalized_sha256": digest(staged[path]),
                        "byte_start": start,
                        "byte_end": start + len(text),
                        "embedded_sha256": digest(text),
                        "consumers": targets,
                    }
                )
        if name.endswith(".svg"):
            png = str(Path(name).with_suffix(".png"))
            if png in originals:
                receipt = _receipt(
                    manifest, name, raw_hashes[name], raw_hashes[png], lineage_root
                )
                png_path = originals[png]
                if receipt and canonical.get(png_path):
                    entry["relationships"].append(
                        {
                            "kind": "retained_editable_original",
                            "normalized_path": png_path,
                            "normalized_sha256": raw_hashes[png],
                            "image_conversion": receipt,
                            "consumers": canonical[png_path],
                        }
                    )
        entry["status"] = "mapped" if entry["relationships"] else "unresolved"
        bindings.append(entry)
    fingerprint = digest(
        json.dumps({"manifest": manifest, "files": raw_hashes}, sort_keys=True).encode()
    )
    return {
        "schema_version": 1,
        "contract": "wright.input-bindings.v1",
        "scenario_id": manifest["scenario_id"],
        "attempt_id": report["attempt_id"],
        "source_sha256": report["source_sha256"],
        "dataset_digest": fingerprint,
        "raw_manifest": manifest,
        "input_manifest": [
            {"path": path, "sha256": digest(data)}
            for path, data in sorted(staged.items())
        ],
        "bindings": bindings,
        "complete": all(item["status"] == "mapped" for item in bindings),
        "scope": "observed_input_preparation_not_execution_or_engineering_validation",
    }


def validate_bindings(
    document, *, workspace_root, source_path, expected_case=None, require_complete=True
):
    """Reconstruct every byte/span/port edge rather than trust caller assertions."""
    if (
        document.get("contract") != "wright.input-bindings.v1"
        or document.get("schema_version") != 1
    ):
        raise ValueError("Unsupported input binding contract")
    if not isinstance(document.get("scenario_id"), str) or any(
        c not in "abcdefghijklmnopqrstuvwxyz0123456789-"
        for c in document["scenario_id"]
    ):
        raise ValueError("Invalid input binding scenario identity")
    # Reuse embedded conversion receipts, validating their identities through the
    # same strict matcher without filesystem publication or historical claims.
    import tempfile

    with tempfile.TemporaryDirectory(prefix="wright-binding-validation-") as temporary:
        receipts = Path(temporary) / document["scenario_id"]
        receipts.mkdir()
        for entry in document["bindings"]:
            for relation in entry.get("relationships", []):
                receipt = relation.get("image_conversion")
                if receipt:
                    for key in ("source_sha256", "output_sha256"):
                        if len(receipt.get(key, "")) != 64 or any(
                            c not in "0123456789abcdef" for c in receipt[key]
                        ):
                            raise ValueError("Malformed normalization digest")
                    (
                        receipts
                        / (
                            receipt["source_sha256"]
                            + "-"
                            + receipt["output_sha256"]
                            + ".json"
                        )
                    ).write_text(json.dumps(receipt), encoding="utf-8")
        report = {
            "workspace_root": workspace_root,
            "source": str(source_path),
            "source_sha256": document["source_sha256"],
            "attempt_id": document["attempt_id"],
            "input_manifest": document["input_manifest"],
        }
        actual = build_bindings(
            report, manifest=document["raw_manifest"], lineage_root=temporary
        )
    if actual != document:
        raise ValueError(
            "Input binding map omitted or corrupted actual raw/normalized/canonical lineage"
        )
    if require_complete and not actual["complete"]:
        raise ValueError("Input binding map has unconsumed or unproven original files")
    if expected_case:
        for field, key in (
            ("scenario_id", "scenario_id"),
            ("attempt_id", "attempt_id"),
            ("source_sha256", "source_digest"),
            ("dataset_digest", "dataset_digest"),
        ):
            if document[field] != expected_case[key]:
                raise ValueError(
                    "Input binding evidence belongs to a different execution identity"
                )
    return actual


def emit_for_preparation(report, scenario_directory):
    manifest = json.loads(
        (Path(scenario_directory) / "scenario.json").read_text(encoding="utf-8")
    )
    document = build_bindings(
        report, manifest=manifest, raw_directory=scenario_directory
    )
    target = Path(report["source"]).with_name("input-bindings.json")
    raw = json.dumps(document, indent=2, ensure_ascii=False).encode() + b"\n"
    if target.exists() and target.read_bytes() != raw:
        raise ValueError("Attempt input binding observation is immutable")
    target.write_bytes(raw)
    report["input_binding_evidence"] = {
        "path": str(target),
        "sha256": digest(raw),
        "complete": document["complete"],
    }
    return document


def validate_case(case):
    evidence = case.get("input_binding_evidence")
    if not evidence:
        if case.get("input_binding_contract"):
            raise ValueError(
                "Execution manifest requires missing input binding evidence"
            )
        return None  # Legacy enrolled attempts remain immutable and observable.
    raw = Path(evidence["path"]).read_bytes()
    if digest(raw) != evidence["sha256"]:
        raise ValueError("Input binding evidence digest changed")
    document = json.loads(raw)
    saved_source = WorkspacePath(case["workspace_root"]).resolve(
        case["source_path"], must_exist=True
    )
    if digest(saved_source.read_bytes()) != case["source_digest"]:
        raise ValueError("Saved canonical source bytes changed")
    return validate_bindings(
        document,
        workspace_root=case["workspace_root"],
        source_path=saved_source,
        expected_case=case,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--scenario-directory", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = json.loads(Path(args.prepared).read_text(encoding="utf-8"))
    scenario = Path(args.scenario_directory)
    value = build_bindings(
        report,
        manifest=json.loads((scenario / "scenario.json").read_text(encoding="utf-8")),
        raw_directory=scenario,
    )
    target = Path(args.output)
    if target.exists():
        raise ValueError("Observation target already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "complete": value["complete"],
                "files": len(value["bindings"]),
                "unresolved": [
                    x["raw_file"] for x in value["bindings"] if x["status"] != "mapped"
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
