import asyncio
from types import SimpleNamespace

import httpx
import pytest

from agent_adapters import report_generation


def test_response_read_timeout_remains_distinct_from_model_configuration(monkeypatch):
    class TimedOutClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.ReadTimeout("private upstream diagnostic must not be exposed")

    monkeypatch.setattr(
        report_generation,
        "resolve_hermes_api_settings",
        lambda: SimpleNamespace(base_url="http://127.0.0.1:8642", api_key=""),
    )
    monkeypatch.setattr(report_generation.httpx, "AsyncClient", TimedOutClient)
    with pytest.raises(TimeoutError, match="within 180 seconds") as error:
        asyncio.run(
            report_generation.generate_workflow_response("Create a report", "markdown")
        )
    assert "private" not in str(error.value)
    assert "Model Setup" not in str(error.value)
