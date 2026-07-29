from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from tests.native_runtime.adapter_support import load_adapter_commands


COMMANDS = load_adapter_commands()


def test_commands_register_real_wright_dispatcher() -> None:
    context = MagicMock()
    COMMANDS.register_commands(context)
    context.register_command.assert_called_once()
    kwargs = context.register_command.call_args.kwargs
    assert kwargs["name"] == "wright"
    assert asyncio.run(kwargs["handler"]("")) == COMMANDS.WRIGHT_HELP_TEXT


def test_commands_contain_no_repository_or_build_fallback() -> None:
    source = open(COMMANDS.__file__, encoding="utf-8").read().lower()
    for forbidden in ("detect_repo_dir", "npm run", "git clone", "docker compose"):
        assert forbidden not in source
