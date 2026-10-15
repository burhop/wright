import type { ProcessClient } from "@wright/process-client";
import type { WorkflowReasoningStatusReader } from "../../services/desktop-reasoning-status";
import { CommonProcessView } from "../../components/process-interfaces/CommonProcessView";
import "../../components/process-interfaces/process-workspace.css";
import "./native-panel.css";

/** Offline next-slice composition. No model worker, authority or UI executor. */
export function NativeProcessPanel({
  client,
  sessionId,
  workspaceName,
  title,
  runId,
  readReasoningStatus,
  readOnly = false,
  theme,
  onOpenWorkflow,
  onRunAttached,
  onPrepareAnother,
  onDirty,
}: {
  readonly client: ProcessClient;
  readonly sessionId: string;
  readonly workspaceName: string;
  readonly title: string;
  readonly runId?: string;
  readonly readReasoningStatus: WorkflowReasoningStatusReader;
  readonly readOnly?: boolean;
  readonly onOpenWorkflow?: () => void;
  readonly onRunAttached?: (runId: string) => void;
  readonly onPrepareAnother?: () => void;
  readonly onDirty?: (pending: boolean) => void;
  readonly theme?: "dark" | "light";
}) {
  return (
    <main className="native-workflow-panel" data-control-style="neutral">
      <header className="native-workflow-panel__context">
        <b>{workspaceName}</b>
        <span>Run and results</span>
        {onOpenWorkflow && (
          <button type="button" onClick={onOpenWorkflow}>
            Open workflow
          </button>
        )}
        <small>
          Progress, results and declared questions come from Wright. Use this
          conversation for AI tasks.
        </small>
      </header>
      <div
        className="native-process-panel"
        style={{ flex: "1 1 0", minHeight: 0, overflow: "auto" }}
      >
        <CommonProcessView
          client={client}
          sessionId={sessionId}
          title={title}
          runId={runId}
          readReasoningStatus={readReasoningStatus}
          readOnly={readOnly}
          theme={theme}
          canReadRepresentations
          onUpload={(file, definition) =>
            client.uploadInput(definition.input_id, file)
          }
          onRunAttached={onRunAttached}
          onPrepareAnother={onPrepareAnother}
          onUnsavedChange={onDirty}
        />
      </div>
    </main>
  );
}
