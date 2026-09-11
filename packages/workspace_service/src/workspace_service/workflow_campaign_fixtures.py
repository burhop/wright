"""Bounded, digest-checked workspace fixtures for repeatable development runs."""

import json
from pathlib import Path
from .workflow_campaign import sha
from .workspace_path import WorkspacePath

MAX_FIXTURE_BYTES = 100 * 1024 * 1024


def create_bundle(manifest, ids, destination):
    cases = [c for c in manifest["cases"] if c["id"] in ids]
    if not ids or set(ids) != {c["id"] for c in cases}:
        raise ValueError("Select explicit known workflow IDs.")
    root = WorkspacePath(manifest["workspace"])
    files = {c["path"]: c["source_sha256"] for c in cases}
    for case in cases:
        for item in case["inputs"]:
            if item.get("path"):
                files.setdefault(item["path"], item.get("sha256"))
    if len(files) > 128:
        raise ValueError("A fixture bundle is limited to 128 files.")
    contents = {}
    total = 0
    for path, expected in files.items():
        source = root.resolve(path, must_exist=True)
        if source.stat().st_size + total > MAX_FIXTURE_BYTES:
            raise ValueError("Fixture bundle exceeds 100 MiB.")
        content = source.read_bytes()
        total += len(content)
        if total > MAX_FIXTURE_BYTES:
            raise ValueError("Fixture bundle exceeds 100 MiB.")
        if expected and sha(content) != expected:
            raise ValueError(f"Fixture changed since inventory: {path}")
        contents[path] = content
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    target = WorkspacePath(str(destination))
    records = []
    for path, content in contents.items():
        output = target.resolve("files/" + path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(content)
        records.append({"path": path, "sha256": sha(content), "bytes": len(content)})
    metadata = {
        "schema_version": 1,
        "profile": "development-fixtures",
        "cases": cases,
        "files": records,
        "limitations": [
            "Application identities and credentials are not portable. Select the intended server/open document before running.",
            "This bundle contains inputs and definitions, not a claim of live verification.",
        ],
    }
    (destination / "bundle.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def restore_bundle(bundle, workspace):
    """Restore only missing fixtures; never overwrite different user content."""
    bundle = Path(bundle)
    metadata = json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))
    records = metadata.get("files", [])
    if metadata.get("schema_version") != 1 or not records or len(records) > 128:
        raise ValueError("Invalid fixture bundle.")
    origin = WorkspacePath(str(bundle))
    target = WorkspacePath(str(workspace))
    pending = []
    total = 0
    seen = set()
    for item in records:
        source = origin.resolve("files/" + item["path"], must_exist=True)
        output = target.resolve(item["path"])
        if str(output).casefold() in seen:
            raise ValueError("Duplicate fixture destination.")
        seen.add(str(output).casefold())
        if source.stat().st_size + total > MAX_FIXTURE_BYTES:
            raise ValueError("Fixture bundle exceeds 100 MiB.")
        content = source.read_bytes()
        total += len(content)
        if (
            total > MAX_FIXTURE_BYTES
            or len(content) != item["bytes"]
            or sha(content) != item["sha256"]
        ):
            raise ValueError("Fixture digest or size does not match its manifest.")
        if output.exists():
            if (
                output.stat().st_size != len(content)
                or sha(output.read_bytes()) != item["sha256"]
            ):
                raise ValueError(f"Existing workspace file differs: {item['path']}")
        else:
            pending.append((output, content))
    for output, content in pending:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(content)
    return {
        "restored_files": len(pending),
        "unchanged_files": len(records) - len(pending),
    }
