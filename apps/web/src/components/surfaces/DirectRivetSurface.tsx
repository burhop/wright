import { useCallback, useEffect, useRef, useState } from "react";

import {
  FolderIcon,
  OpenExternalIcon,
  PlayIcon,
  PlusIcon,
  SaveIcon,
  SearchIcon,
} from "../common/Icons";
import {
  workspaceService,
  type RivetWorkflowDocument,
  type RivetWorkflowOperation,
} from "../../services/workspace-service";

const requestId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

interface DirectRivetSurfaceProps {
  readonly url: string;
  readonly sessionId: string;
  readonly initialSlug: string;
  readonly onOpenInBrowser: () => void;
  readonly onWorkflowLoaded?: (workflow: RivetWorkflowDocument) => void;
}

export function DirectRivetSurface({
  url,
  sessionId,
  initialSlug,
  onOpenInBrowser,
  onWorkflowLoaded,
}: DirectRivetSurfaceProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const [workflows, setWorkflows] = useState<RivetWorkflowOperation[]>([]);
  const [selectedSlug, setSelectedSlug] = useState(initialSlug);
  const [document, setDocument] = useState<RivetWorkflowDocument | null>(null);
  const [status, setStatus] = useState("Rivet workspace controls are ready.");
  const [busy, setBusy] = useState(false);

  const targetOrigin = new URL(url).origin;

  const sendProjectToFrame = useCallback(
    (project: string) => {
      iframeRef.current?.contentWindow?.postMessage(
        {
          type: "wright-rivet:set-project",
          requestId: requestId(),
          project,
        },
        targetOrigin,
      );
    },
    [targetOrigin],
  );

  const requestProjectFromFrame = useCallback(async (): Promise<string | null> => {
    const id = requestId();
    return await new Promise((resolve) => {
      let timeout = 0;
      const onMessage = (event: MessageEvent) => {
        if (event.origin !== targetOrigin) return;
        const message = event.data || {};
        if (
          message.type === "wright-rivet:project" &&
          message.requestId === id
        ) {
          window.clearTimeout(timeout);
          window.removeEventListener("message", onMessage);
          resolve(typeof message.project === "string" ? message.project : null);
        }
      };
      timeout = window.setTimeout(() => {
        window.removeEventListener("message", onMessage);
        resolve(null);
      }, 800);
      window.addEventListener("message", onMessage);
      iframeRef.current?.contentWindow?.postMessage(
        { type: "wright-rivet:get-project", requestId: id },
        targetOrigin,
      );
    });
  }, [targetOrigin]);

  const refreshCatalog = useCallback(async () => {
    const catalog = await workspaceService.listRivetWorkflowOperations(sessionId);
    setWorkflows(catalog);
    return catalog;
  }, [sessionId]);

  const openWorkflow = useCallback(
    async (slug: string) => {
      setBusy(true);
      try {
        const loaded = await workspaceService.readRivetWorkflow(sessionId, slug);
        setSelectedSlug(loaded.slug);
        setDocument(loaded);
        onWorkflowLoaded?.(loaded);
        sendProjectToFrame(loaded.project);
        setStatus(`${loaded.slug}.rivet-project opened from this workspace.`);
      } catch (error) {
        setStatus(
          error instanceof Error ? error.message : "Unable to open Rivet workflow.",
        );
      } finally {
        setBusy(false);
      }
    },
    [onWorkflowLoaded, sendProjectToFrame, sessionId],
  );

  const createWorkflow = async () => {
    setBusy(true);
    try {
      const created = await workspaceService.createBlankRivetWorkflow(sessionId);
      await refreshCatalog();
      await openWorkflow(created.slug);
      setStatus(`${created.slug}.rivet-project created in this workspace.`);
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Unable to create Rivet workflow.",
      );
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const catalog = await refreshCatalog();
        const slug =
          catalog.find((workflow) => workflow.slug === initialSlug)?.slug ||
          catalog[0]?.slug ||
          initialSlug;
        if (!cancelled) {
          await openWorkflow(slug);
        }
      } catch (error) {
        if (!cancelled) {
          setStatus(
            error instanceof Error
              ? error.message
              : "Rivet workflows are unavailable.",
          );
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [initialSlug, openWorkflow, refreshCatalog]);

  const saveWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const project = (await requestProjectFromFrame()) || document.project;
      const saved = await workspaceService.saveRivetWorkflow(
        sessionId,
        document.slug,
        document.revision,
        project,
        document.datasets,
      );
      const reloaded = await workspaceService.readRivetWorkflow(
        sessionId,
        saved.slug,
      );
      setDocument(reloaded);
      onWorkflowLoaded?.(reloaded);
      await refreshCatalog();
      setStatus(`Saved ${reloaded.slug}.rivet-project revision ${reloaded.revision}.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to save workflow.");
    } finally {
      setBusy(false);
    }
  };

  const runWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const run = await workspaceService.runRivetWorkflow(sessionId, document.slug);
      setStatus(`Run ${run.run_id} is ${run.state}.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to run workflow.");
    } finally {
      setBusy(false);
    }
  };

  const lintWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const result = await workspaceService.lintRivetWorkflowGraph(
        sessionId,
        document.slug,
      );
      setStatus(
        result.issues.length
          ? `${result.issues.length} graph issue(s) found.`
          : "Graph lint passed.",
      );
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Unable to lint workflow.");
    } finally {
      setBusy(false);
    }
  };

  const iconButtonStyle = {
    width: 32,
    height: 32,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    border: "1px solid transparent",
    borderRadius: "var(--radius-sm, 4px)",
    background: "transparent",
    color: "var(--color-secondary)",
    cursor: "pointer",
  };

  return (
    <div
      data-testid="direct-rivet-surface"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        background: "var(--color-neutral)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid var(--color-border)",
          background: "var(--color-surface-elevated)",
          minHeight: 44,
        }}
      >
        <strong
          style={{
            padding: "10px 14px",
            color: "var(--color-primary)",
            fontWeight: 600,
          }}
        >
          {document ? `${document.slug}.rivet-project` : "Rivet"}
        </strong>
        <select
          data-testid="direct-rivet-workflow-select"
          value={selectedSlug}
          disabled={busy || workflows.length === 0}
          onChange={(event) => setSelectedSlug(event.target.value)}
          style={{
            minWidth: 120,
            height: 30,
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm, 4px)",
            color: "var(--color-primary)",
            fontSize: "0.75rem",
          }}
          aria-label="Rivet workflow"
        >
          {workflows.map((workflow) => (
            <option key={workflow.workflow_id} value={workflow.slug}>
              {workflow.slug}
            </option>
          ))}
        </select>
        <button
          type="button"
          data-testid="direct-rivet-new-workspace"
          aria-label="New blank Rivet workflow"
          title="New blank Rivet workflow"
          disabled={busy}
          onClick={() => void createWorkflow()}
          style={iconButtonStyle}
        >
          <PlusIcon size={16} />
        </button>
        <button
          type="button"
          data-testid="direct-rivet-open-workspace"
          aria-label="Open Rivet workflow from workspace"
          title="Open Rivet workflow from workspace"
          disabled={busy || !selectedSlug}
          onClick={() => void openWorkflow(selectedSlug)}
          style={iconButtonStyle}
        >
          <FolderIcon size={16} />
        </button>
        <button
          type="button"
          data-testid="direct-rivet-save-workspace"
          aria-label="Save Rivet workflow to workspace"
          title="Save Rivet workflow to workspace"
          disabled={busy || !document}
          onClick={() => void saveWorkflow()}
          style={iconButtonStyle}
        >
          <SaveIcon size={16} />
        </button>
        <button
          type="button"
          data-testid="direct-rivet-lint"
          aria-label="Lint Rivet graph"
          title="Lint Rivet graph"
          disabled={busy || !document}
          onClick={() => void lintWorkflow()}
          style={iconButtonStyle}
        >
          <SearchIcon size={16} />
        </button>
        <button
          type="button"
          data-testid="direct-rivet-run"
          aria-label="Run Rivet workflow"
          title="Run Rivet workflow"
          disabled={busy || !document}
          onClick={() => void runWorkflow()}
          style={iconButtonStyle}
        >
          <PlayIcon size={16} />
        </button>
        <div style={{ flex: 1 }} />
        <span
          data-testid="direct-rivet-status"
          style={{
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            maxWidth: "40%",
            color: "var(--color-secondary)",
            fontSize: "0.72rem",
          }}
        >
          {status}
        </span>
        <button
          type="button"
          data-testid="direct-rivet-open-browser"
          aria-label="Open Rivet in browser"
          title="Open Rivet in browser"
          onClick={onOpenInBrowser}
          style={{
            width: 32,
            height: 32,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            marginRight: 8,
            border: "1px solid transparent",
            borderRadius: "var(--radius-sm, 4px)",
            background: "transparent",
            color: "var(--color-secondary)",
            cursor: "pointer",
          }}
        >
          <OpenExternalIcon size={16} />
        </button>
      </div>
      <iframe
        ref={iframeRef}
        title="Rivet"
        src={url}
        onLoad={() => {
          if (document) sendProjectToFrame(document.project);
        }}
        style={{
          flex: 1,
          width: "100%",
          minHeight: 0,
          border: 0,
          background: "#fff",
        }}
      />
    </div>
  );
}
