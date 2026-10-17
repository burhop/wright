import { useEffect, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import { NativeRunEvidence } from "./NativeRunEvidence";

export interface RecordedRun {
  run_id: string | null;
  path: string;
  status: string;
  started_at: string | null;
  source_digest: string | null;
}

/** Recorder observations only. Opening delegates to the exact process owner. */
export function NativeRecentRuns({
  workspace,
  paths,
  call,
  onOpen,
}: {
  readonly workspace: DesktopWorkspace;
  readonly paths: string[];
  readonly call: HomeCall;
  readonly onOpen?: (path: string, run: RecordedRun) => Promise<void>;
}) {
  const [path, setPath] = useState("");
  const [runs, setRuns] = useState<RecordedRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [selected, setSelected] = useState<RecordedRun>();
  useEffect(() => {
    let active = true;
    setRuns([]);
    setSelected(undefined);
    setError("");
    if (!path) return;
    setLoading(true);
    void call("wright_workflow_history", {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      path,
    })
      .then((result) => {
        if (result.isError) throw new Error("History unavailable");
        const data = result.structuredContent;
        if (
          data?.workspace_id !== workspace.workspace_id ||
          data.session_id !== workspace.session_id ||
          data.workflow_path !== path ||
          !Array.isArray(data.runs)
        )
          throw new Error("History scope differs");
        if (active) setRuns(data.runs as RecordedRun[]);
      })
      .catch(() => {
        if (active)
          setError(
            "Run history could not be read. Refresh to retry; nothing was resumed.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [call, workspace.workspace_id, workspace.session_id, path, refresh]);
  return (
    <section aria-label="Recent runs">
      <h2>Recent runs</h2>
      <p>Choose a workflow to read its latest recorded runs.</p>
      <label htmlFor="wright-history-source">Workflow history</label>
      <select
        id="wright-history-source"
        value={path}
        disabled={opening}
        onChange={(event) => setPath(event.target.value)}
      >
        <option value="" disabled>
          Choose a workflow
        </option>
        {paths.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>
      <button
        disabled={!path || loading || opening}
        onClick={() => setRefresh((value) => value + 1)}
      >
        Refresh runs
      </button>
      {loading && <p role="status">Loading run history…</p>}
      {error && <p role="alert">{error}</p>}
      {path && !loading && !error && runs.length === 0 && (
        <p>No recorded runs for this workflow.</p>
      )}
      <ul>
        {runs.map((run) => (
          <li key={run.path}>
            <strong>{run.status.replaceAll("_", " ")}</strong>
            <small>{run.started_at ?? "Start time unreported"}</small>
            <small>{run.run_id ?? run.path}</small>
            {run.run_id && run.source_digest && (
              <button
                disabled={opening || loading}
                onClick={() => setSelected(run)}
              >
                Read saved evidence
              </button>
            )}
            {onOpen && run.run_id && run.source_digest ? (
              <button
                disabled={opening || loading}
                onClick={() => {
                  setOpening(true);
                  setError("");
                  void onOpen(path, run)
                    .catch(() =>
                      setError(
                        "This exact run could not be opened. Its source may have changed; no run was started or resumed.",
                      ),
                    )
                    .finally(() => setOpening(false));
                }}
              >
                Open working view
              </button>
            ) : (
              <small>Exact run navigation unavailable for this record.</small>
            )}
          </li>
        ))}
      </ul>
      {selected?.run_id && selected.source_digest && path && (
        <NativeRunEvidence
          key={`${path}:${selected.run_id}:${selected.source_digest}`}
          workspace={workspace}
          path={path}
          run={selected}
          call={call}
        />
      )}
    </section>
  );
}
