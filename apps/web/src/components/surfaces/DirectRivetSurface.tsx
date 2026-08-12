import { useCallback, useEffect, useRef, useState } from "react";

import {
  BookOpenIcon,
  CloseIcon,
  OpenExternalIcon,
  PlayIcon,
  PlusIcon,
  SaveIcon,
  SearchIcon,
} from "../common/Icons";
import {
  workspaceService,
  type RivetWorkflowDocument,
  type RivetWorkflowRun,
  type RivetWorkflowTemplate,
} from "../../services/workspace-service";
import { directRivetCanvasFrameUrl } from "../../services/rivet-editor";

const requestId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

type RunNotice = {
  readonly tone: "info" | "success" | "error";
  readonly message: string;
};

const outputValuePreview = (value: unknown): string => {
  const unwrapped =
    value &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    "value" in value
      ? (value as { value: unknown }).value
      : value;
  if (typeof unwrapped === "string") return JSON.stringify(unwrapped);
  try {
    const serialized = JSON.stringify(unwrapped);
    return serialized === undefined ? String(unwrapped) : serialized;
  } catch {
    return String(unwrapped);
  }
};

const runOutputPreview = (outputs: Record<string, unknown> | null): string => {
  if (!outputs) return "";
  const preview = Object.entries(outputs)
    .filter(([name]) => name !== "cost")
    .slice(0, 3)
    .map(([name, value]) => `${name}: ${outputValuePreview(value)}`)
    .join(", ");
  return preview.length > 220 ? `${preview.slice(0, 217)}...` : preview;
};

const runSummary = (run: RivetWorkflowRun): string => {
  if (run.state === "succeeded") {
    const duration = run.duration_ms == null ? "" : ` in ${run.duration_ms} ms`;
    const outputs = runOutputPreview(run.outputs);
    return `Run succeeded${duration}.${outputs ? ` Output: ${outputs}` : " No outputs were returned."}`;
  }
  if (run.state === "failed" || run.state === "cancelled") {
    return `Run ${run.state}${run.reason ? `: ${run.reason}` : "."}`;
  }
  return `Run is ${run.state}.`;
};

interface DirectRivetSurfaceProps {
  readonly url: string;
  readonly sessionId: string;
  readonly initialSlug: string;
  readonly onOpenInBrowser: () => void;
  readonly onWorkflowLoaded?: (workflow: RivetWorkflowDocument) => void;
  readonly onEditorReady?: () => void;
  readonly onEditorUnavailable?: (reason: string) => void;
  readonly externalRevisionToken?: string | null;
}

