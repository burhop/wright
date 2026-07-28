#!/usr/bin/env python3
"""Activate one immutable Wright version in a protected Hermes package channel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", choices=("test", "stable"), required=True)
    parser.add_argument(
        "--distribution", choices=("wright-engineering",), required=True
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    endpoint = os.environ.get("HERMES_PACKAGE_CHANNEL_URL", "").strip()
    token = os.environ.get("HERMES_PACKAGE_CHANNEL_TOKEN", "").strip()
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https" or not parsed.netloc:
        parser.error("HERMES_PACKAGE_CHANNEL_URL must be an HTTPS endpoint")
    if not token:
        parser.error("HERMES_PACKAGE_CHANNEL_TOKEN is required")
    wheel = args.wheel.resolve(strict=True)
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    request_payload = json.dumps(
        {
            "action": "activate",
            "channel": args.channel,
            "distribution": args.distribution,
            "version": args.version,
            "wheel_filename": wheel.name,
            "wheel_sha256": digest,
        }
    ).encode()
    request = urllib.request.Request(
        endpoint,
        data=request_payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(
            f"Hermes channel activation failed: {type(exc).__name__}", file=sys.stderr
        )
        return 1
    expected = {
        "channel": args.channel,
        "distribution": args.distribution,
        "version": args.version,
        "wheel_sha256": digest,
    }
    if not isinstance(result, dict) or any(
        result.get(k) != v for k, v in expected.items()
    ):
        print(
            "Hermes channel returned inconsistent activation evidence", file=sys.stderr
        )
        return 1
    verification_url = str(result.get("verification_url", ""))
    if urllib.parse.urlparse(verification_url).scheme != "https":
        print("Hermes channel omitted an HTTPS verification URL", file=sys.stderr)
        return 1
    evidence = {
        "schema_version": 1,
        **expected,
        "previous_version": result.get("previous_version"),
        "verification_url": verification_url,
        "activation_id": result.get("activation_id"),
        "status": "verified",
    }
    args.output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
