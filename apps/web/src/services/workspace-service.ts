import { logger } from './logger';

const workspaceLogger = logger.child('WorkspaceService');

export interface WorkspaceNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number | null;
  last_modified: number;
  children: WorkspaceNode[] | null;
}

const API_BASE = 'http://127.0.0.1:8000';

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
}

export const workspaceService = new WorkspaceService();
export default workspaceService;
