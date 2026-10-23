import { useEffect, useState } from "react";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";
import type { RecordedRun } from "./NativeRecentRuns";
import {
  readNativeRecordedRun,
  type NativeRecordedRun,
} from "./native-recorded-run";
import type { WorkspaceEngineeringResult } from "../../services/workspace-service";
import { EngineeringResults } from "../workflow-recovery/EngineeringResults";
import { NativeFileDownload } from "./NativeFileDownload";

function allResults(
  results: WorkspaceEngineeringResult[],
): WorkspaceEngineeringResult[] {
  return results.flatMap((result) => [result, ...allResults(result.exports)]);
}

/** Read-only recorder facts. Current process action/review gates are separate. */
export function NativeRunEvidence({
  workspace,
  path,
  run,
  call,
}: {
  workspace: DesktopWorkspace;
  path: string;
  run: Pick<RecordedRun, "run_id" | "source_digest">;
  call: HomeCall;
}) {
  const [record, setRecord] = useState<NativeRecordedRun>();
  const [error, setError] = useState(false);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let current = true;
    setRecord(undefined);
    setError(false);
    void readNativeRecordedRun(call, {
      workspace_id: workspace.workspace_id,
      session_id: workspace.session_id,
      path,
      run_id: run.run_id,
      source_digest: run.source_digest,
    })
      .then((value) => {
        if (current) setRecord(value);
      })
      .catch(() => {
        if (current) setError(true);
      });
    return () => {
      current = false;
    };
  }, [
    call,
    workspace.workspace_id,
    workspace.session_id,
    path,
    run.run_id,
    run.source_digest,
    refresh,
  ]);
  return (
    <section aria-label="Saved run evidence">
      <h3>Saved run evidence</h3>
      <p>
        This view reads recorded evidence. It cannot resume work, approve a
        result or repeat an action.
      </p>
      <button onClick={() => setRefresh((value) => value + 1)}>
        Refresh saved evidence
      </button>
      {error ? (
        <p role="alert">
          This exact saved run could not be read. Nothing was started or
          resumed.
        </p>
      ) : !record ? (
        <p role="status">Reading the saved run…</p>
      ) : (
        <>
          <p>Recorded state: {record.status.replaceAll("_", " ")}.</p>
          {!record.source_matches_current && (
            <p>
              The workflow has changed since this run. These are its saved
              results; current workflow actions remain separate.
            </p>
          )}
          {record.error && <p>{record.error}</p>}
          {!record.results.length && (
            <p>No result files were recorded for this run.</p>
          )}
          {allResults(record.results).map((result) => {
            const files = result.representations.filter(
              (rep) => rep.kind === "workspace_file",
            );
            return (
              <article key={result.id}>
                <EngineeringResults
                  results={[{ ...result, representations: files, exports: [] }]}
                />
                {result.representations.some(
                  (rep) => rep.kind !== "workspace_file",
                ) && (
                  <p>
                    Live application, cloud and value representations are not
                    opened from this saved-file view.
                  </p>
                )}
                {files.map((file) => (
                  <div key={file.location}>
                    {file.sha256 && /^[a-f0-9]{64}$/.test(file.sha256) ? (
                      <NativeFileDownload
                        key={`${record.run_id}:${result.id}:${file.location}:${file.sha256}`}
                        call={call}
                        workspace={workspace}
                        path={file.location}
                        recordedEvidence={{
                          runId: record.run_id,
                          sha256: file.sha256,
                        }}
                      />
                    ) : (
                      <p>
                        No recorded byte hash is available for this file. Exact
                        evidence download is unavailable.
                      </p>
                    )}
                  </div>
                ))}
              </article>
            );
          })}
          <details>
            <summary>Recorded identity</summary>
            <p>{record.run_id}</p>
            <p className="native-connection-endpoint">
              Source: {record.source_digest}
            </p>
          </details>
        </>
      )}
    </section>
  );
}
