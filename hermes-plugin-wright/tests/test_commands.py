from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from hermes_plugin_wright.commands import WRIGHT_HELP_TEXT, register_commands


def test_legacy_commands_delegate_to_native_dispatcher() -> None:
    context = MagicMock()
    register_commands(context, object())
    context.register_command.assert_called_once()
    kwargs = context.register_command.call_args.kwargs
    assert kwargs["name"] == "wright"
    assert asyncio.run(kwargs["handler"]("")) == WRIGHT_HELP_TEXT


def test_legacy_commands_contain_no_repository_or_build_fallback() -> None:
    import hermes_plugin_wright.commands as commands

    source = open(commands.__file__, encoding="utf-8").read().lower()
    for forbidden in ("detect_repo_dir", "wright_repo_dir", "npm", "git", "docker"):
        assert forbidden not in source
