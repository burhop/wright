"""Fixed frontend build envelope. Model output supplies neither commands nor dependencies."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from importlib.resources import files
import json
from pathlib import Path
from uuid import uuid4

from core.process_interfaces import BuildReport, InterfaceManifest, SourceEnvelope
from core.process_interactions import ProcessRef, Reason
from core.process_validation import canonical_digest, canonical_json
from core.redaction import redact_text

from .errors import ProcessInterfaceError, safe_diagnostic


@dataclass(frozen=True)
class BuildToolchain:
    """Trusted installation settings, never fields in an authoring response."""

    node: Path
    dependency_root: Path
    client_root: Path
    kit_root: Path
    timeout_seconds: int = 120
    maximum_bundle_bytes: int = 31_457_280

    def __post_init__(self):
        if not 1 <= self.timeout_seconds <= 120:
            raise ValueError("Compiler timeout must be within 1–120 seconds")
        if not 1 <= self.maximum_bundle_bytes <= 31_457_280:
            raise ValueError("Compiled bundle limit must be within 1–30 MiB")

    def describe(self) -> dict:
        """Actual local package identity; missing resources are actionable."""
        paths = {
            "typescript": self.dependency_root / "node_modules/typescript/package.json",
            "vite": self.dependency_root / "node_modules/vite/package.json",
            "react": self.dependency_root / "node_modules/react/package.json",
            "react-dom": self.dependency_root / "node_modules/react-dom/package.json",
            "react-markdown": self.dependency_root
            / "node_modules/react-markdown/package.json",
            "remark-gfm": self.dependency_root / "node_modules/remark-gfm/package.json",
            "three": self.dependency_root / "node_modules/three/package.json",
            "@types/react": self.dependency_root
            / "node_modules/@types/react/package.json",
            "@types/react-dom": self.dependency_root
            / "node_modules/@types/react-dom/package.json",
            "@types/three": self.dependency_root
            / "node_modules/@types/three/package.json",
            "@wright/process-client": self.client_root / "package.json",
            "@wright/ui-kit": self.kit_root / "package.json",
        }
        try:
            if not self.node.is_file():
                raise OSError("Node executable is unavailable")
            resources = files("workspace_service.process_interfaces.resources")
            declared = json.loads(
                resources.joinpath("toolchain.json").read_text(encoding="utf-8")
            )
            packages = {}
            for name, path in paths.items():
                raw = path.read_bytes()
                data = json.loads(raw)
                if data.get("name") != name or not data.get("version"):
                    raise ValueError("Unexpected installed package identity")
                if data["version"] != declared["packages"][name]:
                    raise ValueError(
                        "Installed compiler packages differ from Wright's qualified fixed toolchain"
                    )
                packages[name] = {
                    "version": data["version"],
                    "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                }
            public_source_hashes = {}
            for package_root in (self.client_root, self.kit_root):
                for path in sorted((package_root / "src").rglob("*")):
                    if path.is_file():
                        public_source_hashes[
                            f"{package_root.name}/{path.relative_to(package_root).as_posix()}"
                        ] = hashlib.sha256(path.read_bytes()).hexdigest()
            script = (
                files("workspace_service.process_interfaces.resources")
                .joinpath("fixed-builder.mjs")
                .read_bytes()
            )
        except (OSError, ValueError) as exc:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The local interface compiler is unavailable.",
                "Configure the qualified local Node, compiler and public Wright packages.",
                details={"diagnostic": str(exc)},
            ) from None
        return {
            "packages": packages,
            "public_source_digest": canonical_digest(public_source_hashes),
            "builder_sha256": hashlib.sha256(script).hexdigest(),
            "timeout_seconds": self.timeout_seconds,
            "maximum_bundle_bytes": self.maximum_bundle_bytes,
        }


def validate_manifest_bindings(
    manifest: InterfaceManifest,
    process: ProcessRef,
    catalog: list[dict],
    *,
    allow_process_revision: bool = False,
) -> tuple[Reason, ...]:
    """Compare against a server-derived catalog, including schema and exact ports."""
    same_family = (
        manifest.process.workspace_id == process.workspace_id
        and manifest.process.source_path == process.source_path
    )
    if manifest.process != process and not (allow_process_revision and same_family):
        raise ProcessInterfaceError(
            "SCOPE_DENIED",
            "This interface names another accepted process.",
            "Use the process reference supplied by Wright.",
        )
    if (manifest.client_version, manifest.kit_version) != ("1.0.0", "1.0.0"):
        raise ProcessInterfaceError(
            "UI_INCOMPATIBLE",
            "The interface requires unsupported client or kit versions.",
            "Generate against the installed public client and kit version 1.0.0.",
        )
    if "process.read" not in manifest.capabilities:
        raise ProcessInterfaceError(
            "UI_INCOMPATIBLE",
            "A process interface must declare its scoped read operation.",
            "Include process.read so the host can supply authoritative process context.",
        )
    missing = []
    for binding in manifest.bindings:
        matches = [
            item
            for item in catalog
            if item.get("kind") == binding.kind
            and item.get("selector") == binding.selector
        ]
        valid = len(matches) == 1 and all(
            getattr(binding, name) == matches[0].get(name)
            for name in ("block_id", "port_id", "expected_schema")
        )
        if valid:
            continue
        reason = Reason(
            code="UI_BINDING_UNRESOLVED",
            message=f"Interface binding {binding.binding_id} does not match its accepted declaration.",
            correction=binding.fallback
            or "Update the selector, exact port and schema from Wright's supplied binding catalog.",
            binding_id=binding.binding_id,
        )
        if binding.required:
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                reason.message,
                reason.correction,
                details={"binding_id": binding.binding_id},
            )
        missing.append(reason)
    return tuple(missing)


@dataclass(frozen=True)
class BuiltInterface:
    report: BuildReport
    root: Path
    dist: Path | None


def public_build_diagnostic(message, *, draft, toolchain):
    """Compiler locations remain useful without exporting private host paths."""
    text = str(message)
    for path, label in sorted(
        [
            (draft, "<interface>"),
            (toolchain.dependency_root, "<compiler>"),
            (toolchain.client_root, "<process-client>"),
            (toolchain.kit_root, "<ui-kit>"),
        ],
        key=lambda item: len(str(item[0])),
        reverse=True,
    ):
        for spelling in (str(path), path.as_posix(), str(path).replace("/", "\\")):
            text = text.replace(spelling, label)
    return redact_text(text)[:2000]


async def build_interface(
    *,
    source: SourceEnvelope,
    manifest: InterfaceManifest,
    process: ProcessRef,
    catalog: list[dict],
    toolchain: BuildToolchain,
    builds_root: Path,
) -> BuiltInterface:
    """Own one fresh private draft and bounded fixed Node child; no generated scripts."""
    validate_manifest_bindings(manifest, process, catalog)
    description = toolchain.describe()
    # Revalidate mutable mappings before using bytes and freeze this invocation.
    source = SourceEnvelope.model_validate_json(canonical_json(source))
    manifest = InterfaceManifest.model_validate_json(canonical_json(manifest))
    source_digest, manifest_digest = (
        canonical_digest(source),
        canonical_digest(manifest),
    )
    build_id = "build-" + uuid4().hex
    builds_root = builds_root.resolve()
    builds_root.mkdir(parents=True, exist_ok=True)
    draft = builds_root / build_id
    draft.mkdir()
    for name, text in source.files.items():
        (draft / name).write_text(text, encoding="utf-8")
    for name, asset in source.assets.items():
        path = draft / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(asset.decoded())
    resource = files("workspace_service.process_interfaces.resources").joinpath(
        "fixed-builder.mjs"
    )
    script = draft / "wright-fixed-builder.mjs"
    script.write_bytes(resource.read_bytes())
    request = draft / "wright-build-request.json"
    request.write_text(
        json.dumps(
            {
                "root": str(draft),
                "dependencyRoot": str(toolchain.dependency_root.resolve()),
                "clientRoot": str(toolchain.client_root.resolve()),
                "kitRoot": str(toolchain.kit_root.resolve()),
                "assets": list(source.assets),
                "packages": description["packages"],
            }
        ),
        encoding="utf-8",
    )
    diagnostics = []
    process_child = None
    try:
        process_child = await asyncio.create_subprocess_exec(
            str(toolchain.node),
            str(script),
            str(request),
            cwd=str(draft),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        async with asyncio.timeout(toolchain.timeout_seconds):
            raw = await process_child.stdout.read(262145)
            if len(raw) > 262144:
                raise ValueError("Compiler diagnostics exceed the fixed bound")
            await process_child.wait()
        result = json.loads(raw)
        if process_child.returncode or not result.get("ok"):
            for message in result.get("diagnostics", [])[:64]:
                diagnostics.append(
                    Reason(
                        code="UI_BUILD_FAILED",
                        message=public_build_diagnostic(
                            message, draft=draft, toolchain=toolchain
                        )
                        or "Compiler rejected the interface.",
                        correction="Correct the bounded compiler diagnostic and rebuild through Wright.",
                    )
                )
            if not diagnostics:
                raise ValueError("Compiler did not return a successful report")
    except asyncio.CancelledError:
        if process_child is not None and process_child.returncode is None:
            process_child.kill()
            await process_child.wait()
        raise
    except (TimeoutError, OSError, ValueError) as exc:
        diagnostics = [
            Reason(
                code="UI_BUILD_FAILED",
                message="Wright could not complete the fixed interface build.",
                correction="Check the local compiler or correct the returned build diagnostic, then retry.",
            )
        ]
        (draft / "compiler-diagnostic.json").write_text(
            json.dumps(safe_diagnostic({"diagnostic": str(exc)})), encoding="utf-8"
        )
    finally:
        if process_child is not None and process_child.returncode is None:
            process_child.kill()
            await process_child.wait()
    bundled_bytes, inventory = 0, {}
    dist = draft / "dist"
    if not diagnostics:
        for path in sorted(dist.rglob("*")):
            if path.is_symlink():
                diagnostics.append(
                    Reason(
                        code="UI_BUILD_FAILED",
                        message="Compiler output contains an unsupported link.",
                        correction="Build only regular static files.",
                    )
                )
                break
            if path.is_file():
                raw = path.read_bytes()
                bundled_bytes += len(raw)
                inventory[path.relative_to(dist).as_posix()] = hashlib.sha256(
                    raw
                ).hexdigest()
        if not inventory or bundled_bytes > toolchain.maximum_bundle_bytes:
            diagnostics.append(
                Reason(
                    code="UI_BUILD_FAILED",
                    message="The static bundle is empty or exceeds the configured size limit.",
                    correction="Reduce interface assets or fix the failed compilation.",
                )
            )
    report = BuildReport(
        build_id=build_id,
        source_digest=source_digest,
        manifest_digest=manifest_digest,
        toolchain_digest=canonical_digest(description),
        bundle_digest=canonical_digest(inventory) if not diagnostics else None,
        state="failed" if diagnostics else "built",
        created_at=datetime.now(timezone.utc).isoformat(),
        diagnostics=tuple(diagnostics),
        bundled_bytes=min(bundled_bytes, 31_457_280),
    )
    (draft / "build-report.json").write_text(canonical_json(report), encoding="utf-8")
    (draft / "binding.json").write_text(canonical_json(manifest), encoding="utf-8")
    (draft / "source.json").write_text(canonical_json(source), encoding="utf-8")
    return BuiltInterface(report, draft, None if diagnostics else dist)
