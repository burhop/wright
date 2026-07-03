import { logger } from "./logger";
import { hostAdapter } from "./host-adapter";
import type { SelectOptions } from "./host-adapter/wright-desktop";

const workspaceLogger = logger.child("WorkspaceService");

export interface WorkspaceNode {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number | null;
  last_modified: number;
  git_status: "Clean" | "M" | "U" | "A" | "D";
  children: WorkspaceNode[] | null;
}

const getApiBase = () => {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }
  const host = window.location.hostname;
  const port = window.location.port;
  if (port === "5173" || port === "5174") {
    return "";
  }
  return `${window.location.protocol}//${host}${port ? `:${port}` : ""}`;
};
export const API_BASE = getApiBase();

export class WorkspaceService {
  async getWorkspaceFiles(sessionId: string): Promise<WorkspaceNode> {
    workspaceLogger.info("Fetching workspace files", { sessionId });

    if (hostAdapter.mode === "desktop") {
      try {
        const config = await window.wrightDesktop?.getConfig();
        const rootPath = config?.workspacePath;
        if (rootPath) {
          return await this.buildWorkspaceTree(rootPath);
        }
      } catch (e: any) {
        workspaceLogger.error(
          "Failed to build workspace tree via IPC, falling back to HTTP",
          { error: e?.message || String(e) },
        );
      }
    }

    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace files", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace files: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.workspace;
  }

