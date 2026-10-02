import { useEffect, useState } from "react";
import { ProcessUI, Section } from "@wright/ui-kit";
import { hostAdapter } from "../../services/host-adapter";
import type { WorkspaceWorkflowRunSummary } from "../../services/workspace-service";

interface HistoricalResult {
  schema_version: "wright.historical-result/1";
  read_only: true;
  workflow_path: string;
  run_log_path: string;
  run: WorkspaceWorkflowRunSummary;
  permitted_actions: [];
}

export function HistoricalResultView({sessionId, workflowPath, runLogPath, onOpenFile, onClose}: {
  sessionId: string; workflowPath: string; runLogPath: string;
  onOpenFile?: (path: string) => void; onClose: () => void;
}) {
  const [result, setResult] = useState<HistoricalResult>();
  const [error, setError] = useState<string>();
  useEffect(() => {
    const controller = new AbortController();
    setResult(undefined); setError(undefined);
    const query = new URLSearchParams({session_id: sessionId, path: workflowPath, run_log_path: runLogPath});
    const endpoint = hostAdapter.resolveBackendUrl("/api/workspace/process-interfaces/historical-results");
    void hostAdapter.fetch(`${endpoint}?${query}`, {signal: controller.signal, cache: "no-store"})
      .then(async response => {
        if (!response.ok) throw new Error("This saved result could not be verified in its owning workspace.");
        const value = await response.json() as HistoricalResult;
        if (value.schema_version !== "wright.historical-result/1" || value.read_only !== true ||
            value.workflow_path !== workflowPath || value.run_log_path !== runLogPath ||
            !value.run || !Array.isArray(value.run.results) || !Array.isArray(value.permitted_actions) || value.permitted_actions.length)
          throw new Error("This saved result has an incompatible history format.");
        if (!controller.signal.aborted) setResult(value);
      }).catch(reason => {if (!controller.signal.aborted) setError(reason instanceof Error ? reason.message : "The saved result is unavailable.");});
    return () => controller.abort();
  }, [sessionId, workflowPath, runLogPath]);
  return <ProcessUI><Section title="Saved workflow result" description="Historical evidence only. This view does not resume work, check a device or send an operation.">
    <button className="wp-button" type="button" onClick={onClose}>Back to workflow</button>
    {!result && !error && <p role="status">Opening the saved result…</p>}
    {error && <p role="alert">{error}</p>}
    {result && <>
      <p>Recorded run: {result.run.run_id} · {result.run.status}</p>
      {result.run.source_matches_current === false && <p>The workflow has changed since this run. These results belong to its recorded source revision.</p>}
      {result.run.error && <p>Recorded error: {result.run.error}</p>}
      {onOpenFile && <button className="wp-link" type="button" onClick={() => onOpenFile(runLogPath)}>Open saved run record</button>}
      {result.run.results.map(output => <Section key={output.id} title={output.name}>
        <p>{output.artifact_role ?? output.kind} · {output.id}</p>
        {output.representations.map((representation, index) => <p key={index}>
          {representation.format} · {representation.revision ?? "Revision not recorded"}
          {representation.kind === "workspace_file" && onOpenFile && <button className="wp-link" type="button" onClick={() => onOpenFile(representation.location)}>Open saved artifact</button>}
        </p>)}
      </Section>)}
      {!result.run.results.length && <p>No retained outputs were recorded for this run.</p>}
    </>}
  </Section></ProcessUI>;
}
