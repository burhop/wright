from __future__ import annotations

import json
from datetime import UTC, datetime
from time import perf_counter

from tool_registry.capability_views import (
    CapabilityFilters,
    build_capability_views,
    paginate_capabilities,
)
from tool_registry.catalog_models import CatalogEntry
from tool_registry.compatibility import observe_machine
from tool_registry.config_import import preview_configuration


def _observation():
    return observe_machine(
        clock=lambda: datetime(2026, 8, 13, tzinfo=UTC),
        which=lambda name: None,
        version_reader=lambda path: None,
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test",
        architecture_reader=lambda: "x86_64",
        network_policy="unknown",
    )


def _entries(count: int) -> list[CatalogEntry]:
    return [
        CatalogEntry.model_validate(
            {
                "id": f"fixture-capability-{index:04d}",
                "name": f"Fixture Engineering Capability {index:04d}",
                "vendor": "Wright fixture",
                "description": f"Inspect bracket family {index % 25}",
                "domains": ["cad" if index % 2 == 0 else "fea"],
                "tags": ["bracket", f"family-{index % 25}"],
                "transport": "stdio",
                "command": ["fixture-mcp"],
                "locality": "local",
                "weight": "light",
                "platform_support": {"linux_x64": {"status": "yes", "tested": True}},
                "source_records": [
                    {"url": f"https://example.test/capabilities/{index}"}
                ],
            }
        )
        for index in range(count)
    ]


def test_search_and_filter_one_thousand_records_under_250_ms() -> None:
    entries = _entries(1_000)
    observation = _observation()

    started = perf_counter()
    views = build_capability_views(entries, [], observation)
    result = paginate_capabilities(
        entries,
        views,
        filters=CapabilityFilters(
            search="bracket family-7", domains=frozenset({"fea"})
        ),
        limit=200,
    )
    elapsed = perf_counter() - started

    assert result.total > 0
    assert all("fea" in capability.domains for capability in result.capabilities)
    assert elapsed < 0.250, f"1,000-record search took {elapsed:.3f}s"


def test_one_hundred_server_import_under_one_second() -> None:
    document = json.dumps(
        {
            "mcpServers": {
                f"Fixture {index:03d}": {
                    "command": "uvx",
                    "args": [f"fixture-{index:03d}"],
                    "env": {"API_TOKEN": "discard-me"},
                }
                for index in range(100)
            }
        }
    )

    started = perf_counter()
    preview = preview_configuration(document, now=datetime(2026, 8, 13, tzinfo=UTC))
    elapsed = perf_counter() - started

    assert len(preview["drafts"]) == 100
    assert preview["source_discarded"] is True
    assert "discard-me" not in json.dumps(preview)
    assert elapsed < 1.0, f"100-server import took {elapsed:.3f}s"