export function DirectRivetSurface({
  url,
  sessionId,
  initialSlug,
  onOpenInBrowser,
  onWorkflowLoaded,
  onEditorReady,
  onEditorUnavailable,
  externalRevisionToken = null,
}: DirectRivetSurfaceProps) {
  const iframeRef = useRef<HTMLIFrameElement | null>(null);
  const readyRef = useRef(false);
  const postOpenStatusRef = useRef<string | null>(null);
  const onWorkflowLoadedRef = useRef(onWorkflowLoaded);
  const onEditorReadyRef = useRef(onEditorReady);
  const onEditorUnavailableRef = useRef(onEditorUnavailable);
  const lastExternalRevisionTokenRef = useRef<string | null>(null);
  const [document, setDocument] = useState<RivetWorkflowDocument | null>(null);
  const [templates, setTemplates] = useState<RivetWorkflowTemplate[]>([]);
  const [templatePickerOpen, setTemplatePickerOpen] = useState(false);
  const [runPanelOpen, setRunPanelOpen] = useState(false);
  const [runGraph, setRunGraph] = useState("");
  const [runInputs, setRunInputs] = useState("{}");
  const [activeRun, setActiveRun] = useState<RivetWorkflowRun | null>(null);
  const [runNotice, setRunNotice] = useState<RunNotice | null>(null);
  const [status, setStatus] = useState("Loading Rivet 2 graph canvas...");
  const [busy, setBusy] = useState(false);
  const [editorReady, setEditorReady] = useState(false);
  const [aiStatus, setAiStatus] = useState<
    "checking" | "available" | "unavailable"
  >("checking");

  const targetOrigin = new URL(url).origin;
  const frameUrl = directRivetCanvasFrameUrl(url, window.location.origin);

  useEffect(() => {
    onWorkflowLoadedRef.current = onWorkflowLoaded;
  }, [onWorkflowLoaded]);

  useEffect(() => {
    onEditorReadyRef.current = onEditorReady;
    onEditorUnavailableRef.current = onEditorUnavailable;
  }, [onEditorReady, onEditorUnavailable]);

  const bridgeRequest = useCallback(
    async <T extends Record<string, unknown>>(
      request: Record<string, unknown>,
      responseType: string,
    ): Promise<T> => {
      if (!readyRef.current)
        throw new Error("Rivet 2 graph canvas is not ready.");
      const frameWindow = iframeRef.current?.contentWindow;
      if (!frameWindow) throw new Error("Rivet 2 graph canvas is unavailable.");
      const id = String(request.requestId);
      return await new Promise<T>((resolve, reject) => {
        let timeout = 0;
        const cleanup = () => {
          window.clearTimeout(timeout);
          window.removeEventListener("message", onMessage);
        };
        const onMessage = (event: MessageEvent) => {
          if (event.source !== frameWindow || event.origin !== targetOrigin)
            return;
          const message = event.data || {};
          if (message.requestId !== id) return;
          if (message.type === "wright-rivet:error") {
            cleanup();
            reject(
              new Error(
                typeof message.message === "string"
                  ? message.message
                  : "Rivet 2 graph canvas rejected the request.",
              ),
            );
            return;
          }
          if (message.type === responseType) {
            cleanup();
            resolve(message as T);
          }
        };
        timeout = window.setTimeout(() => {
          cleanup();
          reject(new Error("Rivet 2 graph canvas did not respond in time."));
        }, 5000);
        window.addEventListener("message", onMessage);
        frameWindow.postMessage(request, targetOrigin);
      });
    },
    [targetOrigin],
  );

  const sendProjectToFrame = useCallback(
    async (workflow: RivetWorkflowDocument) => {
      const id = requestId();
      await bridgeRequest(
        {
          type: "wright-rivet:set-project",
          requestId: id,
          project: workflow.project,
          path: `${workflow.slug}.rivet-project`,
        },
        "wright-rivet:project-set",
      );
    },
    [bridgeRequest],
  );

  const requestProjectFromFrame = useCallback(async (): Promise<string> => {
    const id = requestId();
    const message = await bridgeRequest<{ project?: unknown }>(
      { type: "wright-rivet:get-project", requestId: id },
      "wright-rivet:project",
    );
    if (typeof message.project !== "string") {
      throw new Error("Rivet 2 returned an invalid workflow project.");
    }
    return message.project;
  }, [bridgeRequest]);

  const refreshCatalog = useCallback(async () => {
    return await workspaceService.listRivetWorkflowOperations(sessionId);
  }, [sessionId]);

  const openWorkflow = useCallback(
    async (
      slug: string,
      knownCatalog?: Awaited<ReturnType<typeof refreshCatalog>>,
    ) => {
      setBusy(true);
      try {
        const [loaded, catalog] = await Promise.all([
          workspaceService.readRivetWorkflow(sessionId, slug),
          knownCatalog ? Promise.resolve(knownCatalog) : refreshCatalog(),
        ]);
        const operation = catalog.find(
          (workflow) => workflow.slug === loaded.slug,
        );
        const hydrated = operation
          ? {
              ...loaded,
              review_state: operation.review_state,
              reviewer: operation.reviewer,
              reviewed_at: operation.reviewed_at,
            }
          : loaded;
        setDocument(hydrated);
        setActiveRun(null);
        setRunNotice(null);
        setRunPanelOpen(false);
        if (hydrated.slug !== initialSlug) {
          onWorkflowLoadedRef.current?.(hydrated);
        }
        setStatus(
          readyRef.current
            ? "Opening workflow on the graph canvas..."
            : "Waiting for the graph canvas to open the workflow...",
        );
      } catch (error) {
        setStatus(
          error instanceof Error
            ? error.message
            : "Unable to open Rivet workflow.",
        );
      } finally {
        setBusy(false);
      }
    },
    [initialSlug, refreshCatalog, sessionId],
  );

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      const frameWindow = iframeRef.current?.contentWindow;
      if (
        !frameWindow ||
        event.source !== frameWindow ||
        event.origin !== targetOrigin
      ) {
        return;
      }
      const message = event.data || {};
      if (message.type === "wright-rivet:ready") {
        readyRef.current = true;
        setEditorReady(true);
        setStatus("Rivet 2 graph canvas is ready.");
        onEditorReadyRef.current?.();
      } else if (message.type === "wright-rivet:ai-status") {
        const available = message.available === true;
        setAiStatus(available ? "available" : "unavailable");
        if (!available) {
          setStatus(
            "Rivet AI is unavailable; the graph canvas remains usable.",
          );
        }
      } else if (
        message.type === "wright-rivet:error" &&
        typeof message.requestId !== "string"
      ) {
        setStatus(
          typeof message.message === "string"
            ? message.message
            : "Rivet 2 graph canvas reported an error.",
        );
      }
    };
    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, [targetOrigin]);

  useEffect(() => {
    if (!editorReady || !document) return;
    let cancelled = false;
    void sendProjectToFrame(document)
      .then(() => {
        if (!cancelled) {
          setStatus(
            postOpenStatusRef.current || "Workflow opened from this workspace.",
          );
          postOpenStatusRef.current = null;
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setStatus(
            error instanceof Error
              ? error.message
              : "Unable to place the workflow on the Rivet 2 canvas.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [document, editorReady, sendProjectToFrame]);

  useEffect(() => {
    if (
      !externalRevisionToken ||
      !document ||
      lastExternalRevisionTokenRef.current === externalRevisionToken
    ) {
      return;
    }
    lastExternalRevisionTokenRef.current = externalRevisionToken;
    let cancelled = false;
    void workspaceService
      .readRivetWorkflow(sessionId, document.slug)
      .then((loaded) => {
        if (cancelled) return;
        if (
          loaded.revision !== document.revision ||
          loaded.etag !== document.etag
        ) {
          postOpenStatusRef.current = `Workflow updated by Wright AI at revision ${loaded.revision}.`;
          setDocument(loaded);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setStatus(
            error instanceof Error
              ? error.message
              : "Unable to refresh the Rivet workflow after Wright AI changed it.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, [document, externalRevisionToken, sessionId]);

  const createWorkflow = async () => {
    setBusy(true);
    try {
      const created =
        await workspaceService.createBlankRivetWorkflow(sessionId);
      await refreshCatalog();
      await openWorkflow(created.slug);
      setStatus("Blank workflow created in this workspace.");
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

  const createWorkflowFromTemplate = async (
    template: RivetWorkflowTemplate,
  ) => {
    setBusy(true);
    try {
      const created = await workspaceService.createRivetWorkflowFromTemplate(
        sessionId,
        template,
      );
      setTemplatePickerOpen(false);
      await openWorkflow(created.slug);
      setStatus(`Workflow created from ${template.title}.`);
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : "Unable to create a workflow from this template.",
      );
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    void workspaceService
      .listRivetWorkflowTemplates()
      .then((availableTemplates) => {
        if (!cancelled) setTemplates(availableTemplates);
      })
      .catch((error) => {
        if (!cancelled) {
          setStatus(
            error instanceof Error
              ? error.message
              : "Rivet templates are unavailable.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

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
          await openWorkflow(slug, catalog);
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

  useEffect(() => {
    const runId = activeRun?.run_id;
    const runState = activeRun?.state;
    if (
      !runId ||
      !runState ||
      !["queued", "running", "cancelling"].includes(runState)
    ) {
      return;
    }
    let cancelled = false;
    let timer = 0;
    const poll = async () => {
      try {
        const [run, history] = await Promise.all([
          workspaceService.getRivetWorkflowRun(sessionId, runId),
          workspaceService.getRivetWorkflowHistory(sessionId, runId),
        ]);
        if (cancelled) return;
        setActiveRun(run);
        const latest = history.at(-1);
        const phase =
          typeof latest?.payload?.phase === "string"
            ? latest.payload.phase.replaceAll("-", " ")
            : null;
        setStatus(
          run.state === "succeeded"
            ? `Run ${run.run_id} succeeded.`
            : run.state === "failed" || run.state === "cancelled"
              ? `Run ${run.run_id} ${run.state}${run.reason ? `: ${run.reason}` : "."}`
              : phase
                ? `Run ${run.run_id}: ${phase}.`
                : `Run ${run.run_id} is ${run.state}.`,
        );
        setRunNotice({
          tone:
            run.state === "succeeded"
              ? "success"
              : run.state === "failed" || run.state === "cancelled"
                ? "error"
                : "info",
          message: runSummary(run),
        });
        if (["queued", "running", "cancelling"].includes(run.state)) {
          timer = window.setTimeout(poll, 250);
        }
      } catch (error) {
        if (!cancelled) {
          setStatus(
            error instanceof Error
              ? error.message
              : "Workflow run status is unavailable.",
          );
          setRunNotice({
            tone: "error",
            message:
              error instanceof Error
                ? error.message
                : "Workflow run status is unavailable.",
          });
        }
      }
    };
    timer = window.setTimeout(poll, 50);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [activeRun?.run_id, activeRun?.state, sessionId]);

  const saveWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const project = await requestProjectFromFrame();
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
      postOpenStatusRef.current = `Workflow saved at revision ${reloaded.revision}.`;
      setDocument(reloaded);
      setRunNotice({
        tone: "info",
        message: `Revision ${reloaded.revision} was saved and now needs approval before it can run.`,
      });
      if (reloaded.slug !== initialSlug) {
        onWorkflowLoadedRef.current?.(reloaded);
      }
      await refreshCatalog();
      setStatus(`Workflow saved at revision ${reloaded.revision}.`);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to save workflow.";
      setStatus(message);
      setRunNotice({ tone: "error", message });
    } finally {
      setBusy(false);
    }
  };

  const approveWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const currentProject = await requestProjectFromFrame();
      if (currentProject !== document.project) {
        const message =
          "Save the current canvas changes before approving this workflow.";
        setStatus(message);
        setRunNotice({ tone: "error", message });
        return;
      }
      const reviewed = await workspaceService.reviewRivetWorkflow(
        sessionId,
        document.slug,
        "approved",
        "local-user",
      );
      setDocument((current) =>
        current &&
        current.slug === reviewed.slug &&
        current.revision === reviewed.revision
          ? { ...current, ...reviewed }
          : current,
      );
      const message = `Revision ${reviewed.revision} approved. It is ready to run.`;
      setStatus(message);
      setRunNotice({ tone: "success", message });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Unable to approve this workflow revision.";
      setStatus(message);
      setRunNotice({ tone: "error", message });
    } finally {
      setBusy(false);
    }
  };

  const runWorkflow = async () => {
    if (!document) return;
    setBusy(true);
    try {
      const currentProject = await requestProjectFromFrame();
      if (currentProject !== document.project) {
        const message =
          "Save the current canvas changes before running this workflow.";
        setStatus(message);
        setRunNotice({ tone: "error", message });
        return;
      }
      const parsedInputs = JSON.parse(runInputs);
      if (
        !parsedInputs ||
        typeof parsedInputs !== "object" ||
        Array.isArray(parsedInputs)
      ) {
        throw new Error("Run inputs must be a JSON object.");
      }
      const run = await workspaceService.runRivetWorkflow(
        sessionId,
        document.slug,
        {
          expectedRevision: document.revision,
          expectedDigest: document.etag,
          graph: runGraph.trim() || undefined,
          inputs: parsedInputs,
        },
      );
      setActiveRun(run);
      setRunPanelOpen(false);
      setStatus(`Run ${run.run_id} is ${run.state}.`);
      setRunNotice({ tone: "info", message: runSummary(run) });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to run workflow.";
      setStatus(message);
      setRunNotice({ tone: "error", message });
    } finally {
      setBusy(false);
    }
  };

  const cancelRun = async () => {
    if (!activeRun) return;
    setBusy(true);
    try {
      const cancelled = await workspaceService.cancelRivetWorkflow(
        sessionId,
        activeRun,
      );
      setActiveRun(cancelled);
      setStatus(`Run ${cancelled.run_id} is ${cancelled.state}.`);
      setRunNotice({ tone: "error", message: runSummary(cancelled) });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Workflow cancellation failed.";
      setStatus(message);
      setRunNotice({ tone: "error", message });
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
      setStatus(
        error instanceof Error ? error.message : "Unable to lint workflow.",
      );
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
        data-testid="direct-rivet-toolbar"
        style={{
          display: "flex",
          alignItems: "center",
          borderBottom: "1px solid var(--color-border)",
          background:
            "var(--color-surface-elevated, var(--color-surface, #131b2e))",
          minHeight: 44,
          padding: "0 8px",
          position: "relative",
        }}
      >
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
        <div style={{ position: "relative" }}>
          <button
            type="button"
            data-testid="direct-rivet-template-picker"
            aria-label="New Rivet workflow from template"
            title="New Rivet workflow from template"
            aria-expanded={templatePickerOpen}
            disabled={busy}
            onClick={() => setTemplatePickerOpen((open) => !open)}
            style={iconButtonStyle}
          >
            <BookOpenIcon size={16} />
          </button>
          {templatePickerOpen && (
            <div
              role="dialog"
              aria-label="Rivet workflow templates"
              data-testid="direct-rivet-template-menu"
              onKeyDown={(event) => {
                if (event.key === "Escape") setTemplatePickerOpen(false);
              }}
              style={{
                position: "absolute",
                top: 38,
                left: 0,
                zIndex: 20,
                width: 340,
                maxHeight: 420,
                overflowY: "auto",
                padding: 8,
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md, 6px)",
                background: "var(--color-surface, #131b2e)",
                opacity: 1,
                boxShadow: "var(--shadow-lg, 0 12px 32px rgba(0, 0, 0, 0.35))",
              }}
            >
              {templates.length === 0 ? (
                <p
                  role="status"
                  style={{ margin: 8, color: "var(--color-secondary)" }}
                >
                  No workflow templates are available.
                </p>
              ) : (
                templates.map((template) => (
                  <button
                    key={template.template_id}
                    type="button"
                    data-testid={`direct-rivet-template-${template.template_id}`}
                    disabled={busy}
                    onClick={() => void createWorkflowFromTemplate(template)}
                    style={{
                      display: "block",
                      width: "100%",
                      padding: "10px 12px",
                      border: 0,
                      borderRadius: "var(--radius-sm, 4px)",
                      background: "transparent",
                      color: "var(--color-primary)",
                      textAlign: "left",
                      cursor: "pointer",
                    }}
                  >
                    <span style={{ display: "block", fontWeight: 600 }}>
                      {template.title}
                    </span>
                    <span
                      style={{
                        display: "block",
                        marginTop: 2,
                        color: "var(--color-secondary)",
                        fontSize: "0.72rem",
                        lineHeight: 1.35,
                      }}
                    >
                      {template.description}
                    </span>
                    {template.requirements.length > 0 && (
                      <span
                        style={{
                          display: "block",
                          marginTop: 5,
                          color: "var(--color-warning, #f59e0b)",
                          fontSize: "0.66rem",
                        }}
                      >
                        Requires:{" "}
                        {template.requirements.join(", ").replaceAll("-", " ")}
                      </span>
                    )}
                  </button>
                ))
              )}
            </div>
          )}
        </div>
        <button
          type="button"
          data-testid="direct-rivet-save-workspace"
          aria-label="Save Rivet workflow to workspace"
          title="Save Rivet workflow to workspace"
          disabled={busy || !document || !editorReady}
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
        {activeRun &&
        ["queued", "running", "cancelling"].includes(activeRun.state) ? (
          <button
            type="button"
            data-testid="direct-rivet-cancel"
            aria-label="Cancel Rivet workflow run"
            title="Cancel Rivet workflow run"
            disabled={busy || activeRun.state === "cancelling"}
            onClick={() => void cancelRun()}
            style={iconButtonStyle}
          >
            <CloseIcon size={16} />
          </button>
        ) : (
          <button
            type="button"
            data-testid="direct-rivet-run"
            aria-label="Run Rivet workflow"
            title="Run Rivet workflow"
            aria-expanded={runPanelOpen}
            disabled={busy || !document || !editorReady}
            onClick={() => setRunPanelOpen((open) => !open)}
            style={iconButtonStyle}
          >
            <PlayIcon size={16} />
          </button>
        )}
        {runPanelOpen && document && (
          <div
            role="dialog"
            aria-label="Run Rivet workflow"
            data-testid="direct-rivet-run-panel"
            style={{
              position: "absolute",
              top: 40,
              left: 108,
              zIndex: 20,
              width: 320,
              padding: 10,
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md, 6px)",
              background:
                "var(--color-surface-elevated, var(--color-surface, #131b2e))",
              color: "var(--color-primary, #f1f5f9)",
              opacity: 1,
              boxShadow: "var(--shadow-lg, 0 12px 32px rgba(0, 0, 0, 0.35))",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 8,
                marginBottom: 10,
              }}
            >
              <strong style={{ fontSize: "0.8rem" }}>Run Rivet workflow</strong>
              <span
                data-testid="direct-rivet-review-state"
                style={{
                  borderRadius: 999,
                  padding: "2px 7px",
                  background:
                    document.review_state === "approved"
                      ? "rgba(16, 185, 129, 0.16)"
                      : "rgba(245, 158, 11, 0.16)",
                  color:
                    document.review_state === "approved"
                      ? "var(--color-success, #10b981)"
                      : "var(--color-warning, #f59e0b)",
                  fontSize: "0.66rem",
                  fontWeight: 600,
                }}
              >
                {document.review_state === "approved"
                  ? `Revision ${document.revision} approved`
                  : `Revision ${document.revision} needs approval`}
              </span>
            </div>
            {document.review_state !== "approved" && (
              <p
                style={{
                  margin: "0 0 10px",
                  color: "var(--color-text-muted, #aab3c5)",
                  fontSize: "0.7rem",
                  lineHeight: 1.4,
                }}
              >
                Review and approve this saved revision before running it. Saving
                later changes will require a new approval.
              </p>
            )}
            <label style={{ display: "block", fontSize: "0.72rem" }}>
              Graph (blank uses project main graph)
              <input
                data-testid="direct-rivet-run-graph"
                value={runGraph}
                onChange={(event) => setRunGraph(event.target.value)}
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  marginTop: 4,
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-sm, 4px)",
                  background: "var(--color-surface-subtle, #0d1220)",
                  color: "var(--color-primary, #f1f5f9)",
                  padding: "6px 8px",
                }}
              />
            </label>
            <label
              style={{ display: "block", marginTop: 8, fontSize: "0.72rem" }}
            >
              Inputs (JSON object; omitted values use graph defaults)
              <textarea
                data-testid="direct-rivet-run-inputs"
                value={runInputs}
                rows={3}
                onChange={(event) => setRunInputs(event.target.value)}
                style={{
                  boxSizing: "border-box",
                  width: "100%",
                  marginTop: 4,
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-sm, 4px)",
                  background: "var(--color-surface-subtle, #0d1220)",
                  color: "var(--color-primary, #f1f5f9)",
                  padding: "6px 8px",
                  resize: "vertical",
                }}
              />
            </label>
            {document.review_state !== "approved" && (
              <button
                type="button"
                data-testid="direct-rivet-run-approve"
                disabled={busy}
                onClick={() => void approveWorkflow()}
                style={{ marginTop: 8, marginRight: 8 }}
              >
                Approve revision {document.revision}
              </button>
            )}
            <button
              type="button"
              data-testid="direct-rivet-run-start"
              disabled={busy || document.review_state !== "approved"}
              onClick={() => void runWorkflow()}
              style={{ marginTop: 8 }}
            >
              Run revision {document.revision}
            </button>
          </div>
        )}
        {activeRun && (
          <span
            data-testid="direct-rivet-run-result"
            title={
              activeRun.outputs
                ? JSON.stringify(activeRun.outputs)
                : activeRun.reason || `Run ${activeRun.state}`
            }
            style={{
              maxWidth: 360,
              marginLeft: 6,
              overflow: "hidden",
              color: "var(--color-secondary)",
              fontSize: "0.68rem",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {activeRun.state}
            {activeRun.duration_ms != null
              ? ` · ${activeRun.duration_ms} ms`
              : ""}
            {runOutputPreview(activeRun.outputs)
              ? ` · ${runOutputPreview(activeRun.outputs)}`
              : ""}
          </span>
        )}
        <div style={{ flex: 1 }} />
        <span
          data-testid="direct-rivet-ai-status"
          title={
            aiStatus === "available"
              ? "Rivet AI is connected through Hermes"
              : aiStatus === "unavailable"
                ? "Rivet AI is unavailable"
                : "Checking Rivet AI"
          }
          aria-label={
            aiStatus === "available"
              ? "Rivet AI connected"
              : aiStatus === "unavailable"
                ? "Rivet AI unavailable"
                : "Checking Rivet AI"
          }
          style={{
            width: 8,
            height: 8,
            marginRight: 8,
            borderRadius: "50%",
            background:
              aiStatus === "available"
                ? "var(--color-success, #10b981)"
                : aiStatus === "unavailable"
                  ? "var(--color-warning, #f59e0b)"
                  : "var(--color-secondary)",
          }}
        />
        <span
          data-testid="direct-rivet-status"
          role="status"
          aria-live="polite"
          style={{
            position: "absolute",
            width: 1,
            height: 1,
            padding: 0,
            margin: -1,
            overflow: "hidden",
            clip: "rect(0, 0, 0, 0)",
            whiteSpace: "nowrap",
            border: 0,
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
      {runNotice && (
        <div
          data-testid="direct-rivet-run-feedback"
          role={runNotice.tone === "error" ? "alert" : "status"}
          aria-live={runNotice.tone === "error" ? "assertive" : "polite"}
          style={{
            padding: "8px 12px",
            borderBottom: "1px solid var(--color-border)",
            background:
              runNotice.tone === "success"
                ? "rgba(16, 185, 129, 0.14)"
                : runNotice.tone === "error"
                  ? "rgba(248, 113, 113, 0.14)"
                  : "rgba(56, 189, 248, 0.12)",
            color:
              runNotice.tone === "success"
                ? "var(--color-success, #10b981)"
                : runNotice.tone === "error"
                  ? "var(--color-error, #f87171)"
                  : "var(--color-secondary, #38bdf8)",
            fontSize: "0.75rem",
            fontWeight: 600,
            lineHeight: 1.4,
          }}
        >
          {runNotice.message}
        </div>
      )}
      <iframe
        ref={iframeRef}
        title="Rivet graph canvas"
        src={frameUrl}
        onLoad={() => {
          readyRef.current = false;
          setEditorReady(false);
          setAiStatus("checking");
          try {
            const body = iframeRef.current?.contentDocument?.body;
            const visibleText =
              body?.childElementCount === 0
                ? body.textContent?.trim()
                : body?.childElementCount === 1 &&
                    body.firstElementChild?.tagName === "PRE"
                  ? body.firstElementChild.textContent?.trim()
                  : "";
            const previewFailure = visibleText?.match(
              /SURFACE_PREVIEW_(?:UNAUTHORIZED|GONE)|Preview link expired/i,
            )?.[0];
            if (previewFailure) {
              setStatus("Rivet preview authorization expired. Reconnecting...");
              onEditorUnavailableRef.current?.(previewFailure);
              return;
            }
          } catch {
            // Production previews are cross-origin; readiness is confirmed by
            // the exact-origin bridge message instead of DOM inspection.
          }
          setStatus("Loading Rivet 2 graph canvas...");
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
