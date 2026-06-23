import { logger } from "./logger";

const mcpLogger = logger.child("McpService");

export interface EnvVarDefinition {
  name: string;
  label: string;
  description?: string;
  required: boolean;
  secret: boolean;
}

export interface CredentialStatusResponse {
  server_id: string;
  env_vars: EnvVarDefinition[];
  configured: Record<string, boolean>;
}

export interface McpServer {
  server_id: string;
  name: string;
  type: "stdio" | "sse" | "webmcp";
  command?: string[] | string;
  is_active: boolean;
  is_installed: boolean;
  status: "active" | "inactive" | "error";
  error_message?: string;
  category: string;
  created_at: number;
  updated_at: number;
  image_url?: string;
  description?: string;
  source_url?: string;
  installed_version?: string;
  env_vars?: EnvVarDefinition[];
  credentials_configured?: Record<string, boolean>;
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
  type: "stdio" | "sse" | "webmcp";
  command?: string[] | string;
  category: string;
  image_url?: string;
  description?: string;
  source_url?: string;
}
export interface VersionCheckResult {
  server_id: string;
  installed: string | null;
  latest: string | null;
  update_available: boolean;
  error: string | null;
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
const API_BASE = getApiBase();

export class McpService {
  async getServers(): Promise<McpServer[]> {
    mcpLogger.info("Fetching MCP servers");
    const response = await fetch(`${API_BASE}/api/mcp/servers`);
    if (!response.ok) {
      mcpLogger.error("Failed to fetch MCP servers", {
        status: response.status,
      });
      throw new Error(`Failed to fetch MCP servers: ${response.statusText}`);
    }
    const data = await response.json();
    return data.servers;
  }

  async registerServer(
    payload: RegisterServerPayload,
  ): Promise<{ server_id: string; name: string; status: string }> {
    mcpLogger.info("Registering custom MCP server", { ...payload } as Record<
      string,
      unknown
    >);
    const response = await fetch(`${API_BASE}/api/mcp/servers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to register MCP server", { msg });
      throw new Error(msg);
    }

    return response.json();
  }

  async toggleServer(serverId: string, isActive: boolean): Promise<McpServer> {
    mcpLogger.info("Toggling server active state", { serverId, isActive });
    const response = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ is_active: isActive }),
    });

    if (!response.ok) {
      mcpLogger.error("Failed to toggle MCP server state", {
        status: response.status,
      });
      throw new Error(`Failed to toggle MCP server: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "", // backend patch returns server_id, is_active, status, error_message
      type: data.type,
      is_active: data.is_active,
      is_installed: data.is_installed || false,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
    };
  }

  async deleteServer(serverId: string): Promise<void> {
    mcpLogger.info("Deleting MCP server", { serverId });
    const response = await fetch(`${API_BASE}/api/mcp/servers/${serverId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      mcpLogger.error("Failed to delete MCP server", {
        status: response.status,
      });
      throw new Error(`Failed to delete MCP server: ${response.statusText}`);
    }
  }

  async getTools(): Promise<McpTool[]> {
    mcpLogger.info("Fetching MCP tools");
    const response = await fetch(`${API_BASE}/api/mcp/tools`);
    if (!response.ok) {
      mcpLogger.error("Failed to fetch MCP tools", { status: response.status });
      throw new Error(`Failed to fetch MCP tools: ${response.statusText}`);
    }
    const data = await response.json();
    return data.tools;
  }

  async toggleTool(toolId: string, isEnabled: boolean): Promise<McpTool> {
    mcpLogger.info("Toggling tool enabled state", { toolId, isEnabled });
    const response = await fetch(`${API_BASE}/api/mcp/tools/${toolId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ is_enabled: isEnabled }),
    });

    if (!response.ok) {
      mcpLogger.error("Failed to toggle tool state", {
        status: response.status,
      });
      throw new Error(`Failed to toggle MCP tool: ${response.statusText}`);
    }

