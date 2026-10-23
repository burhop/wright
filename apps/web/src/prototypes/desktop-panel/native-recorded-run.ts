import type { WorkspaceWorkflowRunSummary } from "../../services/workspace-service";
import type { HomeCall } from "./NativeHomePanel";

export type NativeRecordedRun = WorkspaceWorkflowRunSummary & {
  run_id: string;
};

/** Read the existing recorder, never the latest run or an execution endpoint. */
export async function readNativeRecordedRun(
  call: HomeCall,
  subject: {
    workspace_id: string;
    session_id: string;
    path: string;
    run_id: string | null;
    source_digest: string | null;
  },
): Promise<NativeRecordedRun> {
  if (!subject.run_id || !subject.source_digest)
    throw new Error("Missing exact run identity");
  const reply = await call("wright_recorded_run_read", { request: subject });
  const data = reply.structuredContent;
  const record = data?.record as WorkspaceWorkflowRunSummary | undefined;
  if (
    reply.isError ||
    data?.workspace_id !== subject.workspace_id ||
    data.session_id !== subject.session_id ||
    data.workflow_path !== subject.path ||
    !record ||
    record.run_id !== subject.run_id ||
    record.source_digest !== subject.source_digest ||
    typeof record.source_matches_current !== "boolean" ||
    typeof record.status !== "string" ||
    typeof record.path !== "string" ||
    !Array.isArray(record.results)
  ) {
    throw new Error("Exact saved run evidence is unavailable");
  }
  return record as NativeRecordedRun;
}
