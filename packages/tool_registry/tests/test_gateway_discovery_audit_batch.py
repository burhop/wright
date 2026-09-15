"""Discovery retains exact policy audits before any tool can dispatch."""

import pytest

from packages.tool_registry.tests.test_gateway_service import service


class BatchAudit:
    def __init__(self):
        self.batches = []
        self.single_events = []

    def record_many(self, events):
        self.batches.append([dict(event) for event in events])

    def record(self, event):
        self.single_events.append(dict(event))


def test_batch_and_legacy_audits_keep_identical_scoped_decisions():
    legacy, _, audit = service()
    batched, _, _ = service()
    batch = batched.audit = BatchAudit()
    for session in ("s1", "s2"):
        assert batched.list_tools(session) == legacy.list_tools(session)
    flattened = [event for group in batch.batches for event in group]

    def clean(events):
        return [
            {key: value for key, value in event.items() if key != "correlation_id"}
            for event in events
        ]

    assert clean(flattened) == clean(audit.events)
    assert len(batch.batches) == 2
    assert batch.single_events == []
    assert {event["workspace_id"] for event in flattened} == {"w1", "w2"}


def test_failed_discovery_still_records_already_observed_decisions():
    instance, _, _ = service()
    batch = instance.audit = BatchAudit()
    original = instance.catalog.tools

    def broken(server_id):
        yield from original(server_id)
        raise RuntimeError("Catalog unavailable after its first tool")

    instance.catalog.tools = broken
    with pytest.raises(RuntimeError, match="Catalog unavailable"):
        instance.list_tools("s1")
    assert len(batch.batches) == 1
    assert batch.batches[0][0]["target_name"] == "run"
    assert batch.batches[0][0]["operation"] == "tool.list"


@pytest.mark.asyncio
async def test_failed_audit_batch_prevents_native_dispatch():
    instance, lifecycle, _ = service()

    class FailedAudit(BatchAudit):
        def record_many(self, events):
            raise OSError("Audit persistence unavailable")

    audit = instance.audit = FailedAudit()
    with pytest.raises(OSError, match="Audit persistence"):
        await instance.call_tool("s1", "request", "cad__run", {"shape": "cube"})
    assert lifecycle.calls == []
    assert audit.single_events == []
