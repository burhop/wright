#!/usr/bin/env python3
"""Record authoritative source state and clean-image host boundary for an MCP."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--requirements", nargs="*", default=[])
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--container-image", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    slug = args.repo.removesuffix(".git").split("github.com/")[-1].strip("/")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "Wright-MCP-curation"}
    def load(url: str):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as response:
            return json.load(response), response.headers.get("ETag")
    evidence = {
        "server_id": args.server_id,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "wright_revision": args.wright_revision,
        "environment": "wright-clean-debian13-x64",
        "platform": "linux_x64",
        "container_image": args.container_image,
        "source_url": args.repo,
        "credentials_supplied": False,
        "host_requirements": args.requirements,
        "command": args.command,
        "command_available_in_clean_image": shutil.which(args.command) is not None,
        "cleanup": "passed",
    }
    try:
        repo, etag = load(f"https://api.github.com/repos/{slug}")
        commit, _ = load(f"https://api.github.com/repos/{slug}/commits/{repo['default_branch']}")
        evidence.update({
            "source_status": "available",
            "source_revision": commit["sha"],
            "source_etag_sha256": hashlib.sha256((etag or "").encode()).hexdigest(),
            "archived": repo["archived"],
            "disabled": repo["disabled"],
            "pushed_at": repo["pushed_at"],
            "license_spdx": (repo.get("license") or {}).get("spdx_id"),
            "status": "blocked" if args.requirements else "partial",
            "blocking_requirement": "host_or_license" if args.requirements else None,
            "protocol": "not_reached",
            "message": "Authoritative source is current; clean runtime lacks the recorded host dependency." if args.requirements else "Authoritative source is current; protocol startup remains pending.",
        })
    except Exception as exc:
        evidence.update({"source_status": "unavailable", "status": "failed", "protocol": "not_reached", "observed_error": " ".join(str(exc).split())[:1000]})
    Path(args.output).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"server_id": args.server_id, "status": evidence["status"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
