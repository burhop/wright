import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FileTree from "../common/FileTree";
import DiffViewer from "../common/DiffViewer";
import EditorTabs from "./EditorTabs";
import ViewerInspector from "./ViewerInspector";
import {
  WorkspaceActivityBar,
  type WorkspaceSidebarId,
} from "./WorkspaceActivityBar";
import { useChat } from "../../store/sessions";
import {
  dedupeEditorTabs,
  normalizeEditorTabPath,
  useViewerPanel,
} from "../../store/viewer";
import { viewerRegistry } from "../../services/viewer-panel/registry";
import { PanelHostImpl } from "../../services/viewer-panel/panel-host";
import type { FileDescriptor } from "../../services/viewer-panel/types";
import {
  workspaceService,
  type WorkspaceNode,
  type WorkspaceInfo,
  MergeConflictError,
} from "../../services/workspace-service";
import {
  agentService,
  type HermesModelOptionGroup,
} from "../../services/agent-service";
import useHealthStatus from "../../hooks/useHealthStatus";
import ChatTranscript from "./ChatTranscript";
import MessageComposer from "./MessageComposer";
import { MaximizeIcon, MinimizeIcon, SearchIcon } from "../common/Icons";
import type { EditorTab } from "../../store/viewer";
import { workspaceSurfacesEnabled } from "../../services/surfaces/feature-flags";
import { rivetWorkflowsTabEnabled } from "../../services/surfaces/feature-flags";
import { ManagedRivetSurface } from "../surfaces/ManagedRivetSurface";
import { DirectBrepSurface } from "../surfaces/DirectBrepSurface";
import { SurfaceWorkspace } from "../surfaces/SurfaceWorkspace";
import { usePersistentSurfaceLayout } from "../../store/surface-layout";
import { WorkspaceLayout } from "../workspace/WorkspaceLayout";
import { PaneSeparator } from "../workspace/PaneSeparator";
import { ResponsivePaneSwitcher } from "../workspace/ResponsivePaneSwitcher";
import { resolveWorkspaceLayout } from "../workspace/workspace-layout";
import {
  SurfaceFocusManager,
  installF6HostRegionCycle,
} from "../../services/surfaces/focus-manager";
import { isBrepToolActivity } from "../../services/brep-panel-activity";
import { workspaceRivetWorkflowSlug } from "../../services/rivet-editor";

const DIRECT_RIVET_TAB_PREFIX = "/.wright/rivet-workflows";
const DIRECT_BREP_TAB_PATH = "/.wright/apps/brep";

function directRivetTabPath(slug: string): string {
  return `${DIRECT_RIVET_TAB_PREFIX}/${slug}/workflow.rivet-project`;
}

function isDirectRivetTab(path: string | null): boolean {
  return normalizeEditorTabPath(path ?? "").startsWith(
    `${DIRECT_RIVET_TAB_PREFIX}/`,
  );
}

function rivetSlugFromTabPath(path: string): string | null {
  const normalized = normalizeEditorTabPath(path);
  if (!isDirectRivetTab(normalized)) return null;
  return (
    normalized.slice(DIRECT_RIVET_TAB_PREFIX.length + 1).split("/")[0] || null
  );
}

function isDirectBrepTab(path: string | null): boolean {
  return normalizeEditorTabPath(path ?? "") === DIRECT_BREP_TAB_PATH;
}

function isVisibleBrepServer(server: {
  name?: string;
  source_url?: string | null;
}): boolean {
  return (
    server.name?.trim().toLowerCase() === "brep mcp" &&
    server.source_url?.toLowerCase().includes("brep-mcp") === true
  );
}

interface CompactMcpServer {
  server_id: string;
  name: string;
  type: string;
  is_active: boolean;
  is_installed: boolean;
  description?: string | null;
  source_url?: string | null;
}

function findFileInTree(
  node: WorkspaceNode,
  targetPath: string,
): WorkspaceNode | null {
  if (node.path === targetPath) {
    return node;
  }
  if (node.children) {
    for (const child of node.children) {
      const found = findFileInTree(child, targetPath);
      if (found) return found;
    }
  }
  return null;
}

interface WorkspacePanelProps {
  workspaceId?: string;
  sessionId?: string;
  workspace?: WorkspaceInfo;
  onSessionChange?: (sessionId: string) => void;
}

function cleanSessionOptionTitle(session: { title?: string | null }): string {
  return typeof session.title === "string" && session.title.trim()
    ? session.title.trim()
    : "Untitled Session";
}

function truncateSessionOptionLabel(title: string): string {
  return title.length > 24 ? `${title.slice(0, 22)}...` : title;
}

function getSessionOptionLabels(
  sessions: Array<{ title?: string | null; sessionId: string }>,
): Map<string, string> {
  const counts = new Map<string, number>();
  const labels = new Map<string, string>();

  for (const session of sessions) {
    const baseTitle = cleanSessionOptionTitle(session);
    const key = baseTitle.toLocaleLowerCase();
    const count = (counts.get(key) || 0) + 1;
    counts.set(key, count);
    const title = count === 1 ? baseTitle : `${baseTitle} (${count})`;
    labels.set(session.sessionId, truncateSessionOptionLabel(title));
  }

  return labels;
}

