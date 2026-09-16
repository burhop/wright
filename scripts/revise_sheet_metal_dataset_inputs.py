"""Register additive R1 human inputs while preserving prior manifests and hashes.

Does not stage workflows, enroll grants or execute CAD. Revisions live outside
the thirty scenario slots and retain exact previous scenario.json bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from engineering_dataset_campaign import DEFAULT_INPUTS, load_dataset


ADDENDUM = "stock-selection-revision-r1.md"
REVISION = "2026-09-12-sheet-stock-r1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def publish(inputs: Path, *, templates=None, addendum_name=ADDENDUM, revision_name=REVISION, scenario_id=None, reason=None):
    if Path(addendum_name).name != addendum_name or not addendum_name.endswith(".md"):
        raise ValueError("Addendum must be a top-level Markdown filename")
    if Path(revision_name).name != revision_name or not revision_name or revision_name in {".", ".."}:
        raise ValueError("Revision must be a single directory name")
    inputs = inputs.resolve()
    config = json.loads((inputs / "campaign.json").read_text(encoding="utf-8"))
    revisions = inputs / "revisions" / revision_name
    revisions.mkdir(parents=True, exist_ok=True)
    rows = []
    for folder in sorted((inputs / "scenarios" / "sheet-metal-supplier-handoff").iterdir()):
        path = folder / "scenario.json"
        original_raw = path.read_bytes()
        manifest = json.loads(original_raw)
        identity = manifest["scenario_id"]
        if scenario_id is not None and identity != scenario_id:
            continue
        archived = revisions / identity
        archived.mkdir(exist_ok=True)
        ledger_path = archived / "revision.json"
        if ledger_path.exists():
            ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
            if sha(original_raw) != ledger["revised_manifest_sha256"]:
                raise ValueError("Active manifest differs from recorded revision")
            for name, expected in ledger["retained_original_files"].items():
                if sha((folder / name).read_bytes()) != expected:
                    raise ValueError("Original human file changed: " + name)
            if sha((folder / addendum_name).read_bytes()) != ledger["addendum_sha256"]:
                raise ValueError("Recorded addendum changed")
            rows.append(ledger)
            continue
        if addendum_name in manifest["files"]["context"]:
            raise ValueError("Addendum was activated without an archived revision")
        kwargs = {} if templates is None else {"templates": templates}
        before = load_dataset(path, inputs, config, **kwargs)
        original_files = {p.name: sha(p.read_bytes()) for p in folder.iterdir()
                          if p.is_file() and p.name not in {"scenario.json", addendum_name}}
        addendum = (folder / addendum_name).read_bytes()
        if not addendum:
            raise ValueError("Additive human document must be nonempty")
        previous = archived / "scenario.before.json"
        if previous.exists() and previous.read_bytes() != original_raw:
            raise ValueError("Prior manifest snapshot is immutable")
        if not previous.exists():
            previous.write_bytes(original_raw)
        manifest["files"]["context"].append(addendum_name)
        revised_raw = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
        path.write_bytes(revised_raw)
        after = load_dataset(path, inputs, config, **kwargs)
        ledger = {
            "schema_version": 1, "revision": revision_name, "scenario_id": identity,
            "reason": reason or "Explicit fictional stock-compatible bounds, sourced-row selection and geometric native-label mapping; preserve mandatory DFM, geometry, approvals and manufacturing HOLD.",
            "prior_dataset_digest": before["digest"], "dataset_digest": after["digest"],
            "template_digest": before["template_digest"],
            "original_manifest_sha256": sha(original_raw),
            "revised_manifest_sha256": sha(revised_raw),
            "retained_original_files": original_files,
            "addendum": addendum_name, "addendum_sha256": sha(addendum),
            "prior_manifest": "scenario.before.json", "execution_started": False,
        }
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        rows.append(ledger)
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--addendum", default=ADDENDUM)
    parser.add_argument("--revision", default=REVISION)
    parser.add_argument("--scenario")
    parser.add_argument("--reason")
    args = parser.parse_args()
    print(json.dumps({"status": "input_revisions_published", "revisions": publish(args.inputs, addendum_name=args.addendum, revision_name=args.revision, scenario_id=args.scenario, reason=args.reason)}, indent=2))