  private async buildWorkspaceTree(dirPath: string): Promise<WorkspaceNode> {
    const name = dirPath.split(/[/\\]/).pop() || dirPath;
    const entries = await hostAdapter.listDirectory(dirPath);
    const children: WorkspaceNode[] = [];

    for (const entry of entries) {
      if (entry.name === ".git" || entry.name === "node_modules") continue;

      if (entry.isDirectory) {
        const childNode = await this.buildWorkspaceTree(entry.path);
        children.push(childNode);
      } else {
        children.push({
          name: entry.name,
          path: entry.path,
          type: "file",
          size: entry.size || 0,
          last_modified: Date.now(),
          git_status: "Clean",
          children: null,
        });
      }
    }

    children.sort((a, b) => {
      if (a.type !== b.type) {
        return a.type === "directory" ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });

    return {
      name,
      path: dirPath,
      type: "directory",
      size: null,
      last_modified: Date.now(),
      git_status: "Clean",
      children,
    };
  }

  async getFileContentArrayBuffer(
    sessionId: string,
    filePath: string,
    backupId?: string,
  ): Promise<ArrayBuffer> {
    workspaceLogger.info("Fetching file content as ArrayBuffer", {
      sessionId,
      filePath,
      backupId,
    });
    if (hostAdapter.mode === "desktop" && !backupId) {
      const text = await hostAdapter.readFile(filePath);
      return new TextEncoder().encode(text).buffer;
    }
    const encodedPath = encodeURIComponent(filePath);
    let url = `${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`;
    if (backupId) {
      url += `&backup_id=${encodeURIComponent(backupId)}`;
    }
    const response = await hostAdapter.fetch(url);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch file content", {
        status: response.status,
      });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    return response.arrayBuffer();
  }

  async getFileContentText(
    sessionId: string,
    filePath: string,
    backupId?: string,
  ): Promise<string> {
    workspaceLogger.info("Fetching file content as text", {
      sessionId,
      filePath,
      backupId,
    });
    if (hostAdapter.mode === "desktop" && !backupId) {
      return hostAdapter.readFile(filePath);
    }
    const encodedPath = encodeURIComponent(filePath);
    let url = `${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`;
    if (backupId) {
      url += `&backup_id=${encodeURIComponent(backupId)}`;
    }
    const response = await hostAdapter.fetch(url);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch file content", {
        status: response.status,
      });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    const contentType = response.headers?.get?.("content-type");
    if (contentType && contentType.includes("application/json")) {
      const data = await response.json();
      return data.content;
    }
    return response.text();
  }

  async createFileNode(
    sessionId: string,
    filePath: string,
    nodeType: "file" | "directory",
  ): Promise<WorkspaceNode> {
    workspaceLogger.info("Creating workspace file node", {
      sessionId,
      filePath,
      nodeType,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          type: nodeType,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to create workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to create file/folder: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteFileNode(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info("Deleting workspace file node", {
      sessionId,
      filePath,
    });
    const encodedPath = encodeURIComponent(filePath);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files?session_id=${sessionId}&path=${encodedPath}`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to delete workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to delete file/folder: ${response.statusText}`);
    }
  }

  async moveFileNode(
    sessionId: string,
    sourcePath: string,
    destinationPath: string,
  ): Promise<boolean> {
    workspaceLogger.info("Moving workspace file node", {
      sessionId,
      sourcePath,
      destinationPath,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/move`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          source_path: sourcePath,
          destination_path: destinationPath,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to move workspace file node", {
        status: response.status,
      });
      throw new Error(`Failed to move file/folder: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getGitStatus(sessionId: string): Promise<{
    branch_name: string;
    is_clean: boolean;
    changes: {
      path: string;
      git_status: string;
      staged: boolean;
      file_size?: number;
    }[];
  }> {
    workspaceLogger.info("Fetching git status", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/status?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git status", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git status: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitDiff(sessionId: string, filePath: string): Promise<string> {
    workspaceLogger.info("Fetching git diff", { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/diff?session_id=${sessionId}&path=${encodedPath}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git diff", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git diff: ${response.statusText}`);
    }
    const data = await response.json();
    return data.diff;
  }

  async revertFile(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info("Reverting file changes", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/revert`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to revert file changes", {
        status: response.status,
      });
      throw new Error(`Failed to revert file changes: ${response.statusText}`);
    }
  }

  async commitChanges(
    sessionId: string,
    message: string,
  ): Promise<{
    success: boolean;
    commit_hash: string;
    message: string;
    timestamp: number;
  }> {
    workspaceLogger.info("Committing changes", { sessionId, message });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/commit`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to commit changes", {
        status: response.status,
      });
      throw new Error(`Failed to commit changes: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitHistory(
    sessionId: string,
    limit = 50,
  ): Promise<{
    commits: {
      commit_hash: string;
      message: string;
      author: string;
      timestamp: number;
    }[];
  }> {
    workspaceLogger.info("Fetching git history", { sessionId, limit });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/history?session_id=${sessionId}&limit=${limit}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch git history", {
        status: response.status,
      });
      throw new Error(`Failed to fetch git history: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceConfig(sessionId: string): Promise<{
    workspace_id: string;
    git_remote_url: string | null;
    git_username: string | null;
    has_token: boolean;
    workspace_path?: string;
    workspace_prompt?: string | null;
    git_large_file_threshold?: number | null;
  }> {
    workspaceLogger.info("Fetching workspace config", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/config?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace config", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace config: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async updateWorkspaceConfig(
    sessionId: string,
    remoteUrl: string | null,
    username: string | null,
    token: string | null,
    workspacePrompt?: string | null,
    gitLargeFileThreshold?: number | null,
  ): Promise<{ success: boolean; workspace_id: string }> {
    workspaceLogger.info("Updating workspace config", {
      sessionId,
      remoteUrl,
      username,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/config`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          git_remote_url: remoteUrl,
          git_username: username,
          git_token: token,
          workspace_prompt: workspacePrompt,
          git_large_file_threshold: gitLargeFileThreshold,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to update workspace config", {
        status: response.status,
      });
      throw new Error(
        `Failed to update workspace config: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async pushCommits(
    sessionId: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Pushing commits to remote", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/push`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to push commits", {
        status: response.status,
      });
      throw new Error(`Failed to push changes: ${response.statusText}`);
    }
    return response.json();
  }

  async pullCommits(
    sessionId: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Pulling commits from remote", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/pull`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      },
    );
    if (response.status === 409) {
      const data = await response.json();
      throw new MergeConflictError(
        data.message || "Pull resulted in merge conflicts",
        data.conflicted_files || [],
      );
    }
    if (!response.ok) {
      workspaceLogger.error("Failed to pull commits", {
        status: response.status,
      });
      throw new Error(`Failed to pull changes: ${response.statusText}`);
    }
    return response.json();
  }
  async checkoutBranch(
    sessionId: string,
    branchName: string,
    create = false,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Checking out branch", {
      sessionId,
      branchName,
      create,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/branch`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          branch_name: branchName,
          create,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Failed to checkout branch: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async mergeBranch(
    sessionId: string,
    branchName: string,
  ): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info("Merging branch", { sessionId, branchName });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/git/merge`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          branch_name: branchName,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(
        data.detail || `Failed to merge branch: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async saveFileContent(
    sessionId: string,
    filePath: string,
    content: string,
  ): Promise<boolean> {
    workspaceLogger.info("Saving file content", { sessionId, filePath });
    if (hostAdapter.mode === "desktop") {
      await hostAdapter.writeFile(filePath, content);
      return true;
    }
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/content`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          content,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to save file content", {
        status: response.status,
      });
      throw new Error(`Failed to save file: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async backupFileContent(
    sessionId: string,
    filePath: string,
    content: string,
  ): Promise<string> {
    workspaceLogger.info("Backing up file content", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/backup`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
          content,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to backup file content", {
        status: response.status,
      });
      throw new Error(`Failed to backup file: ${response.statusText}`);
    }
    const data = await response.json();
    return data.backup_id;
  }

  async deleteBackup(sessionId: string, backupId: string): Promise<boolean> {
    workspaceLogger.info("Deleting file backup", { sessionId, backupId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/backup`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          backup_id: backupId,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to delete backup", {
        status: response.status,
      });
      throw new Error(`Failed to delete backup: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getWorkspaceTools(sessionId: string): Promise<string[]> {
    workspaceLogger.info("Fetching workspace tools", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/tools?session_id=${sessionId}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace tools", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch workspace tools: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.enabled_tools;
  }

  async toggleWorkspaceTool(
    sessionId: string,
    serverId: string,
    isEnabled: boolean,
  ): Promise<boolean> {
    workspaceLogger.info("Toggling workspace tool", {
      sessionId,
      serverId,
      isEnabled,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/tools/toggle`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          server_id: serverId,
          is_enabled: isEnabled,
        }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to toggle workspace tool", {
        status: response.status,
      });
      throw new Error(`Failed to toggle tool: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getRecentWorkspaces(): Promise<WorkspaceInfo[]> {
    workspaceLogger.info("Fetching recent workspaces");
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/recent`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch recent workspaces", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch recent workspaces: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.workspaces;
  }

  async getAllWorkspaces(): Promise<WorkspaceInfo[]> {
    workspaceLogger.info("Fetching all workspaces");
    const response = await hostAdapter.fetch(`${API_BASE}/api/workspace/list`);
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch all workspaces", {
        status: response.status,
      });
      throw new Error(`Failed to fetch all workspaces: ${response.statusText}`);
    }
    const data = await response.json();
    return data.workspaces;
  }

  async activateWorkspace(sessionId: string): Promise<boolean> {
    workspaceLogger.info("Activating workspace", { sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/activate`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to activate workspace", {
        status: response.status,
      });
      throw new Error(`Failed to activate workspace: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async createWorkspace(
    name: string,
    localPath?: string,
  ): Promise<WorkspaceInfo> {
    workspaceLogger.info("Creating workspace", { name, localPath });
    const payload: { name: string; local_path?: string } = { name };
    if (localPath) {
      payload.local_path = localPath;
    }
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/create`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      workspaceLogger.error("Failed to create workspace", {
        status: response.status,
      });
      throw new Error(
        errData.detail || `Failed to create workspace: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async getWorkspace(workspaceId: string): Promise<WorkspaceInfo> {
    workspaceLogger.info("Fetching workspace by ID", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch workspace", {
        status: response.status,
      });
      throw new Error(`Failed to fetch workspace: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceSessions(workspaceId: string): Promise<
    {
      sessionId: string;
      title: string;
      createdAt: number;
      updatedAt: number;
      messageCount: number;
    }[]
  > {
    workspaceLogger.info("Fetching workspace sessions", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/sessions`,
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch workspace sessions: ${response.statusText}`);
    }
    const data = await response.json();
    return (data.sessions || []).map((session: any) => ({
      sessionId: session.session_id,
      title: session.title || "Untitled",
      createdAt: session.created_at,
      updatedAt: session.updated_at,
      messageCount: session.message_count || 0,
    }));
  }

  async createWorkspaceSession(workspaceId: string): Promise<{
    sessionId: string;
    title: string;
    createdAt: number;
    updatedAt: number;
    isActive: boolean;
  }> {
    workspaceLogger.info("Creating workspace session", { workspaceId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/sessions`,
      { method: "POST" },
    );
    if (!response.ok) {
      throw new Error(`Failed to create workspace session: ${response.statusText}`);
    }
    const data = await response.json();
    return {
      sessionId: data.session_id,
      title: data.title || "Untitled",
      createdAt: data.created_at,
      updatedAt: data.created_at,
      isActive: true,
    };
  }

  async selectWorkspaceSession(
    workspaceId: string,
    sessionId: string,
  ): Promise<string> {
    workspaceLogger.info("Selecting workspace session", { workspaceId, sessionId });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/session/select`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      throw new Error(`Failed to select workspace session: ${response.statusText}`);
    }
    const data = await response.json();
    return data.session_id || sessionId;
  }

  async getDefaultWorkspaceDir(): Promise<string> {
    workspaceLogger.info("Fetching default workspace dir");
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/default-dir`,
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to fetch default workspace dir", {
        status: response.status,
      });
      throw new Error(
        `Failed to fetch default workspace dir: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.default_dir;
  }

  async updateWorkspaceSession(
    workspaceId: string,
    sessionId: string,
  ): Promise<string> {
    workspaceLogger.info("Updating workspace session ID", {
      workspaceId,
      sessionId,
    });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/session/select`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ session_id: sessionId }),
      },
    );
    if (!response.ok) {
      workspaceLogger.error("Failed to update workspace session", {
        status: response.status,
      });
      throw new Error(
        `Failed to update workspace session: ${response.statusText}`,
      );
    }
    const data = await response.json();
    return data.session_id || sessionId;
  }

  async getMcpStatus(sessionId: string): Promise<{
    status: string;
    message: string;
    running_mcps?: {
      name: string;
      status: string;
      error_message?: string | null;
    }[];
  }> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/mcp-status?session_id=${sessionId}`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get MCP status: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceMcpStatus(workspaceId: string): Promise<{
    status: string;
    message: string;
    running_mcps?: {
      name: string;
      status: string;
      error_message?: string | null;
    }[];
  }> {
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/by-id/${encodeURIComponent(workspaceId)}/mcp-status`,
    );
    if (!response.ok) {
      throw new Error(`Failed to get workspace MCP status: ${response.statusText}`);
    }
    return response.json();
  }

  async runFile(
    sessionId: string,
    filePath: string,
  ): Promise<{
    success: boolean;
    stdout: string;
    stderr: string;
    exit_code: number;
  }> {
    workspaceLogger.info("Running file in workspace", { sessionId, filePath });
    const response = await hostAdapter.fetch(
      `${API_BASE}/api/workspace/files/run`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          path: filePath,
        }),
      },
    );
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      workspaceLogger.error("Failed to run file", {
        status: response.status,
      });
      throw new Error(
        data.detail || `Failed to run file: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async selectFiles(options?: SelectOptions): Promise<string[]> {
    return hostAdapter.selectFiles(options);
  }
}

export interface WorkspaceInfo {
  workspace_id: string;
  session_id: string;
  workspace_name?: string | null;
  local_path: string;
  git_remote_url: string | null;
  git_username: string | null;
  enabled_tools?: string[] | null;
  updated_at: number;
}

export class MergeConflictError extends Error {
  conflictedFiles: string[];
  constructor(message: string, conflictedFiles: string[]) {
    super(message);
    this.name = "MergeConflictError";
    this.conflictedFiles = conflictedFiles;
  }
}

export const workspaceService = new WorkspaceService();
export default workspaceService;
