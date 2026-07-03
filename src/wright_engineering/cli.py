from __future__ import annotations

import argparse

from . import __version__


DOCKER_IMAGE = "burhop/wright"
GHCR_IMAGE = "ghcr.io/burhop/wright"
DOCS_URL = "https://burhop.github.io/wright/"
SUPPORT_EMAIL = "wright@makerengineer.com"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wright",
        description="Public-alpha helper for the Wright local-first engineering appliance.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"wright-engineering {__version__}",
    )
    subcommands = parser.add_subparsers(dest="command")
    subcommands.add_parser("doctor", help="Print alpha install guidance.")

    args = parser.parse_args(argv)
    if args.command in (None, "doctor"):
        print("Wright public alpha")
        print(f"Docker Hub image: {DOCKER_IMAGE}:<tag>")
        print(f"GHCR image: {GHCR_IMAGE}:<tag>")
        print(f"Docs: {DOCS_URL}")
        print(f"Support: {SUPPORT_EMAIL}")
        print("Docker remains the primary end-user install path for alpha.")
        return 0
    parser.error(f"unknown command: {args.command}")
    return 2
