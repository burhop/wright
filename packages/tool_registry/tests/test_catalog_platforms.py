from tool_registry.catalog_models import CatalogEntry
from tool_registry.catalog_platforms import (
    filter_catalog_entries,
    platform_selection_reason,
    resolve_platform_profile,
)


def _entry(entry_id: str, *, linux_arm64: str, docker: str = "yes") -> CatalogEntry:
    return CatalogEntry.model_validate(
        {
            "id": entry_id,
            "name": entry_id,
            "vendor": "Test",
            "description": entry_id,
            "domains": ["cad"],
            "transport": "stdio",
            "command": entry_id,
            "locality": "local",
            "weight": "light",
            "runtime_requirements": {"docker": docker},
            "platform_support": {
                "linux_arm64": {"status": linux_arm64, "tested": False}
            },
        }
    )


def test_resolve_platform_profile_accepts_gb10_alias() -> None:
    profile = resolve_platform_profile("gb10")

    assert profile.id == "gb10-linux-arm64"
    assert profile.platform_key == "linux_arm64"
    assert profile.docker_platform == "linux/arm64"


def test_platform_filter_distinguishes_strict_candidate_and_host_modes() -> None:
    entries = [
        _entry("strict", linux_arm64="yes"),
        _entry("candidate", linux_arm64="likely"),
        _entry("host", linux_arm64="host-dependent"),
        _entry("no-docker", linux_arm64="yes", docker="no"),
    ]

    assert [entry.id for entry in filter_catalog_entries(entries, "gb10")] == [
        "strict",
        "no-docker",
    ]
    assert [
        entry.id
        for entry in filter_catalog_entries(
            entries, "gb10", mode="candidate", require_docker=True
        )
    ] == ["strict", "candidate"]
    assert [
        entry.id
        for entry in filter_catalog_entries(
            entries, "gb10", mode="host", require_docker=True
        )
    ] == ["strict", "candidate", "host"]


def test_platform_selection_reason_names_rejection() -> None:
    entry = _entry("blocked", linux_arm64="unknown")

    assert platform_selection_reason(entry, "gb10") == "linux_arm64 support is unknown"
