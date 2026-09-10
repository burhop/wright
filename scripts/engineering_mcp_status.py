"""Build the independent engineering MCP curation status from catalog evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Iterable

from tool_registry.catalog_curation import build_report
from tool_registry.catalog_models import CatalogEntry
from tool_registry.curation_models import qualification_configuration


IMPLEMENTATION_MODES = {
    "autodesk-product-help-mcp": "native",
    "oasis-open-fem-agent": "native",
    "autocad-mcp-u-c4n": "fallback",
    "rhino-mcp-easehee": "fallback",
    "blender-mcp": "wrapper",
    "brep-mcp": "wrapper",
    "freecad-mcp-nekanat": "wrapper",
    "kicad-mcp-blwfish": "wrapper",
    "openscad-mcp": "wrapper",
    "rosbag-mcp-pypi": "wrapper",
    "kernelcad-mcp": "native",
}

CHAIN_NAMES = {
    "mechanical-cad-fea-review": "Mechanical CAD → structural screening → DXF review",
    "electronics-ecad-enclosure-thermal-test": "KiCad PCB → enclosure → thermal → ROS evidence",
    "field-evidence-controlled-revision": "Field evidence → drawing revision",
}
CHAIN_CALL_COUNTS = {
    "mechanical-cad-fea-review": 8,
    "electronics-ecad-enclosure-thermal-test": 15,
    "field-evidence-controlled-revision": 7,
}

PORTFOLIO_CATEGORIES = (
    {
        "id": "qualified",
        "label": "Available (Qualified)",
        "definition": "Current evidence proves the scoped protocol, backend, and Wright gateway workflow.",
        "action": "Keep the evidence fresh and monitor upstream changes.",
    },
    {
        "id": "preflight_passed",
        "label": "Preview (Preflight passed)",
        "definition": "The implementation passed useful checks, but its complete Wright workflow is not currently qualified.",
        "action": "Complete the backend and gateway scenario.",
    },
    {
        "id": "authentication_required",
        "label": "Connect and verify",
        "definition": "The current endpoint or server reached an authentication challenge. Post-login tools, backend behavior, and Wright gateway operation remain unproven.",
        "action": "Authenticate a dedicated test account, then require tools/list, one safe read, and a Wright gateway call before release.",
    },
    {
        "id": "environment_required",
        "label": "Lab integrations",
        "definition": "Qualification needs host software, a license, hardware, or a dedicated lab environment beyond ordinary user authentication.",
        "action": "Run the scenario in a dedicated environment with the recorded prerequisites.",
    },
    {
        "id": "untested",
        "label": "Untested",
        "definition": "No useful current execution evidence establishes how far the implementation works.",
        "action": "Run the clean-environment preflight.",
    },
    {
        "id": "failed",
        "label": "Needs repair (Failed)",
        "definition": "Current evidence shows an implementation, packaging, startup, or protocol failure.",
        "action": "Fix, replace, or exclude the implementation.",
    },
    {
        "id": "excluded_archive",
        "label": "Closed / Excluded archive",
        "definition": "Retired, superseded, unavailable, duplicate, or not actually an MCP server.",
        "action": "Hide from discovery and retain the decision record to prevent repeated review.",
    },
)
PORTFOLIO_CATEGORY_IDS = tuple(item["id"] for item in PORTFOLIO_CATEGORIES)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _protocol_family(entry: CatalogEntry) -> str:
    if entry.hardware_standard == "mhs_preview":
        return "mhs"
    if entry.hardware_standard == "hardware_mcp":
        return "hardware_mcp"
    return "webmcp" if entry.transport == "webmcp" else "mcp"


def _current_qualification(entry: CatalogEntry, as_of: date):
    configuration = qualification_configuration(entry)
    matches = [
        value
        for value in entry.curation.qualifications
        if value.verified_at <= as_of < value.expires_at
        and value.configuration_sha256 == configuration
    ]
    return max(matches, key=lambda value: value.verified_at, default=None)


def _qualification_status(entry: CatalogEntry, as_of: date) -> str:
    if _current_qualification(entry, as_of):
        return "passing"
    if entry.curation.qualifications:
        return "stale"
    if (
        entry.validation_result.status == "failed"
        or entry.installability_tier == "non_working"
    ):
        return "failing"
    if (
        entry.validation_result.status in {"blocked", "dependency_missing", "skipped"}
        or entry.installability_tier == "blocked"
    ):
        return "blocked"
    return "untested"


def _portfolio_category(
    entry: CatalogEntry, *, disposition: str, qualification_status: str
) -> tuple[str, str]:
    """Classify portfolio action separately from the raw validation result."""
    if disposition == "removed":
        return "excluded_archive", entry.curation.reason
    if qualification_status == "passing":
        return (
            "qualified",
            "Current scoped evidence passed protocol, backend, gateway, and outcome checks.",
        )
    if entry.validation_result.status == "failed":
        return "failed", "Current validation failed; see the latest technical result."
    if entry.validation_result.status == "passed" or qualification_status == "stale":
        return (
            "preflight_passed",
            "Useful validation passed, but a complete current scoped Wright qualification is still required.",
        )
    if entry.validation_result.status in {"dependency_missing", "blocked"}:
        if entry.credentials_required and not entry.host_software_required:
            return (
                "authentication_required",
                "The current server reached an authentication boundary and requires "
                + ", ".join(sorted(set(entry.credentials_required)))
                + ".",
            )
        requirements = sorted(
            set(entry.host_software_required + entry.credentials_required)
        )
        suffix = f" Primary requirements: {', '.join(requirements)}." if requirements else ""
        return (
            "environment_required",
            "Qualification reached an external environment or access boundary."
            + suffix,
        )
    return "untested", "No useful current execution evidence has been recorded."


def _dependency_groups(entry: CatalogEntry) -> list[str]:
    groups = []
    if entry.dependencies.system:
        groups.append("system")
    if entry.dependencies.python:
        groups.append("python")
    if entry.dependencies.node:
        groups.append("node")
    if entry.host_software_required:
        groups.append("host_application")
    if entry.credentials_required:
        groups.append("credentials")
    return groups or ["none"]


def _platform_groups(entry: CatalogEntry) -> list[str]:
    qualified = sorted({item.platform for item in entry.curation.qualifications})
    if qualified:
        return qualified
    declared = sorted(
        key
        for key, value in entry.platform_support.items()
        if value.status in {"yes", "likely", "host-dependent"}
    )
    return declared or ["unknown"]


def _breakdown(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    rows: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        raw = record[field]
        values: Iterable[str] = raw if isinstance(raw, list) else [raw]
        for value in values:
            rows[value][record["portfolio_category"]] += 1
            rows[value]["total"] += 1
    return [
        {
            "key": key,
            **{
                state: counts[state]
                for state in (*PORTFOLIO_CATEGORY_IDS, "total")
            },
        }
        for key, counts in sorted(rows.items())
    ]


def _count_hash_checks(value: Any) -> int:
    if isinstance(value, dict):
        return sum(
            (1 if key == "sha256" or key.endswith("_sha256") else 0)
            + _count_hash_checks(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return sum(_count_hash_checks(item) for item in value)
    return 0


def _change_kind(old: dict[str, Any] | None, new: dict[str, Any] | None) -> str:
    if old is None:
        return "new"
    if new is None:
        return "record_removed"
    old_disposition = old["curation"]["effective_disposition"]
    new_disposition = new["curation"]["effective_disposition"]
    if old_disposition != new_disposition:
        if new_disposition == "curated":
            return "promotion"
        if old_disposition == "curated":
            return "demotion"
        if new_disposition == "removed":
            return "removal"
        return "disposition_changed"
    old_validation = old.get("validation_status")
    new_validation = new.get("validation_status")
    if old_validation != new_validation:
        if new_validation == "passed":
            return "recovery"
        if new_validation in {"failed", "dependency_missing", "blocked"}:
            return "failure"
        return "validation_changed"
    if old["curation"].get("qualifications") != new["curation"].get("qualifications"):
        return "qualification_refreshed"
    return "metadata_changed"


def _changes(
    previous: dict[str, Any] | None, current: dict[str, Any]
) -> dict[str, Any]:
    tracked = (
        "promotion",
        "demotion",
        "new",
        "failure",
        "recovery",
        "removal",
        "record_removed",
        "disposition_changed",
        "validation_changed",
        "qualification_refreshed",
        "metadata_changed",
    )
    if previous is None:
        return {
            "previous_as_of": None,
            "count": 0,
            "summary": {key: 0 for key in tracked},
            "items": [],
        }
    before = {row["id"]: row for row in previous.get("records", [])}
    after = {row["id"]: row for row in current["records"]}
    items = []
    for identity in sorted(before.keys() | after.keys()):
        old = before.get(identity)
        new = after.get(identity)
        if old == new:
            continue
        item = {"server_id": identity, "change": _change_kind(old, new)}
        if old is not None and new is not None:
            old_disposition = old["curation"]["effective_disposition"]
            new_disposition = new["curation"]["effective_disposition"]
            if old_disposition != new_disposition:
                item.update(before=old_disposition, after=new_disposition)
            elif old.get("validation_status") != new.get("validation_status"):
                item.update(
                    before=old.get("validation_status"),
                    after=new.get("validation_status"),
                )
        items.append(item)
    counts = Counter(item["change"] for item in items)
    return {
        "previous_as_of": previous.get("as_of"),
        "count": len(items),
        "summary": {key: counts[key] for key in tracked},
        "items": items,
    }


def _review_evidence(
    entry: CatalogEntry, repository_root: Path, embedded: dict[str, dict[str, str]]
) -> tuple[str | None, str | None, str | None]:
    """Return a review-evidence link, digest, and candidate revision."""
    sources = sorted(
        entry.source_records,
        key=lambda value: (value.observed_at or "", value.kind == "evidence"),
        reverse=True,
    )
    for source in sources:
        if source.kind != "evidence":
            continue
        if source.url.startswith(("https://", "http://")):
            return source.url, None, None
        path = (repository_root / source.url).resolve()
        if repository_root.resolve() not in path.parents or path.suffix != ".json":
            continue
        if not path.is_file() or path.stat().st_size > 512 * 1024:
            continue
        raw = path.read_bytes()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        evidence_id = f"server-review-{entry.id}"
        digest = sha256_bytes(raw)
        embedded[evidence_id] = {
            "sha256": digest,
            "media_type": "application/json",
            "content": raw.decode("utf-8"),
        }
        revision = payload.get("source_revision")
        return (
            f"evidence/{evidence_id}.json",
            digest,
            revision if isinstance(revision, str) else None,
        )
    source = next((value.url for value in sources if value.primary), entry.source_url)
    return source, None, None


def build_engineering_status(
    entries: list[CatalogEntry],
    *,
    as_of: date,
    repository_root: Path,
    process_chains_path: Path,
    previous_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_report(entries, as_of=as_of)
    report_records = {row["id"]: row for row in report["records"]}
    embedded: dict[str, dict[str, str]] = {}
    records = []
    for entry in sorted(entries, key=lambda item: item.id):
        qualification = _current_qualification(entry, as_of)
        status = _qualification_status(entry, as_of)
        evidence_href = None
        evidence_age_days = None
        source_revision = None
        scope = (
            entry.capability_summary[0]
            if entry.capability_summary
            else entry.description
        )
        last_qualified_at = None
        expires_at = None
        evidence_sha256 = None
        if qualification is None:
            evidence_href, evidence_sha256, source_revision = _review_evidence(
                entry, repository_root, embedded
            )
        if qualification is not None:
            evidence_file = repository_root / qualification.evidence_path
            raw = evidence_file.read_bytes()
            if sha256_bytes(raw) != qualification.evidence_sha256:
                raise ValueError(f"Evidence digest mismatch for {entry.id}")
            try:
                evidence_object = json.loads(raw)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Qualification evidence is not JSON for {entry.id}"
                ) from error
            if (
                evidence_object.get("status") != "passed"
                or evidence_object.get("server_id") != entry.id
            ):
                raise ValueError(f"Qualification evidence does not prove {entry.id}")
            evidence_id = f"server-{entry.id}"
            embedded[evidence_id] = {
                "sha256": qualification.evidence_sha256,
                "media_type": "application/json",
                "content": raw.decode("utf-8"),
            }
            evidence_href = f"evidence/{evidence_id}.json"
            evidence_sha256 = qualification.evidence_sha256
            evidence_age_days = (as_of - qualification.verified_at).days
            source_revision = qualification.source_revision
            scope = qualification.workflow
            last_qualified_at = qualification.verified_at.isoformat()
            expires_at = qualification.expires_at.isoformat()
        latest = entry.validation_result
        disposition = report_records[entry.id]["curation"]["effective_disposition"]
        portfolio_category, portfolio_category_reason = _portfolio_category(
            entry,
            disposition=disposition,
            qualification_status=status,
        )
        records.append(
            {
                "server_id": entry.id,
                "name": entry.name,
                "vendor": entry.vendor,
                "source_url": entry.source_url,
                "source_revision": source_revision,
                "scope": scope,
                "implementation_mode": IMPLEMENTATION_MODES.get(entry.id, "unknown"),
                "disposition": disposition,
                "curation_reason": entry.curation.reason,
                "integration_kind": entry.integration_kind,
                "qualification_status": status,
                "portfolio_category": portfolio_category,
                "portfolio_category_reason": portfolio_category_reason,
                "release_eligible": portfolio_category == "qualified",
                "protocol_family": _protocol_family(entry),
                "transport": entry.transport,
                "disciplines": sorted(entry.domains),
                "engineering_stages": list(entry.engineering_stages),
                "platforms": _platform_groups(entry),
                "dependency_groups": _dependency_groups(entry),
                "prerequisites": sorted(
                    set(
                        entry.host_software_required
                        + entry.dependencies.system
                        + entry.dependencies.python
                        + entry.dependencies.node
                    )
                ),
                "credentials": list(entry.credentials_required),
                "last_qualified_at": last_qualified_at,
                "expires_at": expires_at,
                "evidence_age_days": evidence_age_days,
                "latest_result": latest.status,
                "latest_message": latest.message,
                "failure": latest.message if status in {"failing", "blocked"} else None,
                "evidence_href": evidence_href,
                "evidence_sha256": evidence_sha256,
                "owner": entry.curation.owner,
                "review_due": entry.curation.review_due.isoformat()
                if entry.curation.review_due
                else None,
                "next_action": entry.curation.next_action,
            }
        )

    chain_raw = process_chains_path.read_bytes()
    chain_evidence = json.loads(chain_raw)
    if (
        chain_evidence.get("status") != "passed"
        or chain_evidence.get("cleanup") != "passed"
    ):
        raise ValueError("Process-chain evidence is not passing and clean")
    if sum(CHAIN_CALL_COUNTS.values()) != len(chain_evidence.get("calls", [])):
        raise ValueError(
            "Process-chain call count changed without a status recipe update"
        )
    chain_evidence_id = "process-chains"
    embedded[chain_evidence_id] = {
        "sha256": sha256_bytes(chain_raw),
        "media_type": "application/json",
        "content": chain_raw.decode("utf-8"),
    }
    chains = []
    for chain in chain_evidence.get("chains", []):
        handoffs = chain.get("handoffs", [])
        chains.append(
            {
                "chain_id": chain["id"],
                "name": CHAIN_NAMES[chain["id"]],
                "status": chain["status"],
                "call_count": CHAIN_CALL_COUNTS[chain["id"]],
                "handoffs_accepted": sum(
                    item.get("status") == "accepted" for item in handoffs
                ),
                "corrupt_handoffs_rejected": sum(
                    bool(item.get("corrupted_manifest_rejected")) for item in handoffs
                ),
                "artifact_checks": _count_hash_checks(chain),
                "cleanup": chain_evidence["cleanup"],
                "last_run": chain_evidence["observed_at"],
                "evidence_href": f"evidence/{chain_evidence_id}.json",
                "scenario_kind": "synthetic_qualification_fixture",
            }
        )

    status_counts = Counter(record["qualification_status"] for record in records)
    category_counts = Counter(record["portfolio_category"] for record in records)
    curated = report["counts"]["curated"]
    protocol_rows = []
    for family, label in (
        ("mcp", "MCP"),
        ("webmcp", "WebMCP"),
        ("hardware_mcp", "Hardware MCP"),
        ("mhs", "Anthropic Model Hardware Standard"),
    ):
        matching = [record for record in records if record["protocol_family"] == family]
        protocol_rows.append(
            {
                "protocol": family,
                "label": label,
                "known": len(matching),
                "curated": sum(
                    record["disposition"] == "curated" for record in matching
                ),
                "passing": sum(
                    record["qualification_status"] == "passing" for record in matching
                ),
                "physical_operation_qualified": (
                    False if family in {"hardware_mcp", "mhs"} else None
                ),
                "status": (
                    "research_preview"
                    if family == "mhs"
                    else "qualification_required"
                    if family == "hardware_mcp"
                    else "implemented"
                ),
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "as_of": as_of.isoformat(),
        "catalog_sha256": report["catalog_sha256"],
        "policy_version": report["policy_version"],
        "counts": report["counts"],
        "qualification_counts": {
            key: status_counts[key]
            for key in ("passing", "failing", "blocked", "stale", "untested")
        },
        "category_counts": {
            key: category_counts[key] for key in PORTFOLIO_CATEGORY_IDS
        },
        "category_key": list(PORTFOLIO_CATEGORIES),
        "product_release": {
            "categories": ["qualified"],
            "count": sum(record["release_eligible"] for record in records),
            "server_ids": [
                record["server_id"] for record in records if record["release_eligible"]
            ],
        },
        "tested_as_far_as_possible": {
            "categories": [
                "qualified",
                "preflight_passed",
                "authentication_required",
            ],
            "count": sum(
                record["portfolio_category"]
                in {"qualified", "preflight_passed", "authentication_required"}
                for record in records
            ),
            "server_ids": [
                record["server_id"]
                for record in records
                if record["portfolio_category"]
                in {"qualified", "preflight_passed", "authentication_required"}
            ],
        },
        "product_groups": [
            {
                "id": group_id,
                "label": label,
                "count": sum(record["portfolio_category"] == category for record in records),
                "server_ids": [
                    record["server_id"]
                    for record in records
                    if record["portfolio_category"] == category
                ],
            }
            for group_id, label, category in (
                ("available", "Available", "qualified"),
                ("preview", "Preview", "preflight_passed"),
                ("connect_and_verify", "Connect and verify", "authentication_required"),
                ("lab_integrations", "Lab integrations", "environment_required"),
            )
        ],
        "target": {
            "minimum": 10,
            "ideal": 15,
            "maximum": 20,
            "curated": curated,
            "minimum_met": curated >= 10,
            "ideal_met": curated >= 15,
        },
        "breakdowns": {
            "disciplines": _breakdown(records, "disciplines"),
            "protocols": _breakdown(records, "protocol_family"),
            "transports": _breakdown(records, "transport"),
            "platforms": _breakdown(records, "platforms"),
            "dependencies": _breakdown(records, "dependency_groups"),
        },
        "protocol_status": protocol_rows,
        "changes": _changes(previous_report, report),
        "chains": chains,
        "records": records,
        "limitations": report["limitations"]
        + [
            "Passing means the recorded scoped qualification remains current; it does not extend to untested tools, platforms, or host modes.",
            "The three chains are deterministic Tier 1 integration scenarios, not physical product validation or production process proof.",
        ],
        "evidence_payloads": embedded,
    }
