import { useState } from "react";

import type { RivetRunResultItem } from "../../services/workspace-service";
import { displayEvidenceState } from "./rivet-run-evidence";

interface RivetRunResultProps {
  result: RivetRunResultItem;
  onOpenArtifact?: (artifact: Record<string, unknown>) => void;
}

const INDENT = "  ";

function indented(value: string, depth: number): string {
  const prefix = INDENT.repeat(depth);
  return value
    .split("\n")
    .map((line) => `${prefix}${line}`)
    .join("\n");
}

function readableValue(value: unknown, depth = 0): string {
  if (value === null) return "null";
  if (typeof value === "string") return indented(value, depth);
  if (typeof value === "number" || typeof value === "boolean") {
    return `${INDENT.repeat(depth)}${String(value)}`;
  }
  if (Array.isArray(value)) {
    if (value.length === 0) return `${INDENT.repeat(depth)}[]`;
    return value
      .map((item) => {
        const prefix = INDENT.repeat(depth);
        if (
          item === null ||
          typeof item === "number" ||
          typeof item === "boolean" ||
          (typeof item === "string" && !item.includes("\n"))
        ) {
          return `${prefix}- ${String(item)}`;
        }
        return `${prefix}-\n${readableValue(item, depth + 1)}`;
      })
      .join("\n");
  }
  if (typeof value === "object") {
    const entries = Object.entries(value);
    if (entries.length === 0) return `${INDENT.repeat(depth)}{}`;
    return entries
      .map(([key, item]) => {
        const prefix = INDENT.repeat(depth);
        if (
          item === null ||
          typeof item === "number" ||
          typeof item === "boolean" ||
          (typeof item === "string" && !item.includes("\n"))
        ) {
          return `${prefix}${key}: ${String(item)}`;
        }
        return `${prefix}${key}:\n${readableValue(item, depth + 1)}`;
      })
      .join("\n");
  }
  return `${INDENT.repeat(depth)}${String(value)}`;
}

function serializedValue(result: RivetRunResultItem): string {
  if (result.value === null) return result.preview;
  if (typeof result.value === "string") return result.value;
  return JSON.stringify(result.value, null, 2) ?? result.preview;
}

function displayedValue(result: RivetRunResultItem, rendered: string): string {
  if (rendered.length > 0) return rendered;
  if (
    result.evidence_state === "available" &&
    typeof result.value === "string"
  ) {
    return `Empty text (${result.value.length} characters)`;
  }
  return "No value";
}

function downloadJson(result: RivetRunResultItem) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${result.name || "result"}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function RivetRunResult({
  result,
  onOpenArtifact,
}: RivetRunResultProps) {
  const [expanded, setExpanded] = useState(false);
  const serialized = serializedValue(result);
  const rendered =
    result.value !== null &&
    (result.kind === "structured" || result.kind === "list")
      ? readableValue(result.value)
      : serialized;
  const displayed = displayedValue(result, rendered);
  const copy = async () => {
    if (navigator.clipboard) await navigator.clipboard.writeText(serialized);
  };
  return (
    <article
      className="rivet-run-result"
      data-testid={`rivet-run-result-${result.name}`}
    >
      <header>
        <strong>{result.name}</strong>
        <span>{result.data_type || result.kind}</span>
        <span>{displayEvidenceState(result.evidence_state)}</span>
        {!result.complete && (
          <span className="rivet-run-warning">Incomplete</span>
        )}
        {result.redaction_count > 0 && (
          <span className="rivet-run-warning">Redacted</span>
        )}
      </header>
      <pre
        className={expanded ? "is-expanded" : ""}
        data-testid={`rivet-run-result-value-${result.name}`}
      >
        {displayed}
      </pre>
      <div className="rivet-run-actions">
        {rendered.length > 240 && (
          <button
            type="button"
            data-testid={"rivet-run-result-expand-" + result.name}
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? "Collapse" : "Expand"}
          </button>
        )}
        <button
          type="button"
          data-testid={"rivet-run-result-copy-" + result.name}
          onClick={() => void copy()}
        >
          Copy
        </button>
        <button
          type="button"
          data-testid={"rivet-run-result-export-" + result.name}
          onClick={() => downloadJson(result)}
        >
          Export JSON
        </button>
        {result.kind === "link" && typeof result.value === "string" && (
          <a href={result.value} target="_blank" rel="noreferrer">
            Open link
          </a>
        )}
        {result.artifact && onOpenArtifact && (
          <button
            type="button"
            onClick={() => onOpenArtifact(result.artifact!)}
          >
            Open artifact
          </button>
        )}
      </div>
    </article>
  );
}
