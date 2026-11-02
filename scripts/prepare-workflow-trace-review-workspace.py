#!/usr/bin/env python3
"""Index retained campaign evidence as a read-only Wright review workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
from pathlib import Path, PurePosixPath
from typing import Any

from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SELECTION = (
    REPO_ROOT
    / "specs"
    / "083-workflow-trace-review"
    / "evidence"
    / "corpus-manifest.json"
)
TEMPLATE_ROOT = (
    REPO_ROOT
    / "packages"
    / "workspace_service"
    / "src"
    / "workspace_service"
    / "engineering_workflow_templates"
    / "templates"
)
INPUT_ROOT = REPO_ROOT / "tests/datasets/engineering-workflows/scenarios"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _selection(path: Path) -> list[dict[str, str]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    items = document.get("selection")
    if not isinstance(items, list) or not items:
        raise ValueError("the corpus selection is empty or unavailable")
    selected: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("the corpus selection contains an invalid entry")
        values = {key: item.get(key) for key in ("case_id", "attempt_id", "run_path")}
        if any(not isinstance(value, str) or not value for value in values.values()):
            raise ValueError(
                "each corpus entry requires case, attempt, and run identities"
            )
        selected.append(values)  # type: ignore[arg-type]
    if len({item["case_id"] for item in selected}) != len(selected):
        raise ValueError("the corpus selection contains duplicate cases")
    return selected


def _safe_bundle_path(bundle: Path, relative: str) -> Path:
    pure = PurePosixPath(relative.replace("\\", "/"))
    if pure.is_absolute() or ".." in pure.parts:
        raise ValueError(f"unsafe campaign path: {relative}")
    candidate = bundle.joinpath(*pure.parts).resolve(strict=True)
    candidate.relative_to(bundle)
    return candidate


def _template_id(case_id: str) -> str:
    head, separator, suffix = case_id.rpartition("-")
    if not separator or not suffix.isdigit() or not head:
        raise ValueError(f"case identity does not end in a numeric variant: {case_id}")
    return head


def _instantiated_source(template_path: Path, record: dict[str, Any]) -> bytes:
    tokens = {
        match.group(1)
        for step_id in record.get("required_step_ids") or []
        if isinstance(step_id, str)
        if (match := re.search(r"_(t[a-f0-9]{24})$", step_id))
    }
    if len(tokens) > 1:
        raise ValueError("campaign run contains conflicting workflow instance tokens")
    token = next(
        iter(tokens), f"t{hashlib.sha256(str(record).encode()).hexdigest()[:24]}"
    )
    source = template_path.read_text(encoding="utf-8")
    return (
        source.replace("__instance__", token)
        .replace("__input_root__", f"inputs/{token}")
        .encode("utf-8")
    )


def _link_artifact(source: Path, target: Path, *, copy: bool = False) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.is_file() and target.stat().st_size == source.stat().st_size:
            if _sha256(target) == _sha256(source):
                return
        raise ValueError(f"refusing to replace existing review artifact: {target}")
    if copy:
        shutil.copy2(source, target)
        return
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)


def _store_workflow(workspace: Path, relative: str, source: bytes) -> None:
    text = source.decode("utf-8")
    store = WorkspaceWorkflowSourceStore(str(workspace))
    try:
        current = store.read(relative)
    except FileNotFoundError:
        store.create(relative, text)
        return
    if current.source != text:
        raise ValueError(f"refusing to replace existing review workflow: {relative}")


def _recover_input_pack(bundle: Path, workspace: Path, record: dict) -> dict | None:
    """Recover original inputs only from the dataset revision pinned by this run."""
    database = bundle / "campaign.sqlite3"
    if not database.is_file():
        return None
    fingerprint = f"{record.get('dataset_digest')}/{record.get('template_digest')}"
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as connection:
        row = connection.execute(
            "SELECT document FROM dataset_revisions WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()
    if row is None:
        return None
    revision = json.loads(row[0])
    manifest = {
        key: value
        for key, value in revision.items()
        if key not in {"path", "digest", "template_digest", "input_hashes"}
    }
    hashes = revision["input_hashes"]
    actual = hashlib.sha256(
        json.dumps({"manifest": manifest, "files": hashes}, sort_keys=True).encode()
    ).hexdigest()
    if (
        actual != record.get("dataset_digest")
        or manifest["scenario_id"] != record["scenario_id"]
    ):
        raise ValueError("campaign input revision does not match the executed dataset")
    relative = PurePosixPath(revision["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("unsafe campaign input pack path")
    root = (INPUT_ROOT / relative).resolve()
    root.relative_to(INPUT_ROOT.resolve())
    recovered, unavailable = [], []
    for name, expected in hashes.items():
        source = (root / name).resolve()
        source.relative_to(root)
        if not source.is_file() or _sha256(source) != expected:
            unavailable.append(name)
            continue
        target = (
            workspace
            / "runs"
            / record["scenario_id"]
            / "inputs"
            / record["attempt_id"]
            / name
        )
        _link_artifact(source, target, copy=True)
        recovered.append(
            {
                "path": name,
                "sha256": expected,
                "size_bytes": source.stat().st_size,
                "artifact_id": f"campaign-input:{record['scenario_id']}:{record['attempt_id']}:{name}",
                "artifact_role": "input",
                "reference": f"campaign/{record['scenario_id']}/{record['attempt_id']}/inputs/{name}",
            }
        )
    return {
        "dataset_digest": actual,
        "manifest": manifest,
        "input_hashes": hashes,
        "source": "campaign.sqlite3/dataset_revisions",
        "files": recovered,
        "unavailable": unavailable,
        "scope": "original_dataset_inputs_not_full_execution_context",
    }


def _review_supplements(
    workspace: Path,
    record: dict,
    input_pack: dict | None,
    bundle: Path | None = None,
) -> list[dict]:
    """Keep review reconstructions and documentary sources separate from run evidence."""
    case, attempt = record["scenario_id"], record["attempt_id"]
    root = workspace / "runs" / case / "review-sources" / attempt
    supplements = []

    def retain(name: str, content: bytes, role: str, **metadata) -> None:
        root.mkdir(parents=True, exist_ok=True)
        target = root / name
        if target.exists() and target.read_bytes() != content:
            raise ValueError(f"review source changed: {target}")
        target.write_bytes(content)
        supplements.append(
            {
                "path": name,
                "artifact_id": f"review-source:{case}:{attempt}:{name}",
                "artifact_role": role,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
                **metadata,
            }
        )

    if case.startswith("printed-replacement-part-"):
        files = {item["path"]: item for item in (input_pack or {}).get("files", [])}
        constituents = ["user-profile.md", "context.md"]
        if all(name in files for name in constituents):
            # This is the preparation recipe, not recovery of the missing runtime bytes.
            texts = [
                (workspace / "runs" / case / "inputs" / attempt / name).read_text(
                    encoding="utf-8"
                )
                for name in constituents
            ]
            retain(
                "assembled-context.md",
                "\n\n".join(texts).encode(),
                "input_reconstruction",
                reference=f"campaign/{case}/{attempt}/inputs/assembled-context.md",
                source_artifact_ids=[
                    files[name]["artifact_id"] for name in constituents
                ],
                provenance="Reassembled for this review from the digest-verified requester profile and design context, using the campaign preparation recipe. The original assembled execution snapshot was not transferred.",
            )
        checkpoint = (
            REPO_ROOT
            / "specs/081-engineering-workflow-templates/dataset-campaign/rapid-output-loop-checkpoint-2026-09-14.md"
        )
        if checkpoint.is_file():
            content = checkpoint.read_bytes()
            text = content.decode("utf-8")
            if (
                f"`{case}/{attempt}` completed with outputs" in text
                and "one Blender construct/export pass" in text
            ):
                for node_id in record.get("required_step_ids", []):
                    if node_id.startswith("create_mesh"):
                        retain(
                            "campaign-execution-checkpoint.md",
                            content,
                            "source_document",
                            node_id=node_id,
                            software="Blender",
                            provenance="Blender is identified by the campaign's task guidance and successful-pilot checkpoint for this attempt. Raw geometry tool calls and the software version were not transferred.",
                        )
                        break

    if case == "raspberry-pi-enclosure-01" and bundle is not None:
        visual_root = bundle / "visuals" / "ai-cfd-essay"
        produced = {
            item.get("path"): item
            for item in record.get("produced_files") or []
            if isinstance(item, dict)
        }
        source_artifact_ids = [
            produced[name]["artifact_id"]
            for name in ("cfd-comparison.json", "cfd-fields.zip")
            if name in produced and produced[name].get("artifact_id")
        ]
        node_id = next(
            (
                value
                for value in record.get("required_step_ids") or []
                if value.startswith("collect_cfd_results")
            ),
            None,
        )
        visualizations = (
            (
                "raspberry-pi-enclosure-velocity-comparison.png",
                "Airflow comparison",
                "Horizontal air-speed slice at z = 22 mm; the shared 0-2 m/s scale makes the ventilation patterns directly comparable.",
                "Air speed",
            ),
            (
                "raspberry-pi-enclosure-temperature-comparison.png",
                "Temperature comparison",
                "Horizontal temperature slice at z = 22 mm; both variants use the same 24.75-25.45 C scale.",
                "Temperature",
            ),
        )
        for name, title, caption, field in visualizations:
            source = visual_root / name
            if not source.is_file() or node_id is None:
                continue
            retain(
                name,
                source.read_bytes(),
                "review_visualization",
                reference=f"campaign/{case}/{attempt}/review-visualizations/{name}",
                node_id=node_id,
                title=title,
                caption=caption,
                engineering_summary=(
                    "Rendered from the actual OpenFOAM 10 chtMultiRegionFoam VTK fields "
                    "retained by this run. This exploratory analysis did not claim "
                    "steady-state convergence or engineering validation."
                ),
                visualization_parameters={
                    "field": field,
                    "slice_plane": "z = 22 mm",
                    "comparison": "Variant A and Variant B on one shared scale",
                    "renderer": "VTK off-screen rendering",
                },
                source_artifact_ids=source_artifact_ids,
                provenance=(
                    "Review-time visualization derived from this run's retained numerical "
                    "VTK fields; it is not an original solver screenshot or a new simulation."
                ),
            )
    return supplements


def prepare(bundle: Path, workspace: Path, selection_path: Path) -> dict[str, Any]:
    bundle = bundle.resolve(strict=True)
    workspace = workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if bundle == workspace:
        raise ValueError(
            "the review workspace must contain, not replace, the evidence bundle"
        )

    workflows = workspace / "workflows"
    runs = workspace / "runs"
    workflows.mkdir(exist_ok=True)
    runs.mkdir(exist_ok=True)
    indexed: list[dict[str, str]] = []

    for selected in _selection(selection_path):
        case_id = selected["case_id"]
        attempt_id = selected["attempt_id"]
        original_path = _safe_bundle_path(bundle, selected["run_path"])
        original_bytes = original_path.read_bytes()
        if len(original_bytes) > 16 * 1024 * 1024:
            raise ValueError(
                f"campaign run exceeds the Wright review limit: {original_path}"
            )
        record = json.loads(original_bytes)
        if not isinstance(record, dict):
            raise ValueError(f"campaign run is not an object: {original_path}")
        if (
            record.get("scenario_id") != case_id
            or record.get("attempt_id") != attempt_id
        ):
            raise ValueError(f"campaign identity mismatch: {original_path}")

        template_id = _template_id(case_id)
        template_path = TEMPLATE_ROOT / f"{template_id}.workflow.wflow"
        source = _instantiated_source(template_path, record)
        workflow_relative = f"workflows/{case_id}.workflow.wflow"
        _store_workflow(workspace, workflow_relative, source)

        run_dir = runs / case_id
        run_dir.mkdir(exist_ok=True)
        for artifact in record.get("produced_files") or []:
            if not isinstance(artifact, dict) or not isinstance(
                artifact.get("path"), str
            ):
                raise ValueError(f"campaign artifact is invalid: {original_path}")
            relative_artifact = PurePosixPath(artifact["path"].replace("\\", "/"))
            if relative_artifact.is_absolute() or ".." in relative_artifact.parts:
                raise ValueError(f"unsafe campaign artifact path: {artifact['path']}")
            source_artifact = (
                original_path.parent / "artifacts" / Path(*relative_artifact.parts)
            ).resolve(strict=True)
            source_artifact.relative_to(bundle)
            target_artifact = run_dir / "artifacts" / Path(*relative_artifact.parts)
            _link_artifact(source_artifact, target_artifact)

        imported = dict(record)
        imported["workflow_path"] = workflow_relative
        imported["events"] = list(record.get("step_events") or [])
        imported["completed_at"] = record.get("finished_at")
        imported["execution_ended_at"] = record.get("finished_at")
        imported["source_digest"] = hashlib.sha256(source).hexdigest()
        input_pack = _recover_input_pack(bundle, workspace, record)
        if input_pack is not None:
            imported["trace_input_pack"] = input_pack
        imported["trace_review_supplements"] = _review_supplements(
            workspace, record, input_pack, bundle
        )
        imported.setdefault("result", {})
        imported.setdefault("partial_results", {})
        imported["trace_import"] = {
            "schema_version": 1,
            "source_bundle": str(bundle),
            "source_path": selected["run_path"],
            "source_sha256": hashlib.sha256(original_bytes).hexdigest(),
            "source_unchanged": True,
        }
        imported_name = f"{attempt_id}.json"
        imported_path = run_dir / imported_name
        imported_path.write_text(
            json.dumps(imported, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        indexed.append(
            {
                "case_id": case_id,
                "attempt_id": attempt_id,
                "run_id": str(record.get("run_id") or ""),
                "workflow_path": workflow_relative,
                "run_path": str(imported_path.relative_to(workspace)),
                "source_path": selected["run_path"],
                "source_sha256": _sha256(original_path),
            }
        )

    index = {
        "schema_version": 1,
        "kind": "wright_workflow_trace_review_workspace",
        "evidence_bundle": str(bundle),
        "selection": str(selection_path.resolve()),
        "indexed_runs": len(indexed),
        "runs": indexed,
    }
    (workspace / "trace-review-index.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    args = parser.parse_args()
    print(json.dumps(prepare(args.bundle, args.workspace, args.selection), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
