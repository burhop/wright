import { logger } from './logger';

const workspaceLogger = logger.child('WorkspaceService');

export interface WorkspaceNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number | null;
  last_modified: number;
  git_status: 'Clean' | 'M' | 'U' | 'A' | 'D';
  children: WorkspaceNode[] | null;
}

const getApiBase = () => {
  const host = typeof window !== 'undefined' ? window.location.hostname : '127.0.0.1';
  return `http://${host}:8000`;
};
const API_BASE = getApiBase();

export class WorkspaceService {
  async getWorkspaceFiles(sessionId: string): Promise<WorkspaceNode> {
    workspaceLogger.info('Fetching workspace files', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/files?session_id=${sessionId}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch workspace files', { status: response.status });
      throw new Error(`Failed to fetch workspace files: ${response.statusText}`);
    }
    const data = await response.json();
    return data.workspace;
  }

  async getFileContentArrayBuffer(sessionId: string, filePath: string): Promise<ArrayBuffer> {
    workspaceLogger.info('Fetching file content as ArrayBuffer', { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch file content', { status: response.status });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    return response.arrayBuffer();
  }

  async getFileContentText(sessionId: string, filePath: string): Promise<string> {
    workspaceLogger.info('Fetching file content as text', { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API_BASE}/api/workspace/files/content?session_id=${sessionId}&path=${encodedPath}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch file content', { status: response.status });
      throw new Error(`Failed to fetch file content: ${response.statusText}`);
    }
    return response.text();
  }

  async createFileNode(sessionId: string, filePath: string, nodeType: 'file' | 'directory'): Promise<WorkspaceNode> {
    workspaceLogger.info('Creating workspace file node', { sessionId, filePath, nodeType });
    const response = await fetch(`${API_BASE}/api/workspace/files`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        path: filePath,
        type: nodeType,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to create workspace file node', { status: response.status });
      throw new Error(`Failed to create file/folder: ${response.statusText}`);
    }
    return response.json();
  }

  async deleteFileNode(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info('Deleting workspace file node', { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API_BASE}/api/workspace/files?session_id=${sessionId}&path=${encodedPath}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to delete workspace file node', { status: response.status });
      throw new Error(`Failed to delete file/folder: ${response.statusText}`);
    }
  }

  async moveFileNode(sessionId: string, sourcePath: string, destinationPath: string): Promise<boolean> {
    workspaceLogger.info('Moving workspace file node', { sessionId, sourcePath, destinationPath });
    const response = await fetch(`${API_BASE}/api/workspace/files/move`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        source_path: sourcePath,
        destination_path: destinationPath,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to move workspace file node', { status: response.status });
      throw new Error(`Failed to move file/folder: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getGitStatus(sessionId: string): Promise<{ branch_name: string; is_clean: boolean; changes: { path: string; git_status: string; staged: boolean }[] }> {
    workspaceLogger.info('Fetching git status', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/git/status?session_id=${sessionId}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch git status', { status: response.status });
      throw new Error(`Failed to fetch git status: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitDiff(sessionId: string, filePath: string): Promise<string> {
    workspaceLogger.info('Fetching git diff', { sessionId, filePath });
    const encodedPath = encodeURIComponent(filePath);
    const response = await fetch(`${API_BASE}/api/workspace/git/diff?session_id=${sessionId}&path=${encodedPath}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch git diff', { status: response.status });
      throw new Error(`Failed to fetch git diff: ${response.statusText}`);
    }
    const data = await response.json();
    return data.diff;
  }

  async revertFile(sessionId: string, filePath: string): Promise<void> {
    workspaceLogger.info('Reverting file changes', { sessionId, filePath });
    const response = await fetch(`${API_BASE}/api/workspace/git/revert`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        path: filePath,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to revert file changes', { status: response.status });
      throw new Error(`Failed to revert file changes: ${response.statusText}`);
    }
  }

  async commitChanges(sessionId: string, message: string): Promise<{ success: boolean; commit_hash: string; message: string; timestamp: number }> {
    workspaceLogger.info('Committing changes', { sessionId, message });
    const response = await fetch(`${API_BASE}/api/workspace/git/commit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to commit changes', { status: response.status });
      throw new Error(`Failed to commit changes: ${response.statusText}`);
    }
    return response.json();
  }

  async getGitHistory(sessionId: string, limit = 50): Promise<{ commits: { commit_hash: string; message: string; author: string; timestamp: number }[] }> {
    workspaceLogger.info('Fetching git history', { sessionId, limit });
    const response = await fetch(`${API_BASE}/api/workspace/git/history?session_id=${sessionId}&limit=${limit}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch git history', { status: response.status });
      throw new Error(`Failed to fetch git history: ${response.statusText}`);
    }
    return response.json();
  }

  async getWorkspaceConfig(sessionId: string): Promise<{ workspace_id: string; git_remote_url: string | null; git_username: string | null; has_token: boolean; workspace_path?: string }> {
    workspaceLogger.info('Fetching workspace config', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/config?session_id=${sessionId}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch workspace config', { status: response.status });
      throw new Error(`Failed to fetch workspace config: ${response.statusText}`);
    }
    return response.json();
  }

  async updateWorkspaceConfig(
    sessionId: string,
    remoteUrl: string | null,
    username: string | null,
    token: string | null
  ): Promise<{ success: boolean; workspace_id: string }> {
    workspaceLogger.info('Updating workspace config', { sessionId, remoteUrl, username });
    const response = await fetch(`${API_BASE}/api/workspace/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        git_remote_url: remoteUrl,
        git_username: username,
        git_token: token,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to update workspace config', { status: response.status });
      throw new Error(`Failed to update workspace config: ${response.statusText}`);
    }
    return response.json();
  }

  async pushCommits(sessionId: string): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info('Pushing commits to remote', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/git/push`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to push commits', { status: response.status });
      throw new Error(`Failed to push changes: ${response.statusText}`);
    }
    return response.json();
  }

  async pullCommits(sessionId: string): Promise<{ success: boolean; message: string }> {
    workspaceLogger.info('Pulling commits from remote', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/git/pull`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });
    if (response.status === 409) {
      const data = await response.json();
      throw new MergeConflictError(data.message || 'Pull resulted in merge conflicts', data.conflicted_files || []);
    }
    if (!response.ok) {
      workspaceLogger.error('Failed to pull commits', { status: response.status });
      throw new Error(`Failed to pull changes: ${response.statusText}`);
    }
    return response.json();
  }

  async saveFileContent(sessionId: string, filePath: string, content: string): Promise<boolean> {
    workspaceLogger.info('Saving file content', { sessionId, filePath });
    const response = await fetch(`${API_BASE}/api/workspace/files/content`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        path: filePath,
        content,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to save file content', { status: response.status });
      throw new Error(`Failed to save file: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }

  async getWorkspaceTools(sessionId: string): Promise<string[]> {
    workspaceLogger.info('Fetching workspace tools', { sessionId });
    const response = await fetch(`${API_BASE}/api/workspace/tools?session_id=${sessionId}`);
    if (!response.ok) {
      workspaceLogger.error('Failed to fetch workspace tools', { status: response.status });
      throw new Error(`Failed to fetch workspace tools: ${response.statusText}`);
    }
    const data = await response.json();
    return data.enabled_tools;
  }

  async toggleWorkspaceTool(sessionId: string, serverId: string, isEnabled: boolean): Promise<boolean> {
    workspaceLogger.info('Toggling workspace tool', { sessionId, serverId, isEnabled });
    const response = await fetch(`${API_BASE}/api/workspace/tools/toggle`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        server_id: serverId,
        is_enabled: isEnabled,
      }),
    });
    if (!response.ok) {
      workspaceLogger.error('Failed to toggle workspace tool', { status: response.status });
      throw new Error(`Failed to toggle tool: ${response.statusText}`);
    }
    const data = await response.json();
    return data.success;
  }
}

export class MergeConflictError extends Error {
  conflictedFiles: string[];
  constructor(message: string, conflictedFiles: string[]) {
    super(message);
    this.name = 'MergeConflictError';
    this.conflictedFiles = conflictedFiles;
  }
}

export const workspaceService = new WorkspaceService();
export default workspaceService;
