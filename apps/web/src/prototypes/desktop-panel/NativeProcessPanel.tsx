import type { ProcessClient } from "@wright/process-client";
import type { WorkflowReasoningStatusReader } from "../../services/desktop-reasoning-status";
import { CommonProcessView } from "../../components/process-interfaces/CommonProcessView";
import "../../components/process-interfaces/process-workspace.css";
import "./native-panel.css";

/** Offline next-slice composition. No model worker, authority or UI executor. */
export function NativeProcessPanel({client,sessionId,workspaceName,title,runId,readReasoningStatus,readOnly=false,theme}: {
  readonly client: ProcessClient;
  readonly sessionId: string;
  readonly workspaceName: string;
  readonly title: string;
  readonly runId?: string;
  readonly readReasoningStatus: WorkflowReasoningStatusReader;
  readonly readOnly?: boolean;
  readonly theme?: "dark" | "light";
}) {
  return <main className="native-workflow-panel" data-control-style="neutral">
    <header className="native-workflow-panel__context"><b>{workspaceName}</b><span>Run and results</span><small>Progress, results and declared questions come from Wright. Use this conversation for AI tasks.</small></header>
    <div className="native-process-panel" style={{flex:"1 1 0",minHeight:0,overflow:"auto"}}>
      <CommonProcessView client={client} sessionId={sessionId} title={title} runId={runId} readReasoningStatus={readReasoningStatus} readOnly={readOnly} theme={theme} canReadRepresentations />
    </div>
  </main>;
}
