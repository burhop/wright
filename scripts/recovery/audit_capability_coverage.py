#!/usr/bin/env python3
"""Build and verify the exhaustive source-to-capability map for feature 080."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / "specs" / "080-canonical-workflow-recovery"

RELEVANT_SPECS = (
    "054-rivet-workflow-integration",
    "055-rivet-compatibility-spike",
    "056-rivet-workspace-persistence",
    "057-rivet-headless-runner",
    "058-rivet-editor-host-adapters",
    "059-rivet-workspace-tab",
    "060-rivet-wright-nodes",
    "061-rivet-workflow-operations",
    "064-retained-editor-host",
    "066-rivet2-canvas",
    "067-rivet-hermes-ai",
    "068-capability-library",
    "069-rivet-mcp-gateway",
    "070-engineering-scenario-harness",
    "071-local-engineering-model-library",
    "072-chatter-rivet-scenarios",
    "073-program-hardening",
    "074-windows-mcp-qualification",
    "075-rivet-run-inspector",
    "078-process-definition-view",
    "079-visual-workflow-composition",
    "080-canonical-workflow-recovery",
)

CAPABILITIES = {
    "CAP-001": "Canonical definition and immutable revision authority",
    "CAP-002": "Stable tasks and optional group semantics",
    "CAP-003": "Typed ports and artifact contracts",
    "CAP-004": "Data, control, decision, gate, and feedback relationships",
    "CAP-005": "Exact governed implementation and MCP bindings",
    "CAP-006": "Reusable components and collapsed graphs",
    "CAP-007": "Separate stable layout metadata",
    "CAP-008": "Lossless Diagram, Source, and Side by side projections",
    "CAP-009": "Canvas readability and renderer-neutral projection",
    "CAP-010": "Direct manipulation, command batches, undo, and redo",
    "CAP-011": "Contextual engineering step library with bounded search",
    "CAP-012": "Progressive inspector and synchronized selection",
    "CAP-013": "Structured validation, diagnostics, and compatibility",
    "CAP-014": "Input attachment, preview, replacement, and provenance",
    "CAP-015": "Output inspection, lineage, open, download, and lifetime",
    "CAP-016": "Reviewed AI proposals and semantic diff",
    "CAP-017": "Immutable run, step, activity, and output records",
    "CAP-018": "Truthful run states, liveness, cancellation, and reconnect",
    "CAP-019": "Inputs, Outputs, Activity, and Diagnosis per executable block",
    "CAP-020": "Layered failure, needs-input, and bounded recovery",
    "CAP-021": "Truthful execution modes and current-run provenance",
    "CAP-022": "Human approval, authority, and safe external-action boundaries",
    "CAP-023": "Headless, CLI, UI, and host-adapter equivalence",
    "CAP-024": "Security, privacy, resource, and tool-isolation controls",
    "CAP-025": "Engineer usability, accessibility, and responsive operation",
    "CAP-026": "Large-graph performance and keyboard navigation",
    "CAP-027": "Generic domain/provider/tool-independent architecture",
    "CAP-028": "Persistence, migration, offline, rollback, and lifecycle support",
    "CAP-029": "Engineering-process outcomes across the customer story catalog",
    "CAP-030": "Independent engineering oracles and benchmark qualification",
    "CAP-031": "Program control, truthful dashboard, packaging, and release train",
    "CAP-032": "Model configuration, deterministic/AI execution, and exact identity",
    "CAP-033": "Preflight, argument/result maps, and semantic sufficiency",
}


@dataclass(frozen=True)
class Source:
    key: str
    source: str
    source_id: str
    title: str


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def table_sources(path: str, prefixes: tuple[str, ...]) -> list[Source]:
    result: list[Source] = []
    for line in read(path).splitlines():
        match = re.match(r"\| `((?:" + "|".join(prefixes) + r")-[0-9]{2})` \| ([^|]+)", line)
        if match:
            source_id, title = match.groups()
            result.append(Source(f"{path}:{source_id}", path, source_id, title.strip()))
    return result


def requirement_sources(source_name: str, text: str) -> list[Source]:
    result: list[Source] = []
    pattern = re.compile(
        r"^\s*-\s+(?:\*\*)?((?:FR|SC)-\d{3}|RQ-\d{2})(?:\*\*)?:\s*(.*?)"
        r"(?=^\s*-\s+(?:\*\*)?(?:(?:FR|SC)-\d{3}|RQ-\d{2})(?:\*\*)?:|^#{1,6}\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for requirement_id, title in pattern.findall(text):
        result.append(
            Source(
                f"{source_name}:{requirement_id}",
                source_name,
                requirement_id,
                " ".join(title.split()),
            )
        )
    if not result:
        scope = " ".join(line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#"))
        result.append(Source(f"{source_name}:SCOPE", source_name, "SCOPE", scope[:1000]))
    return result


def story_sources() -> list[Source]:
    path = "docs/programs/engineering-process-platform/customer-process-user-stories.md"
    text = read(path)
    matches = list(re.finditer(r"(?:^### |\| )(EPP-US-\d{3})(?: — | \| [^|]+ \| )([^\n|]+)", text, re.MULTILINE))
    by_id: dict[str, Source] = {}
    for match in matches:
        source_id, title = match.groups()
        by_id[source_id] = Source(f"{path}:{source_id}", path, source_id, title.strip())
    return [by_id[f"EPP-US-{number:03d}"] for number in range(1, 101)]


def lesson_sources() -> list[Source]:
    path = "docs/programs/engineering-process-platform/prototype-lesson-dispositions.json"
    data = json.loads(read(path))
    return [
        Source(f"{path}:{item['id']}", path, item["id"], item["program_rule"])
        for item in data["lessons"]
    ]


def decision_sources() -> list[Source]:
    path = "docs/programs/engineering-process-platform/decision-register.json"
    data = json.loads(read(path))
    decisions = data.get("records", data.get("decisions", data if isinstance(data, list) else []))
    result: list[Source] = []
    for item in decisions:
        source_id = str(item.get("id", ""))
        if source_id.startswith("DEC-P0-"):
            title = str(item.get("question") or item.get("title") or item.get("decision") or source_id)
            result.append(Source(f"{path}:{source_id}", path, source_id, title))
    return result


def choose_capability(source: Source) -> str:
    text = f"{source.source_id} {source.title}".lower()
    rules: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("CAP-031", ("dashboard", "release", "packag", "supply chain", "program control", "control plane", "roadmap", "commercial", "repository")),
        ("CAP-030", ("benchmark", "oracle", "holdout", "sampling", "qualif", "engineering correctness")),
        ("CAP-025", ("usability", "accessible", "accessibility", "keyboard", "zoom", "responsive", "engineer-readable", "comprehension", "fixed-height", "document scrolling", "1070 by 791")),
        ("CAP-026", ("large graph", "scale", "performance", "100-block", "200%", "26-step", "26 or more", "25 or fewer")),
        ("CAP-024", ("security", "privacy", "secret", "egress", "telemetry", "resource limit", "no-tools", "isolation")),
        ("CAP-022", ("approval", "approve", "authority", "revocation", "physical", "external action", "send", "start a job")),
        ("CAP-020", ("failure", "recovery", "needs-input", "blocked", "cleanup", "diagnos", "error")),
        ("CAP-018", ("liveness", "cancel", "reconnect", "deadline", "running", "queued", "first event", "terminal")),
        ("CAP-019", ("inputs, outputs", "inputs and outputs", "activity and diagnosis", "executable step exposes", "evidence")),
        ("CAP-021", ("fixture", "validate-only", "unconnected", "provenance", "current-run", "simulation")),
        ("CAP-017", ("run record", "run state", "run/step", "immutable run", "history", "execution state")),
        ("CAP-015", ("output", "download", "open", "lineage", "result", "lifetime", "produced")),
        ("CAP-014", ("attach", "input file", "reference image", "preview", "replacement", "artifact inventory")),
        ("CAP-016", ("ai proposal", "ai-assisted", "semantic diff", "llm", "model-generated", "assumption")),
        ("CAP-033", ("preflight", "argument", "result map", "mapping", "semantic sufficiency", "missing input")),
        ("CAP-005", ("binding", "mcp", "tool identity", "server", "schema", "provider", "capability selection")),
        ("CAP-032", ("model configuration", "deterministic", "ai-capable", "exact identity", "model lock")),
        ("CAP-023", ("headless", "cli", "host adapter", "desktop", "browser", "ui-independent")),
        ("CAP-028", ("persist", "migration", "offline", "rollback", "uninstall", "restart", "workspace", "cas", "storage")),
        ("CAP-013", ("validat", "diagnostic", "invalid", "compatib", "unknown version", "source span", "correction")),
        ("CAP-008", ("diagram", "source", "code", "text", "projection", "parse", "format", "language", "syntax", "engineering-script")),
        ("CAP-010", ("connect", "disconnect", "undo", "redo", "move", "delete", "command", "direct manipulation", "gesture")),
        ("CAP-011", ("palette", "catalog", "friendly", "searchable", "capability library", "step library", "engineering names")),
        ("CAP-012", ("inspector", "selection", "progressive disclosure", "properties")),
        ("CAP-009", ("canvas", "renderer", "react flow", "visual", "lane", "block")),
        ("CAP-007", ("layout", "position", "viewport")),
        ("CAP-006", ("component", "collapsed", "reuse", "subgraph")),
        ("CAP-003", ("port", "artifact contract", "typed artifact", "input", "output")),
        ("CAP-004", ("feedback", "decision", "gate", "relationship", "condition", "control flow", "revision loop")),
        ("CAP-002", ("phase", "block", "instruction", "configuration", "step")),
        ("CAP-001", ("canonical", "revision", "versioned definition", "semantic model", "authority", "identity")),
        ("CAP-027", ("generic", "domain", "vendor", "replaceable", "architecture")),
    )
    for capability_id, needles in rules:
        if any(needle in text for needle in needles):
            return capability_id
    return "CAP-029"


def disposition_for(source: Source, capability_id: str) -> tuple[str, str]:
    if source.source == "specs/080-canonical-workflow-recovery/spec.md" and source.source_id in {
        *(f"FR-{number:03d}" for number in range(43, 57)),
        *(f"SC-{number:03d}" for number in range(15, 21)),
    }:
        return "revise", "Current workspace-owned engineer-authoring correction; implemented and evidence-bound in T068-T078 rather than deferred."
    if source.source == "specs/080-canonical-workflow-recovery/spec.md" and source.source_id in {
        "FR-038",
        "FR-039",
        "SC-012",
        "SC-013",
        "SC-014",
    }:
        return "retain", "Current recovery completion/approval gate; it must be satisfied before the product-review stop, not deferred beyond it."
    if source.source_id.startswith(("BENCH-", "COMM-", "PROG-")):
        return "defer", "Preserved in the source map; outside the recovery concept and still independently gated."
    if source.source_id.startswith("EPP-US-"):
        return "retain", "Customer outcome remains addressable by the generic canonical model; no story-specific dispatch is added."
    if capability_id in {"CAP-026", "CAP-028", "CAP-030", "CAP-031"}:
        return "defer", "Preserved and dependency-ordered after product/visual parity approval."
    if capability_id in {"CAP-008", "CAP-009", "CAP-010", "CAP-012", "CAP-016", "CAP-020"}:
        return "revise", "The semantic need is retained while the prior product treatment is replaced by the recovery concept."
    return "retain", "Retained as a canonical-model, safety, or execution invariant."


def collect_sources() -> list[Source]:
    sources: list[Source] = []
    sources.extend(table_sources("docs/programs/engineering-process-platform/gates.md", ("PROD", "BENCH", "COMM", "PROG")))
    sources.extend(story_sources())
    sources.extend(lesson_sources())
    sources.extend(decision_sources())
    frozen_path = "specs/076-engineering-workflow-prototype/spec.md"
    sources.extend(requirement_sources(f"git:e7bb75c1:{frozen_path}", git_show("e7bb75c1", frozen_path)))
    for spec_dir in RELEVANT_SPECS:
        path = f"specs/{spec_dir}/spec.md"
        sources.extend(requirement_sources(path, read(path)))
    return sources


def main() -> int:
    sources = collect_sources()
    keys = [source.key for source in sources]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise SystemExit(f"duplicate source keys: {duplicates}")

    rows: list[dict[str, str]] = []
    for source in sources:
        capability_id = choose_capability(source)
        disposition, reason = disposition_for(source, capability_id)
        rows.append(
            {
                "source_key": source.key,
                "source": source.source,
                "source_id": source.source_id,
                "source_statement": source.title,
                "capability_id": capability_id,
                "capability": CAPABILITIES[capability_id],
                "disposition": disposition,
                "justification": reason,
            }
        )

    output = FEATURE / "capability-source-map.csv"
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    expected = {
        "product_gates": 11,
        "customer_stories": 100,
        "prototype_lessons": 25,
    }
    actual = {
        "product_gates": sum(row["source_id"].startswith("PROD-") for row in rows),
        "customer_stories": sum(row["source_id"].startswith("EPP-US-") for row in rows),
        "prototype_lessons": sum(row["source_id"].startswith("LL-") for row in rows),
    }
    if actual != expected:
        raise SystemExit(f"core source coverage mismatch: expected {expected}, got {actual}")

    represented = {row["capability_id"] for row in rows}
    unrepresented = sorted(set(CAPABILITIES) - represented)
    if unrepresented:
        raise SystemExit(f"capabilities without any source: {unrepresented}")

    counts_by_source: dict[str, int] = {}
    for row in rows:
        counts_by_source[row["source"]] = counts_by_source.get(row["source"], 0) + 1
    evidence = {
        "status": "PASS",
        "row_count": len(rows),
        "unique_source_key_count": len(set(keys)),
        "capability_count": len(CAPABILITIES),
        "capabilities_represented": len(represented),
        "core_expected": expected,
        "core_actual": actual,
        "counts_by_source": dict(sorted(counts_by_source.items())),
        "scanned_spec_directories": list(RELEVANT_SPECS),
        "unexplained_omissions": [],
    }
    (FEATURE / "evidence" / "capability-coverage.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Capability Coverage Audit",
        "",
        "**Result**: PASS",
        "",
        f"- {len(rows)} unique source requirements mapped.",
        f"- {len(CAPABILITIES)} of {len(CAPABILITIES)} canonical capabilities represented.",
        "- 11/11 product gates, 100/100 customer stories, and 25/25 prototype lessons present.",
        "- Every relevant legacy/frozen `FR-*` and `SC-*` is keyed by source path, so repeated local IDs cannot collide.",
        "- Unexplained omissions: 0.",
        "",
        "## Source counts",
        "",
        "| Source | Rows |",
        "|---|---:|",
    ]
    lines.extend(f"| `{source}` | {count} |" for source, count in sorted(counts_by_source.items()))
    lines.extend(
        [
            "",
            "The CSV is the exhaustive machine trace. `capability-inventory.md` is the review-oriented roll-up; neither changes the authority or passing status of its sources.",
            "",
        ]
    )
    (FEATURE / "evidence" / "capability-coverage.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
