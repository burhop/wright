import React, { useState, useEffect, useCallback } from "react";
import workspaceService from "../../services/workspace-service";

interface McpServer {
  server_id: string;
  name: string;
  type: string;
  is_active: boolean;
  status: string;
  category: string;
  description?: string;
}

interface ToolsMarketplaceProps {
  sessionId: string;
}

export const ToolsMarketplace: React.FC<ToolsMarketplaceProps> = ({
  sessionId,
}) => {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [enabledTools, setEnabledTools] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const host =
        typeof window !== "undefined" ? window.location.hostname : "127.0.0.1";
      const serversResponse = await fetch(
        `http://${host}:8000/api/mcp/servers`,
      );
      if (!serversResponse.ok) {
        throw new Error("Failed to fetch MCP servers list");
      }
      const serversData = await serversResponse.json();
      const enabledList = await workspaceService.getWorkspaceTools(sessionId);

      setServers(serversData.servers);
      setEnabledTools(enabledList);
    } catch (err: unknown) {
      console.error("Failed to load marketplace tools:", err);
      setError(err instanceof Error ? err.message : "Failed to load tools");
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleToggleTool = async (
    serverName: string,
    currentlyEnabled: boolean,
  ) => {
    try {
      await workspaceService.toggleWorkspaceTool(
        sessionId,
        serverName,
        !currentlyEnabled,
      );
      const enabledList = await workspaceService.getWorkspaceTools(sessionId);
      setEnabledTools(enabledList);
    } catch (err: unknown) {
      console.error("Failed to toggle tool:", err);
      alert("Failed to toggle tool setting.");
    }
  };

  if (loading) {
    return (
      <div
        style={{
          padding: "var(--space-md)",
          color: "var(--color-secondary)",
          fontFamily: "var(--font-ui)",
          fontSize: "0.8rem",
        }}
      >
        Loading tools marketplace...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          padding: "var(--space-md)",
          color: "var(--color-error)",
          fontFamily: "var(--font-ui)",
          fontSize: "0.8rem",
        }}
      >
        Warning: {error}
      </div>
    );
  }

  return (
    <div style={{ padding: "var(--space-md)", fontFamily: "var(--font-ui)" }}>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-sm)",
        }}
      >
        {servers.map((server) => {
          const isEnabled = enabledTools.includes(server.name);
          const isGloballyActive = server.is_active;

          return (
            <div
              key={server.server_id}
              style={{
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-md)",
                padding: "var(--space-md)",
                display: "flex",
                flexDirection: "column",
                gap: "var(--space-xs)",
                transition: "border-color 0.2s",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span
                  style={{
                    fontWeight: "600",
                    color: "var(--color-primary)",
                    fontSize: "0.85rem",
                  }}
                >
                  {server.name}
                </span>
                <input
                  type="checkbox"
                  disabled={!isGloballyActive}
                  checked={isGloballyActive && isEnabled}
                  onChange={() => handleToggleTool(server.name, isEnabled)}
                  style={{
                    cursor: isGloballyActive ? "pointer" : "not-allowed",
                  }}
                  title={
                    !isGloballyActive
                      ? "Activate this server in profile to enable"
                      : "Toggle tool access"
                  }
                />
              </div>

              <div
                style={{
                  fontSize: "0.7rem",
                  color: "var(--color-secondary)",
                  display: "flex",
                  gap: "var(--space-sm)",
                }}
              >
                <span>
                  Type:{" "}
                  <strong style={{ textTransform: "uppercase" }}>
                    {server.type}
                  </strong>
                </span>
                <span>
                  Category: <strong>{server.category}</strong>
                </span>
              </div>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--space-xs)",
                  marginTop: "var(--space-xs)",
                }}
              >
                <span
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    backgroundColor: isGloballyActive
                      ? "var(--color-success, #22c55e)"
                      : "#858585",
                  }}
                />
                <span
                  style={{
                    fontSize: "0.65rem",
                    color: isGloballyActive
                      ? "var(--color-success)"
                      : "var(--color-secondary)",
                  }}
                >
                  {isGloballyActive
                    ? "Active in Profile"
                    : "Inactive in Profile"}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ToolsMarketplace;
