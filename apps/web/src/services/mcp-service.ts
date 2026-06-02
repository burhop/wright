import { logger } from './logger';

const mcpLogger = logger.child('McpService');

export interface McpServer {
  server_id: string;
  name: string;
  type: 'stdio' | 'sse' | 'webmcp';
  command?: string[] | string;
  is_active: boolean;
  status: 'active' | 'inactive' | 'error';
  error_message?: string;
  category: string;
  created_at: number;
  updated_at: number;
}

export interface McpTool {
  tool_id: string;
  server_id: string;
  name: string;
  description?: string;
  input_schema: Record<string, any>;
  is_enabled: boolean;
  created_at: number;
}

export interface RegisterServerPayload {
  name: string;
  type: 'stdio' | 'sse' | 'webmcp';
  command?: string[] | string;
  category: string;
}

const API_BASE = 'http://127.0.0.1:8000';

export class McpService {
  async getServers(): Promise<McpServer[]> {
    mcpLogger.info('Fetching MCP servers');
    const response = await fetch(`${API_BASE}/api/mcp/servers`);
    if (!response.ok) {
      mcpLogger.error('Failed to fetch MCP servers', { status: response.status });
      throw new Error(`Failed to fetch MCP servers: ${response.statusText}`);
    }
    const data = await response.json();
    return data.servers;
  }

  async registerServer(payload: RegisterServerPayload): Promise<{ server_id: string; name: string; status: string }> {
    mcpLogger.info('Registering custom MCP server', { ...payload } as Record<string, unknown>);
    const response = await fetch(`${API_BASE}/api/mcp/servers`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error('Failed to register MCP server', { msg });
      throw new Error(msg);
    }

    return response.json();
  }

  async toggleServer(serverId: string, isActive: boolean): Promise<McpServer> {
    mcpLogger.info('Toggling server active state', { serverId, isActive });
    const response = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_active: isActive }),
    });

    if (!response.ok) {
      mcpLogger.error('Failed to toggle MCP server state', { status: response.status });
      throw new Error(`Failed to toggle MCP server: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: '', // backend patch returns server_id, is_active, status, error_message
      type: 'stdio',
      is_active: data.is_active,
      status: data.status,
      error_message: data.error_message,
      category: '',
      created_at: 0,
      updated_at: 0
    };
  }

  async deleteServer(serverId: string): Promise<void> {
    mcpLogger.info('Deleting MCP server', { serverId });
    const response = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      mcpLogger.error('Failed to delete MCP server', { status: response.status });
      throw new Error(`Failed to delete MCP server: ${response.statusText}`);
    }
  }

  async getTools(): Promise<McpTool[]> {
    mcpLogger.info('Fetching MCP tools');
    const response = await fetch(`${API_BASE}/api/mcp/tools`);
    if (!response.ok) {
      mcpLogger.error('Failed to fetch MCP tools', { status: response.status });
      throw new Error(`Failed to fetch MCP tools: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tools;
  }

  async toggleTool(toolId: string, isEnabled: boolean): Promise<McpTool> {
    mcpLogger.info('Toggling tool enabled state', { toolId, isEnabled });
    const response = await fetch(`${API_BASE}/api/mcp/tools/${toolId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ is_enabled: isEnabled }),
    });

    if (!response.ok) {
      mcpLogger.error('Failed to toggle tool state', { status: response.status });
      throw new Error(`Failed to toggle MCP tool: ${response.statusText}`);
    }

    return response.json();
  }
}

export const mcpService = new McpService();
