import logging

import pytest

from tool_registry.runners.stdio import StdioRunner


def test_stdio_runner_redacts_secret_environment_and_command():
    runner = StdioRunner(
        ["server", "--api-key", "command-secret"],
        env={"API_TOKEN": "environment-secret", "NORMAL": "visible"},
    )

    assert "environment-secret" in runner._secret_values()
    assert "visible" not in runner._secret_values()


@pytest.mark.asyncio
async def test_stdio_stderr_redacts_registered_secret(caplog):
    class Reader:
        def __init__(self):
            self.lines = [b"failure environment-secret\n", b""]

        async def readline(self):
            return self.lines.pop(0)

    class Process:
        stderr = Reader()

    runner = StdioRunner(["server"], env={"API_TOKEN": "environment-secret"})
    runner.process = Process()
    with caplog.at_level(logging.WARNING):
        await runner._read_stderr()

    assert "environment-secret" not in caplog.text
