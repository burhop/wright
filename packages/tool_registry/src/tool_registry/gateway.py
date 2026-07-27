"""One-release compatibility launcher for the official SDK STDIO gateway."""

from __future__ import annotations

import os
import sys


def main() -> None:
    if os.getenv("WRIGHT_LEGACY_GATEWAY") != "1":
        raise SystemExit(
            "Legacy tool_registry.gateway is disabled; use `python -m "
            "api.gateway_stdio --session-id ... --workspace-id ...`"
        )
    os.execv(
        sys.executable,
        [sys.executable, "-m", "api.gateway_stdio", *sys.argv[1:]],
    )


if __name__ == "__main__":
    main()
