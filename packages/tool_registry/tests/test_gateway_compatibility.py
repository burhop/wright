from __future__ import annotations

import sys

import pytest

from tool_registry import gateway


def test_legacy_launcher_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("WRIGHT_LEGACY_GATEWAY", raising=False)
    with pytest.raises(SystemExit, match="disabled"):
        gateway.main()


def test_legacy_launcher_delegates_without_handwritten_protocol(monkeypatch) -> None:
    captured = {}
    monkeypatch.setenv("WRIGHT_LEGACY_GATEWAY", "1")
    monkeypatch.setattr(sys, "argv", ["gateway", "--session-id", "s1"])

    def execv(executable, arguments):
        captured["call"] = (executable, arguments)
        raise RuntimeError("exec intercepted")

    monkeypatch.setattr(gateway.os, "execv", execv)
    with pytest.raises(RuntimeError, match="intercepted"):
        gateway.main()
    assert captured["call"] == (
        sys.executable,
        [sys.executable, "-m", "api.gateway_stdio", "--session-id", "s1"],
    )
