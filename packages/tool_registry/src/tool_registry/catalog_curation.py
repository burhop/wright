"""Repeatable, read-only curation reports and bounded public-source intake.

Discovery is untrusted evidence. This module never installs, launches, enables,
or edits a catalog and does not accept arbitrary network destinations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import httpx

from .canonical_catalog import load_canonical_entries
from .catalog_models import CatalogEntry
from .curation_models import (
    ENGINEERING_STAGES,
    evaluate_curation,
    qualification_configuration,
)

POLICY_VERSION = "2026-09-08.1"
MAX_SOURCE_BYTES = 2 * 1024 * 1024


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def build_report(
    entries: list[CatalogEntry], *, as_of: date, platform: str | None = None
) -> dict:
    records = []
    for entry in sorted(entries, key=lambda item: item.id):
        decision = evaluate_curation(
            entry.curation,
            today=as_of,
            platform=platform,
            configuration_sha256=qualification_configuration(entry),
        )
        concerns = []
        if (
            entry.installability_tier == "tested"
            and entry.validation_result.status != "passed"
        ):
            concerns.append("tested_label_without_passing_validation")
        if not entry.engineering_stages:
            concerns.append("lifecycle_scope_missing")
        if not entry.curation.reviewed_at:
            concerns.append("desk_review_missing")
        if decision.review_overdue:
            concerns.append("review_overdue")
        records.append(
            {
                "id": entry.id,
                "name": entry.name,
                "source_url": entry.source_url,
                "integration_kind": entry.integration_kind,
                "hardware_standard": entry.hardware_standard,
                "engineering_stages": entry.engineering_stages,
                "validation_status": entry.validation_result.status,
                "curation": decision.model_dump(mode="json"),
                "concerns": concerns,
            }
        )
    lists = {
        disposition: [
            row["id"]
            for row in records
            if row["curation"]["effective_disposition"] == disposition
        ]
        for disposition in ("curated", "follow_up", "removed")
    }
    coverage = [
        {
            "stage": stage,
            "label": label,
            **{
                disposition: [
                    row["id"]
                    for row in records
                    if stage in row["engineering_stages"]
                    and row["id"] in lists[disposition]
                ]
                for disposition in ("curated", "follow_up")
            },
        }
        for stage, label in ENGINEERING_STAGES.items()
    ]
    material = [
        entry.model_dump(mode="json")
        for entry in sorted(entries, key=lambda item: item.id)
    ]
    return {
        "policy_version": POLICY_VERSION,
        "as_of": as_of.isoformat(),
        "platform": platform,
        "catalog_sha256": _digest(material),
        "counts": {key: len(value) for key, value in lists.items()},
        "lists": lists,
        "coverage": coverage,
        "records": records,
        "limitations": [
            "This report evaluates recorded evidence; it does not run live qualification.",
            "Candidate stage assignments describe intended coverage, not proven end-to-end handoffs.",
            "MHS is a research preview; Wright has not qualified physical device operation.",
        ],
    }


def report_delta(previous: dict, current: dict) -> list[dict]:
    before = {row["id"]: row for row in previous.get("records", [])}
    after = {row["id"]: row for row in current["records"]}
    return [
        {
            "id": identity,
            "change": "added"
            if identity not in before
            else "removed"
            if identity not in after
            else "changed",
        }
        for identity in sorted(before.keys() | after.keys())
        if before.get(identity) != after.get(identity)
    ]


def _cell(value: Any) -> str:
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("\r", " ")
        .replace("<", "&lt;")
    )


def report_markdown(report: dict) -> str:
    lines = [
        "# Wright MCP curation report",
        "",
        f"As of {report['as_of']} · policy {report['policy_version']}",
        "",
        f"Catalog digest: `{report['catalog_sha256']}`",
        "",
        "Recorded decisions only; no MCP was installed or tested by this report.",
        "",
    ]
    for disposition, label in (
        ("curated", "Curated"),
        ("follow_up", "Follow up"),
        ("removed", "Remove from discovery"),
    ):
        lines.extend(
            [
                f"## {label} ({report['counts'][disposition]})",
                "",
                "| Identity | Reason | Next action | Review due |",
                "|---|---|---|---|",
            ]
        )
        for row in report["records"]:
            decision = row["curation"]
            if decision["effective_disposition"] == disposition:
                lines.append(
                    "| "
                    + " | ".join(
                        _cell(value)
                        for value in (
                            row["id"],
                            decision["reason"],
                            decision["next_action"],
                            decision["review_due"] or "Unscheduled",
                        )
                    )
                    + " |"
                )
        lines.append("")
    lines.extend(
        [
            "## Lifecycle coverage",
            "",
            "| Stage | Curated | Follow up |",
            "|---|---:|---:|",
        ]
    )
    for row in report["coverage"]:
        lines.append(
            f"| {row['label']} | {len(row['curated'])} | {len(row['follow_up'])} |"
        )
    lines.extend(["", *report["limitations"], ""])
    return "\n".join(lines)


def _public_json(client: httpx.Client, url: str, *, params: dict | None = None) -> dict:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"api.github.com", "registry.modelcontextprotocol.io"}
        or parsed.port not in {None, 443}
        or parsed.username
        or parsed.password
    ):
        raise ValueError("Unapproved discovery origin")
    with client.stream("GET", url, params=params, follow_redirects=False) as response:
        response.raise_for_status()
        chunks = bytearray()
        for chunk in response.iter_bytes():
            chunks.extend(chunk)
            if len(chunks) > MAX_SOURCE_BYTES:
                raise ValueError("Discovery response exceeds size limit")
    result = json.loads(chunks)
    if not isinstance(result, dict):
        raise ValueError("Expected a source metadata object")
    return result


def github_repository(url: str | None) -> str | None:
    parsed = urlsplit(url or "")
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username
        or parsed.password
    ):
        return None
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if len(parts) != 2 or parts[0] in {"topics", "orgs", "search"}:
        return None
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in parts):
        return None
    return "/".join(parts)


def research_github(entries: list[CatalogEntry], client: httpx.Client) -> list[dict]:
    repositories: dict[str, list[str]] = {}
    for entry in entries:
        repository = github_repository(entry.repository_url or entry.source_url)
        if repository:
            repositories.setdefault(repository, []).append(entry.id)

    def fetch(item: tuple[str, list[str]]) -> dict:
        repository, identities = item
        result = {
            "repository": repository,
            "catalog_ids": sorted(identities),
            "source_url": f"https://api.github.com/repos/{repository}",
        }
        try:
            source = _public_json(client, result["source_url"])
            if not isinstance(source.get("full_name"), str) or not isinstance(
                source.get("archived"), bool
            ):
                raise ValueError("Incomplete repository identity")
            license_data = source.get("license")
            if license_data is not None and not isinstance(license_data, dict):
                raise ValueError("Malformed repository license")
            result.update(
                {
                    "status": "observed",
                    "canonical_repository": source.get("full_name"),
                    "archived": source.get("archived"),
                    "disabled": source.get("disabled"),
                    "pushed_at": source.get("pushed_at"),
                    "updated_at": source.get("updated_at"),
                    "stars": source.get("stargazers_count"),
                    "forks": source.get("forks_count"),
                    "open_issues": source.get("open_issues_count"),
                    "default_branch": source.get("default_branch"),
                    "license_spdx": (license_data or {}).get("spdx_id"),
                }
            )
        except httpx.HTTPStatusError as error:
            result.update(status="unavailable", http_status=error.response.status_code)
        except (httpx.HTTPError, ValueError, TypeError):
            result.update(status="unavailable", reason="source_fetch_failed")
        return result

    with ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(fetch, sorted(repositories.items())))


def discover_registry(
    client: httpx.Client,
    *,
    search: str,
    entries: list[CatalogEntry],
    cursor: str | None = None,
) -> dict:
    """Fetch one bounded page; the caller explicitly advances the returned cursor."""
    if not search.strip() or len(search) > 200 or (cursor and len(cursor) > 2000):
        raise ValueError("A bounded nonempty search is required")
    params = {"search": search, "limit": "100"}
    if cursor:
        params["cursor"] = cursor
    source = _public_json(
        client, "https://registry.modelcontextprotocol.io/v0.1/servers", params=params
    )
    known: dict[str, list[str]] = {}
    for entry in entries:
        repository = github_repository(entry.repository_url or entry.source_url)
        if repository:
            known.setdefault(repository.lower(), []).append(entry.id)
    candidates = []
    seen = set()
    servers = source.get("servers")
    if not isinstance(servers, list):
        raise ValueError("Registry servers must be an array")
    for item in servers[:100]:
        if not isinstance(item, dict):
            continue
        server = item.get("server", {})
        if not isinstance(server, dict):
            continue
        identity = server.get("name")
        version = server.get("version")
        if (
            not isinstance(identity, str)
            or not isinstance(version, str)
            or (identity, version) in seen
        ):
            continue
        seen.add((identity, version))
        repository = server.get("repository")
        repository_url = repository.get("url") if isinstance(repository, dict) else None
        repository_key = (
            github_repository(repository_url)
            if isinstance(repository_url, str)
            else None
        )
        related = sorted(known.get((repository_key or "").lower(), []))
        candidates.append(
            {
                "registry_name": identity[:250],
                "version": version[:150],
                "repository_url": repository_url[:2000]
                if isinstance(repository_url, str)
                else None,
                "related_catalog_ids": related,
                "proposed_disposition": "follow_up",
                "reason": "Untrusted lead. A shared repository does not prove server identity; preserve all existing review decisions until a reviewer matches the implementation.",
            }
        )
    metadata = source.get("metadata")
    next_cursor = metadata.get("nextCursor") if isinstance(metadata, dict) else None
    if next_cursor is not None and (
        not isinstance(next_cursor, str) or len(next_cursor) > 2000
    ):
        raise ValueError("Invalid registry cursor")
    return {"search": search, "next_cursor": next_cursor, "candidates": candidates}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["report", "research", "discover"])
    parser.add_argument(
        "--as-of", type=date.fromisoformat, default=datetime.now(UTC).date()
    )
    parser.add_argument(
        "--platform",
        choices=[
            "windows_11_x64",
            "linux_x64",
            "linux_arm64",
            "macos_x64",
            "macos_arm64",
        ],
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--search")
    parser.add_argument("--cursor")
    args = parser.parse_args(argv)
    entries = load_canonical_entries()
    if args.command == "report":
        report = build_report(entries, as_of=args.as_of, platform=args.platform)
        if args.previous:
            report["delta"] = report_delta(
                json.loads(args.previous.read_text("utf-8")), report
            )
    else:
        with httpx.Client(
            timeout=15,
            trust_env=False,
            follow_redirects=False,
            headers={
                "User-Agent": "Wright-catalog-research",
                "Accept": "application/json",
            },
        ) as client:
            if args.command == "research":
                report = {
                    "observed_at": datetime.now(UTC).isoformat(),
                    "sources": research_github(entries, client),
                    "limitation": "Stars and repository activity do not establish MCP adoption or Wright qualification.",
                }
            else:
                if not args.search:
                    parser.error("discover requires --search")
                try:
                    report = discover_registry(
                        client, search=args.search, entries=entries, cursor=args.cursor
                    )
                except (httpx.HTTPError, ValueError, TypeError):
                    report = {
                        "search": args.search,
                        "complete": False,
                        "error": "source_fetch_failed",
                        "candidates": [],
                    }
                report["observed_at"] = datetime.now(UTC).isoformat()
    if args.command == "research":
        report["complete"] = all(
            source["status"] == "observed" for source in report["sources"]
        )
    else:
        report.setdefault("complete", True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # A failed observation is an attempt, never a replacement for last-good evidence.
    filename = args.command if report["complete"] else f"{args.command}.attempt"
    destination = args.output_dir / f"{filename}.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(destination)
    if args.command == "report":
        (args.output_dir / "report.md").write_text(
            report_markdown(report), encoding="utf-8", newline="\n"
        )
    print(
        json.dumps(
            {
                "command": args.command,
                "output_dir": str(args.output_dir),
                "counts": report.get("counts"),
            }
        )
    )
    return 0 if report["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
