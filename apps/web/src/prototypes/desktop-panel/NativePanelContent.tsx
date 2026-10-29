import { NativeEditorConnections } from "./NativeEditorConnections";
import { WorkflowToolDiscovery } from "../workflow-recovery/workflow-tool-discovery";
import { createNativeToolDiscovery } from "./native-tool-discovery";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ProcessClientError,
  type ProcessRef,
  type NavigationResolution,
} from "@wright/process-client";
import {
  createProcessNavigationDispatcher,
  type ProcessNavigationRequest,
} from "../../services/process-navigation";
import type {
  WorkspaceWorkflowRunSummary,
  WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";
import {
  recoveryWorkflowSourceTitle,
  recoveryWorkflowSourceSummary,
} from "../workflow-recovery/recovery-authoring";
import { readNativeRecordedRun } from "./native-recorded-run";
import { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import { NativeProcessPanel } from "./NativeProcessPanel";
import { NativeRunEvidence } from "./NativeRunEvidence";
import { NativeRecentRuns, type RecordedRun } from "./NativeRecentRuns";
import type { HomeCall } from "./NativeHomePanel";
import type { NativeWorkflowLocation } from "./native-navigation-state";
import { NativeSourceClient } from "./native-source-client";
import type { NativeEditorDraftClient } from "./native-editor-draft-client";
import { WorkflowBundleDialog } from "../workflow-recovery/WorkflowBundleDialog";
import {
  createNativeTransferClient,
  type NativeTransferCall,
} from "./native-transfer-client";
import {
  createNativePanelProcessClient,
  type NativeProcessCall,
} from "./native-process-client";

/** One host surface, existing editor and working controller, no document-tab imitation. */
export function NativePanelContent({
  initial,
  sourceClient,
  draftClient,
  call,
  sessionId,
  workspaceName,
  initialProcess,
  initialRunId,
  initialView,
  workingViewEnabled,
  onDirty,
  theme,
  transferCall,
  onOpenTransferred,
  onAcceptedSource,
  readEvidence,
  onLocationChange,
  openLink,
}: {
  readonly openLink?: (url: string) => Promise<void>;
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly sourceClient: NativeSourceClient;
  readonly draftClient?: NativeEditorDraftClient;
  readonly call: NativeProcessCall;
  readonly sessionId: string;
  readonly workspaceName: string;
  readonly initialProcess?: ProcessRef;
  readonly initialRunId?: string;
  readonly initialView?: "editor" | "working";
  readonly workingViewEnabled: boolean;
  readonly readEvidence?: HomeCall;
  readonly onLocationChange?: (location: NativeWorkflowLocation) => void;
  readonly onDirty: (pending: boolean) => void;
  readonly theme?: "dark" | "light";
  readonly transferCall?: NativeTransferCall;
  readonly onOpenTransferred?: (path: string) => Promise<void>;
  readonly onAcceptedSource?: (
    document: WorkspaceWorkflowSourceDocument,
  ) => void;
}) {
  const [connectionsOpen, setConnectionsOpen] = useState(false);
  const [accepted, setAccepted] = useState(initial);
  const [view, setView] = useState<"editor" | "working">(
    workingViewEnabled
      ? (initialView ?? (initialProcess ? "working" : "editor"))
      : "editor",
  );
  const [process, setProcess] = useState<ProcessRef>(
    initialProcess ?? {
      workspace_id: initial.workspace_id,
      source_path: initial.path,
      source_digest: initial.storage_digest,
    },
  );
  const [run, setRun] = useState(initialRunId);
  const [workingGeneration, setWorkingGeneration] = useState(0);
  const [sourceDirty, setSourceDirty] = useState(false);
  const [workingDirty, setWorkingDirty] = useState(false);
  const [notice, setNotice] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [transferDocument, setTransferDocument] =
    useState<WorkspaceWorkflowSourceDocument | null>(null);
  const [openingTransfer, setOpeningTransfer] = useState(false);
  const [navigation, setNavigation] = useState<ProcessNavigationRequest>();
  const [runDetails, setRunDetails] = useState<{
    run_id: string;
    source_digest: string;
  }>();
  useEffect(() => {
    // A remembered target is reread by the host on reopening. It carries no
    // lifecycle state and cannot attach an old run to a new source revision.
    const digest =
      view === "working" ? process.source_digest : accepted.storage_digest;
    onLocationChange?.({
      path: accepted.path,
      source_digest: digest,
      view,
      ...(run && digest === process.source_digest ? { run_id: run } : {}),
    });
  }, [
    accepted.path,
    accepted.storage_digest,
    process.source_digest,
    run,
    view,
    onLocationChange,
  ]);
  const evidenceKey = JSON.stringify([
    process.workspace_id,
    sessionId,
    process.source_path,
    process.source_digest,
    run,
  ]);
  const [editorEvidence, setEditorEvidence] = useState<{
    key: string;
    record?: WorkspaceWorkflowRunSummary;
    error?: boolean;
  }>();
  useEffect(() => {
    if (view !== "editor" || !run || !readEvidence) return;
    let current = true;
    void readNativeRecordedRun(readEvidence, {
      workspace_id: process.workspace_id,
      session_id: sessionId,
      path: process.source_path,
      source_digest: process.source_digest,
      run_id: run,
    })
      .then((record) => {
        if (current) setEditorEvidence({ key: evidenceKey, record });
      })
      .catch(() => {
        if (current) setEditorEvidence({ key: evidenceKey, error: true });
      });
    return () => {
      current = false;
    };
  }, [view, run, readEvidence, process, sessionId, evidenceKey]);
  const selectedEvidence =
    editorEvidence?.key === evidenceKey ? editorEvidence : undefined;
  const transfer = useMemo(
    () =>
      transferCall
        ? createNativeTransferClient(
            initial.workspace_id,
            sessionId,
            transferCall,
          )
        : undefined,
    [initial.workspace_id, sessionId, transferCall],
  );
  const discoverTools = useMemo(
    () => ({
      read: createNativeToolDiscovery(
        initial.workspace_id,
        sessionId,
        readEvidence,
      ),
      sessionId,
      openConnections: () => setConnectionsOpen(true),
    }),
    [initial.workspace_id, sessionId, readEvidence],
  );
  const transferPending = openingTransfer || !!transferDocument;
  const dispatcher = useMemo(() => createProcessNavigationDispatcher(), []);
  const navigate = useCallback(
    async (
      _process: ProcessRef,
      _target: unknown,
      resolution: NavigationResolution,
    ) => {
      if (sourceDirty || workingDirty || transferPending)
        throw new ProcessClientError({
          code: "CAPABILITY_UNAVAILABLE",
          message: "Finish or reconcile pending edits before navigating.",
          correction: "Your current view is preserved.",
        });
      const target = resolution.target;
      if (target.kind === "process" || target.kind === "block") {
        if (process.source_digest !== accepted.storage_digest)
          throw new ProcessClientError({
            code: "CAPABILITY_UNAVAILABLE",
            message: "This run belongs to an older source revision.",
            correction:
              "Inspect its saved run; open the current workflow separately to edit it.",
          });
        setNavigation({ requestId: crypto.randomUUID(), resolution });
        setRunDetails(undefined);
        setNotice("");
        setView("editor");
      } else if (target.kind === "run" && target.run_id && readEvidence) {
        setRun(target.run_id);
        setRunDetails({
          run_id: target.run_id,
          source_digest: process.source_digest,
        });
        setNotice("");
        setView("working");
      } else {
        throw new ProcessClientError({
          code: "CAPABILITY_UNAVAILABLE",
          message: "This native panel cannot open that navigation target yet.",
          correction: "Inspect the recorded result in View run or Files.",
        });
      }
    },
    [
      sourceDirty,
      workingDirty,
      transferPending,
      process.source_digest,
      accepted.storage_digest,
      readEvidence,
    ],
  );
  useEffect(() => {
    dispatcher.setHost((subject, resolution) =>
      navigate(subject, resolution.target, resolution),
    );
    return () => dispatcher.setHost(undefined);
  }, [dispatcher, navigate]);
  const native = useMemo(
    () =>
      createNativePanelProcessClient({
        process,
        sessionId,
        workspaceName,
        call,
        navigate: dispatcher.navigate,
      }),
    [process, sessionId, workspaceName, call, dispatcher],
  );
  const sourceChange = useCallback(
    (pending: boolean) => {
      setSourceDirty(pending);
      onDirty(pending || workingDirty || transferPending);
    },
    [onDirty, workingDirty, transferPending],
  );
  const workingChange = useCallback(
    (pending: boolean) => {
      setWorkingDirty(pending);
      if (!pending) setNotice("");
      onDirty(pending || sourceDirty || transferPending);
    },
    [onDirty, sourceDirty, transferPending],
  );
  const openWorking = async () => {
    if (sourceDirty || workingDirty || transferPending) return false;
    try {
      const stored = await sourceClient.read();
      if (stored.storage_digest !== accepted.storage_digest) {
        setNotice(
          "The saved workflow changed. Compare or reload it before preparing another run.",
        );
        return false;
      }
      if (process.source_digest !== stored.storage_digest) {
        setProcess({
          workspace_id: stored.workspace_id,
          source_path: stored.path,
          source_digest: stored.storage_digest,
        });
        setRun(undefined);
      }
      setNotice("");
      setView("working");
      return true;
    } catch {
      setNotice(
        "Wright could not read the accepted workflow. Your draft is kept.",
      );
      return false;
    }
  };
  const openEditor = () => {
    if (workingDirty) {
      setNotice(
        "Finish or reconcile the pending change before leaving this working view.",
      );
      return;
    }
    if (process.source_digest !== accepted.storage_digest) {
      setNotice(
        "This run belongs to an older source revision. Open the current workflow from the conversation to edit it.",
      );
      return;
    }
    setNotice("");
    setView("editor");
  };
  const openRecordedRun = async (path: string, recorded: RecordedRun) => {
    if (
      sourceDirty ||
      workingDirty ||
      transferPending ||
      path !== process.source_path ||
      !recorded.run_id ||
      recorded.source_digest !== process.source_digest
    )
      throw new Error("Open this historical record using Read saved evidence.");
    // The recorder row is a navigation target. Only the scoped runtime read
    // confirms that the common view may attach to that exact recorded run.
    await native.client.getSnapshot({ runId: recorded.run_id });
    setRun(recorded.run_id);
    setRunDetails(undefined);
    setWorkingGeneration((value) => value + 1);
    setHistoryOpen(false);
  };
  const openTransferred = async (path: string) => {
    setTransferDocument(null);
    onDirty(sourceDirty || workingDirty);
    try {
      await onOpenTransferred?.(path);
    } catch {
      setNotice(
        "The saved destination is unavailable. Inspect retained import files before another attempt; no import was repeated.",
      );
    }
  };
  const openTransfer = () => {
    setOpeningTransfer(true);
    onDirty(true);
    void sourceClient
      .read()
      .then((observed) => {
        if (observed.storage_digest !== accepted.storage_digest)
          throw new Error(
            "The saved workflow changed. Reload it before transferring.",
          );
        setTransferDocument(observed);
        setOpeningTransfer(false);
      })
      .catch(() => {
        setNotice(
          "Wright could not confirm the current saved workflow. Reload it before transferring; your draft is kept.",
        );
        setOpeningTransfer(false);
        onDirty(sourceDirty || workingDirty);
      });
  };
  return (
    <div style={{ height: "100%", minHeight: 0 }}>
      {connectionsOpen && readEvidence && (
        <NativeEditorConnections
          workspace={{
            workspace_id: initial.workspace_id,
            session_id: sessionId,
            workspace_name: workspaceName,
            available: true,
            reason: null,
          }}
          call={readEvidence}
          openLink={openLink}
          onClose={() => setConnectionsOpen(false)}
        />
      )}
      {connectionsOpen && !readEvidence && (
        <p role="status">
          Connections are unavailable in this editor. Your workflow is kept
          open.
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      {transferDocument && transfer && onOpenTransferred && (
        <WorkflowBundleDialog
          document={transferDocument}
          sessionId={sessionId}
          transfer={transfer}
          listFiles={() =>
            transfer.listFiles(
              transferDocument.path,
              transferDocument.storage_digest,
            )
          }
          listInterfaces={() =>
            transfer.listInterfaces(
              transferDocument.path,
              transferDocument.storage_digest,
            )
          }
          onClose={() => {
            setTransferDocument(null);
            onDirty(sourceDirty || workingDirty);
          }}
          onImported={openTransferred}
          onOpenDestination={openTransferred}
        />
      )}
      <div
        style={{
          display: view === "editor" ? "block" : "none",
          height: "100%",
        }}
      >
        {run && !selectedEvidence?.record && (
          <p role="status">
            {selectedEvidence?.error || !readEvidence
              ? "Selected run evidence could not be read. Choose View run to inspect it."
              : "Reading selected run evidence…"}
          </p>
        )}
        <WorkflowToolDiscovery.Provider value={discoverTools}>
          <NativeWorkflowPanel
            initial={initial}
            client={sourceClient}
            draftClient={draftClient}
            navigation={navigation}
            readOnlyRun={selectedEvidence?.record}
            selectedRunId={run}
            workspaceName={workspaceName}
            onOpenTransfer={
              transfer && onOpenTransferred ? openTransfer : undefined
            }
            transferDisabled={sourceDirty || workingDirty || transferPending}
            onDirty={sourceChange}
            onAccepted={(document) => {
              setAccepted(document);
              onAcceptedSource?.(document);
            }}
            onOpenWorkingView={
              workingViewEnabled ? () => void openWorking() : undefined
            }
          />
        </WorkflowToolDiscovery.Provider>
      </div>
      {view === "working" && workingViewEnabled && (
        <NativeProcessPanel
          key={`${process.source_digest}:${workingGeneration}`}
          {...native}
          canNavigate
          historyOpen={historyOpen}
          onToggleHistory={
            readEvidence ? () => setHistoryOpen((value) => !value) : undefined
          }
          historyDisabled={sourceDirty || workingDirty || transferPending}
          runHistory={
            historyOpen && readEvidence ? (
              <NativeRecentRuns
                workspace={{
                  workspace_id: initial.workspace_id,
                  session_id: sessionId,
                  workspace_name: workspaceName,
                  available: true,
                  reason: null,
                }}
                paths={[process.source_path]}
                initialPath={process.source_path}
                titles={
                  process.source_digest === accepted.storage_digest
                    ? {
                        [process.source_path]:
                          recoveryWorkflowSourceTitle(accepted.source) ??
                          accepted.path,
                      }
                    : undefined
                }
                call={readEvidence}
                onOpen={openRecordedRun}
              />
            ) : undefined
          }
          runDetails={
            runDetails && readEvidence ? (
              <section aria-label="Run details">
                <button type="button" onClick={() => setRunDetails(undefined)}>
                  Close run details
                </button>
                <NativeRunEvidence
                  workspace={{
                    workspace_id: initial.workspace_id,
                    session_id: sessionId,
                    workspace_name: workspaceName,
                    available: true,
                    reason: null,
                  }}
                  path={process.source_path}
                  run={runDetails}
                  call={readEvidence}
                />
              </section>
            ) : undefined
          }
          sessionId={sessionId}
          workspaceName={workspaceName}
          title={
            process.source_digest === accepted.storage_digest
              ? (recoveryWorkflowSourceTitle(accepted.source) ?? accepted.path)
              : process.source_path
          }
          description={
            process.source_digest === accepted.storage_digest
              ? recoveryWorkflowSourceSummary(accepted.source)?.purpose
              : undefined
          }
          runId={run}
          theme={theme}
          onDirty={workingChange}
          onOpenWorkflow={openEditor}
          onRunAttached={setRun}
          onPrepareAnother={async () => {
            if (!(await openWorking())) return;
            setRun(undefined);
            setRunDetails(undefined);
            setNavigation(undefined);
            setWorkingGeneration((value) => value + 1);
          }}
        />
      )}
    </div>
  );
}