    return response.json();
  }

  async installServer(
    serverId: string,
    sessionId?: string | null,
  ): Promise<McpServer> {
    mcpLogger.info("Installing MCP server", { serverId, sessionId });
    const url = sessionId
      ? `${API_BASE}/api/mcp/servers/${serverId}/install?session_id=${sessionId}`
      : `${API_BASE}/api/mcp/servers/${serverId}/install`;
    const response = await fetch(url, { method: "POST" });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to install MCP server", { msg });
      throw new Error(msg);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "",
      type: data.type,
      is_active: false,
      is_installed: data.is_installed,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
    };
  }

  async uninstallServer(
    serverId: string,
    sessionId?: string | null,
  ): Promise<McpServer> {
    mcpLogger.info("Uninstalling MCP server", { serverId, sessionId });
    const url = sessionId
      ? `${API_BASE}/api/mcp/servers/${serverId}/uninstall?session_id=${sessionId}`
      : `${API_BASE}/api/mcp/servers/${serverId}/uninstall`;
    const response = await fetch(url, { method: "POST" });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to uninstall MCP server", { msg });
      throw new Error(msg);
    }

    const data = await response.json();
    return {
      server_id: data.server_id,
      name: "",
      type: data.type,
      is_active: false,
      is_installed: data.is_installed,
      status: data.status,
      error_message: data.error_message,
      category: "",
      created_at: 0,
      updated_at: 0,
    };
  }

  async checkServerVersion(serverId: string): Promise<VersionCheckResult> {
    mcpLogger.info("Checking server version", { serverId });
    const response = await fetch(
      `${API_BASE}/api/mcp/servers/${serverId}/version-check`,
    );
    if (!response.ok) {
      mcpLogger.error("Failed to check server version", {
        status: response.status,
      });
      throw new Error(`Failed to check server version: ${response.statusText}`);
    }
    return response.json();
  }

  async updateServer(serverId: string): Promise<{ installed_version: string }> {
    mcpLogger.info("Updating server", { serverId });
    const response = await fetch(
      `${API_BASE}/api/mcp/servers/${serverId}/update`,
      {
        method: "POST",
      },
    );
    if (!response.ok) {
      mcpLogger.error("Failed to update server", { status: response.status });
      throw new Error(`Failed to update server: ${response.statusText}`);
    }
    return response.json();
  }

  async getCredentialStatus(
    serverId: string,
  ): Promise<CredentialStatusResponse> {
    mcpLogger.info("Fetching credential status", { serverId });
    const response = await fetch(
      `${API_BASE}/api/mcp/servers/${serverId}/credentials`,
    );
    if (!response.ok) {
      mcpLogger.error("Failed to get credential status", {
        status: response.status,
      });
      throw new Error(
        `Failed to get credential status: ${response.statusText}`,
      );
    }
    return response.json();
  }

  async saveCredentials(
    serverId: string,
    credentials: Record<string, string>,
  ): Promise<CredentialStatusResponse> {
    mcpLogger.info("Saving credentials", { serverId });
    const response = await fetch(
      `${API_BASE}/api/mcp/servers/${serverId}/credentials`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ credentials }),
      },
    );
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      const msg = errData.detail || response.statusText;
      mcpLogger.error("Failed to save credentials", { msg });
      throw new Error(msg);
    }
    return response.json();
  }

  async deleteCredentials(serverId: string): Promise<void> {
    mcpLogger.info("Deleting credentials", { serverId });
    const response = await fetch(
      `${API_BASE}/api/mcp/servers/${serverId}/credentials`,
      {
        method: "DELETE",
      },
    );
    if (!response.ok) {
      mcpLogger.error("Failed to delete credentials", {
        status: response.status,
      });
      throw new Error(
        `Failed to delete credentials: ${response.statusText}`,
      );
    }
  }
}

export const mcpService = new McpService();
