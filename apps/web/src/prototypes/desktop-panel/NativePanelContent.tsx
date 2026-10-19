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
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { recoveryWorkflowSourceTitle } from "../workflow-recovery/recovery-authoring";
import { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import { NativeProcessPanel } from "./NativeProcessPanel";
import { NativeRunEvidence } from "./NativeRunEvidence";
import type { HomeCall } from "./NativeHomePanel";
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
  workingViewEnabled,
  onDirty,
  theme,
  transferCall,
  onOpenTransferred,
  onAcceptedSource,
  readEvidence,
}: {
  readonly initial: WorkspaceWorkflowSourceDocument;
  readonly sourceClient: NativeSourceClient;
  readonly draftClient?: NativeEditorDraftClient;
  readonly call: NativeProcessCall;
  readonly sessionId: string;
  readonly workspaceName: string;
  readonly initialProcess?: ProcessRef;
  readonly initialRunId?: string;
  readonly workingViewEnabled: boolean;
  readonly readEvidence?: HomeCall;
  readonly onDirty: (pending: boolean) => void;
  readonly theme?: "dark" | "light";
  readonly transferCall?: NativeTransferCall;
  readonly onOpenTransferred?: (path: string) => Promise<void>;
  readonly onAcceptedSource?: (
    document: WorkspaceWorkflowSourceDocument,
  ) => void;
}) {
  const [accepted, setAccepted] = useState(initial);
  const [view, setView] = useState<"editor" | "working">(
    initialProcess && workingViewEnabled ? "working" : "editor",
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
  const [transferDocument, setTransferDocument] =
    useState<WorkspaceWorkflowSourceDocument | null>(null);
  const [openingTransfer, setOpeningTransfer] = useState(false);
  const [navigation, setNavigation] = useState<ProcessNavigationRequest>();
  const [runDetails, setRunDetails] = useState<{
    run_id: string;
    source_digest: string;
  }>();
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
          correction:
            "Inspect the recorded result in Run and results or Files.",
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
    if (sourceDirty || workingDirty || transferPending) return;
    try {
      const stored = await sourceClient.read();
      if (stored.storage_digest !== accepted.storage_digest) {
        setNotice(
          "The saved workflow changed. Compare or reload it before preparing another run.",
        );
        return;
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
    } catch {
      setNotice(
        "Wright could not read the accepted workflow. Your draft is kept.",
      );
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
        <NativeWorkflowPanel
          initial={initial}
          client={sourceClient}
          draftClient={draftClient}
          navigation={navigation}
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
      </div>
      {view === "working" && workingViewEnabled && (
        <NativeProcessPanel
          key={`${process.source_digest}:${workingGeneration}`}
          {...native}
          canNavigate
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
          runId={run}
          theme={theme}
          onDirty={workingChange}
          onOpenWorkflow={openEditor}
          onRunAttached={setRun}
          onPrepareAnother={() => {
            setRun(undefined);
            setWorkingGeneration((value) => value + 1);
          }}
        />
      )}
    </div>
  );
}
