import { useCallback, useMemo } from "react";
import type { ProcessRef } from "@wright/process-client";
import { createWorkspaceProcessClient } from "../../services/process-client";
import type { ProcessWorkspaceTab as WorkingTab } from "../../services/process-workspace-tabs";
import { CommonProcessView } from "./CommonProcessView";

export interface ProcessWorkspaceTabProps {
  readonly tab: WorkingTab;
  readonly sessionId: string;
  readonly onRunAttached: (
    path: string,
    process: ProcessRef,
    runId: string,
  ) => void;
  readonly onOpenDefinition?: (process: ProcessRef) => void;
  readonly onPrepareAnother: (process: ProcessRef) => void;
}

/** Trusted workspace host. This does not resolve file providers or execute a graph. */
export function ProcessWorkspaceTab({
  tab,
  sessionId,
  onRunAttached,
  onOpenDefinition,
  onPrepareAnother,
}: ProcessWorkspaceTabProps) {
  const {
    workspace_id,
    source_path,
    source_digest,
    semantic_digest,
    source_contract,
  } = tab.processView.process;
  const process = useMemo<ProcessRef>(
    () => ({
      workspace_id,
      source_path,
      source_digest,
      ...(semantic_digest !== undefined ? { semantic_digest } : {}),
      ...(source_contract !== undefined ? { source_contract } : {}),
    }),
    [
      workspace_id,
      source_path,
      source_digest,
      semantic_digest,
      source_contract,
    ],
  );
  const client = useMemo(
    () => createWorkspaceProcessClient({ process, sessionId }),
    [process, sessionId],
  );
  const attached = useCallback(
    (runId: string) => onRunAttached(tab.path, process, runId),
    [onRunAttached, process, tab.path],
  );
  const prepareAnother = useCallback(
    () => onPrepareAnother(process),
    [onPrepareAnother, process],
  );
  return (
    <section
      data-testid="workspace-process-view"
      data-process-path={process.source_path}
      data-run-id={tab.processView.run_id}
      aria-label={tab.name}
      style={{ width: "100%", minWidth: 0, minHeight: 0, overflow: "auto" }}
    >
      {onOpenDefinition && (
        <div style={{ padding: "8px 16px" }}>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            data-testid="process-open-definition"
            onClick={() => onOpenDefinition(process)}
          >
            Open workflow
          </button>
        </div>
      )}
      <CommonProcessView
        client={client}
        sessionId={sessionId}
        title={tab.name}
        runId={tab.processView.run_id}
        onRunAttached={attached}
        onPrepareAnother={prepareAnother}
      />
    </section>
  );
}
