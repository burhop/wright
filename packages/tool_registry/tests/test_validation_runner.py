from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import sqlite3

import pytest
from data_vault import upgrade_database
from tool_registry.compatibility import observe_machine
from tool_registry.validation_evidence import latest_capability_validation_evidence
from tool_registry.validation_runner import run_capability_validation

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


class FixtureClient:
    def __init__(self, *, fail_at: str | None = None):
        self.calls: list[str] = []
        self.fail_at = fail_at

    async def initialize(self):
        self.calls.append("initialize")
        if self.fail_at == "initialize":
            raise RuntimeError("credential value must not survive")
        return {"serverInfo": {"name": "fixture", "version": "1.2.0"}}

    async def initialized(self):
        self.calls.append("notifications/initialized")

    async def list_tools(self):
        self.calls.append("tools/list")
        if self.fail_at == "tools/list":
            raise RuntimeError("list failed")
        return [
            {
                "name": "health",
                "inputSchema": {"type": "object"},
                "description": "not retained",
            }
        ]

    async def call_tool(self, name, arguments):
        self.calls.append(f"tools/call:{name}")
        return {"ok": True, "sensitive_result": "not retained"}


def _observation():
    return observe_machine(
        clock=lambda: NOW,
        which=lambda _name: None,
        version_reader=lambda _path: None,
        system_reader=lambda: "Linux",
        version_system_reader=lambda: "test",
        architecture_reader=lambda: "x86_64",
        network_policy="offline",
    )


def _seed_references(database, observation) -> None:
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO catalog_snapshots (
                snapshot_id, channel, sequence, schema_version, issued_at,
                expires_at, payload_sha256, payload_json, verification_state
            ) VALUES ('snapshot-one', 'test', 1, 1, 1, 2, ?, ?, 'active')""",
            (DIGEST_A, json.dumps({"servers": []})),
        )
        connection.execute(
            """INSERT INTO machine_compatibility_observations (
                observation_id, observed_at, expires_at, platform_key, os_name,
                os_version, architecture, distribution_mode, observation_json, digest
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                observation.observation_id,
                int(observation.observed_at.timestamp()),
                int(observation.expires_at.timestamp()),
                observation.platform_key,
                observation.os_name,
                observation.os_version,
                observation.architecture,
                observation.distribution_mode,
                observation.model_dump_json(),
                observation.digest,
            ),
        )
        connection.commit()


async def _run(database, client, **changes):
    observation = _observation()
    values = {
        "capability_id": "fixture-capability",
        "server_id": "fixture-server",
        "snapshot_id": "snapshot-one",
        "capability_document": {"id": "fixture-capability", "transport": "stdio"},
        "observation": observation,
        "server_revision": "1.2.0",
        "credential_status": {"TOKEN": True},
        "client": client,
        "read_only_probe": {
            "name": "health",
            "arguments": {"detail": False},
            "limitation": "Fixture health only",
        },
        "clock": lambda: NOW,
        "trace_id": "trace-runner",
    }
    values.update(changes)
    with sqlite3.connect(database) as connection:
        present = connection.execute(
            "SELECT COUNT(*) FROM catalog_snapshots WHERE snapshot_id='snapshot-one'"
        ).fetchone()[0]
    if not present:
        _seed_references(database, observation)
    return await run_capability_validation(database, **values)


@pytest.mark.asyncio
async def test_runner_initializes_discovers_and_hashes_read_only_probe(
    tmp_path,
) -> None:
    database = tmp_path / "runner.db"
    upgrade_database(database)
    client = FixtureClient()

    evidence = await _run(database, client)

    assert evidence.state == "passed"
    assert client.calls == [
        "initialize",
        "notifications/initialized",
        "tools/list",
        "tools/call:health",
    ]
    assert evidence.tool_count == 1
    assert len(evidence.schema_digest or "") == 64
    assert evidence.read_only_probe["limitation"] == "Fixture health only"
    serialized = evidence.model_dump_json()
    assert "not retained" not in serialized
    assert "sensitive_result" not in serialized
    assert latest_capability_validation_evidence(database, "fixture-server") == evidence


