import { createContext, useContext, useMemo } from "react";

import type { DraftDiagnostic } from "./draft-intents";

const DraftDiagnosticIdsContext = createContext<ReadonlySet<string>>(new Set());

export function useDraftDiagnosticIds(): ReadonlySet<string> {
  return useContext(DraftDiagnosticIdsContext);
}

export function DraftDiagnosticProvider({
  diagnostics,
  children,
}: {
  readonly diagnostics: readonly DraftDiagnostic[];
  readonly children: React.ReactNode;
}): React.ReactNode {
  const affected = useMemo(
    () => new Set(diagnostics.flatMap((item) => item.affected_semantic_ids)),
    [diagnostics],
  );
  return (
    <DraftDiagnosticIdsContext.Provider value={affected}>
      {children}
    </DraftDiagnosticIdsContext.Provider>
  );
}

export function DraftDiagnostics({
  diagnostics,
}: {
  readonly diagnostics: readonly DraftDiagnostic[];
}): React.ReactNode {
  if (diagnostics.length === 0) return null;
  return (
    <section
      className="workflow-composer__diagnostics"
      data-testid="workflow-composer-diagnostics"
      aria-labelledby="workflow-composer-diagnostics-heading"
      role="alert"
    >
      <h2 id="workflow-composer-diagnostics-heading">
        Edit not applied · {diagnostics.length} diagnostic{diagnostics.length === 1 ? "" : "s"}
      </h2>
      <p>The last valid working draft and current saved revision are unchanged.</p>
      <ol>
        {diagnostics.map((item) => (
          <li
            data-testid={`workflow-diagnostic-${item.code}`}
            key={`${item.code}:${item.path}:${item.affected_semantic_ids.join(":")}`}
          >
            <strong><code>{item.code}</code></strong>
            <span>{item.explanation}</span>
            <span><b>Affected:</b> {item.affected_semantic_ids.join(", ") || "Complete draft"}</span>
            <span><b>Correction:</b> {item.correction}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