export function WorkspacePanel({
  workspaceId: _workspaceId,
  sessionId: propSessionId,
  workspace: initialWorkspace,
  onSessionChange,
}: WorkspacePanelProps) {
  const {
    state,
    createSession,
    selectSession,
    sendMessage,
    steerMessage,
    refreshSessions,
    cancelActiveStream,
  } = useChat();
  const navigate = useNavigate();
  const surfacesEnabled = workspaceSurfacesEnabled();
  const workflowsTabEnabled = rivetWorkflowsTabEnabled();

  const [panelWidth, setPanelWidth] = useState<number>(window.innerWidth);
  const containerRef = useRef<HTMLDivElement>(null);
  const [observedContainer, setObservedContainer] =
    useState<HTMLDivElement | null>(null);
  const attachContainerRef = useCallback((node: HTMLDivElement | null) => {
    containerRef.current = node;
    setObservedContainer(node);
  }, []);
  const [workspaceInfo, setWorkspaceInfo] = useState<WorkspaceInfo | null>(
    initialWorkspace ?? null,
  );
  const [workspacePath, setWorkspacePath] = useState<string>(
    initialWorkspace?.local_path ?? "",
  );
  const [workspaceRoot, setWorkspaceRoot] = useState<WorkspaceNode | null>(
    null,
  );
  const workspaceRootRef = useRef<WorkspaceNode | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const routeSessionId = propSessionId || workspaceInfo?.session_id || null;
  const activeSessionId = state.activeSessionId || routeSessionId || null;
  const workspaceFileSessionId = routeSessionId || activeSessionId;
  const sessionOptionLabels = useMemo(
    () => getSessionOptionLabels(state.sessions),
    [state.sessions],
  );

  useEffect(() => {
    if (typeof ResizeObserver === "undefined") return;
    if (!observedContainer) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setPanelWidth(entry.contentRect.width);
      }
    });
    observer.observe(observedContainer);
    return () => observer.disconnect();
  }, [observedContainer]);

  // Refresh sessions when workspace changes
  useEffect(() => {
    refreshSessions(_workspaceId);
  }, [_workspaceId, refreshSessions]);

  // Fetch workspace details when workspace changes
  useEffect(() => {
    if (!_workspaceId) return;
    if (initialWorkspace?.workspace_id === _workspaceId) {
      setWorkspaceInfo(initialWorkspace);
      setWorkspacePath(initialWorkspace.local_path || "");
      return;
    }
    let isMounted = true;
    const fetchWorkspaceInfo = async () => {
      try {
        const info = await workspaceService.getWorkspace(_workspaceId);
        if (isMounted) {
          setWorkspaceInfo(info);
          if (info.local_path) {
            setWorkspacePath(info.local_path);
          }
        }
      } catch (err) {
        console.error("Failed to fetch workspace info:", err);
      }
    };
    fetchWorkspaceInfo();
    return () => {
      isMounted = false;
    };
  }, [_workspaceId, initialWorkspace]);

  // Sync the route workspace session into global chat state on mount or when it changes.
  useEffect(() => {
    if (routeSessionId) {
      selectSession(routeSessionId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeSessionId]);

  const statuses = useHealthStatus();
  const agentServiceStatus = statuses.find(
    (s) => s.serviceId === "hermes-agent",
  );
  const agentStatus = agentServiceStatus?.state;
  const agentError = agentServiceStatus?.error;
  const isAgentDisconnected = agentStatus === "disconnected";

  const activeSession =
    state.sessions.find((s) => s.sessionId === activeSessionId) || null;
  const activeSessionStreamState = activeSessionId
    ? state.streamStates?.[activeSessionId]
    : undefined;
  const isActiveSessionStreaming = Boolean(
    activeSessionStreamState?.isStreaming,
  );
  const activeSessionStreamedText =
    activeSessionStreamState?.streamedText || "";
  const activeSessionTool = activeSessionStreamState?.activeTool || null;
  const activeSessionStreamActivity =
    activeSessionStreamState?.streamActivity || [];
  const activeSessionQueuedPrompts = activeSessionId
    ? (state.promptQueue ?? []).filter(
        (prompt) => prompt.sessionId === activeSessionId,
      )
    : [];

  const loadHermesModels = useCallback(async () => {
    setIsLoadingModels(true);
    try {
      const options = await agentService.listHermesModels();
      setModelGroups(options.groups);
      setSelectedModel(
        options.current_value || options.groups[0]?.options[0]?.value || "",
      );
      setModelError(null);
    } catch (err) {
      console.error("Failed to fetch Hermes model options", err);
      setModelGroups([]);
      setSelectedModel("");
      setModelError("Model list unavailable");
    } finally {
      setIsLoadingModels(false);
    }
  }, []);

  // Load active agent and model catalog on mount
  useEffect(() => {
    const initializeAgent = async () => {
      try {
        const active = await agentService.getActiveAgent();
        if (active !== "hermes") {
          await agentService.setActiveAgent("hermes");
        }
      } catch (err) {
        console.error("Failed to fetch active agent from backend", err);
      }
      await loadHermesModels();
    };
    initializeAgent();
  }, [loadHermesModels]);

  const handleModelChange = async (newModel: string) => {
    const option = modelGroups
      .flatMap((group) => group.options)
      .find((item) => item.value === newModel);
    if (!option) {
      setSelectedModel(newModel);
      return;
    }

    const previousModel = selectedModel;
    setSelectedModel(newModel);
    setModelError(null);
    try {
      await agentService.setActiveAgent("hermes", activeSessionId);
      const result = await agentService.setHermesModel(
        option.provider,
        option.model,
        activeSessionId,
      );
      if (result.confirm_required) {
        setSelectedModel(previousModel);
        setModelError(
          result.confirm_message || "Model selection needs confirmation",
        );
        return;
      }
      await loadHermesModels();
    } catch (err) {
      console.error("Failed to change Hermes model", err);
      setSelectedModel(previousModel);
      setModelError(
        err instanceof Error ? err.message : "Failed to change model",
      );
    }
  };

  const renderModelOptions = () => {
    if (isLoadingModels) {
      return <option value="">Loading models...</option>;
    }
    if (modelGroups.length === 0) {
      return <option value="">Hermes models unavailable</option>;
    }
    return modelGroups.map((group) => (
      <optgroup key={group.provider} label={group.label}>
        {group.options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </optgroup>
    ));
  };

  // --- Layout state persistence via localStorage ---
  const layoutKey = useMemo(
    () => (_workspaceId ? `wright-workspace-layout-${_workspaceId}` : null),
    [_workspaceId],
  );

  // Read saved layout once on mount
  const savedLayout = useMemo(() => {
    if (!layoutKey) return null;
    try {
      const raw = localStorage.getItem(layoutKey);
      if (raw) return JSON.parse(raw);
    } catch {
      /* ignore corrupt data */
    }
    return null;
  }, [layoutKey]);

  // Layout states — initialised from localStorage when available
  const [activeSidebar, setActiveSidebar] = useState<WorkspaceSidebarId>(
    savedLayout?.activeSidebar === "marketplace" ||
      savedLayout?.activeSidebar === "files" ||
      savedLayout?.activeSidebar === "git" ||
      savedLayout?.activeSidebar === "settings" ||
      savedLayout?.activeSidebar === "docs"
      ? savedLayout.activeSidebar
      : "files",
  );
  // Switch to the chat-only thin shell when the legacy workspace has no room
  // for the full editor layout.
  const isThin = panelWidth < 768 && !surfacesEnabled;
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(
    savedLayout?.isSidebarCollapsed ?? false,
  );
  const [isAgentCollapsed, setIsAgentCollapsed] = useState<boolean>(
    savedLayout?.isAgentCollapsed ?? false,
  );
  const {
    openTabs,
    activeTabPath,
    openTab,
    openTransientTab,
    closeTab,
    setActiveTabPath,
    getDocument,
    getProvider,
    updateTabPath,
    reloadDocument,
    resetViewer,
  } = useViewerPanel();

  // Resize and model states
  const [leftSidebarWidth, setLeftSidebarWidth] = useState<number>(
    savedLayout?.leftSidebarWidth ?? 260,
  );
  const [rightSidebarWidth, setRightSidebarWidth] = useState<number>(
    savedLayout?.rightSidebarWidth ?? 360,
  );
  const [isLeftDragging, setIsLeftDragging] = useState<boolean>(false);
  const [isRightDragging, setIsRightDragging] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [modelGroups, setModelGroups] = useState<HermesModelOptionGroup[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);
  const [modelError, setModelError] = useState<string | null>(null);
  const normalSurfacePaneWidth = Math.max(
    1,
    panelWidth -
      48 -
      (isSidebarCollapsed ? 0 : leftSidebarWidth) -
      (isSidebarCollapsed ? 0 : 4),
  );
  const [surfaceLayout, surfaceLayoutDispatch] = usePersistentSurfaceLayout(
    _workspaceId ?? "unbound-workspace",
    normalSurfacePaneWidth,
  );
  const surfacePaneContainerWidth =
    surfaceLayout.wideMode === "focus" ? panelWidth : normalSurfacePaneWidth;
  const resolvedSurfaceLayout = resolveWorkspaceLayout(
    surfaceLayout,
    surfacePaneContainerWidth,
  );
  const surfaceChromeHidden =
    surfacesEnabled &&
    (surfaceLayout.mode === "focus" || surfaceLayout.mode === "narrow");
  const surfaceFocusManager = useMemo(() => new SurfaceFocusManager(), []);

  const enterSurfaceFocus = () => {
    surfaceFocusManager.rememberInitiator(
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null,
    );
    surfaceLayoutDispatch({
      type: "enter_focus",
      containerWidth: panelWidth,
    });
  };

  const exitSurfaceFocus = () => {
    surfaceLayoutDispatch({
      type: "exit_focus",
      containerWidth: normalSurfacePaneWidth,
    });
    queueMicrotask(() =>
      surfaceFocusManager.restoreInitiator(
        containerRef.current?.querySelector<HTMLElement>(
          '[data-focus-region="tabs"] [role="tab"][aria-selected="true"]',
        ) ?? null,
      ),
    );
  };

  useEffect(() => {
    surfaceLayoutDispatch({
      type: "resize_container",
      containerWidth: surfacePaneContainerWidth,
    });
  }, [surfaceLayoutDispatch, surfacePaneContainerWidth]);

  useEffect(() => {
    if (!surfacesEnabled || !containerRef.current) return;
    return installF6HostRegionCycle(containerRef.current, () => ({
      chat:
        containerRef.current?.querySelector<HTMLElement>(
          '[data-focus-region="chat"] button, [data-focus-region="chat"] textarea, [data-focus-region="chat"] input',
        ) ?? null,
      tabs:
        containerRef.current?.querySelector<HTMLElement>(
          '[data-focus-region="tabs"] [role="tab"][tabindex="0"]',
        ) ?? null,
      toolbar:
        containerRef.current?.querySelector<HTMLElement>(
          '[data-focus-region="toolbar"] button',
        ) ?? null,
      frameReturn:
        containerRef.current?.querySelector<HTMLElement>(
          '[data-focus-region="frame-return"]',
        ) ?? null,
    }));
  }, [surfacesEnabled]);

  // Workspace Config state
  const [workspacePrompt, setWorkspacePrompt] = useState("");
  const [gitLargeFileThreshold, setGitLargeFileThreshold] =
    useState<number>(10);

  // Compact MCP tools state
  const [mcpServers, setMcpServers] = useState<CompactMcpServer[]>([]);
  const [enabledTools, setEnabledTools] = useState<string[]>([]);
  const [mcpLoading, setMcpLoading] = useState(false);
  const [mcpError, setMcpError] = useState<string | null>(null);
  const prefetchedMcpWorkspaceRef = useRef<string | null>(null);

  const installedServers = mcpServers.filter(
    (server) => server.is_installed && server.server_id !== "rivet-workflows",
  );

  // File tree expanded directories — persisted so the tree stays open across refresh
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
    () => new Set<string>(savedLayout?.expandedPaths ?? []),
  );
  const [isUnresponsive, setIsUnresponsive] = useState<boolean>(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);

  const handleToggleExpand = useCallback((path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  }, []);

  // Persist layout state to localStorage on changes (debounced via microtask)
  const layoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (!layoutKey) return;
    if (layoutTimerRef.current) clearTimeout(layoutTimerRef.current);
    layoutTimerRef.current = setTimeout(() => {
      const state = {
        activeSidebar,
        isSidebarCollapsed,
        isAgentCollapsed,
        openTabs: dedupeEditorTabs(openTabs),
        activeTabPath: activeTabPath
          ? normalizeEditorTabPath(activeTabPath)
          : null,
        leftSidebarWidth,
        rightSidebarWidth,
        expandedPaths: Array.from(expandedPaths),
      };
      try {
        localStorage.setItem(layoutKey, JSON.stringify(state));
      } catch {
        /* quota exceeded — not critical */
      }
    }, 300);
    return () => {
      if (layoutTimerRef.current) clearTimeout(layoutTimerRef.current);
    };
  }, [
    layoutKey,
    activeSidebar,
    isSidebarCollapsed,
    isAgentCollapsed,
    openTabs,
    activeTabPath,
    leftSidebarWidth,
    rightSidebarWidth,
    expandedPaths,
  ]);

  useEffect(() => {
    workspaceRootRef.current = workspaceRoot;
  }, [workspaceRoot]);

  const selectChatSession = useCallback(
    async (sessionId: string): Promise<void> => {
      setError(null);
      await selectSession(sessionId);
    },
    [selectSession],
  );

  const bindSessionToWorkspace = useCallback(
    async (sessionId: string): Promise<string | undefined> => {
      let resolvedSessionId = sessionId;

      if (_workspaceId) {
        try {
          resolvedSessionId = await workspaceService.updateWorkspaceSession(
            _workspaceId,
            sessionId,
          );
        } catch (err) {
          console.error("Failed to update workspace session association", err);
          setError("Failed to bind new session to workspace");
          return undefined;
        }
      }

      setError(null);
      setWorkspaceInfo((prev) =>
        prev ? { ...prev, session_id: resolvedSessionId } : prev,
      );
      await selectSession(resolvedSessionId);
      if (onSessionChange) {
        onSessionChange(resolvedSessionId);
      }
      return resolvedSessionId;
    },
    [_workspaceId, onSessionChange, selectSession],
  );

  // Git state
  const [, setGitBranch] = useState<string>("main");
  const [, setGitChanges] = useState<
    { path: string; git_status: string; staged: boolean; file_size?: number }[]
  >([]);
  const [, setGitHistory] = useState<
    {
      commit_hash: string;
      message: string;
      author: string;
      timestamp: number;
    }[]
  >([]);
  const [, setGitLoading] = useState(false);
  const [, setGitError] = useState<string | null>(null);
  const [activeDiffFile, setActiveDiffFile] = useState<{
    path: string;
    diffText: string;
  } | null>(null);

  // Remote Options state
  const [remoteUrl, setRemoteUrl] = useState("");
  const [gitUsername, setGitUsername] = useState("");
  const [gitToken, setGitToken] = useState("");
  const [optionsSaved, setOptionsSaved] = useState(false);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [optionsError, setOptionsError] = useState<string | null>(null);

  // Refs for tracking modified files in polling loop
  const activeTabPathRef = useRef<string | null>(null);
  const openTabsRef = useRef<EditorTab[]>([]);

  useEffect(() => {
    activeTabPathRef.current = activeTabPath;
  }, [activeTabPath]);

  useEffect(() => {
    openTabsRef.current = openTabs;
  }, [openTabs]);

  const viewerContainerRef = useRef<HTMLDivElement>(null);
  const sendMessageRef = useRef(sendMessage);

  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);

  useEffect(() => {
    resetViewer();
    setWorkspaceRoot(null);
    workspaceRootRef.current = null;
    setActiveDiffFile(null);
    setIsInspectorOpen(false);
    setIsUnresponsive(false);
    if (viewerContainerRef.current) {
      viewerContainerRef.current.replaceChildren();
    }
  }, [_workspaceId, resetViewer]);

  // Synchronise stored tabs from savedLayout on mount/initialisation
  const tabsInitialized = useRef(false);
  useEffect(() => {
    tabsInitialized.current = false;
  }, [layoutKey]);

  useEffect(() => {
    if (
      !tabsInitialized.current &&
      savedLayout?.openTabs &&
      workspaceFileSessionId
    ) {
      tabsInitialized.current = true;
      const syncTabs = async () => {
        for (const tab of dedupeEditorTabs(savedLayout.openTabs)) {
          const tabPath = normalizeEditorTabPath(tab.path);
          const savedWorkflowSlug = workspaceRivetWorkflowSlug(tabPath);
          if (
            isDirectRivetTab(tabPath) ||
            tab.type === "rivet" ||
            savedWorkflowSlug
          ) {
            const slug =
              rivetSlugFromTabPath(tabPath) || savedWorkflowSlug || "rivet";
            openTransientTab({
              name: `${slug}.rivet-project`,
              path: directRivetTabPath(slug),
              type: "rivet",
            });
            continue;
          }
          if (isDirectBrepTab(tabPath) || tab.type === "brep") {
            openTransientTab({
              name: "BREP",
              path: DIRECT_BREP_TAB_PATH,
              type: "brep",
            });
            continue;
          }
          const fileNode = workspaceRootRef.current
            ? findFileInTree(workspaceRootRef.current, tabPath)
            : null;
          const ext = tabPath.split(".").pop()?.toLowerCase() || "";
          const name = tabPath.split("/").pop() || tabPath;
          let mimeType = "text/plain";
          if (ext === "pdf") mimeType = "application/pdf";
          else if (ext === "png") mimeType = "image/png";
          else if (ext === "jpg" || ext === "jpeg") mimeType = "image/jpeg";
          else if (ext === "webp") mimeType = "image/webp";
          else if (ext === "gif") mimeType = "image/gif";
          else if (ext === "bmp") mimeType = "image/bmp";
          else if (ext === "svg") mimeType = "image/svg+xml";
          else if (ext === "stl") mimeType = "application/sla";
          else if (ext === "step") mimeType = "application/step";
          else if (ext === "md" || ext === "markdown")
            mimeType = "text/markdown";
          const file: FileDescriptor = {
            id: tabPath,
            uri: tabPath,
            name,
            extension: ext,
            mimeType,
            size: fileNode?.size || undefined,
            metadata: { last_modified: fileNode?.last_modified },
          };
          await openTab(file, "preview", workspaceFileSessionId || undefined);
        }
        if (savedLayout.activeTabPath) {
          const savedWorkflowSlug = workspaceRivetWorkflowSlug(
            savedLayout.activeTabPath,
          );
          setActiveTabPath(
            savedWorkflowSlug
              ? directRivetTabPath(savedWorkflowSlug)
              : normalizeEditorTabPath(savedLayout.activeTabPath),
          );
        }
      };
      syncTabs();
    }
  }, [
    savedLayout,
    workspaceFileSessionId,
    openTab,
    openTransientTab,
    setActiveTabPath,
  ]);

  // Pluggable resolution of active tab viewer
  useEffect(() => {
    if (!activeTabPath || !viewerContainerRef.current) return;
    if (isDirectRivetTab(activeTabPath) || isDirectBrepTab(activeTabPath)) {
      viewerContainerRef.current.replaceChildren();
      return;
    }

    const fileNode = workspaceRootRef.current
      ? findFileInTree(workspaceRootRef.current, activeTabPath)
      : null;
    const ext = activeTabPath.split(".").pop()?.toLowerCase() || "";
    const name = activeTabPath.split("/").pop() || activeTabPath;

    let mimeType = "text/plain";
    if (ext === "pdf") mimeType = "application/pdf";
    else if (ext === "png") mimeType = "image/png";
    else if (ext === "jpg" || ext === "jpeg") mimeType = "image/jpeg";
    else if (ext === "webp") mimeType = "image/webp";
    else if (ext === "gif") mimeType = "image/gif";
    else if (ext === "bmp") mimeType = "image/bmp";
    else if (ext === "svg") mimeType = "image/svg+xml";
    else if (ext === "stl") mimeType = "application/sla";
    else if (ext === "step") mimeType = "application/step";
    else if (ext === "json") mimeType = "application/json";
    else if (ext === "md" || ext === "markdown") mimeType = "text/markdown";

    const file: FileDescriptor = {
      id: activeTabPath,
      uri: activeTabPath,
      name,
      extension: ext,
      mimeType,
      size: fileNode?.size || undefined,
      metadata: { last_modified: fileNode?.last_modified },
    };

    const mode = "preview";
    const contribution = viewerRegistry.getDefaultViewer(file, mode);
    if (!contribution) return;

    const provider =
      getProvider(activeTabPath) || contribution.providerFactory();

    let activeDocument = getDocument(activeTabPath);
    let cancelled = false;

    const token = {
      isCancellationRequested: cancelled,
      onCancellationRequested: () => {
        return { dispose: () => {} };
      },
    };

    const host = new PanelHostImpl(
      `panel-${activeTabPath}`,
      name,
      viewerContainerRef.current,
      true,
      true,
      contribution.id === "iframe-viewer",
    );

    const subUnresponsive = host.onDidBecomeUnresponsive?.(() => {
      setIsUnresponsive(true);
    });

    const subResponsive = host.onDidBecomeResponsive?.(() => {
      setIsUnresponsive(false);
    });

    const loadViewer = async () => {
      try {
        if (!activeDocument) {
          activeDocument = await provider.openDocument(file, {
            sessionId: workspaceFileSessionId || undefined,
          });
        }
        if (!cancelled && viewerContainerRef.current) {
          await provider.resolveViewer(activeDocument, host, mode, token);
        }
      } catch (err) {
        console.error("Failed to load pluggable viewer:", err);
      }
    };

    const container = viewerContainerRef.current;
    const handleViewerMessage = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { type, content } = customEvent.detail || {};
      if (type === "create-prompt" && content) {
        // Viewer actions belong to this workspace's bound conversation even
        // when the global session list has not refreshed yet.
        sendMessageRef.current(
          content,
          undefined,
          false,
          workspaceFileSessionId || undefined,
        );
      }
    };
    container?.addEventListener("viewer-message", handleViewerMessage);

    loadViewer();

    return () => {
      cancelled = true;
      subUnresponsive?.dispose();
      subResponsive?.dispose();
      host.dispose();
      setIsUnresponsive(false);
      container?.removeEventListener("viewer-message", handleViewerMessage);
      container?.replaceChildren();
    };
  }, [activeTabPath, workspaceFileSessionId, getDocument, getProvider]);

  // Fetch Git Data helper
  const fetchGitData = useCallback(async () => {
    if (!activeSessionId) return;
    setGitLoading(true);
    setGitError(null);
    try {
      const statusRes = await workspaceService.getGitStatus(activeSessionId);
      setGitBranch(statusRes.branch_name);
      setGitChanges(statusRes.changes);

      const historyRes = await workspaceService.getGitHistory(activeSessionId);
      setGitHistory(historyRes.commits);
    } catch (err: unknown) {
      console.error("Failed to fetch Git data:", err);
    } finally {
      setGitLoading(false);
    }
  }, [
    activeSessionId,
    setGitLoading,
    setGitError,
    setGitBranch,
    setGitChanges,
    setGitHistory,
  ]);

  // Fetch workspace config helper
  const fetchConfig = useCallback(async () => {
    if (!activeSessionId) return;
    setOptionsLoading(true);
    setOptionsError(null);
    try {
      const config = await workspaceService.getWorkspaceConfig(activeSessionId);
      setRemoteUrl(config.git_remote_url || "");
      setGitUsername(config.git_username || "");
      setGitToken(config.has_token ? "••••••••" : "");
      setWorkspacePrompt(config.workspace_prompt || "");
      setGitLargeFileThreshold(config.git_large_file_threshold ?? 10);
      if (config.workspace_path) {
        setWorkspacePath(config.workspace_path);
      }
    } catch (err: unknown) {
      console.error("Failed to fetch workspace config:", err);
      setOptionsError("Failed to load workspace settings.");
    } finally {
      setOptionsLoading(false);
    }
  }, [
    activeSessionId,
    setOptionsLoading,
    setOptionsError,
    setRemoteUrl,
    setGitUsername,
    setGitToken,
    setWorkspacePrompt,
    setGitLargeFileThreshold,
    setWorkspacePath,
  ]);

  // Workspace Polling Loop for disk changes
  useEffect(() => {
    if (!workspaceFileSessionId) {
      setWorkspaceRoot(null);
      setLoading(false);
      return;
    }

    let isMounted = true;
    let refreshInFlight = false;

    const fetchWorkspace = async (isInitial = false) => {
      if (refreshInFlight) return;
      refreshInFlight = true;
      if (isInitial) setLoading(true);
      try {
        const tree = await workspaceService.getWorkspaceFiles(
          workspaceFileSessionId,
        );
        if (!isMounted) return;
        setWorkspaceRoot(tree);
        setError(null);

        // Check if active file tab has been modified on disk
        const currentPath = activeTabPathRef.current;
        if (currentPath) {
          const fileNode = findFileInTree(tree, currentPath);
          if (fileNode) {
            const activeTabObj = openTabsRef.current.find(
              (t) => t.path === currentPath,
            );
            if (
              activeTabObj &&
              activeTabObj.last_modified !== undefined &&
              fileNode.last_modified > activeTabObj.last_modified
            ) {
              console.log(
                `Hot-reloading disk modifications for: ${currentPath}`,
              );
              try {
                const ext = currentPath.split(".").pop()?.toLowerCase() || "";
                const name = currentPath.split("/").pop() || currentPath;
                const file: FileDescriptor = {
                  id: currentPath,
                  uri: currentPath,
                  name,
                  extension: ext,
                  mimeType: "text/plain",
                  metadata: { last_modified: fileNode.last_modified },
                };
                await reloadDocument(file);
              } catch (err) {
                console.error("Failed to hot-reload modified file:", err);
              }
            }
          }
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        console.error("Error fetching workspace files:", err);
        setError("Failed to fetch workspace files");
      } finally {
        refreshInFlight = false;
        if (isMounted && isInitial) setLoading(false);
      }
    };

    fetchWorkspace(true);

    const intervalId = setInterval(() => {
      fetchWorkspace(false);
    }, 5000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [workspaceFileSessionId, reloadDocument]);

  // Load settings and git data on sidebar tab activation
  useEffect(() => {
    if (activeSidebar === "git") {
      fetchGitData();
    } else if (activeSidebar === "settings") {
      fetchConfig();
    }
  }, [activeSidebar, fetchGitData, fetchConfig]);

  // Options save handlers
  const handleSaveOptions = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSessionId) return;
    setOptionsLoading(true);
    setOptionsError(null);
    setOptionsSaved(false);
    try {
      const tokenToSend = gitToken === "••••••••" ? null : gitToken;
      await workspaceService.updateWorkspaceConfig(
        activeSessionId,
        remoteUrl.trim() || null,
        gitUsername.trim() || null,
        tokenToSend,
        workspacePrompt.trim() || null,
        gitLargeFileThreshold,
      );
      setOptionsSaved(true);
      setTimeout(() => setOptionsSaved(false), 3000);
      await fetchConfig();
    } catch (err: unknown) {
      setOptionsError(
        err instanceof Error ? err.message : "Save settings failed",
      );
    } finally {
      setOptionsLoading(false);
    }
  };

  const handlePush = async () => {
    if (!activeSessionId) return;
    setOptionsLoading(true);
    setOptionsError(null);
    try {
      await workspaceService.pushCommits(activeSessionId);
      alert("Push completed successfully!");
    } catch (err: unknown) {
      setOptionsError(err instanceof Error ? err.message : "Push failed");
    } finally {
      setOptionsLoading(false);
    }
  };

  const handlePull = async () => {
    if (!activeSessionId) return;
    setOptionsLoading(true);
    setOptionsError(null);
    try {
      await workspaceService.pullCommits(activeSessionId);
      alert("Pull completed successfully!");
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();
    } catch (err: unknown) {
      if (err instanceof MergeConflictError) {
        setOptionsError(
          `Merge conflict in files: ${err.conflictedFiles.join(", ")}`,
        );
      } else {
        setOptionsError(err instanceof Error ? err.message : "Pull failed");
      }
    } finally {
      setOptionsLoading(false);
    }
  };

  // Git Action Handlers
  const handleRevert = async (filePath: string) => {
    if (!activeSessionId) return;
    if (!confirm(`Are you sure you want to revert changes in ${filePath}?`))
      return;
    setGitLoading(true);
    setGitError(null);
    try {
      await workspaceService.revertFile(activeSessionId, filePath);
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();
      if (activeDiffFile?.path === filePath) {
        setActiveDiffFile(null);
      }
    } catch (err: unknown) {
      setGitError(err instanceof Error ? err.message : "Revert failed");
    } finally {
      setGitLoading(false);
    }
  };

  // Click file in Tree → Open Tab
  const handleFileClick = async (path: string) => {
    if (!activeSessionId) return;

    const savedWorkflowSlug = workspaceRivetWorkflowSlug(path);
    if (savedWorkflowSlug && workspaceFileSessionId) {
      const workflow = await workspaceService.readRivetWorkflow(
        workspaceFileSessionId,
        savedWorkflowSlug,
      );
      openTransientTab({
        name: `${workflow.slug}.rivet-project`,
        path: directRivetTabPath(workflow.slug),
        type: "rivet",
      });
      if (surfaceLayout.mode === "narrow") {
        surfaceLayoutDispatch({
          type: "select_narrow_pane",
          pane: "surface",
        });
      }
      return;
    }

    const ext = path.split(".").pop()?.toLowerCase() || "";
    const name = path.split("/").pop() || path;
    const fileNode = workspaceRoot ? findFileInTree(workspaceRoot, path) : null;

    let mimeType = "text/plain";
    if (ext === "pdf") mimeType = "application/pdf";
    else if (ext === "png") mimeType = "image/png";
    else if (ext === "jpg" || ext === "jpeg") mimeType = "image/jpeg";
    else if (ext === "webp") mimeType = "image/webp";
    else if (ext === "gif") mimeType = "image/gif";
    else if (ext === "bmp") mimeType = "image/bmp";
    else if (ext === "svg") mimeType = "image/svg+xml";
    else if (ext === "stl") mimeType = "application/sla";
    else if (ext === "step") mimeType = "application/step";
    else if (ext === "json") mimeType = "application/json";

    const file: FileDescriptor = {
      id: path,
      uri: path,
      name,
      extension: ext,
      mimeType,
      size: fileNode?.size || undefined,
      metadata: { last_modified: fileNode?.last_modified },
    };

    try {
      await openTab(file, "preview", workspaceFileSessionId || undefined);
    } catch (err: unknown) {
      console.error("Failed to open workspace file:", err);
      setError(
        err instanceof Error
          ? `Could not open ${name}: ${err.message}`
          : `Could not open ${name}.`,
      );
    }
  };

  // File tree operations
  const handleCreate = async (
    parentPath: string,
    name: string,
    type: "file" | "directory",
  ) => {
    if (!activeSessionId) return;
    try {
      const fullPath =
        parentPath === "/" ? `/${name}` : `${parentPath}/${name}`;
      await workspaceService.createFileNode(activeSessionId, fullPath, type);
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();
    } catch (err: unknown) {
      console.error("Failed to create file node:", err);
      throw err;
    }
  };

  const handleDelete = async (filePath: string) => {
    if (!activeSessionId) return;
    try {
      await workspaceService.deleteFileNode(activeSessionId, filePath);
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();
      handleCloseTab(filePath);
    } catch (err: unknown) {
      console.error("Failed to delete file node:", err);
      throw err;
    }
  };

  const handleRename = async (oldPath: string, newPath: string) => {
    if (!activeSessionId) return;
    try {
      await workspaceService.moveFileNode(activeSessionId, oldPath, newPath);
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();

      // Update tabs if opened
      const newName = newPath.split("/").pop() || newPath;
      updateTabPath(oldPath, newPath, newName);
    } catch (err: unknown) {
      console.error("Failed to rename file node:", err);
      throw err;
    }
  };

  const handleMove = async (sourcePath: string, destPath: string) => {
    if (!activeSessionId) return;
    try {
      await workspaceService.moveFileNode(
        activeSessionId,
        sourcePath,
        destPath,
      );
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();

      const newName = destPath.split("/").pop() || destPath;
      updateTabPath(sourcePath, destPath, newName);
    } catch (err: unknown) {
      console.error("Failed to move file node:", err);
      throw err;
    }
  };

  const handleCloseTab = (path: string) => {
    const normalizedPath = normalizeEditorTabPath(path);
    const remainingTabs = openTabs.filter((tab) => tab.path !== normalizedPath);
    closeTab(path);

    if (remainingTabs.length === 0) {
      setIsInspectorOpen(false);
      setIsUnresponsive(false);
      setActiveDiffFile(null);
      if (viewerContainerRef.current) {
        viewerContainerRef.current.replaceChildren();
      }
    }
  };

  const handleSelectTab = (path: string) => {
    setActiveTabPath(path);
  };

  // Resize listeners
  const handleLeftMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsLeftDragging(true);
  };

  const handleRightMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsRightDragging(true);
  };

  useEffect(() => {
    if (!isLeftDragging) return;
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = e.clientX - 48;
      if (newWidth > 150 && newWidth < 600) {
        setLeftSidebarWidth(newWidth);
      }
    };
    const handleMouseUp = () => {
      setIsLeftDragging(false);
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isLeftDragging]);

  useEffect(() => {
    if (!isRightDragging) return;
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 150 && newWidth < 600) {
        setRightSidebarWidth(newWidth);
      }
    };
    const handleMouseUp = () => {
      setIsRightDragging(false);
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isRightDragging]);

  // Toggle activity bar sidebar
  const handleActivityBarClick = (sidebar: WorkspaceSidebarId) => {
    if (activeSidebar === sidebar) {
      setIsSidebarCollapsed((collapsed) => !collapsed);
    } else {
      setActiveSidebar(sidebar);
      setIsSidebarCollapsed(false);
    }
  };

  // Helper to construct API URL
  const getApiUrl = (path: string) => {
    const port = window.location.port;
    const base = port === "5173" || port === "5174" ? "" : "";
    return `${base}${path}`;
  };

  const fetchMcpData = useCallback(async () => {
    if (!_workspaceId && !activeSessionId) return;
    setMcpLoading(true);
    setMcpError(null);
    try {
      const serverRequest = fetch(getApiUrl("/api/mcp/servers/installed")).then(
        async (response) => {
          if (!response.ok)
            throw new Error("Installed MCP list is unavailable");
          const data = await response.json();
          return (data.servers || []) as CompactMcpServer[];
        },
      );
      const enabledRequest = _workspaceId
        ? workspaceService.getWorkspaceToolsById(_workspaceId)
        : workspaceService.getWorkspaceTools(activeSessionId!);
      const [serversResult, enabledResult] = await Promise.allSettled([
        serverRequest,
        enabledRequest,
      ]);
      const failures: unknown[] = [];
      if (serversResult.status === "fulfilled") {
        setMcpServers(serversResult.value);
      } else {
        failures.push(serversResult.reason);
      }
      if (enabledResult.status === "fulfilled") {
        setEnabledTools(enabledResult.value || []);
      } else {
        failures.push(enabledResult.reason);
      }
      if (failures.length > 0) {
        failures.forEach((failure) =>
          console.error("Failed to load compact MCP list", failure),
        );
        setMcpError("Workspace tools could not be fully loaded.");
      }
    } finally {
      setMcpLoading(false);
    }
  }, [_workspaceId, activeSessionId]);

  useEffect(() => {
    const key = _workspaceId || activeSessionId;
    if (!key || prefetchedMcpWorkspaceRef.current === key) return;
    prefetchedMcpWorkspaceRef.current = key;
    void fetchMcpData();
  }, [_workspaceId, activeSessionId, fetchMcpData]);

  const handleToggleMcpTool = async (
    serverId: string,
    currentlyEnabled: boolean,
  ) => {
    if (!_workspaceId && !activeSessionId) return;
    try {
      if (_workspaceId) {
        await workspaceService.toggleWorkspaceToolById(
          _workspaceId,
          serverId,
          !currentlyEnabled,
        );
      } else {
        await workspaceService.toggleWorkspaceTool(
          activeSessionId!,
          serverId,
          !currentlyEnabled,
        );
      }
      // Re-fetch enabled tools list
      const enabledList = _workspaceId
        ? await workspaceService.getWorkspaceToolsById(_workspaceId)
        : await workspaceService.getWorkspaceTools(activeSessionId!);
      setEnabledTools(enabledList || []);
    } catch (err) {
      console.error("Failed to toggle MCP tool", err);
    }
  };

  const openRivetWorkflowTab = useCallback(
    (slug?: string) => {
      if (!workspaceFileSessionId) return;
      setIsSidebarCollapsed(true);
      const initialSlug = slug || "rivet";
      const initialPath = directRivetTabPath(initialSlug);
      openTransientTab({
        name: `${initialSlug}.rivet-project`,
        path: initialPath,
        type: "rivet",
      });
      const workflowRequest = slug
        ? workspaceService.readRivetWorkflow(workspaceFileSessionId, slug)
        : workspaceService.ensureDefaultRivetWorkflow(workspaceFileSessionId);
      void workflowRequest
        .then((workflow) => {
          updateTabPath(
            initialPath,
            directRivetTabPath(workflow.slug),
            `${workflow.slug}.rivet-project`,
          );
        })
        .catch((error) => {
          console.error("Rivet workflow preparation failed", error);
        });
      if (surfaceLayout.mode === "narrow") {
        surfaceLayoutDispatch({
          type: "select_narrow_pane",
          pane: "surface",
        });
      }
    },
    [
      openTransientTab,
      surfaceLayout.mode,
      surfaceLayoutDispatch,
      updateTabPath,
      workspaceFileSessionId,
    ],
  );

  const openBrepPanelTab = useCallback(() => {
    if (!workspaceFileSessionId) return;
    setIsSidebarCollapsed(true);
    openTransientTab({
      name: "BREP",
      path: DIRECT_BREP_TAB_PATH,
      type: "brep",
    });
    if (surfaceLayout.mode === "narrow") {
      surfaceLayoutDispatch({
        type: "select_narrow_pane",
        pane: "surface",
      });
    }
  }, [
    openTransientTab,
    surfaceLayout.mode,
    surfaceLayoutDispatch,
    workspaceFileSessionId,
  ]);

  const lastBrepActivityRef = useRef<string | null>(null);
  useEffect(() => {
    const activity = [...activeSessionStreamActivity]
      .reverse()
      .find(isBrepToolActivity);
    if (!activity || lastBrepActivityRef.current === activity.id) return;

    lastBrepActivityRef.current = activity.id;
    openBrepPanelTab();
  }, [activeSessionStreamActivity, openBrepPanelTab]);

  const directRivetTabs = openTabs.filter(
    (tab) => isDirectRivetTab(tab.path) || tab.type === "rivet",
  );
  const activeDirectRivetSlug = activeTabPath
    ? rivetSlugFromTabPath(activeTabPath)
    : null;
  const activeDirectRivet = activeDirectRivetSlug !== null;
  const activeRivetUiContext = useMemo(
    () => ({ activeRivetSlug: activeDirectRivetSlug }),
    [activeDirectRivetSlug],
  );
  const sendMessageWithSurfaceContext = useCallback(
    (message: string, attachments?: string[]) =>
      sendMessage(message, attachments, false, undefined, activeRivetUiContext),
    [activeRivetUiContext, sendMessage],
  );
  const steerMessageWithSurfaceContext = useCallback(
    (message: string, attachments?: string[]) =>
      steerMessage(message, attachments, activeRivetUiContext),
    [activeRivetUiContext, steerMessage],
  );
  const rivetMutationVersion =
    activeSessionStreamState?.rivetMutationVersion || 0;
  const rivetExternalRevisionToken =
    activeSessionId && !isActiveSessionStreaming && rivetMutationVersion > 0
      ? `${activeSessionId}:${rivetMutationVersion}`
      : null;
  const directBrepTabs = openTabs.filter(
    (tab) => isDirectBrepTab(tab.path) || tab.type === "brep",
  );
  const activeDirectBrep = isDirectBrepTab(activeTabPath);

  useEffect(() => {
    if (activeDirectRivet || activeDirectBrep) {
      setIsSidebarCollapsed(true);
    }
  }, [activeDirectBrep, activeDirectRivet]);

  if (isThin) {
    return (
      <div
        ref={attachContainerRef}
        data-testid="workspace-panel"
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          width: "100%",
          backgroundColor: "var(--color-surface)",
          color: "var(--color-primary)",
          overflow: "hidden",
        }}
      >
        <div
          data-testid="agent-sidebar"
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            overflow: "hidden",
            position: "relative",
          }}
        >
          {/* Agent Tools Window Header */}
          <div
            data-testid="agent-tools-window"
            style={{
              padding: "var(--space-sm) var(--space-md)",
              borderBottom: "1px solid var(--color-border)",
              backgroundColor: "var(--color-surface-subtle)",
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-xs)",
            }}
          >
            {/* Row 1: Title */}
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span
                style={{
                  fontSize: "0.75rem",
                  fontWeight: "bold",
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  color: "#969696",
                }}
              >
                Agent Control Pane
              </span>
            </div>

            {/* Row 2: Model and Session Selector + New Session Button */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-xs)",
                width: "100%",
              }}
            >
              {/* Model Select */}
              <label htmlFor="llm-model-select" style={{ fontSize: "0.65rem" }}>
                Model
              </label>
              <select
                id="llm-model-select"
                data-testid="llm-model-select"
                value={selectedModel}
                onChange={(e) => handleModelChange(e.target.value)}
                disabled={isLoadingModels || modelGroups.length === 0}
                style={{
                  flex: 1,
                  backgroundColor: "var(--color-surface-subtle)",
                  color: "var(--color-primary)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "6px",
                  fontSize: "0.75rem",
                  outline: "none",
                  cursor: "pointer",
                  transition: "border-color var(--transition-fast)",
                }}
                title={modelError || "Select LLM Model"}
              >
                {renderModelOptions()}
              </select>
              {modelError ? (
                <span
                  style={{
                    color: "var(--color-warning)",
                    fontSize: "0.65rem",
                  }}
                  title={modelError}
                >
                  !
                </span>
              ) : null}

              <label
                htmlFor="workspace-session-select"
                style={{ fontSize: "0.65rem" }}
              >
                Session
              </label>
              <select
                id="workspace-session-select"
                data-testid="sessions-sidebar"
                value={activeSessionId || ""}
                onChange={async (e) => {
                  const newSessId = e.target.value;
                  if (newSessId) {
                    await selectChatSession(newSessId);
                  }
                }}
                style={{
                  flex: 1.5,
                  backgroundColor: "var(--color-surface-subtle)",
                  color: "var(--color-primary)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                  padding: "6px",
                  fontSize: "0.75rem",
                  outline: "none",
                  cursor: "pointer",
                  textOverflow: "ellipsis",
                  transition: "border-color var(--transition-fast)",
                }}
                title="Select Session Context"
              >
                {state.sessions.length === 0 ? (
                  <option value="" data-testid="session-none">
                    No sessions
                  </option>
                ) : (
                  state.sessions.map((session) => (
                    <option
                      key={session.sessionId}
                      value={session.sessionId}
                      data-testid={`session-${session.sessionId}`}
                    >
                      {sessionOptionLabels.get(session.sessionId) ||
                        "Untitled Session"}
                    </option>
                  ))
                )}
              </select>

              {/* New Session Button */}
              <button
                data-testid="create-session-btn"
                onClick={async () => {
                  const newId = await createSession(
                    workspacePath,
                    _workspaceId,
                  );
                  if (newId) {
                    await bindSessionToWorkspace(newId);
                  }
                }}
                style={{
                  backgroundColor: "var(--color-secondary)",
                  color: "var(--color-surface-subtle)",
                  border: "none",
                  borderRadius: "var(--radius-md)",
                  width: "28px",
                  height: "28px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                  fontWeight: "bold",
                  fontSize: "0.9rem",
                  transition:
                    "background-color var(--transition-fast), box-shadow var(--transition-fast)",
                  boxShadow: "var(--shadow-glow)",
                }}
                title="Create New Session"
              >
                ＋
              </button>
            </div>
          </div>

          {isAgentDisconnected && (
            <div
              data-testid="health-banner-hermes"
              style={{
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                borderBottom: "1px solid rgba(239, 68, 68, 0.2)",
                color: "var(--color-error, #f87171)",
                padding: "var(--space-sm) var(--space-md)",
                fontSize: "0.75rem",
                display: "flex",
                alignItems: "center",
                gap: "var(--space-xs)",
                fontFamily: "var(--font-ui)",
              }}
            >
              <span
                title={agentError || undefined}
                style={{ lineHeight: 1.35, overflowWrap: "anywhere" }}
              >
                Hermes agent is not available.
                {agentError
                  ? ` ${agentError}`
                  : " Check that the wright profile WebUI is running."}
              </span>
            </div>
          )}

          <div
            style={{
              flex: 1,
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ flex: 1, overflowY: "auto" }}>
              <ChatTranscript
                session={activeSession}
                isStreaming={isActiveSessionStreaming}
                streamStartedAt={activeSessionStreamState?.startedAt ?? null}
                streamedText={activeSessionStreamedText}
                activeTool={activeSessionTool}
                streamActivity={activeSessionStreamActivity}
                onOpenFile={handleFileClick}
                activeSessionId={activeSessionId || undefined}
                workspacePath={workspacePath || undefined}
              />
            </div>

            {activeSession && (
              <div
                style={{
                  padding: "var(--space-md)",
                  borderTop: "1px solid var(--color-border)",
                  backgroundColor: "var(--color-surface-subtle)",
                }}
              >
                <MessageComposer
                  onSend={sendMessageWithSurfaceContext}
                  onSteer={steerMessageWithSurfaceContext}
                  isStreaming={isActiveSessionStreaming}
                  onCancel={cancelActiveStream}
                  sessionId={activeSessionId || undefined}
                  workspaceId={_workspaceId}
                  queuedPrompts={activeSessionQueuedPrompts}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <WorkspaceLayout
      ref={attachContainerRef}
      data-testid="workspace-panel"
      {...(surfacesEnabled ? { "data-workspace-surfaces": "enabled" } : {})}
      layout={surfaceLayout}
      paneContainerWidth={surfacePaneContainerWidth}
      leftSidebarWidth={leftSidebarWidth}
      leftSidebarCollapsed={isSidebarCollapsed}
      chatCollapsed={isAgentCollapsed}
      legacyChatWidth={rightSidebarWidth}
      adaptive={surfacesEnabled}
      resizing={isLeftDragging || isRightDragging}
    >
      {surfacesEnabled && surfaceLayout.mode === "narrow" && (
        <ResponsivePaneSwitcher
          controlsOnly
          activePane={surfaceLayout.narrowPane}
          onChange={(pane) =>
            surfaceLayoutDispatch({ type: "select_narrow_pane", pane })
          }
          hiddenChatUpdate={activeSessionStreamedText ? "Chat updated." : null}
        />
      )}
      {!surfaceChromeHidden && (
        <WorkspaceActivityBar
          activeSidebar={activeSidebar}
          isSidebarCollapsed={isSidebarCollapsed}
          onBack={() => navigate("/")}
          onSelectSidebar={handleActivityBarClick}
          onOpenRivetEditor={() => {
            void openRivetWorkflowTab();
          }}
          onOpenBrepPanel={openBrepPanelTab}
          workflowsEnabled={workflowsTabEnabled}
        />
      )}

      {/* 2. Left Sidebar Panel (collapsible) */}
      <div
        data-testid="workspace-sidebar"
        style={{
          backgroundColor: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          gridColumn: "2",
          display: surfaceChromeHidden || isSidebarCollapsed ? "none" : "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {activeSidebar === "marketplace" && (
          <div
            style={{ display: "flex", flexDirection: "column", height: "100%" }}
          >
            <div
              style={{
                padding: "var(--space-md)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "1px",
                borderBottom: "1px solid var(--color-border)",
                color: "var(--color-primary)",
              }}
            >
              MCP Tools Selector
            </div>
            <div
              style={{ flex: 1, overflowY: "auto", padding: "var(--space-md)" }}
            >
              {mcpError && (
                <div
                  role="alert"
                  style={{
                    color: "var(--color-warning, #f59e0b)",
                    fontSize: "0.72rem",
                    marginBottom: "var(--space-sm)",
                  }}
                >
                  {mcpError}{" "}
                  <button type="button" onClick={() => void fetchMcpData()}>
                    Retry
                  </button>
                </div>
              )}
              {mcpLoading && installedServers.length === 0 ? (
                <div
                  style={{
                    color: "var(--color-secondary)",
                    fontSize: "0.75rem",
                  }}
                >
                  Loading workspace tools...
                </div>
              ) : installedServers.length === 0 ? (
                <div
                  style={{
                    color: "var(--color-secondary)",
                    fontSize: "0.75rem",
                  }}
                >
                  No MCP servers configured.
                </div>
              ) : (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-sm)",
                  }}
                >
                  {installedServers.map((server) => {
                    const isEnabled =
                      enabledTools.includes(server.name) ||
                      enabledTools.includes(server.server_id);
                    const isGloballyActive = server.is_active;
                    const isBrep = isVisibleBrepServer(server);

                    return (
                      <div
                        key={server.server_id}
                        data-testid={`mcp-server-item-${server.name.toLowerCase()}`}
                        style={{
                          backgroundColor: "var(--color-surface-subtle)",
                          border: "1px solid var(--color-border)",
                          borderRadius: "var(--radius-md)",
                          padding: "var(--space-sm)",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          gap: "var(--space-sm)",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "2px",
                            textAlign: "left",
                            flex: 1,
                          }}
                        >
                          <span
                            style={{
                              fontWeight: "600",
                              fontSize: "0.8rem",
                              color: "var(--color-primary)",
                            }}
                          >
                            {server.name}
                          </span>
                          <span
                            style={{
                              fontSize: "0.65rem",
                              color: "var(--color-secondary)",
                              textOverflow: "ellipsis",
                              overflow: "hidden",
                              whiteSpace: "nowrap",
                              maxWidth: "180px",
                            }}
                          >
                            {server.description || `MCP type: ${server.type}`}
                          </span>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "4px",
                              marginTop: "2px",
                            }}
                          >
                            <span
                              style={{
                                width: "5px",
                                height: "5px",
                                borderRadius: "50%",
                                backgroundColor: isGloballyActive
                                  ? "var(--color-success)"
                                  : "#858585",
                              }}
                            />
                            <span
                              style={{
                                fontSize: "0.6rem",
                                color: "var(--color-secondary)",
                              }}
                            >
                              {isGloballyActive ? "active" : "inactive"}
                            </span>
                          </div>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            alignItems: "flex-end",
                            gap: "var(--space-xs, 4px)",
                          }}
                        >
                          <input
                            data-testid={`mcp-toggle-${server.name.toLowerCase()}`}
                            type="checkbox"
                            checked={isEnabled}
                            onChange={() =>
                              handleToggleMcpTool(server.server_id, isEnabled)
                            }
                            style={{ cursor: "pointer" }}
                          />
                          {isBrep && (
                            <button
                              type="button"
                              data-testid="open-brep-panel"
                              onClick={openBrepPanelTab}
                              disabled={!isEnabled}
                              title={
                                isEnabled
                                  ? "Open BREP in a Wright panel"
                                  : "Enable BREP MCP before opening its panel"
                              }
                              style={{
                                cursor: isEnabled ? "pointer" : "not-allowed",
                                fontSize: "0.65rem",
                                padding: "2px 6px",
                              }}
                            >
                              Open panel
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
        {activeSidebar === "files" && (
          <div
            style={{ display: "flex", flexDirection: "column", height: "100%" }}
          >
            <div
              style={{
                padding: "var(--space-md)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "1px",
                borderBottom: "1px solid var(--color-border)",
                color: "var(--color-primary)",
              }}
            >
              {workspaceInfo?.workspace_name || "Workspace"} Files
            </div>
            <div
              style={{ flex: 1, overflowY: "auto", padding: "var(--space-sm)" }}
            >
              {loading && !workspaceRoot ? (
                <div
                  style={{
                    color: "var(--color-secondary)",
                    fontSize: "0.75rem",
                    padding: "var(--space-sm)",
                  }}
                >
                  Loading workspace...
                </div>
              ) : error ? (
                <div
                  style={{
                    color: "var(--color-error)",
                    fontSize: "0.75rem",
                    padding: "var(--space-sm)",
                  }}
                >
                  {error}
                </div>
              ) : workspaceRoot ? (
                <FileTree
                  node={workspaceRoot}
                  onFileClick={handleFileClick}
                  onCreate={handleCreate}
                  onDelete={handleDelete}
                  onRename={handleRename}
                  onMove={handleMove}
                  expandedPaths={expandedPaths}
                  onToggleExpand={handleToggleExpand}
                />
              ) : (
                <div
                  style={{
                    color: "var(--color-secondary)",
                    fontSize: "0.75rem",
                    padding: "var(--space-sm)",
                  }}
                >
                  No active workspace.
                </div>
              )}
            </div>
          </div>
        )}

        {activeSidebar === "git" && (
          <div
            data-testid="git-panel-coming-soon"
            aria-disabled="true"
            style={{
              display: "flex",
              flexDirection: "column",
              height: "100%",
              pointerEvents: "none",
              opacity: 0.72,
            }}
          >
            <div
              style={{
                padding: "var(--space-md)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "1px",
                borderBottom: "1px solid var(--color-border)",
                color: "var(--color-primary)",
              }}
            >
              Git Version Control
            </div>
            <div
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "var(--space-sm)",
                padding: "var(--space-lg)",
                textAlign: "center",
                color: "var(--color-secondary)",
              }}
            >
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: "700",
                  letterSpacing: "1px",
                  textTransform: "uppercase",
                  color: "var(--color-primary)",
                }}
              >
                Coming soon
              </div>
              <div
                style={{
                  maxWidth: "220px",
                  fontSize: "0.75rem",
                  lineHeight: 1.45,
                }}
              >
                Git controls are disabled while this workflow is being finished.
              </div>
            </div>
          </div>
        )}

        {activeSidebar === "settings" && (
          <div
            style={{ display: "flex", flexDirection: "column", height: "100%" }}
          >
            <div
              style={{
                padding: "var(--space-md)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "1px",
                borderBottom: "1px solid var(--color-border)",
                color: "var(--color-primary)",
              }}
            >
              Workspace Settings
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "var(--space-md)",
                fontSize: "0.75rem",
                textAlign: "left",
              }}
            >
              {optionsError && (
                <div
                  style={{
                    color: "var(--color-error)",
                    fontSize: "0.7rem",
                    marginBottom: "var(--space-xs)",
                  }}
                >
                  ⚠️ {optionsError}
                </div>
              )}

              <form
                onSubmit={handleSaveOptions}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-md)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-xs)",
                    borderBottom: "1px solid var(--color-border)",
                    paddingBottom: "var(--space-md)",
                    marginBottom: "var(--space-xs)",
                  }}
                >
                  <span
                    style={{
                      fontWeight: "bold",
                      marginBottom: "var(--space-xs)",
                      color: "var(--color-secondary)",
                    }}
                  >
                    Git Credentials
                  </span>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    <label>Git Remote URL</label>
                    <input
                      data-testid="workspace-settings-remote-url"
                      type="text"
                      value={remoteUrl}
                      onChange={(e) => setRemoteUrl(e.target.value)}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        padding: "4px var(--space-xs)",
                        fontSize: "0.75rem",
                        outline: "none",
                        borderRadius: "var(--radius-sm)",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                      marginTop: "var(--space-xs)",
                    }}
                  >
                    <label>Git Username</label>
                    <input
                      data-testid="workspace-settings-username"
                      type="text"
                      value={gitUsername}
                      onChange={(e) => setGitUsername(e.target.value)}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        padding: "4px var(--space-xs)",
                        fontSize: "0.75rem",
                        outline: "none",
                        borderRadius: "var(--radius-sm)",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                      marginTop: "var(--space-xs)",
                    }}
                  >
                    <label>Personal Access Token</label>
                    <input
                      data-testid="workspace-settings-token"
                      type="password"
                      value={gitToken}
                      onChange={(e) => setGitToken(e.target.value)}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        padding: "4px var(--space-xs)",
                        fontSize: "0.75rem",
                        outline: "none",
                        borderRadius: "var(--radius-sm)",
                      }}
                    />
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-xs)",
                    borderBottom: "1px solid var(--color-border)",
                    paddingBottom: "var(--space-md)",
                    marginBottom: "var(--space-xs)",
                  }}
                >
                  <span
                    style={{
                      fontWeight: "bold",
                      marginBottom: "var(--space-xs)",
                      color: "var(--color-secondary)",
                    }}
                  >
                    Hermes Prompt Context
                  </span>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    <label>System Prompt Overlay</label>
                    <textarea
                      data-testid="workspace-prompt-input"
                      rows={5}
                      placeholder="Add custom system instructions for Hermes in this workspace..."
                      value={workspacePrompt}
                      onChange={(e) => setWorkspacePrompt(e.target.value)}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        padding: "var(--space-xs)",
                        fontSize: "0.75rem",
                        outline: "none",
                        borderRadius: "var(--radius-sm)",
                        fontFamily: "var(--font-mono)",
                        resize: "vertical",
                      }}
                    />
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-xs)",
                  }}
                >
                  <span
                    style={{
                      fontWeight: "bold",
                      marginBottom: "var(--space-xs)",
                      color: "var(--color-secondary)",
                    }}
                  >
                    File Exclusions & Limits
                  </span>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "2px",
                    }}
                  >
                    <label>Oversized Warning Threshold (MB)</label>
                    <input
                      data-testid="workspace-settings-git-threshold"
                      type="number"
                      min={1}
                      max={100}
                      value={gitLargeFileThreshold}
                      onChange={(e) =>
                        setGitLargeFileThreshold(parseInt(e.target.value) || 10)
                      }
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        padding: "4px var(--space-xs)",
                        fontSize: "0.75rem",
                        outline: "none",
                        borderRadius: "var(--radius-sm)",
                        width: "80px",
                      }}
                    />
                  </div>
                </div>

                <button
                  data-testid="workspace-settings-save-btn"
                  type="submit"
                  disabled={optionsLoading}
                  style={{
                    backgroundColor: "var(--color-secondary)",
                    color: "var(--color-surface-subtle)",
                    border: "none",
                    padding: "6px var(--space-md)",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "0.75rem",
                    borderRadius: "var(--radius-sm)",
                    marginTop: "var(--space-sm)",
                  }}
                >
                  Save Settings
                </button>
                {optionsSaved && (
                  <div
                    style={{
                      color: "var(--color-success)",
                      fontSize: "0.65rem",
                      textAlign: "center",
                    }}
                  >
                    ✓ Saved!
                  </div>
                )}
              </form>

              <div
                style={{
                  display: "flex",
                  gap: "var(--space-xs)",
                  marginTop: "var(--space-md)",
                }}
              >
                <button
                  data-testid="workspace-pull-btn"
                  onClick={handlePull}
                  disabled={optionsLoading || !remoteUrl}
                  style={{
                    flex: 1,
                    backgroundColor: "var(--color-surface-subtle)",
                    color: "var(--color-primary)",
                    border: "1px solid var(--color-border)",
                    cursor: "pointer",
                    padding: "4px",
                    fontSize: "0.7rem",
                    borderRadius: "var(--radius-sm)",
                  }}
                >
                  Pull
                </button>
                <button
                  data-testid="workspace-push-btn"
                  onClick={handlePush}
                  disabled={optionsLoading || !remoteUrl}
                  style={{
                    flex: 1,
                    backgroundColor: "var(--color-surface-subtle)",
                    color: "var(--color-primary)",
                    border: "1px solid var(--color-border)",
                    cursor: "pointer",
                    padding: "4px",
                    fontSize: "0.7rem",
                    borderRadius: "var(--radius-sm)",
                  }}
                >
                  Push
                </button>
              </div>
            </div>
          </div>
        )}

        {activeSidebar === "docs" && (
          <div
            style={{ display: "flex", flexDirection: "column", height: "100%" }}
          >
            <div
              style={{
                padding: "var(--space-md)",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "1px",
                borderBottom: "1px solid var(--color-border)",
                color: "var(--color-primary)",
              }}
            >
              Docs & Learning
            </div>
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                padding: "var(--space-md)",
                fontSize: "0.75rem",
                textAlign: "left",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-md)",
              }}
            >
              {[
                {
                  title: "Start Here",
                  body: "Use these references when you need install help, Hermes plugin details, or MCP tool guidance.",
                  links: [
                    [
                      "Wright quickstart",
                      "https://github.com/burhop/wright/blob/dev/docs/getting-started/quickstart-local.md",
                    ],
                    [
                      "Hermes plugin guide",
                      "https://github.com/burhop/wright/blob/dev/docs/getting-started/hermes-plugin.md",
                    ],
                    [
                      "Hermes desktop notes",
                      "https://github.com/burhop/wright/blob/dev/docs/hermes-desktop-wright.md",
                    ],
                    [
                      "MCP tools catalog",
                      "https://github.com/burhop/wright/blob/dev/docs/mcp-catalog/tools-list.md",
                    ],
                  ],
                },
              ].map((section) => (
                <div
                  key={section.title}
                  style={{
                    borderBottom: "1px solid var(--color-border)",
                    paddingBottom: "var(--space-sm)",
                  }}
                >
                  <h4
                    style={{
                      margin: 0,
                      fontWeight: 600,
                      fontSize: "0.85rem",
                      color: "var(--color-secondary)",
                    }}
                  >
                    {section.title}
                  </h4>
                  <p
                    style={{
                      margin: "6px 0",
                      fontSize: "0.7rem",
                      color: "var(--color-secondary)",
                      lineHeight: "1.4",
                    }}
                  >
                    {section.body}
                  </p>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                    }}
                  >
                    {section.links.map(([label, href]) => (
                      <a
                        key={href}
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        style={{
                          color: "var(--color-secondary)",
                          textDecoration: "underline",
                          textUnderlineOffset: "2px",
                          overflowWrap: "anywhere",
                        }}
                      >
                        {label}
                      </a>
                    ))}
                  </div>
                </div>
              ))}

              <div
                style={{
                  borderBottom: "1px solid var(--color-border)",
                  paddingBottom: "var(--space-sm)",
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    color: "var(--color-secondary)",
                  }}
                >
                  Suggested Prompts
                </h4>
                <p
                  style={{
                    margin: "6px 0",
                    fontSize: "0.7rem",
                    color: "var(--color-secondary)",
                    lineHeight: "1.4",
                  }}
                >
                  Send one of these to Hermes to bootstrap the current workspace
                  context.
                </p>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                  }}
                >
                  {[
                    [
                      "Explain this workspace",
                      "Summarize this Wright workspace. Identify the open files, available MCP tools, likely CAD workflow, and the next three useful actions.",
                    ],
                    [
                      "Check available CAD tools",
                      "List the MCP tools available in this session and explain which ones are useful for Onshape CAD creation, inspection, rendering, and export.",
                    ],
                    [
                      "Plan the next CAD step",
                      "Review the active design/specification files and propose a concise next-step plan before making any CAD changes.",
                    ],
                  ].map(([label, prompt]) => (
                    <button
                      key={label}
                      type="button"
                      onClick={() => sendMessageWithSurfaceContext(prompt)}
                      disabled={!activeSessionId || isActiveSessionStreaming}
                      style={{
                        backgroundColor: "var(--color-surface-subtle)",
                        color: "var(--color-primary)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-sm)",
                        padding: "6px 8px",
                        fontSize: "0.7rem",
                        fontWeight: 600,
                        textAlign: "left",
                        cursor:
                          !activeSessionId || isActiveSessionStreaming
                            ? "not-allowed"
                            : "pointer",
                        opacity:
                          !activeSessionId || isActiveSessionStreaming
                            ? 0.55
                            : 1,
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h4
                  style={{
                    margin: 0,
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    color: "var(--color-secondary)",
                  }}
                >
                  Workspace Notes
                </h4>
                <p
                  style={{
                    margin: "6px 0 0",
                    fontSize: "0.7rem",
                    color: "var(--color-secondary)",
                    lineHeight: "1.4",
                  }}
                >
                  Workspace Settings can add persistent context for Hermes. MCP
                  tools can be enabled from the MCP Tools Selector and are then
                  exposed to the active Hermes session.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Left Sidebar Resize Handle */}
      {!surfaceChromeHidden && !isSidebarCollapsed && (
        <div
          data-testid="left-resize-handle"
          style={{
            gridColumn: "3",
            width: "4px",
            cursor: "col-resize",
            backgroundColor: isLeftDragging
              ? "var(--color-secondary)"
              : "transparent",
            zIndex: 10,
            transition: "background-color 0.2s",
          }}
          onMouseDown={handleLeftMouseDown}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = "var(--color-secondary)";
          }}
          onMouseLeave={(e) => {
            if (!isLeftDragging)
              e.currentTarget.style.backgroundColor = "transparent";
          }}
        />
      )}

      {/* 3. Central Tabbed Editor View */}
      <div
        data-testid="workspace-surface-pane"
        style={{
          gridColumn:
            surfacesEnabled && surfaceLayout.mode === "narrow" ? "1" : "4",
          display:
            surfacesEnabled &&
            surfaceLayout.mode === "narrow" &&
            surfaceLayout.narrowPane !== "surface"
              ? "none"
              : "flex",
          flexDirection: "column",
          backgroundColor: "var(--color-neutral)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {surfacesEnabled && _workspaceId && workspaceFileSessionId && (
          <SurfaceWorkspace
            workspaceId={_workspaceId}
            sessionId={workspaceFileSessionId}
            focusMode={surfaceLayout.wideMode === "focus"}
            onEnterFocus={enterSurfaceFocus}
            onExitFocus={exitSurfaceFocus}
          />
        )}
        {openTabs.length > 0 && (
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              backgroundColor: "var(--color-neutral-dark, #121212)",
              paddingRight: "var(--space-md, 12px)",
            }}
          >
            <div style={{ flex: 1, overflow: "hidden" }}>
              <EditorTabs
                tabs={openTabs}
                activeTabPath={activeTabPath}
                onSelectTab={handleSelectTab}
                onCloseTab={handleCloseTab}
              />
            </div>
            {activeTabPath && (
              <button
                data-testid="workspace-tab-focus"
                aria-label={
                  surfaceLayout.wideMode === "focus"
                    ? "Restore workspace layout"
                    : "Maximize active tab"
                }
                onClick={() => {
                  if (surfaceLayout.wideMode === "focus") {
                    exitSurfaceFocus();
                  } else {
                    enterSurfaceFocus();
                  }
                }}
                style={{
                  width: 32,
                  height: 32,
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "transparent",
                  border: "1px solid transparent",
                  borderRadius: "var(--radius-sm, 4px)",
                  color:
                    surfaceLayout.wideMode === "focus"
                      ? "var(--color-secondary, #aaaaaa)"
                      : "var(--color-primary, #ffffff)",
                  opacity: 0.75,
                  cursor: "pointer",
                }}
                title={
                  surfaceLayout.wideMode === "focus"
                    ? "Restore workspace layout"
                    : "Maximize active tab"
                }
              >
                {surfaceLayout.wideMode === "focus" ? (
                  <MinimizeIcon size={16} />
                ) : (
                  <MaximizeIcon size={16} />
                )}
              </button>
            )}
            {activeTabPath && !activeDirectRivet && !activeDirectBrep && (
              <button
                data-testid="viewer-inspector-toggle"
                onClick={() => setIsInspectorOpen(!isInspectorOpen)}
                style={{
                  background: "none",
                  border: "none",
                  color: isInspectorOpen
                    ? "var(--color-secondary, #aaaaaa)"
                    : "var(--color-primary, #ffffff)",
                  opacity: 0.7,
                  cursor: "pointer",
                  padding: "8px",
                  fontSize: "0.9rem",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                title="Inspect Viewer Details"
              >
                <SearchIcon size={16} />
              </button>
            )}
          </div>
        )}

        <div
          style={{
            flex: 1,
            display: "flex",
            overflow: "hidden",
            position: "relative",
          }}
        >
          {directRivetTabs.map((tab) => {
            const slug = rivetSlugFromTabPath(tab.path) || "rivet";
            if (!_workspaceId || !workspaceFileSessionId) return null;
            const isActive = activeTabPath === tab.path;
            return (
              <div
                key={tab.path}
                data-testid={`retained-direct-rivet-panel-${slug}`}
                aria-hidden={!isActive}
                style={{
                  position: isActive ? "relative" : "absolute",
                  inset: isActive ? undefined : 0,
                  zIndex: isActive ? 1 : 0,
                  display: isActive ? "flex" : "none",
                  width: "100%",
                  height: "100%",
                  visibility: isActive ? "visible" : "hidden",
                  pointerEvents: isActive ? "auto" : "none",
                }}
              >
                <ManagedRivetSurface
                  workspaceId={_workspaceId}
                  sessionId={workspaceFileSessionId}
                  initialSlug={slug}
                  externalRevisionToken={
                    isActive ? rivetExternalRevisionToken : null
                  }
                  onWorkflowLoaded={(workflow) => {
                    updateTabPath(
                      tab.path,
                      directRivetTabPath(workflow.slug),
                      `${workflow.slug}.rivet-project`,
                    );
                  }}
                />
              </div>
            );
          })}
          {directBrepTabs.map((tab) => {
            const isActive = activeTabPath === tab.path;
            return (
              <div
                key={tab.path}
                data-testid="retained-direct-brep-panel"
                aria-hidden={!isActive}
                style={{
                  position: isActive ? "relative" : "absolute",
                  inset: isActive ? undefined : 0,
                  zIndex: isActive ? 1 : 0,
                  display: isActive ? "flex" : "none",
                  width: "100%",
                  height: "100%",
                  visibility: isActive ? "visible" : "hidden",
                  pointerEvents: isActive ? "auto" : "none",
                }}
              >
                <DirectBrepSurface sessionId={workspaceFileSessionId || ""} />
              </div>
            );
          })}
          {!activeDirectRivet && !activeDirectBrep && activeTabPath ? (
            <>
              <div
                ref={viewerContainerRef}
                data-testid="viewer-container"
                style={{ flex: 1, height: "100%", overflow: "hidden" }}
              />
              {isInspectorOpen && (
                <ViewerInspector
                  onClose={() => setIsInspectorOpen(false)}
                  isResponsive={!isUnresponsive}
                />
              )}
              {isUnresponsive && (
                <div
                  data-testid="watchdog-overlay"
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: "rgba(0, 0, 0, 0.75)",
                    backdropFilter: "blur(4px)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    zIndex: 1000,
                    color: "white",
                    fontFamily: "var(--font-ui)",
                    padding: "var(--space-lg)",
                  }}
                >
                  <div
                    style={{
                      backgroundColor: "var(--color-surface, #202020)",
                      border: "1px solid var(--color-error, #ef4444)",
                      borderRadius: "var(--radius-md, 8px)",
                      padding: "var(--space-lg)",
                      maxWidth: "400px",
                      textAlign: "center",
                      boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "2rem",
                        marginBottom: "var(--space-sm)",
                      }}
                    >
                      ⚠️
                    </div>
                    <h4
                      style={{
                        margin: "0 0 var(--space-sm)",
                        color: "var(--color-error, #ef4444)",
                      }}
                    >
                      Viewer Unresponsive
                    </h4>
                    <p
                      style={{
                        margin: "0 0 var(--space-lg)",
                        fontSize: "0.85rem",
                        opacity: 0.8,
                        lineHeight: 1.5,
                      }}
                    >
                      The viewer panel is not responding. You can try reloading
                      it, or close it to release resources.
                    </p>
                    <div
                      style={{
                        display: "flex",
                        gap: "var(--space-md)",
                        justifyContent: "center",
                      }}
                    >
                      <button
                        data-testid="watchdog-reload"
                        onClick={async () => {
                          if (activeTabPath) {
                            const fileNode = workspaceRoot
                              ? findFileInTree(workspaceRoot, activeTabPath)
                              : null;
                            if (fileNode) {
                              const ext =
                                activeTabPath.split(".").pop()?.toLowerCase() ||
                                "";
                              const name =
                                activeTabPath.split("/").pop() || activeTabPath;
                              const file: FileDescriptor = {
                                id: activeTabPath,
                                uri: activeTabPath,
                                name,
                                extension: ext,
                                mimeType:
                                  ext === "pdf"
                                    ? "application/pdf"
                                    : "text/plain",
                                size: fileNode?.size || undefined,
                                metadata: {
                                  last_modified: fileNode?.last_modified,
                                },
                              };
                              await reloadDocument(file);
                            }
                          }
                          setIsUnresponsive(false);
                        }}
                        style={{
                          backgroundColor: "var(--color-accent, #4f46e5)",
                          color: "white",
                          border: "none",
                          borderRadius: "var(--radius-sm, 4px)",
                          padding: "var(--space-xs) var(--space-md)",
                          cursor: "pointer",
                          fontSize: "0.85rem",
                          fontWeight: "600",
                        }}
                      >
                        Reload
                      </button>
                      <button
                        data-testid="watchdog-close"
                        onClick={() => {
                          if (activeTabPath) {
                            handleCloseTab(activeTabPath);
                          }
                        }}
                        style={{
                          backgroundColor: "rgba(255, 255, 255, 0.1)",
                          color: "var(--color-primary, #ffffff)",
                          border: "1px solid var(--color-border, #333333)",
                          borderRadius: "var(--radius-sm, 4px)",
                          padding: "var(--space-xs) var(--space-md)",
                          cursor: "pointer",
                          fontSize: "0.85rem",
                          fontWeight: "600",
                        }}
                      >
                        Close Tab
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : !activeDirectRivet && !activeDirectBrep ? (
            /* Welcome / landing screen when no tabs are open */
            <div
              data-testid="workspace-empty-state"
              style={{
                flex: 1,
                width: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                height: "100%",
                color: "var(--color-secondary)",
                fontFamily: "var(--font-ui)",
                gap: "var(--space-md)",
              }}
            >
              <div style={{ fontSize: "3rem", opacity: 0.4 }}>💻</div>
              <div
                style={{
                  fontSize: "0.9rem",
                  fontWeight: "600",
                  color: "var(--color-primary)",
                }}
              >
                Wright Engineering Workspace
              </div>
              <div
                style={{
                  fontSize: "0.75rem",
                  opacity: 0.6,
                  maxWidth: "280px",
                  textAlign: "center",
                  lineHeight: "1.4",
                }}
              >
                Click any file in the left sidebar explorer to open a viewer or
                code editor tab.
              </div>
            </div>
          ) : null}
        </div>

        {/* Diff Overlay Panel (if viewing git diff) */}
        {activeDiffFile && (
          <div
            style={{
              position: "absolute",
              top: "35px",
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: "var(--color-surface)",
              zIndex: 10,
              display: "flex",
              flexDirection: "column",
              padding: "var(--space-md)",
              borderTop: "1px solid var(--color-border)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "var(--space-sm)",
                fontSize: "0.8rem",
              }}
            >
              <span style={{ fontWeight: "bold" }}>
                Diff: {activeDiffFile.path}
              </span>
              <div style={{ display: "flex", gap: "var(--space-xs)" }}>
                <button
                  onClick={() => handleRevert(activeDiffFile.path)}
                  style={{
                    backgroundColor: "var(--color-error)",
                    color: "white",
                    border: "none",
                    borderRadius: "var(--radius-xs)",
                    padding: "2px var(--space-sm)",
                    cursor: "pointer",
                    fontSize: "0.7rem",
                  }}
                >
                  Revert
                </button>
                <button
                  onClick={() => setActiveDiffFile(null)}
                  style={{
                    background: "none",
                    border: "none",
                    color: "#ffffff",
                    cursor: "pointer",
                    fontSize: "0.9rem",
                  }}
                >
                  ✕
                </button>
              </div>
            </div>
            <div
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
              }}
            >
              <DiffViewer diffText={activeDiffFile.diffText} />
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar Resize Handle */}
      {(!surfacesEnabled || surfaceLayout.mode !== "narrow") &&
        !isAgentCollapsed &&
        (surfacesEnabled ? (
          <PaneSeparator
            valueBasisPoints={resolvedSurfaceLayout.chatBasisPoints}
            minimumBasisPoints={resolvedSurfaceLayout.minimumChatBasisPoints}
            maximumBasisPoints={resolvedSurfaceLayout.maximumChatBasisPoints}
            onChange={(value) =>
              surfaceLayoutDispatch({
                type: "set_chat_basis_points",
                value,
                containerWidth: surfacePaneContainerWidth,
              })
            }
          />
        ) : (
          <div
            data-testid="right-resize-handle"
            style={{
              gridColumn: "5",
              width: "4px",
              cursor: "col-resize",
              backgroundColor: isRightDragging
                ? "var(--color-secondary)"
                : "transparent",
              zIndex: 10,
              transition: "background-color 0.2s",
            }}
            onMouseDown={handleRightMouseDown}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--color-secondary)";
            }}
            onMouseLeave={(e) => {
              if (!isRightDragging)
                e.currentTarget.style.backgroundColor = "transparent";
            }}
          />
        ))}

      {/* 4. Right Sidebar Drawer (Agent chat) */}
      <div
        data-testid="agent-sidebar"
        data-focus-region="chat"
        style={{
          backgroundColor: "var(--color-surface)",
          borderLeft: "1px solid var(--color-border)",
          gridColumn:
            surfacesEnabled && surfaceLayout.mode === "narrow" ? "1" : "6",
          display:
            surfacesEnabled && surfaceLayout.mode === "narrow"
              ? surfaceLayout.narrowPane === "chat"
                ? "flex"
                : "none"
              : isAgentCollapsed
                ? "none"
                : "flex",
          flexDirection: "column",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {/* Agent Tools Window Header */}
        <div
          data-testid="agent-tools-window"
          style={{
            padding: "var(--space-sm) var(--space-md)",
            borderBottom: "1px solid var(--color-border)",
            backgroundColor: "var(--color-surface-subtle)",
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-xs)",
          }}
        >
          {/* Row 1: Title and Collapse */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: "bold",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                color: "#969696",
              }}
            >
              Agent Control Pane
            </span>
            <button
              onClick={() => setIsAgentCollapsed(true)}
              style={{
                background: "none",
                border: "none",
                color: "#858585",
                cursor: "pointer",
                fontSize: "0.8rem",
              }}
              title="Collapse Agent Console"
            >
              ▶
            </button>
          </div>

          {/* Row 2: Model and Session Selector + New Session Button */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xs)",
              width: "100%",
            }}
          >
            {/* Model Select */}
            <label htmlFor="llm-model-select" style={{ fontSize: "0.65rem" }}>
              Model
            </label>
            <select
              id="llm-model-select"
              data-testid="llm-model-select"
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={isLoadingModels || modelGroups.length === 0}
              style={{
                flex: 1,
                backgroundColor: "var(--color-surface-subtle)",
                color: "var(--color-primary)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "6px",
                fontSize: "0.75rem",
                outline: "none",
                cursor: "pointer",
                transition: "border-color var(--transition-fast)",
              }}
              title={modelError || "Select LLM Model"}
            >
              {renderModelOptions()}
            </select>
            {modelError ? (
              <span
                style={{
                  color: "var(--color-warning)",
                  fontSize: "0.65rem",
                }}
                title={modelError}
              >
                !
              </span>
            ) : null}

            <label
              htmlFor="workspace-session-select"
              style={{ fontSize: "0.65rem" }}
            >
              Session
            </label>
            <select
              id="workspace-session-select"
              data-testid="sessions-sidebar"
              value={activeSessionId || ""}
              onChange={async (e) => {
                const newSessId = e.target.value;
                if (newSessId) {
                  await selectChatSession(newSessId);
                }
              }}
              style={{
                flex: 1.5,
                backgroundColor: "var(--color-surface-subtle)",
                color: "var(--color-primary)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "6px",
                fontSize: "0.75rem",
                outline: "none",
                cursor: "pointer",
                textOverflow: "ellipsis",
                transition: "border-color var(--transition-fast)",
              }}
              title="Select Session Context"
            >
              {state.sessions.length === 0 ? (
                <option value="" data-testid="session-none">
                  No sessions
                </option>
              ) : (
                state.sessions.map((session) => (
                  <option
                    key={session.sessionId}
                    value={session.sessionId}
                    data-testid={`session-${session.sessionId}`}
                  >
                    {sessionOptionLabels.get(session.sessionId) ||
                      "Untitled Session"}
                  </option>
                ))
              )}
            </select>

            {/* New Session Button */}
            <button
              data-testid="create-session-btn"
              onClick={async () => {
                const newId = await createSession(workspacePath, _workspaceId);
                if (newId) {
                  await bindSessionToWorkspace(newId);
                }
              }}
              style={{
                backgroundColor: "var(--color-secondary)",
                color: "var(--color-surface-subtle)",
                border: "none",
                borderRadius: "var(--radius-md)",
                width: "28px",
                height: "28px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontWeight: "bold",
                fontSize: "0.9rem",
                transition:
                  "background-color var(--transition-fast), box-shadow var(--transition-fast)",
                boxShadow: "var(--shadow-glow)",
              }}
              title="Create New Session"
            >
              ＋
            </button>
          </div>
        </div>

        {isAgentDisconnected && (
          <div
            data-testid="health-banner-hermes"
            style={{
              backgroundColor: "rgba(239, 68, 68, 0.1)",
              borderBottom: "1px solid rgba(239, 68, 68, 0.2)",
              color: "var(--color-error, #f87171)",
              padding: "var(--space-sm) var(--space-md)",
              fontSize: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xs)",
              fontFamily: "var(--font-ui)",
            }}
          >
            <span
              title={agentError || undefined}
              style={{ lineHeight: 1.35, overflowWrap: "anywhere" }}
            >
              Hermes agent is not available.
              {agentError
                ? ` ${agentError}`
                : " Check that the wright profile WebUI is running."}
            </span>
          </div>
        )}

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ flex: 1, overflowY: "auto" }}>
            <ChatTranscript
              session={activeSession}
              isStreaming={isActiveSessionStreaming}
              streamStartedAt={activeSessionStreamState?.startedAt ?? null}
              streamedText={activeSessionStreamedText}
              activeTool={activeSessionTool}
              streamActivity={activeSessionStreamActivity}
              onOpenFile={handleFileClick}
              activeSessionId={activeSessionId || undefined}
              workspacePath={workspacePath || undefined}
            />
          </div>

          {activeSession && (
            <div
              style={{
                padding: "var(--space-md)",
                borderTop: "1px solid var(--color-border)",
                backgroundColor: "var(--color-surface-subtle)",
              }}
            >
              <MessageComposer
                onSend={sendMessageWithSurfaceContext}
                onSteer={steerMessageWithSurfaceContext}
                isStreaming={isActiveSessionStreaming}
                onCancel={cancelActiveStream}
                sessionId={activeSessionId || undefined}
                workspaceId={_workspaceId}
                queuedPrompts={activeSessionQueuedPrompts}
              />
            </div>
          )}
        </div>
      </div>

      {/* Floating Expand button for Right Agent Drawer if collapsed */}
      {isAgentCollapsed &&
        (!surfacesEnabled || surfaceLayout.wideMode !== "focus") &&
        (!surfacesEnabled || surfaceLayout.mode !== "narrow") && (
          <button
            data-testid="agent-sidebar-toggle"
            onClick={() => setIsAgentCollapsed(false)}
            style={{
              position: "absolute",
              right: "var(--space-md)",
              top: "var(--space-md)",
              backgroundColor: "var(--color-secondary)",
              color: "var(--color-surface-subtle)",
              border: "none",
              borderRadius: "50%",
              width: "36px",
              height: "36px",
              cursor: "pointer",
              boxShadow: "var(--shadow-glow-active)",
              zIndex: 10,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.8rem",
              fontWeight: "bold",
              transition:
                "background-color var(--transition-fast), box-shadow var(--transition-fast)",
            }}
            title="Open Agent Console"
          >
            ◀
          </button>
        )}
    </WorkspaceLayout>
  );
}

export default WorkspacePanel;
