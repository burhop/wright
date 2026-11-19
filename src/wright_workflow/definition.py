"""Read an exact source document or definition bundle without acquiring capabilities."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .bundle import BUNDLE_MAX_BYTES, BundleDependency, WorkflowBundle
from .contracts import canonical_digest
from .dependencies import check_dependencies, dependency_inventory
from .graph import WorkflowGraph, compile_graph
from .source import (
    WorkflowSourceExecutionError,
    parse_sections,
    validate_authoring_sections,
)


@dataclass(frozen=True)
class Definition:
    raw: bytes
    source: bytes
    source_digest: str
    graph: WorkflowGraph
    bundle: WorkflowBundle | None
    dependencies: tuple[BundleDependency, ...]

    @property
    def required_features(self):
        """Identify the selected handlers without connecting to a provider."""
        from .fixed import FIXED_SETTINGS

        result = {}
        for block_id, block in self.graph.blocks.items():
            fields = block["fields"]
            settings = fields.get("settings", {})
            if block["kind"] == "input":
                result[block_id] = ["input"]
                continue
            template = settings.get("authoring_template") or fields.get(
                "performed_by", "task"
            )
            result[block_id] = [template]
            if template == "mcp-tool":
                result[block_id].extend(sorted(set(settings) - FIXED_SETTINGS))
        return result


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def parse(document: str | bytes | Path) -> Definition:
    """A string is source text. Pass a Path to read a file without changing its line endings."""
    try:
        if isinstance(document, Path):
            with document.open("rb") as handle:
                raw = handle.read(BUNDLE_MAX_BYTES + 1)
        else:
            raw = document.encode("utf-8") if isinstance(document, str) else document
        if len(raw) > BUNDLE_MAX_BYTES:
            raise ValueError("Document exceeds the 20 MiB transfer limit")
        text = raw.decode("utf-8")
        bundle = None
        if text.lstrip().startswith("{"):
            envelope = json.loads(text, object_pairs_hook=_unique_keys)
            if "bundle" in envelope:
                if set(envelope) != {"bundle", "bundle_digest"}:
                    raise ValueError(
                        "Export wrapper requires exactly bundle and bundle_digest"
                    )
                bundle = WorkflowBundle.model_validate(envelope["bundle"])
                if canonical_digest(bundle) != envelope["bundle_digest"]:
                    raise ValueError("Export wrapper digest differs from its bundle")
            else:
                bundle = WorkflowBundle.model_validate(envelope)
            text = bundle.source
        source = text.encode("utf-8")
        if len(source) > 1_048_576:
            raise ValueError("Workflow source exceeds 1 MiB")
        sections = parse_sections(text)
        validate_authoring_sections(sections)
        graph = compile_graph(sections)
        required = dependency_inventory(sections)
        if bundle is not None:
            check_dependencies(sections, required, bundle)
    except (ValueError, OSError, RecursionError) as exc:
        raise WorkflowSourceExecutionError(
            "WORKFLOW_SOURCE_INVALID",
            str(exc),
            "Correct the source or regenerate the bundle.",
        ) from exc
    return Definition(
        raw,
        source,
        hashlib.sha256(source).hexdigest(),
        graph,
        bundle,
        bundle.dependencies if bundle else required,
    )
