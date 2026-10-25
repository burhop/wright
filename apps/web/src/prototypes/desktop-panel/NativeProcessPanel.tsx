import type { ProcessClient } from "@wright/process-client";
import type { ReactNode } from "react";
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
  canNavigate = false,
  runDetails,
  runHistory,
  historyOpen = false,
  historyDisabled = false,
  onToggleHistory,
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
  readonly canNavigate?: boolean;
  readonly runDetails?: ReactNode;
  readonly runHistory?: ReactNode;
  readonly historyOpen?: boolean;
  readonly historyDisabled?: boolean;
  readonly onToggleHistory?: () => void;
}) {
  return (
    <main className="native-workflow-panel" data-control-style="neutral">
      <header className="native-workflow-panel__context">
        <span className="native-workflow-panel__workspace">
          {workspaceName}
        </span>
        <nav className="native-workflow-views" aria-label="Workflow views">
          {onOpenWorkflow && (
            <button
              type="button"
              aria-label="Edit workflow"
              onClick={onOpenWorkflow}
            >
              Edit workflow
            </button>
          )}
          <button
            type="button"
            aria-current="page"
            onClick={
              historyOpen && !historyDisabled ? onToggleHistory : undefined
            }
          >
            Run and results
          </button>
        </nav>
        {onToggleHistory && (
          <button
            type="button"
            aria-expanded={historyOpen}
            disabled={historyDisabled}
            onClick={onToggleHistory}
          >
            {historyOpen ? "Back to current view" : "Run history"}
          </button>
        )}
        <small className="native-workflow-panel__view-hint">
          {runId
            ? `Run ${runId} · results and progress are read from Wright.`
            : "Prepare inputs and check readiness here. Run history opens existing results without starting work."}
        </small>
      </header>
      <div
        className="native-process-panel"
        style={{ flex: "1 1 0", minHeight: 0, overflow: "auto" }}
      >
        {runHistory && (
          <div className="native-workflow-history native-home">
            {runHistory}
          </div>
        )}
        <div hidden={historyOpen}>
          {runDetails}
          <CommonProcessView
            client={client}
            sessionId={sessionId}
            title={title}
            runId={runId}
            readReasoningStatus={readReasoningStatus}
            readOnly={readOnly}
            theme={theme}
            canReadRepresentations
            canNavigate={canNavigate}
            onUpload={(file, definition) =>
              client.uploadInput(definition.input_id, file)
            }
            onRunAttached={onRunAttached}
            onPrepareAnother={onPrepareAnother}
            onUnsavedChange={onDirty}
          />
        </div>
      </div>
    </main>
  );
}
