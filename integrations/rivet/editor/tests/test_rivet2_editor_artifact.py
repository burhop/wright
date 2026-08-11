from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


EDITOR_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = EDITOR_ROOT / "manifest.json"
PINNED_REPOSITORY = "https://github.com/valerypopoff/rivet2.0.git"
PINNED_REVISION = "4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053"
RETIRED_MARKERS = ("1.25.0", "@ironclad/rivet", "Ironclad/rivet")
PUBLIC_ASSET_PATTERN = re.compile(
    rb"https?://(?:fonts\.(?:googleapis|gstatic)\.com|cdn\.|unpkg\.|jsdelivr\.)",
    re.IGNORECASE,
)


def _manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_manifest_pins_exact_rivet2_source_and_bounded_inputs() -> None:
    manifest = _manifest()

    assert manifest["schema_version"] == 2
    assert manifest["rivet_version"] == "2.8.9"
    assert manifest["source"] == {
        "repository": PINNED_REPOSITORY,
        "revision": PINNED_REVISION,
        "package": "@valerypopoff/rivet-app",
        "package_version": "2.8.9",
    }
    assert manifest["license"] == "MIT"

    for category in ("patches", "wrapper"):
        entries = manifest[category]
        assert isinstance(entries, list) and entries
        for entry in entries:
            assert isinstance(entry, dict)
            path = EDITOR_ROOT / str(entry["path"])
            assert path.is_file()
            assert entry["sha256"] == _sha256(path)


def test_bridge_contract_is_native_typed_and_origin_scoped() -> None:
    bridge = (EDITOR_ROOT / "wrapper" / "WrightEditorBridge.tsx").read_text(
        encoding="utf-8"
    )

    for message_type in (
        "wright-rivet:ready",
        "wright-rivet:set-project",
        "wright-rivet:project-set",
        "wright-rivet:get-project",
        "wright-rivet:project",
        "wright-rivet:error",
    ):
        assert message_type in bridge
    assert "event.source !== window.parent" in bridge
    assert "event.origin !== expectedParentOrigin" in bridge
    assert "deserializeProject" in bridge
    assert "serializeProject" in bridge
    assert "openProjectSnapshot" in bridge
    assert "replaceCurrent" in bridge
    assert "MemoryStorage" in bridge
    assert "showOpenFilePicker" not in bridge
    assert "indexedDB" not in bridge


def test_canvas_patch_mounts_only_graph_authoring_surfaces() -> None:
    patch = (EDITOR_ROOT / "patches" / "rivet2-canvas-only.patch").read_text(
        encoding="utf-8"
    )

    assert "canvasOnly?: boolean" in patch
    assert "canvasOnly && <GraphBuilder" in patch
    assert "!canvasOnly && <ProjectSelector" in patch
    assert "!canvasOnly && isCanvasMode" in patch
    assert "!canvasOnly && !openingProjectSelected" in patch
    assert "<ActionBar" in patch
    assert "<StatusBar" in patch
    assert "<LeftSidebar" in patch
    assert "!canvasOnly && <HelpModal" in patch
    assert "if (!canvasOnly)" in patch


def test_checked_in_artifact_inventory_and_tree_digest_are_exact() -> None:
    manifest = _manifest()
    files = manifest["files"]
    assert isinstance(files, list) and files

    digest_lines: list[str] = []
    recorded_paths: set[str] = set()
    for entry in files:
        assert isinstance(entry, dict)
        relative = str(entry["path"])
        path = EDITOR_ROOT / relative
        assert path.is_file(), relative
        assert entry["bytes"] == path.stat().st_size
        assert entry["sha256"] == _sha256(path)
        recorded_paths.add(relative)
        digest_lines.append(f"{entry['sha256']}  {relative}\n")

    actual_paths = {
        path.relative_to(EDITOR_ROOT).as_posix()
        for path in (EDITOR_ROOT / "dist").rglob("*")
        if path.is_file()
    }
    assert recorded_paths == actual_paths
    tree_digest = hashlib.sha256("".join(digest_lines).encode()).hexdigest()
    assert manifest["tree_sha256"] == tree_digest

    entrypoint = EDITOR_ROOT / str(manifest["entrypoint"])
    assert manifest["sha256"] == _sha256(entrypoint)


def test_shipped_editor_has_no_public_asset_or_retired_fallback() -> None:
    manifest = _manifest()
    for entry in manifest["files"]:
        path = EDITOR_ROOT / str(entry["path"])
        content = path.read_bytes()
        assert not PUBLIC_ASSET_PATTERN.search(content), path

    shipped_sources = [MANIFEST_PATH, EDITOR_ROOT / "host.py"]
    shipped_sources.extend(
        path
        for path in (EDITOR_ROOT / "dist").rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".js", ".css", ".json"}
    )
    for path in shipped_sources:
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in RETIRED_MARKERS:
            assert marker not in text, f"{marker!r} remains in {path}"
