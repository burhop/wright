import { useCallback, useEffect, useMemo, useState } from "react";
import {
  type InputDefinition,
  type NavigationResolution,
  type ProcessRef,
} from "@wright/process-client";
import {
  createProcessNavigationDispatcher,
  type ProcessNavigationRequest,
} from "../../services/process-navigation";
import { createWorkspaceProcessClient } from "../../services/process-client";
import type { ProcessWorkspaceTab as WorkingTab, ProcessInterfaceLocator } from "../../services/process-workspace-tabs";
import { CommonProcessView } from "./CommonProcessView";
import { createInterfaceAuthoringClient } from "../../services/process-ui-authoring";
import { InterfaceAuthoringPanel } from "./InterfaceAuthoringPanel";
import { ProcessInterfaceView } from "./ProcessInterfaceView";

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
  readonly onNavigate?: (
    process: ProcessRef,
    resolution: NavigationResolution,
  ) => Promise<void>;
  readonly navigation?: ProcessNavigationRequest;
  readonly onOpenInterface?: (process: ProcessRef, locator: ProcessInterfaceLocator, title: string, runId?: string) => void;
}

/** Trusted workspace host. This does not resolve file providers or execute a graph. */
export function ProcessWorkspaceTab({
  tab,
  sessionId,
  onRunAttached,
  onOpenDefinition,
  onPrepareAnother,
  onNavigate,
  navigation,
  onOpenInterface,
}: ProcessWorkspaceTabProps) {
  const [authoringShown, setAuthoringShown] = useState(false);
  const [showCommon, setShowCommon] = useState(false);
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
  const navigationHost = useMemo(() => createProcessNavigationDispatcher(), []);
  useEffect(() => {
    navigationHost.setHost(onNavigate);
    return () => navigationHost.setHost(undefined);
  }, [onNavigate, navigationHost]);
  const client = useMemo(
    () =>
      createWorkspaceProcessClient({
        process,
        sessionId,
        navigate: navigationHost.navigate,
      }),
    [process, sessionId, navigationHost],
  );
  const attached = useCallback(
    (runId: string) => onRunAttached(tab.path, process, runId),
    [onRunAttached, process, tab.path],
  );
  const authoring = useMemo(() => createInterfaceAuthoringClient(process, sessionId), [process, sessionId]);
  const upload = useCallback(
    (file: File, definition: InputDefinition) =>
      client.uploadInput(definition.input_id, file),
    [client],
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
      {onOpenInterface && <div className="wp-row" style={{padding: "8px 16px"}}>
        <button className="recovery-button recovery-button--secondary" type="button" onClick={() => setAuthoringShown(value => !value)}>
          {authoringShown ? "Hide interface controls" : "Create or choose interface"}
        </button>
        {tab.processView.interface && showCommon && <button className="recovery-button recovery-button--secondary" type="button" onClick={() => setShowCommon(false)}>
          Return to interface
        </button>}
      </div>}
      {authoringShown && onOpenInterface && <InterfaceAuthoringPanel client={authoring} sessionId={sessionId} viewId={tab.processView.view_id}
        initialUiId={tab.processView.interface?.ui_id}
        initialJobId={tab.processView.interface?.kind === "preview" ? tab.processView.interface.job_id : undefined}
        onOpenPreview={async view => {
          if (!view.preview) return;
          onOpenInterface(process, {kind: "preview", ui_id: view.preview.manifest.ui_id, revision_id: view.preview.manifest.revision_id,
            job_id: view.job.job_id}, view.preview.manifest.title, tab.processView.run_id);
        }} onOpenSaved={async (ui, revision) => {
          onOpenInterface(process, {kind: "working", ui_id: ui.ui_id, revision_id: revision.manifest.revision_id}, revision.manifest.title, tab.processView.run_id);
        }}/>}
      {tab.processView.interface && !showCommon ? <ProcessInterfaceView client={authoring} locator={tab.processView.interface}
        sessionId={sessionId} viewId={tab.processView.view_id} runId={tab.processView.run_id} onUseCommon={() => setShowCommon(true)}
        onRunAttached={attached} onNavigate={onNavigate ? target => client.navigate(target) : undefined}/>
      : <CommonProcessView
        client={client}
        sessionId={sessionId}
        title={tab.name}
        runId={tab.processView.run_id}
        onRunAttached={attached}
        onPrepareAnother={prepareAnother}
        onUpload={upload}
        canReadRepresentations
        canNavigate={!!onNavigate}
        navigation={navigation}
      />}
    </section>
  );
}
