import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import FileTree from "../common/FileTree";
import ThreeDViewer from "../common/ThreeDViewer";
import DiffViewer from "../common/DiffViewer";
import EditorTabs from "../common/EditorTabs";
import FileEditor from "../common/FileEditor";
import ImagePreviewer from "../common/ImagePreviewer";
import { useChat } from "../../store/sessions";
import {
  workspaceService,
  type WorkspaceNode,
  type WorkspaceInfo,
  MergeConflictError,
} from "../../services/workspace-service";
import { agentService } from "../../services/agent-service";
import useHealthStatus from "../../hooks/useHealthStatus";
import ChatTranscript from "./ChatTranscript";
import MessageComposer from "./MessageComposer";
import {
  FolderIcon,
  GitIcon,
  SettingsIcon,
  BackIcon,
  MCPIcon,
  BookOpenIcon,
} from "../common/Icons";

import type { EditorTab } from "../../store/types";

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
  onSessionChange?: (sessionId: string) => void;
}

export function WorkspacePanel({
  workspaceId: _workspaceId,
  sessionId: propSessionId,
  onSessionChange,
}: WorkspacePanelProps) {
  const { state, createSession, selectSession, sendMessage, refreshSessions, cancelActiveStream } = useChat();
  const navigate = useNavigate();

  // Refresh sessions when workspace changes
  useEffect(() => {
    refreshSessions(_workspaceId);
  }, [_workspaceId, refreshSessions]);

  // Fetch workspace details when workspace changes
  useEffect(() => {
    if (!_workspaceId) return;
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
  }, [_workspaceId]);

  // Sync the prop sessionId into global chat state on mount or when the prop changes.
  // Only depend on propSessionId to avoid loops from context-value churn.
  useEffect(() => {
    if (propSessionId) {
      selectSession(propSessionId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [propSessionId]);

  // Always prefer the workspace-specific session from the route over the
  // ChatProvider's globally-active session (which may belong to a different workspace).
  const activeSessionId = propSessionId || state.activeSessionId;
  const statuses = useHealthStatus();
  const agentStatus = statuses.find(
    (s) => s.serviceId === "hermes-agent",
  )?.state;
  const isAgentDisconnected = agentStatus === "disconnected";

  const activeSession =
    state.sessions.find((s) => s.sessionId === activeSessionId) || null;

  // Load active agent on mount
  useEffect(() => {
    const fetchActiveAgent = async () => {
      try {
        const active = await agentService.getActiveAgent();
        if (active === "hermes") setSelectedModel("Hermes");
        else if (active === "openclaw") setSelectedModel("openclaw");
        else if (active === "pi") setSelectedModel("PI");
        else if (active === "qwen") setSelectedModel("Qwen");
        else setSelectedModel(active);
      } catch (err) {
        console.error("Failed to fetch active agent from backend", err);
      }
    };
    fetchActiveAgent();
  }, []);

  const handleModelChange = async (newModel: string) => {
    setSelectedModel(newModel);
    try {
      await agentService.setActiveAgent(
        newModel.toLowerCase(),
        activeSessionId,
      );
    } catch (err) {
      console.error("Failed to change active agent on backend", err);
    }
  };

  // --- Layout state persistence via localStorage ---
  const layoutKey = useMemo(
    () => (propSessionId ? `wright-workspace-layout-${propSessionId}` : null),
    [propSessionId],
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
  const [activeSidebar, setActiveSidebar] = useState<
    "marketplace" | "files" | "git" | "settings" | "docs"
  >(savedLayout?.activeSidebar ?? "files");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(
    savedLayout?.isSidebarCollapsed ?? false,
  );
  const [isAgentCollapsed, setIsAgentCollapsed] = useState<boolean>(
    savedLayout?.isAgentCollapsed ?? false,
  );
  const [openTabs, setOpenTabs] = useState<EditorTab[]>(
    savedLayout?.openTabs ?? [],
  );
  const [activeTabPath, setActiveTabPath] = useState<string | null>(
    savedLayout?.activeTabPath ?? null,
  );

  // Resize and model states
  const [leftSidebarWidth, setLeftSidebarWidth] = useState<number>(
    savedLayout?.leftSidebarWidth ?? 260,
  );
  const [rightSidebarWidth, setRightSidebarWidth] = useState<number>(
    savedLayout?.rightSidebarWidth ?? 360,
  );
  const [isLeftDragging, setIsLeftDragging] = useState<boolean>(false);
  const [isRightDragging, setIsRightDragging] = useState<boolean>(false);
  const [selectedModel, setSelectedModel] = useState<string>("Hermes");

  // Workspace Config state
  const [workspacePrompt, setWorkspacePrompt] = useState("");
  const [gitLargeFileThreshold, setGitLargeFileThreshold] = useState<number>(10);

  // Compact MCP tools state
  const [mcpServers, setMcpServers] = useState<any[]>([]);
  const [enabledTools, setEnabledTools] = useState<string[]>([]);
  const [mcpLoading, setMcpLoading] = useState(false);

  const installedServers = mcpServers.filter((s) => s.is_installed);

  // File tree expanded directories — persisted so the tree stays open across refresh
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(
    () => new Set<string>(savedLayout?.expandedPaths ?? []),
  );

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
        openTabs,
        activeTabPath,
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

  // File loading states
  const [loadedContents, setLoadedContents] = useState<Record<string, any>>({});
  const [loadingContentPath, setLoadingContentPath] = useState<string | null>(
    null,
  );

  const [workspaceRoot, setWorkspaceRoot] = useState<WorkspaceNode | null>(
    null,
  );
  const [workspaceInfo, setWorkspaceInfo] = useState<WorkspaceInfo | null>(null);
  const [workspacePath, setWorkspacePath] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Git state
  const [gitBranch, setGitBranch] = useState<string>("main");
  const [gitChanges, setGitChanges] = useState<
    { path: string; git_status: string; staged: boolean; file_size?: number }[]
  >([]);
  const [gitHistory, setGitHistory] = useState<
    {
      commit_hash: string;
      message: string;
      author: string;
      timestamp: number;
    }[]
  >([]);
  const [commitMessage, setCommitMessage] = useState("");
  const [gitLoading, setGitLoading] = useState(false);
  const [gitError, setGitError] = useState<string | null>(null);
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

  // Keep compatibility with webmcp event integration
  useEffect(() => {
    const handleWebMcpRequest = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { callId, method } = customEvent.detail || {};

      if (!callId) return;

      if (method === "get_selected_part") {
        const responseEvent = new CustomEvent("webmcp:response", {
          detail: {
            callId,
            result: {
              partId: "part-aba8973b-31a8",
              dimensions: [12.0, 5.5, 2.3],
            },
          },
        });
        window.dispatchEvent(responseEvent);
      }
    };

    window.addEventListener("webmcp:request", handleWebMcpRequest);
    return () => {
      window.removeEventListener("webmcp:request", handleWebMcpRequest);
    };
  }, []);

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

  // Load active tab content dynamically
  useEffect(() => {
    if (!activeTabPath || !activeSessionId) return;
    if (loadedContents[activeTabPath] !== undefined) return;

    let isMounted = true;
    const fetchTabContent = async () => {
      setLoadingContentPath(activeTabPath);
      try {
        const ext = activeTabPath.split(".").pop()?.toLowerCase() || "";
        if (
          ext === "stl" ||
          ["png", "jpg", "jpeg", "svg", "gif", "webp", "bmp"].includes(ext)
        ) {
          const buffer = await workspaceService.getFileContentArrayBuffer(
            activeSessionId,
            activeTabPath,
          );
          if (isMounted) {
            setLoadedContents((prev) => ({ ...prev, [activeTabPath]: buffer }));
          }
        } else {
          const text = await workspaceService.getFileContentText(
            activeSessionId,
            activeTabPath,
          );
          if (isMounted) {
            setLoadedContents((prev) => ({ ...prev, [activeTabPath]: text }));
          }
        }
      } catch (err) {
        console.error("Failed to fetch tab content:", err);
      } finally {
        if (isMounted) setLoadingContentPath(null);
      }
    };

    fetchTabContent();
    return () => {
      isMounted = false;
    };
  }, [activeTabPath, activeSessionId, loadedContents]);

  // Workspace Polling Loop for disk changes
  useEffect(() => {
    if (!activeSessionId) {
      setWorkspaceRoot(null);
      setLoading(false);
      return;
    }

    let isMounted = true;

    const fetchWorkspace = async (isInitial = false) => {
      if (isInitial) setLoading(true);
      try {
        const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
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
              fileNode.last_modified > activeTabObj.last_modified
            ) {
              console.log(
                `Hot-reloading disk modifications for: ${currentPath}`,
              );
              try {
                const ext = currentPath.split(".").pop()?.toLowerCase() || "";
                if (
                  ext === "stl" ||
                  ["png", "jpg", "jpeg", "svg", "gif", "webp", "bmp"].includes(ext)
                ) {
                  const updatedBuffer =
                    await workspaceService.getFileContentArrayBuffer(
                      activeSessionId,
                      currentPath,
                    );
                  if (!isMounted) return;
                  setLoadedContents((prev) => ({
                    ...prev,
                    [currentPath]: updatedBuffer,
                  }));
                } else {
                  const updatedText = await workspaceService.getFileContentText(
                    activeSessionId,
                    currentPath,
                  );
                  if (!isMounted) return;
                  setLoadedContents((prev) => ({
                    ...prev,
                    [currentPath]: updatedText,
                  }));
                }
                // Update tab's timestamp record
                setOpenTabs((prev) =>
                  prev.map((t) =>
                    t.path === currentPath
                      ? { ...t, last_modified: fileNode.last_modified }
                      : t,
                  ),
                );
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
        if (isMounted && isInitial) setLoading(false);
      }
    };

    fetchWorkspace(true);

    const intervalId = setInterval(() => {
      fetchWorkspace(false);
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, [activeSessionId]);

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
  const handleCommit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSessionId || !commitMessage.trim()) return;
    setGitLoading(true);
    setGitError(null);
    try {
      await workspaceService.commitChanges(
        activeSessionId,
        commitMessage.trim(),
      );
      setCommitMessage("");
      const tree = await workspaceService.getWorkspaceFiles(activeSessionId);
      setWorkspaceRoot(tree);
      await fetchGitData();
    } catch (err: unknown) {
      setGitError(err instanceof Error ? err.message : "Commit failed");
    } finally {
      setGitLoading(false);
    }
  };

  const handleViewDiff = async (filePath: string) => {
    if (!activeSessionId) return;
    setGitLoading(true);
    setGitError(null);
    try {
      const diffText = await workspaceService.getGitDiff(
        activeSessionId,
        filePath,
      );
      setActiveDiffFile({ path: filePath, diffText });
    } catch (err: unknown) {
      setGitError(err instanceof Error ? err.message : "Failed to view diff");
    } finally {
      setGitLoading(false);
    }
  };

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

    const ext = path.split(".").pop()?.toLowerCase() || "";
    let tabType: "stl" | "image" | "code" | "text" = "text";
    if (ext === "stl") {
      tabType = "stl";
    } else if (["png", "jpg", "jpeg", "svg", "gif", "webp", "bmp"].includes(ext)) {
      tabType = "image";
    } else if (["py", "scad", "json", "md", "txt"].includes(ext)) {
      tabType = "code";
    }

    const fileName = path.split("/").pop() || path;

    const existingTab = openTabs.find((t) => t.path === path);
    if (!existingTab) {
      let fileNode: WorkspaceNode | null = null;
      if (workspaceRoot) {
        fileNode = findFileInTree(workspaceRoot, path);
      }
      const newTab: EditorTab = {
        path,
        name: fileName,
        type: tabType,
        isDirty: false,
        last_modified: fileNode ? fileNode.last_modified : Date.now(),
      };
      setOpenTabs([...openTabs, newTab]);
    }
    setActiveTabPath(path);
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
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === oldPath
            ? { ...t, path: newPath, name: newPath.split("/").pop() || newPath }
            : t,
        ),
      );
      if (activeTabPath === oldPath) {
        setActiveTabPath(newPath);
      }
      // Migrate contents cache
      if (loadedContents[oldPath] !== undefined) {
        setLoadedContents((prev) => {
          const updated = { ...prev, [newPath]: prev[oldPath] };
          delete updated[oldPath];
          return updated;
        });
      }
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

      if (activeTabPath === sourcePath) {
        setActiveTabPath(destPath);
      }
    } catch (err: unknown) {
      console.error("Failed to move file node:", err);
      throw err;
    }
  };

  const handleCloseTab = (path: string) => {
    const remaining = openTabs.filter((t) => t.path !== path);
    setOpenTabs(remaining);

    // Clear content cache to free memory
    setLoadedContents((prev) => {
      const updated = { ...prev };
      delete updated[path];
      return updated;
    });

    if (activeTabPath === path) {
      setActiveTabPath(
        remaining.length > 0 ? remaining[remaining.length - 1].path : null,
      );
    }
  };

  const handleSelectTab = (path: string) => {
    setActiveTabPath(path);
  };

  const handleSaveStatusChange = (path: string, isDirty: boolean) => {
    setOpenTabs((prev) =>
      prev.map((t) => (t.path === path ? { ...t, isDirty } : t)),
    );
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
  const handleActivityBarClick = (
    sidebar: "marketplace" | "files" | "git" | "settings" | "docs",
  ) => {
    if (activeSidebar === sidebar) {
      setIsSidebarCollapsed(!isSidebarCollapsed);
    } else {
      setActiveSidebar(sidebar);
      setIsSidebarCollapsed(false);
    }
  };

  // Helper to construct API URL
  const getApiUrl = (path: string) => {
    const host = window.location.hostname;
    const port = window.location.port;
    const base =
      port === "5173" || port === "5174" ? `http://${host}:8000` : "";
    return `${base}${path}`;
  };

  const fetchMcpData = useCallback(async () => {
    if (!activeSessionId) return;
    setMcpLoading(true);
    try {
      const serversRes = await fetch(getApiUrl("/api/mcp/servers"));
      if (serversRes.ok) {
        const data = await serversRes.json();
        setMcpServers(data.servers || []);
      }
      
      const enabledList = await workspaceService.getWorkspaceTools(activeSessionId);
      setEnabledTools(enabledList || []);
    } catch (err) {
      console.error("Failed to load compact MCP list", err);
    } finally {
      setMcpLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    if (activeSidebar === "marketplace") {
      fetchMcpData();
    }
  }, [activeSidebar, fetchMcpData]);

  const handleToggleMcpTool = async (serverName: string, currentlyEnabled: boolean) => {
    if (!activeSessionId) return;
    try {
      await workspaceService.toggleWorkspaceTool(activeSessionId, serverName, !currentlyEnabled);
      // Re-fetch enabled tools list
      const enabledList = await workspaceService.getWorkspaceTools(activeSessionId);
      setEnabledTools(enabledList || []);
    } catch (err) {
      console.error("Failed to toggle MCP tool", err);
    }
  };

  const activeTabObj = openTabs.find((t) => t.path === activeTabPath);

  return (
    <div
      data-testid="workspace-panel"
      style={{
        display: "grid",
        gridTemplateColumns: `48px ${isSidebarCollapsed ? "0px" : `${leftSidebarWidth}px`} ${isSidebarCollapsed ? "0px" : "4px"} 1fr ${isAgentCollapsed ? "0px" : "4px"} ${isAgentCollapsed ? "0px" : `${rightSidebarWidth}px`}`,
        height: "100%",
        width: "100%",
        backgroundColor: "var(--color-neutral)",
        color: "var(--color-primary)",
        overflow: "hidden",
        transition:
          isLeftDragging || isRightDragging
            ? "none"
            : "grid-template-columns 0.15s ease-out",
      }}
    >
      {/* 1. Activity Bar (far left) */}
      <div
        style={{
          backgroundColor: "var(--color-surface-subtle)",
          borderRight: "1px solid var(--color-border)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          paddingTop: "var(--space-md)",
          gap: "var(--space-md)",
          zIndex: 5,
        }}
      >
        <button
          data-testid="activity-bar-back-btn"
          onClick={() => navigate("/")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity: 0.45,
            color: "var(--color-primary)",
          }}
          title="Back to Dashboard"
          className="activity-bar-icon"
        >
          <BackIcon size={20} />
        </button>
        <button
          data-testid="activity-bar-explorer-btn"
          onClick={() => handleActivityBarClick("files")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity:
              !isSidebarCollapsed && activeSidebar === "files" ? 1 : 0.45,
            color:
              !isSidebarCollapsed && activeSidebar === "files"
                ? "var(--color-secondary)"
                : "var(--color-primary)",
          }}
          title="Workspace Files"
          className="activity-bar-icon"
        >
          <FolderIcon size={20} />
        </button>
        <button
          data-testid="activity-bar-mcp-btn"
          onClick={() => handleActivityBarClick("marketplace")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity:
              !isSidebarCollapsed && activeSidebar === "marketplace" ? 1 : 0.45,
            color:
              !isSidebarCollapsed && activeSidebar === "marketplace"
                ? "var(--color-secondary)"
                : "var(--color-primary)",
          }}
          title="MCP Tools"
          className="activity-bar-icon"
        >
          <MCPIcon size={20} />
        </button>
        <button
          data-testid="activity-bar-git-btn"
          onClick={() => handleActivityBarClick("git")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity: !isSidebarCollapsed && activeSidebar === "git" ? 1 : 0.45,
            color:
              !isSidebarCollapsed && activeSidebar === "git"
                ? "var(--color-secondary)"
                : "var(--color-primary)",
          }}
          title="Git Version Control"
          className="activity-bar-icon"
        >
          <GitIcon size={20} />
        </button>
        <button
          data-testid="activity-bar-settings-btn"
          onClick={() => handleActivityBarClick("settings")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity:
              !isSidebarCollapsed && activeSidebar === "settings" ? 1 : 0.45,
            color:
              !isSidebarCollapsed && activeSidebar === "settings"
                ? "var(--color-secondary)"
                : "var(--color-primary)",
          }}
          title="Workspace Settings"
          className="activity-bar-icon"
        >
          <SettingsIcon size={20} />
        </button>
        <button
          data-testid="activity-bar-docs-btn"
          onClick={() => handleActivityBarClick("docs")}
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: "var(--space-xs)",
            opacity:
              !isSidebarCollapsed && activeSidebar === "docs" ? 1 : 0.45,
            color:
              !isSidebarCollapsed && activeSidebar === "docs"
                ? "var(--color-secondary)"
                : "var(--color-primary)",
          }}
          title="Docs & Tutorials"
          className="activity-bar-icon"
        >
          <BookOpenIcon size={20} />
        </button>
      </div>

      {/* 2. Left Sidebar Panel (collapsible) */}
      <div
        data-testid="workspace-sidebar"
        style={{
          backgroundColor: "var(--color-surface)",
          borderRight: "1px solid var(--color-border)",
          display: isSidebarCollapsed ? "none" : "flex",
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
            <div style={{ flex: 1, overflowY: "auto", padding: "var(--space-md)" }}>
              {mcpLoading ? (
                <div style={{ color: "var(--color-secondary)", fontSize: "0.75rem" }}>Loading workspace tools...</div>
              ) : installedServers.length === 0 ? (
                <div style={{ color: "var(--color-secondary)", fontSize: "0.75rem" }}>No MCP servers configured.</div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
                  {installedServers.map((server) => {
                    const isEnabled = enabledTools.includes(server.name) || enabledTools.includes(server.server_id);
                    const isGloballyActive = server.is_active;

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
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px", textAlign: "left", flex: 1 }}>
                          <span style={{ fontWeight: "600", fontSize: "0.8rem", color: "var(--color-primary)" }}>
                            {server.name}
                          </span>
                          <span style={{ fontSize: "0.65rem", color: "var(--color-secondary)", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", maxWidth: "180px" }}>
                            {server.description || `MCP type: ${server.type}`}
                          </span>
                          <div style={{ display: "flex", alignItems: "center", gap: "4px", marginTop: "2px" }}>
                            <span
                              style={{
                                width: "5px",
                                height: "5px",
                                borderRadius: "50%",
                                backgroundColor: isGloballyActive ? "var(--color-success)" : "#858585",
                              }}
                            />
                            <span style={{ fontSize: "0.6rem", color: "var(--color-secondary)" }}>
                              {isGloballyActive ? "active" : "inactive"}
                            </span>
                          </div>
                        </div>
                        <input
                          data-testid={`mcp-toggle-${server.name.toLowerCase()}`}
                          type="checkbox"
                          checked={isEnabled}
                          onChange={() => handleToggleMcpTool(server.name, isEnabled)}
                          style={{ cursor: "pointer" }}
                        />
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
              Git Version Control
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
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-xs)",
                  marginBottom: "var(--space-md)",
                  backgroundColor: "var(--color-surface-subtle)",
                  padding: "var(--space-sm)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-md)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: "600" }}>Branch: 🌿 {gitBranch}</span>
                </div>
                <div style={{ display: "flex", gap: "var(--space-xs)", marginTop: "2px" }}>
                  <button
                    data-testid="git-new-branch-btn"
                    onClick={async () => {
                      const name = prompt("Enter new branch name:");
                      if (!name || !name.trim()) return;
                      if (!activeSessionId) return;
                      setGitLoading(true);
                      try {
                        await workspaceService.checkoutBranch(activeSessionId, name.trim(), true);
                        alert(`Created and switched to branch: ${name}`);
                        await fetchGitData();
                      } catch (err: any) {
                        alert(err.message || "Failed to create branch");
                      } finally {
                        setGitLoading(false);
                      }
                    }}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      padding: "3px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      borderRadius: "var(--radius-sm)",
                      fontWeight: "600",
                      color: "var(--color-primary)",
                    }}
                  >
                    New Branch
                  </button>
                  <button
                    data-testid="git-merge-btn"
                    onClick={async () => {
                      const name = prompt("Enter branch name to merge into current branch:");
                      if (!name || !name.trim()) return;
                      if (!activeSessionId) return;
                      setGitLoading(true);
                      try {
                        const res = await workspaceService.mergeBranch(activeSessionId, name.trim());
                        alert(res.message || "Branch merged successfully");
                        await fetchGitData();
                      } catch (err: any) {
                        alert(err.message || "Failed to merge branch");
                      } finally {
                        setGitLoading(false);
                      }
                    }}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      padding: "3px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      borderRadius: "var(--radius-sm)",
                      fontWeight: "600",
                      color: "var(--color-primary)",
                    }}
                  >
                    Merge
                  </button>
                </div>

                <div style={{ display: "flex", gap: "var(--space-xs)", marginTop: "2px" }}>
                  <button
                    data-testid="git-pull-btn"
                    onClick={async () => {
                      setGitLoading(true);
                      try {
                        await handlePull();
                      } catch (err) {
                        // Handled inside handlePull
                      } finally {
                        setGitLoading(false);
                      }
                    }}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      padding: "3px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      borderRadius: "var(--radius-sm)",
                      fontWeight: "600",
                      color: "var(--color-primary)",
                    }}
                  >
                    Pull
                  </button>
                  <button
                    data-testid="git-push-btn"
                    onClick={async () => {
                      setGitLoading(true);
                      try {
                        await handlePush();
                      } catch (err) {
                        // Handled inside handlePush
                      } finally {
                        setGitLoading(false);
                      }
                    }}
                    style={{
                      flex: 1,
                      backgroundColor: "var(--color-surface)",
                      border: "1px solid var(--color-border)",
                      padding: "3px",
                      cursor: "pointer",
                      fontSize: "0.65rem",
                      borderRadius: "var(--radius-sm)",
                      fontWeight: "600",
                      color: "var(--color-primary)",
                    }}
                  >
                    Push
                  </button>
                </div>
              </div>

              {gitError && (
                <div
                  style={{
                    color: "var(--color-error)",
                    fontSize: "0.7rem",
                    marginBottom: "var(--space-sm)",
                  }}
                >
                  ⚠️ {gitError}
                </div>
              )}

              <form
                onSubmit={handleCommit}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-xs)",
                  marginBottom: "var(--space-md)",
                }}
              >
                <input
                  type="text"
                  placeholder="Commit message..."
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  style={{
                    backgroundColor: "var(--color-surface-subtle)",
                    color: "var(--color-primary)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-sm)",
                    padding: "4px var(--space-sm)",
                    fontSize: "0.75rem",
                    outline: "none",
                  }}
                />
                <button
                  type="submit"
                  disabled={
                    gitLoading ||
                    gitChanges.length === 0 ||
                    !commitMessage.trim()
                  }
                  style={{
                    backgroundColor: "var(--color-secondary)",
                    color: "var(--color-surface-subtle)",
                    border: "none",
                    borderRadius: "var(--radius-sm)",
                    padding: "5px",
                    cursor: "pointer",
                    fontWeight: "600",
                    fontSize: "0.7rem",
                    opacity:
                      gitChanges.length === 0 || !commitMessage.trim()
                        ? 0.6
                        : 1,
                  }}
                >
                  Commit Changes
                </button>
              </form>

              {/* Git Changes List */}
              <div style={{ marginBottom: "var(--space-md)" }}>
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>
                  Changes ({gitChanges.length})
                </div>
                {gitChanges.length === 0 ? (
                  <div style={{ fontSize: "0.7rem", opacity: 0.7 }}>
                    No unstaged changes.
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                    }}
                  >
                    {gitChanges.map((c) => {
                      const isOversized = c.file_size && c.file_size > (gitLargeFileThreshold * 1024 * 1024);
                      return (
                        <div
                          key={c.path}
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "2px",
                            padding: "6px",
                            backgroundColor: "var(--color-surface-subtle)",
                            border: `1px solid ${isOversized ? "var(--color-error)" : "var(--color-border)"}`,
                            borderRadius: "var(--radius-xs)",
                            fontSize: "0.7rem",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <span
                              style={{
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                maxWidth: "150px",
                              }}
                              title={c.path}
                            >
                              <strong style={{ marginRight: "6px" }}>
                                {c.git_status}
                              </strong>
                              {c.path}
                            </span>
                            <div style={{ display: "flex", gap: "2px" }}>
                              <button
                                onClick={() => handleViewDiff(c.path)}
                                style={{
                                  background: "none",
                                  border: "none",
                                  cursor: "pointer",
                                  fontSize: "0.75rem",
                                  color: "var(--color-primary)",
                                }}
                                title="View Diff"
                              >
                                🔍
                              </button>
                              <button
                                onClick={() => handleRevert(c.path)}
                                style={{
                                  background: "none",
                                  border: "none",
                                  cursor: "pointer",
                                  fontSize: "0.75rem",
                                  color: "var(--color-error)",
                                }}
                                title="Revert File"
                              >
                                ⎌
                              </button>
                            </div>
                          </div>

                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "2px" }}>
                            <span style={{ fontSize: "0.6rem", color: "var(--color-secondary)" }}>
                              {c.file_size ? `${(c.file_size / (1024 * 1024)).toFixed(2)} MB` : "unknown size"}
                            </span>
                            {isOversized && (
                              <span
                                style={{
                                  backgroundColor: "rgba(239, 68, 68, 0.15)",
                                  color: "var(--color-error)",
                                  padding: "1px 4px",
                                  borderRadius: "2px",
                                  fontSize: "0.55rem",
                                  fontWeight: "bold",
                                }}
                              >
                                ⚠️ OVERSIZED (&gt;{gitLargeFileThreshold}MB)
                              </span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Git History List */}
              <div style={{ marginTop: "var(--space-md)" }}>
                <div style={{ fontWeight: "600", marginBottom: "4px" }}>
                  History ({gitHistory.length})
                </div>
                {gitHistory.length === 0 ? (
                  <div style={{ fontSize: "0.7rem", opacity: 0.7 }}>
                    No commits found.
                  </div>
                ) : (
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                      maxHeight: "150px",
                      overflowY: "auto",
                    }}
                  >
                    {gitHistory.map((h) => (
                      <div
                        key={h.commit_hash}
                        style={{
                          padding: "4px",
                          backgroundColor: "var(--color-surface-subtle)",
                          borderRadius: "var(--radius-xs)",
                          display: "flex",
                          flexDirection: "column",
                          gap: "2px",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontSize: "0.6rem",
                            opacity: 0.7,
                          }}
                        >
                          <span>👤 {h.author}</span>
                          <span style={{ fontFamily: "monospace" }}>
                            {h.commit_hash.substring(0, 7)}
                          </span>
                        </div>
                        <span
                          style={{
                            fontWeight: "500",
                            color: "var(--color-primary)",
                            fontSize: "0.7rem",
                          }}
                        >
                          {h.message}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
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
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)", borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-md)", marginBottom: "var(--space-xs)" }}>
                  <span style={{ fontWeight: "bold", marginBottom: "var(--space-xs)", color: "var(--color-secondary)" }}>Git Credentials</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
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
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginTop: "var(--space-xs)" }}>
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
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px", marginTop: "var(--space-xs)" }}>
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

                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)", borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-md)", marginBottom: "var(--space-xs)" }}>
                  <span style={{ fontWeight: "bold", marginBottom: "var(--space-xs)", color: "var(--color-secondary)" }}>Hermes Prompt Context</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
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

                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)" }}>
                  <span style={{ fontWeight: "bold", marginBottom: "var(--space-xs)", color: "var(--color-secondary)" }}>File Exclusions & Limits</span>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <label>Oversized Warning Threshold (MB)</label>
                    <input
                      data-testid="workspace-settings-git-threshold"
                      type="number"
                      min={1}
                      max={100}
                      value={gitLargeFileThreshold}
                      onChange={(e) => setGitLargeFileThreshold(parseInt(e.target.value) || 10)}
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
              <div style={{ borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-sm)" }}>
                <h4 style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--color-secondary)" }}>
                  💡 Customizing Hermes Prompt
                </h4>
                <p style={{ marginTop: "4px", fontSize: "0.7rem", color: "var(--color-secondary)", lineHeight: "1.4" }}>
                  Use the <strong>Workspace Settings</strong> tab to supply custom context prompt overlays. This context is synced immediately with the local `.hermes.md` file and injected into Hermes's environment for specialized code generations.
                </p>
              </div>

              <div style={{ borderBottom: "1px solid var(--color-border)", paddingBottom: "var(--space-sm)" }}>
                <h4 style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--color-secondary)" }}>
                  🌿 Managing Branches & Merges
                </h4>
                <p style={{ marginTop: "4px", fontSize: "0.7rem", color: "var(--color-secondary)", lineHeight: "1.4" }}>
                  To create a new workspace task branch, use the <strong>New Branch</strong> button. Check out or switch branches seamlessly. Use the <strong>Merge</strong> tool to consolidate branch features into your active branch context.
                </p>
              </div>

              <div>
                <h4 style={{ fontWeight: 600, fontSize: "0.85rem", color: "var(--color-secondary)" }}>
                  🛠 Active MCP Tools integration
                </h4>
                <p style={{ marginTop: "4px", fontSize: "0.7rem", color: "var(--color-secondary)", lineHeight: "1.4" }}>
                  Ensure you enable required MCP tools under the <strong>MCP Tools Selector</strong> tab. Toggled tools are dynamically exposed to the Hermes session prompt for real-time model interactions.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Left Sidebar Resize Handle */}
      {!isSidebarCollapsed && (
        <div
          data-testid="left-resize-handle"
          style={{
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
        style={{
          display: "flex",
          flexDirection: "column",
          backgroundColor: "var(--color-neutral)",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <EditorTabs
          tabs={openTabs}
          activeTabPath={activeTabPath}
          onSelectTab={handleSelectTab}
          onCloseTab={handleCloseTab}
        />

        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
          {activeTabPath ? (
            loadingContentPath === activeTabPath ? (
              <div
                style={{
                  display: "flex",
                  height: "100%",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--color-secondary)",
                  fontFamily: "var(--font-ui)",
                  fontSize: "0.8rem",
                }}
              >
                Loading file content...
              </div>
            ) : activeTabObj?.type === "stl" &&
              loadedContents[activeTabPath] ? (
              <ThreeDViewer
                arrayBuffer={loadedContents[activeTabPath]}
                fileName={activeTabObj.name}
              />
            ) : activeTabObj?.type === "image" &&
              loadedContents[activeTabPath] ? (
              <ImagePreviewer
                arrayBuffer={loadedContents[activeTabPath]}
                fileName={activeTabObj.name}
              />
            ) : (activeTabObj?.type === "code" ||
                activeTabObj?.type === "text") &&
              loadedContents[activeTabPath] !== undefined ? (
              <FileEditor
                sessionId={activeSessionId || ""}
                filePath={activeTabPath}
                initialContent={loadedContents[activeTabPath]}
                onSaveStatusChange={(isDirty) =>
                  handleSaveStatusChange(activeTabPath, isDirty)
                }
              />
            ) : (
              <div
                style={{
                  display: "flex",
                  height: "100%",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--color-secondary)",
                  fontFamily: "var(--font-ui)",
                  fontSize: "0.8rem",
                }}
              >
                Failed to render file or file is empty.
              </div>
            )
          ) : (
            /* Welcome / landing screen when no tabs are open */
            <div
              style={{
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
                Double-click any file in the left sidebar explorer to open a
                viewer or code editor tab.
              </div>
            </div>
          )}
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
      {!isAgentCollapsed && (
        <div
          data-testid="right-resize-handle"
          style={{
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
      )}

      {/* 4. Right Sidebar Drawer (Agent chat) */}
      <div
        data-testid="agent-sidebar"
        style={{
          backgroundColor: "var(--color-surface)",
          borderLeft: "1px solid var(--color-border)",
          display: isAgentCollapsed ? "none" : "flex",
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
            <select
              data-testid="llm-model-select"
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
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
              title="Select LLM Model"
            >
              <option value="Hermes">Hermes (Active)</option>
              <option value="Qwen">Qwen</option>
              <option value="openclaw">openclaw</option>
              <option value="PI">PI</option>
            </select>

            <select
              data-testid="sessions-sidebar"
              value={state.activeSessionId || ""}
              onChange={async (e) => {
                const newSessId = e.target.value;
                if (newSessId) {
                  selectSession(newSessId);
                  if (onSessionChange) {
                    onSessionChange(newSessId);
                  }
                  if (_workspaceId) {
                    try {
                      await workspaceService.updateWorkspaceSession(
                        _workspaceId,
                        newSessId,
                      );
                    } catch (err) {
                      console.error(
                        "Failed to update workspace session association",
                        err,
                      );
                    }
                  }
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
                    {session.title.length > 20
                      ? `${session.title.slice(0, 18)}...`
                      : session.title}
                  </option>
                ))
              )}
            </select>

            {/* New Session Button */}
            <button
              data-testid="create-session-btn"
              onClick={async () => {
                const newId = await createSession(workspacePath);
                if (newId) {
                  selectSession(newId);
                  if (onSessionChange) {
                    onSessionChange(newId);
                  }
                  if (_workspaceId) {
                    try {
                      await workspaceService.updateWorkspaceSession(
                        _workspaceId,
                        newId,
                      );
                    } catch (err) {
                      console.error(
                        "Failed to update workspace session association",
                        err,
                      );
                    }
                  }
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
              color: "#ef4444",
              padding: "var(--space-sm) var(--space-md)",
              fontSize: "0.75rem",
              display: "flex",
              alignItems: "center",
              gap: "var(--space-xs)",
              fontFamily: "var(--font-ui)",
            }}
          >
            <span>
              ⚠️ Hermes agent is not available. Check that the wright profile
              WebUI is running.
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
              isStreaming={state.isStreaming}
              streamedText={state.streamedText}
              activeTool={state.activeTool}
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
                onSend={sendMessage}
                isStreaming={state.isStreaming}
                onCancel={cancelActiveStream}
                sessionId={activeSessionId || undefined}
              />
            </div>
          )}
        </div>
      </div>

      {/* Floating Expand button for Right Agent Drawer if collapsed */}
      {isAgentCollapsed && (
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
    </div>
  );
}

export default WorkspacePanel;
