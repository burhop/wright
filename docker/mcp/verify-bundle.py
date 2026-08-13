#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"}
SUPPORTED_PROFILES = {
    "permissive",
    "gpl-2.0-runtime-redistribution",
    "lgpl-runtime-redistribution",
    "internal-reviewed-source",
    "remote-only",
    "blocked",
}
GPL_2_LICENSES = {"GPL-2.0-only", "GPL-2.0-or-later"}
LGPL_LICENSES = {
    "LGPL-2.0-only",
    "LGPL-2.0-or-later",
    "LGPL-2.1-only",
    "LGPL-2.1-or-later",
    "LGPL-3.0-only",
    "LGPL-3.0-or-later",
}
FLOATING_GIT_REFS = {
    "main",
    "master",
    "dev",
    "develop",
    "latest",
    "head",
    "trunk",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


class BundleValidationError(ValueError):
    """Raised when an MCP bundle cannot be safely redistributed."""


def _ensure_local_tool_registry_import_path() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    for package_src in sorted((repository_root / "packages").glob("*/src")):
        sys.path.insert(0, str(package_src))


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BundleValidationError(f"bundle file not found: {path}") from exc
    if not isinstance(payload, dict):
        raise BundleValidationError("bundle manifest must be a mapping")
    return payload


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BundleValidationError(f"{field} must be a mapping")
    return value


def _require_text(mapping: dict[str, Any], field: str, context: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise BundleValidationError(f"{context}.{field} is required")
    return value.strip()


def _require_list(mapping: dict[str, Any], field: str, context: str) -> list[Any]:
    value = mapping.get(field)
    if not isinstance(value, list) or not value:
        raise BundleValidationError(f"{context}.{field} is required")
    return value


def _is_exact_git_ref(ref: str) -> bool:
    lowered = ref.lower()
    if lowered in FLOATING_GIT_REFS or lowered.startswith(("refs/heads/", "origin/")):
        return False
    return bool(
        SHA_RE.fullmatch(ref)
        or lowered.startswith("refs/tags/")
        or lowered.startswith("v")
    )


def _is_exact_package_version(version: str) -> bool:
    if any(token in version for token in ("*", "^", "~", ">", "<", "=")):
        return False
    return bool(SEMVER_RE.fullmatch(version))


def _validate_source(item_id: str, source: dict[str, Any], field: str) -> None:
    source_type = _require_text(source, "type", f"{item_id}.{field}")
    if source_type == "git":
        ref = _require_text(source, "ref", f"{item_id}.{field}")
        _require_text(source, "url", f"{item_id}.{field}")
        if not _is_exact_git_ref(ref):
            raise BundleValidationError(
                f"{item_id}.{field} uses floating git ref: {ref}"
            )
    elif source_type == "configured_git":
        _require_text(source, "url_env", f"{item_id}.{field}")
        _require_text(source, "ref_env", f"{item_id}.{field}")
        _require_text(source, "source_reference", f"{item_id}.{field}")
        default_ref = source.get("default_ref")
        if (
            isinstance(default_ref, str)
            and default_ref.strip()
            and not _is_exact_git_ref(default_ref.strip())
        ):
            raise BundleValidationError(
                f"{item_id}.{field} uses floating default git ref: {default_ref}"
            )
    elif source_type == "package":
        version = _require_text(source, "version", f"{item_id}.{field}")
        if not _is_exact_package_version(version):
            raise BundleValidationError(
                f"{item_id}.{field} uses non-exact package version: {version}"
            )
    elif source_type == "apt":
        _require_list(source, "packages", f"{item_id}.{field}")
    elif source_type in {"github_release", "sourceforge_release"}:
        _require_text(source, "version", f"{item_id}.{field}")
        _require_text(source, "url", f"{item_id}.{field}")
    elif source_type in {"external", "unresolved"}:
        return
    else:
        raise BundleValidationError(
            f"{item_id}.{field} has unsupported source type: {source_type}"
        )


def _license(source: dict[str, Any]) -> str | None:
    value = source.get("license")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _validate_permissive(item_id: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    for source in sources:
        license_name = _license(source)
        if license_name and license_name not in PERMISSIVE_LICENSES:
            raise BundleValidationError(
                f"{item_id} has non-permissive license {license_name} without a compliance profile"
            )
    return {"profile_id": "permissive", "required_artifacts": ["license", "notice"]}


def _validate_copyleft_runtime(
    item_id: str,
    profile: dict[str, Any],
    sources: list[dict[str, Any]],
    profile_id: str,
    allowed_licenses: set[str],
) -> dict[str, Any]:
    licenses = {
        license_name for source in sources if (license_name := _license(source))
    }
    if not licenses.intersection(allowed_licenses):
        allowed = ", ".join(sorted(allowed_licenses))
        raise BundleValidationError(
            f"{item_id} {profile_id} requires one of: {allowed}"
        )
    if profile.get("runtime_use_only") is not True:
        raise BundleValidationError(
            f"{item_id}.compliance_profile.runtime_use_only must be true"
        )
    if profile.get("modification_status") != "unmodified":
        raise BundleValidationError(
            f"{item_id}.compliance_profile.modification_status must be unmodified"
        )
    for field in ("source_access", "license_text", "no_warranty_notice"):
        _require_text(profile, field, f"{item_id}.compliance_profile")
    return {
        "profile_id": profile_id,
        "spdx": sorted(licenses),
        "modification_status": profile["modification_status"],
        "source_access": profile["source_access"],
        "required_artifacts": [
            "license_text",
            "copyright_notices",
            "no_warranty_notice",
            "source_access",
        ],
    }


def _validate_internal_reviewed(
    item_id: str, profile: dict[str, Any], sources: list[dict[str, Any]]
) -> dict[str, Any]:
    if not any(source.get("type") == "configured_git" for source in sources):
        raise BundleValidationError(
            f"{item_id} internal-reviewed-source requires configured_git"
        )
    for field in ("source_access", "redistribution_scope"):
        _require_text(profile, field, f"{item_id}.compliance_profile")
    return {
        "profile_id": "internal-reviewed-source",
        "source_access": profile["source_access"],
        "redistribution_scope": profile["redistribution_scope"],
        "required_artifacts": ["source_access", "license_or_internal_approval"],
    }


def _validate_compliance(
    item_id: str,
    profile: dict[str, Any],
    sources: list[dict[str, Any]],
    *,
    local_enabled: bool,
) -> dict[str, Any]:
    profile_id = _require_text(profile, "id", f"{item_id}.compliance_profile")
    if profile_id not in SUPPORTED_PROFILES:
        raise BundleValidationError(
            f"{item_id} has unsupported compliance profile: {profile_id}"
        )
    if not local_enabled:
        if profile_id == "blocked":
            return {"profile_id": "blocked"}
        if profile_id == "remote-only":
            return {"profile_id": "remote-only"}
        raise BundleValidationError(
            f"{item_id} non-local entries cannot use profile {profile_id}"
        )
    if profile_id == "permissive":
        return _validate_permissive(item_id, sources)
    if profile_id == "gpl-2.0-runtime-redistribution":
        return _validate_copyleft_runtime(
            item_id, profile, sources, profile_id, GPL_2_LICENSES
        )
    if profile_id == "lgpl-runtime-redistribution":
        return _validate_copyleft_runtime(
            item_id, profile, sources, profile_id, LGPL_LICENSES
        )
    if profile_id == "internal-reviewed-source":
        return _validate_internal_reviewed(item_id, profile, sources)
    raise BundleValidationError(
        f"{item_id} local_enabled cannot use profile {profile_id}"
    )


def _availability_status(item_id: str, item: dict[str, Any]) -> tuple[str, bool]:
    availability = _require_text(item, "availability", item_id)
    if availability == "local_enabled":
        return "accepted", True
    if availability == "blocked_pending_review":
        return "blocked", False
    if availability in {"remote_only", "windows_only"}:
        return "remote_only", False
    raise BundleValidationError(f"{item_id}.availability is invalid: {availability}")


def _validate_install(item_id: str, item: dict[str, Any], local_enabled: bool) -> None:
    install = item.get("install")
    if local_enabled:
        _require_mapping(install, f"{item_id}.install")
    elif install is not None and not isinstance(install, dict):
        raise BundleValidationError(f"{item_id}.install must be a mapping")


def _validate_application(item: dict[str, Any]) -> dict[str, Any]:
    app_id = _require_text(item, "id", "application")
    status, local_enabled = _availability_status(app_id, item)
    source = _require_mapping(item.get("source"), f"{app_id}.source")
    _validate_source(app_id, source, "source")
    profile = _require_mapping(
        item.get("compliance_profile"), f"{app_id}.compliance_profile"
    )
    compliance = _validate_compliance(
        app_id, profile, [source], local_enabled=local_enabled
    )
    _validate_install(app_id, item, local_enabled)
    if local_enabled and "health_probe" not in item:
        raise BundleValidationError(
            f"{app_id}.health_probe is required for local_enabled"
        )
    return {
        "id": app_id,
        "display_name": item.get("display_name", app_id),
        "availability": item.get("availability"),
        "status": status,
        "compliance": compliance,
    }


def _validate_server(item: dict[str, Any], application_ids: set[str]) -> dict[str, Any]:
    server_id = _require_text(item, "id", "mcp_server")
    status, local_enabled = _availability_status(server_id, item)
    application_id = item.get("application_id")
    if application_id is not None:
        if not isinstance(application_id, str) or not application_id.strip():
            raise BundleValidationError(
                f"{server_id}.application_id must be null or a non-empty string"
            )
        if application_id not in application_ids:
            raise BundleValidationError(
                f"{server_id}.application_id references unknown application: {application_id}"
            )
    source = _require_mapping(item.get("mcp_source"), f"{server_id}.mcp_source")
    _validate_source(server_id, source, "mcp_source")
    profile = _require_mapping(
        item.get("compliance_profile"), f"{server_id}.compliance_profile"
    )
    compliance = _validate_compliance(
        server_id, profile, [source], local_enabled=local_enabled
    )
    _validate_install(server_id, item, local_enabled)
    if local_enabled:
        if "launch" not in item:
            raise BundleValidationError(
                f"{server_id}.launch is required for local_enabled"
            )
        if "health_probe" not in item:
            raise BundleValidationError(
                f"{server_id}.health_probe is required for local_enabled"
            )
    return {
        "id": server_id,
        "display_name": item.get("display_name", server_id),
        "application_id": application_id,
        "availability": item.get("availability"),
        "status": status,
        "compliance": compliance,
    }


def _ensure_unique(items: list[dict[str, Any]], kind: str) -> None:
    seen: set[str] = set()
    for item in items:
        item_id = _require_text(item, "id", kind)
        if item_id in seen:
            raise BundleValidationError(f"duplicate {kind} id: {item_id}")
        seen.add(item_id)


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    if bundle.get("schema_version") != 1:
        raise BundleValidationError("schema_version must be 1")
    bundle_id = _require_text(bundle, "bundle_id", "bundle")
    applications = bundle.get("applications")
    servers = bundle.get("mcp_servers")
    if not isinstance(applications, list) or not applications:
        raise BundleValidationError("applications must be a non-empty list")
    if not isinstance(servers, list) or not servers:
        raise BundleValidationError("mcp_servers must be a non-empty list")
    app_items = [_require_mapping(item, "application") for item in applications]
    server_items = [_require_mapping(item, "mcp_server") for item in servers]
    _ensure_unique(app_items, "application")
    _ensure_unique(server_items, "mcp_server")
    validated_apps = [_validate_application(item) for item in app_items]
    application_ids = {item["id"] for item in validated_apps}
    validated_servers = [
        _validate_server(item, application_ids) for item in server_items
    ]
    if bundle.get("target_platform"):
        try:
            from tool_registry.catalog_bundle import (
                validate_bundle_catalog_compatibility,
            )
        except ImportError as exc:
            _ensure_local_tool_registry_import_path()
            try:
                from tool_registry.catalog_bundle import (
                    validate_bundle_catalog_compatibility,
                )
            except ImportError:
                raise BundleValidationError(
                    "target_platform requires the Wright tool_registry package"
                ) from exc
        try:
            validate_bundle_catalog_compatibility(bundle)
        except ValueError as exc:
            raise BundleValidationError(str(exc)) from exc
    return {
        "ok": True,
        "bundle_id": bundle_id,
        "applications": validated_apps,
        "mcp_servers": validated_servers,
    }


def validate_bundle_file(path: str | Path) -> dict[str, Any]:
    return validate_bundle(_load_yaml(Path(path)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Wright MCP bundle manifest"
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_bundle_file(args.bundle)
    except BundleValidationError as exc:
        print(f"mcp bundle invalid: {exc}", file=sys.stderr)
        return 2
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
