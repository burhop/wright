"""Desktop MCP entrypoint within the installed Wright runtime environment."""

import argparse
from pathlib import Path

from .mcp_bridge import WrightDesktopClient, server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args(argv)
    client = WrightDesktopClient.from_runtime(
        api_url=args.api_url,
        token_path=args.token_file,
    )
    server(
        client,
        native_editor=True,
        native_working_view=True,
        native_workspace_files=True,
    ).run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
