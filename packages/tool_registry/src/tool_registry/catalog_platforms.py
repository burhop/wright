from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from .catalog_models import CatalogEntry


SelectionMode = Literal["strict", "candidate", "host"]


@dataclass(frozen=True)
class CatalogPlatformProfile:
    id: str
    label: str
    platform_key: str
    docker_platform: str
    bundle_file: str
    aliases: tuple[str, ...] = ()


PLATFORM_PROFILES: dict[str, CatalogPlatformProfile] = {
    "linux-amd64": CatalogPlatformProfile(
        id="linux-amd64",
        label="Linux x86_64 PC",
        platform_key="linux_x64",
        docker_platform="linux/amd64",
        bundle_file="mcp-bundle.yaml",
        aliases=("pc-linux-amd64", "linux-x64", "linux_x64"),
    ),
    "gb10-linux-arm64": CatalogPlatformProfile(
        id="gb10-linux-arm64",
        label="NVIDIA GB10 Linux ARM64",
        platform_key="linux_arm64",
        docker_platform="linux/arm64",
        bundle_file="mcp-bundle.linux-arm64.yaml",
        aliases=("gb10", "linux-arm64", "linux_aarch64", "linux_arm64"),
    ),
    "windows-amd64": CatalogPlatformProfile(
        id="windows-amd64",
        label="Windows x86_64 PC",
        platform_key="windows_11_x64",
        docker_platform="windows/amd64",
        bundle_file="mcp-bundle.windows-amd64.yaml",
        aliases=("pc-windows-amd64", "windows-x64", "windows_11_x64"),
    ),
}

_PROFILE_ALIASES = {
    alias: profile_id
    for profile_id, profile in PLATFORM_PROFILES.items()
    for alias in (profile_id, *profile.aliases)
}


def resolve_platform_profile(target: str) -> CatalogPlatformProfile:
    try:
        return PLATFORM_PROFILES[_PROFILE_ALIASES[target]]
    except KeyError as exc:
        choices = ", ".join(sorted(_PROFILE_ALIASES))
        raise ValueError(
            f"Unknown catalog platform target '{target}'. Expected one of: {choices}"
        ) from exc


def platform_selection_reason(
    entry: CatalogEntry,
    target: str | CatalogPlatformProfile,
    *,
    mode: SelectionMode = "strict",
    require_docker: bool = False,
) -> str | None:
    profile = resolve_platform_profile(target) if isinstance(target, str) else target
    support = entry.platform_support.get(profile.platform_key)
    if support is None:
        return f"missing {profile.platform_key} platform support"

    allowed_statuses = {"yes"}
    if mode in {"candidate", "host"}:
        allowed_statuses.add("likely")
    if mode == "host":
        allowed_statuses.add("host-dependent")

    if support.status not in allowed_statuses:
        return f"{profile.platform_key} support is {support.status}"
    if entry.installability_tier in {"blocked", "non_working"}:
        return f"installability is {entry.installability_tier}"
    if require_docker and entry.runtime_requirements.docker not in {"yes", "partial"}:
        return f"Docker support is {entry.runtime_requirements.docker}"
    return None


def is_platform_compatible(
    entry: CatalogEntry,
    target: str | CatalogPlatformProfile,
    *,
    mode: SelectionMode = "strict",
    require_docker: bool = False,
) -> bool:
    return (
        platform_selection_reason(
            entry, target, mode=mode, require_docker=require_docker
        )
        is None
    )


def filter_catalog_entries(
    entries: Iterable[CatalogEntry],
    target: str | CatalogPlatformProfile,
    *,
    mode: SelectionMode = "strict",
    require_docker: bool = False,
) -> list[CatalogEntry]:
    profile = resolve_platform_profile(target) if isinstance(target, str) else target
    return [
        entry
        for entry in entries
        if is_platform_compatible(
            entry, profile, mode=mode, require_docker=require_docker
        )
    ]