@pytest.mark.asyncio
async def test_runner_records_failure_unavailable_and_cancellation(tmp_path) -> None:
    database = tmp_path / "runner-failures.db"
    upgrade_database(database)

    failed = await _run(database, FixtureClient(fail_at="tools/list"))
    assert failed.state == "failed"
    assert failed.protocol_steps["tools/list"] == "failed"
    assert "list failed" not in failed.model_dump_json()

    blocked = await _run(
        database,
        None,
        server_id="missing-client",
        capability_id="missing-client",
    )
    assert blocked.state == "blocked"
    assert blocked.missing_requirements == ["configured_validation_client"]

    checks = iter([False, True])
    cancelled = await _run(
        database,
        FixtureClient(),
        server_id="cancelled-client",
        capability_id="cancelled-client",
        cancel_requested=lambda: next(checks, True),
    )
    assert cancelled.state == "blocked"
    assert "validation_cancelled" in cancelled.reason_codes
    assert "failed" not in cancelled.protocol_steps.values()


@pytest.mark.asyncio
async def test_local_validation_accepts_finite_numeric_schema_and_probe_evidence(
    tmp_path,
):
    database = tmp_path / "numeric-schemas.db"
    upgrade_database(database)

    class NumericClient(FixtureClient):
        default = 0.5

        async def list_tools(self):
            self.calls.append("tools/list")
            return [
                {
                    "name": "measure",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "tolerance": {
                                "type": "number",
                                "default": self.default,
                                "minimum": 0.001,
                            }
                        },
                    },
                }
            ]

        async def call_tool(self, name, arguments):
            self.calls.append("tools/call:" + name)
            return {"measurement": 3.125, "private": "not retained"}

    client = NumericClient()
    first = await _run(
        database,
        client,
        read_only_probe={
            "name": "measure",
            "arguments": {"tolerance": 0.5},
            "limitation": "Synthetic numeric measurement only",
        },
    )
    assert first.state == "passed" and first.tool_count == 1
    assert first.protocol_steps["tools/list"] == "passed"
    assert len(first.schema_digest) == 64
    assert first.read_only_probe["status"] == "passed"
    assert set(first.read_only_probe) == {
        "name",
        "argument_digest",
        "result_digest",
        "status",
        "limitation",
    }
    assert "not retained" not in first.model_dump_json()
    client.default = 0.75
    changed = await _run(
        database, client, read_only_probe=None, clock=lambda: NOW + timedelta(seconds=1)
    )
    assert changed.state == "passed" and changed.schema_digest != first.schema_digest
    assert latest_capability_validation_evidence(database, "fixture-server") == changed


@pytest.mark.asyncio
@pytest.mark.parametrize("nonfinite", [float("nan"), float("inf"), -float("inf")])
async def test_local_validation_rejects_nonfinite_tool_schema(tmp_path, nonfinite):
    database = tmp_path / "invalid-numeric-schema.db"
    upgrade_database(database)

    class InvalidSchemaClient(FixtureClient):
        async def list_tools(self):
            return [
                {
                    "name": "measure",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "value": {
                                "type": "number",
                                "default": nonfinite,
                            }
                        },
                    },
                }
            ]

    client = InvalidSchemaClient()
    evidence = await _run(database, client)
    assert evidence.state == "failed" and evidence.schema_digest is None
    assert evidence.protocol_steps["tools/list"] == "failed"
    assert not any(call.startswith("tools/call") for call in client.calls)


@pytest.mark.asyncio
async def test_local_validation_preserves_strict_catalog_metadata_hashing(tmp_path):
    from tool_registry.catalog_signing import CatalogVerificationError

    database = tmp_path / "strict-catalog.db"
    upgrade_database(database)
    client = FixtureClient()
    with pytest.raises(CatalogVerificationError, match="Floating-point"):
        await _run(
            database, client, capability_document={"id": "fixture", "revision": 0.5}
        )
    assert client.calls == []
