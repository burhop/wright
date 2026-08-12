#!/usr/bin/env python3
"""Build one inspected Wright native Hermes application candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = ROOT / "apps" / "web"
WEB_DIST = WEB_ROOT / "dist"
PACKAGED_WEB = ROOT / "src" / "wright_engineering" / "static" / "web"
RUNTIME_EXTRA_LOCK = ROOT / "src" / "wright_engineering" / "runtime-extra-lock.json"
FORBIDDEN_PARTS = {"node_modules", ".git", ".env", "src"}
FORBIDDEN_SUFFIXES = {".map", ".key", ".pem", ".token", ".sqlite", ".db"}
TEXT_ASSET_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".svg",
    ".txt",
    ".webmanifest",
    ".xml",
}
PRESERVED_RUNTIME_WEB_ASSETS = ("third-party-licenses-api.txt",)


class CandidateBuildError(RuntimeError):
    pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument(
        "--skip-frontend-build",
        action="store_true",
        help="Use an already-built apps/web/dist (candidate tests only).",
    )
    return parser


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=900,
    )
    if completed.returncode:
        raise CandidateBuildError(
            f"candidate command failed ({command[0]}): {completed.stdout[-4000:]}"
        )


def build_frontend() -> None:
    npm = shutil.which("npm")
    if npm is None:
        raise CandidateBuildError("npm is required only on the release build host")
    _run([npm, "ci"], cwd=WEB_ROOT)
    _run([npm, "run", "build"], cwd=WEB_ROOT)


def inspect_web_dist(source: Path) -> list[dict[str, object]]:
    if not (source / "index.html").is_file():
        raise CandidateBuildError("frontend build did not produce index.html")
    if not (source / "assets").is_dir():
        raise CandidateBuildError("frontend build did not produce assets/")
    entries: list[dict[str, object]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise CandidateBuildError(f"frontend symlink is forbidden: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        lowered = {part.lower() for part in relative.parts}
        if lowered & FORBIDDEN_PARTS or path.suffix.lower() in FORBIDDEN_SUFFIXES:
            raise CandidateBuildError(f"forbidden frontend artifact: {relative}")
        entries.append(
            {
                "path": relative.as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries


def normalize_text_assets(root: Path) -> None:
    """Make manifest-addressed text assets byte-stable across build hosts."""
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_ASSET_SUFFIXES:
            continue
        payload = path.read_bytes()
        normalized = payload.replace(b"\r\n", b"\n")
        if normalized != payload:
            path.write_bytes(normalized)


def write_asset_manifest(
    destination: Path, entries: Iterable[dict[str, object]]
) -> str:
    manifest = {"schema_version": 1, "files": list(entries)}
    encoded = json.dumps(manifest, sort_keys=True, indent=2) + "\n"
    destination.write_text(encoded, encoding="utf-8", newline="\n")
    return sha256_file(destination)


def stage_frontend() -> str:
    preserved_assets: dict[str, bytes] = {}
    if PACKAGED_WEB.exists():
        for relative in PRESERVED_RUNTIME_WEB_ASSETS:
            source = PACKAGED_WEB / relative
            if source.is_file():
                preserved_assets[relative] = source.read_bytes()
        shutil.rmtree(PACKAGED_WEB)
    shutil.copytree(WEB_DIST, PACKAGED_WEB)
    for relative, payload in preserved_assets.items():
        destination = PACKAGED_WEB / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
    normalize_text_assets(PACKAGED_WEB)
    entries = inspect_web_dist(PACKAGED_WEB)
    return write_asset_manifest(PACKAGED_WEB / "asset-manifest.json", entries)


def stage_runtime_extra_lock() -> str:
    project = __import__("tomllib").loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    requirements = sorted(set(project["optional-dependencies"]["runtime"]))
    if not requirements:
        raise CandidateBuildError("runtime extra must not be empty")
    payload = {
        "schema_version": 1,
        "distribution": project["name"],
        "version": project["version"],
        "requirements": requirements,
        "uv_lock_sha256": sha256_file(ROOT / "uv.lock"),
    }
    encoded = json.dumps(payload, sort_keys=True, indent=2) + "\n"
    RUNTIME_EXTRA_LOCK.write_text(encoded, encoding="utf-8", newline="\n")
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _safe_output(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    forbidden = {ROOT, Path(resolved.anchor), Path.home().resolve(strict=False)}
    if resolved in forbidden:
        raise CandidateBuildError(f"unsafe candidate output directory: {resolved}")
    return resolved


def build_distributions(output: Path) -> list[Path]:
    output = _safe_output(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    _run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--wheel",
            "--outdir",
            str(output),
            str(ROOT),
        ],
        cwd=ROOT,
    )
    artifacts = sorted(
        path
        for path in output.iterdir()
        if path.suffix == ".whl" or path.name.endswith(".tar.gz")
    )
    if len(artifacts) != 2:
        raise CandidateBuildError("expected exactly one wheel and one source archive")
    return artifacts


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.skip_frontend_build:
        build_frontend()
    web_manifest_hash = stage_frontend()
    runtime_extra_lock_hash = stage_runtime_extra_lock()
    artifacts = build_distributions(args.output)

    sys.path.insert(0, str(ROOT))
    from scripts.release.python_artifacts import validate_native_distribution

    inspections = [validate_native_distribution(path) for path in artifacts]

    evidence = {
        "schema_version": 1,
        "distribution": "wright-engineering",
        "version": __import__("tomllib").loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]["version"],
        "ui_manifest_sha256": web_manifest_hash,
        "runtime_extra_lock_sha256": runtime_extra_lock_hash,
        "compatibility_sha256": sha256_file(
            ROOT / "src" / "wright_engineering" / "compatibility.json"
        ),
        "native_inspections": [
            {
                "artifact_kind": item.artifact_kind,
                "bundled_modules": list(item.bundled_modules),
                "ui_manifest_sha256": item.ui_manifest_sha256,
                "runtime_extra_lock_sha256": item.runtime_extra_lock_sha256,
            }
            for item in inspections
        ],
        "artifacts": [
            {
                "filename": path.name,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in artifacts
        ],
    }
    evidence_path = args.evidence.expanduser().resolve(strict=False)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
