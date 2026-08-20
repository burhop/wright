import { useState } from "react";

import type { RivetRunResultItem } from "../../services/workspace-service";

interface RivetRunResultProps {
  result: RivetRunResultItem;
  onOpenArtifact?: (artifact: Record<string, unknown>) => void;
}

function downloadJson(result: RivetRunResultItem) {
  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${result.name || "result"}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function RivetRunResult({ result, onOpenArtifact }: RivetRunResultProps) {
  const [expanded, setExpanded] = useState(false);
  const rendered = result.value === null ? result.preview : typeof result.value === "string" ? result.value : JSON.stringify(result.value, null, 2);
  const copy = async () => {
    if (navigator.clipboard) await navigator.clipboard.writeText(rendered);
  };
  return (
    <article className="rivet-run-result" data-testid={`rivet-run-result-${result.name}`}>
      <header>
        <strong>{result.name}</strong>
        <span>{result.kind}</span>
        {!result.complete && <span className="rivet-run-warning">Incomplete</span>}
        {result.redaction_count > 0 && <span className="rivet-run-warning">Redacted</span>}
      </header>
      <pre className={expanded ? "is-expanded" : ""}>{rendered || "No value"}</pre>
      <div className="rivet-run-actions">
        {rendered.length > 240 && <button type="button" onClick={() => setExpanded((value) => !value)}>{expanded ? "Collapse" : "Expand"}</button>}
        <button type="button" onClick={() => void copy()}>Copy</button>
        <button type="button" onClick={() => downloadJson(result)}>Export JSON</button>
        {result.kind === "link" && typeof result.value === "string" && (
          <a href={result.value} target="_blank" rel="noreferrer">Open link</a>
        )}
        {result.artifact && onOpenArtifact && <button type="button" onClick={() => onOpenArtifact(result.artifact!)}>Open artifact</button>}
      </div>
    </article>
  );
}
