import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  type ReactNode,
} from "react";
import { mcpService } from "../services/mcp-service";
import type {
  McpServer,
  McpTool,
  VersionCheckResult,
  CredentialStatusResponse,
  PlatformSupportRecord,
} from "../services/mcp-service";

const defaultPlatformSupport = (): Record<string, PlatformSupportRecord> => ({
  windows_11_x64: { status: "unknown", tested: false, notes: "not tested" },
  linux_x64: { status: "unknown", tested: false, notes: "not tested" },
  linux_arm64: { status: "unknown", tested: false, notes: "not tested" },
  macos_x64: { status: "unknown", tested: false, notes: "not tested" },
  macos_arm64: { status: "unknown", tested: false, notes: "not tested" },
});

export interface ToolsState {
  servers: McpServer[];
  tools: McpTool[];
  isLoading: boolean;
  error: string | null;
}

type ToolsAction =
  | { type: "SET_LOADING"; isLoading: boolean }
  | { type: "SET_ERROR"; error: string | null }
  | { type: "SET_SERVERS"; servers: McpServer[] }
  | { type: "SET_TOOLS"; tools: McpTool[] }
  | { type: "ADD_SERVER"; server: McpServer }
  | { type: "UPDATE_SERVER"; serverId: string; updates: Partial<McpServer> }
  | { type: "DELETE_SERVER"; serverId: string }
  | { type: "UPDATE_TOOL"; toolId: string; updates: Partial<McpTool> };

const initialState: ToolsState = {
  servers: [],
  tools: [],
  isLoading: false,
  error: null,
};

function toolsReducer(state: ToolsState, action: ToolsAction): ToolsState {
  switch (action.type) {
    case "SET_LOADING":
      return { ...state, isLoading: action.isLoading };
    case "SET_ERROR":
      return { ...state, error: action.error };
    case "SET_SERVERS":
      return { ...state, servers: action.servers };
    case "SET_TOOLS":
      return { ...state, tools: action.tools };
    case "ADD_SERVER":
      return { ...state, servers: [...state.servers, action.server] };
    case "UPDATE_SERVER":
      return {
        ...state,
        servers: state.servers.map((s) =>
          s.server_id === action.serverId ? { ...s, ...action.updates } : s,
        ),
      };
    case "DELETE_SERVER":
      return {
        ...state,
        servers: state.servers.filter((s) => s.server_id !== action.serverId),
        tools: state.tools.filter((t) => t.server_id !== action.serverId),
      };
    case "UPDATE_TOOL":
      return {
        ...state,
        tools: state.tools.map((t) =>
          t.tool_id === action.toolId ? { ...t, ...action.updates } : t,
        ),
      };
    default:
      return state;
  }
}

interface ToolsContextProps extends ToolsState {
  fetchServersAndTools: () => Promise<void>;
  registerCustomServer: (
    name: string,
    type: "stdio" | "sse" | "webmcp",
    command: string[] | string,
    category: string,
    imageUrl?: string,
    description?: string,
    sourceUrl?: string,
  ) => Promise<void>;
  toggleServerState: (serverId: string, isActive: boolean) => Promise<void>;
  installServerState: (
    serverId: string,
    sessionId?: string | null,
  ) => Promise<void>;
  uninstallServerState: (
    serverId: string,
    sessionId?: string | null,
  ) => Promise<void>;
  deleteServerState: (serverId: string) => Promise<void>;
  toggleToolState: (toolId: string, isEnabled: boolean) => Promise<void>;
  checkServerVersion: (serverId: string) => Promise<VersionCheckResult>;
  updateServerState: (serverId: string) => Promise<void>;
  saveCredentials: (
    serverId: string,
    credentials: Record<string, string>,
  ) => Promise<CredentialStatusResponse>;
  deleteCredentials: (serverId: string) => Promise<void>;
}

const ToolsContext = createContext<ToolsContextProps | undefined>(undefined);

export function ToolsProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(toolsReducer, initialState);

  const fetchServersAndTools = async () => {
    dispatch({ type: "SET_LOADING", isLoading: true });
    dispatch({ type: "SET_ERROR", error: null });
    try {
      const [servers, tools] = await Promise.all([
        mcpService.getServers(),
        mcpService.getTools(),
      ]);
      dispatch({ type: "SET_SERVERS", servers });
      dispatch({ type: "SET_TOOLS", tools });
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to fetch registry data",
      });
    } finally {
      dispatch({ type: "SET_LOADING", isLoading: false });
    }
  };

  const registerCustomServer = async (
    name: string,
    type: "stdio" | "sse" | "webmcp",
    command: string[] | string,
    category: string,
    imageUrl?: string,
    description?: string,
    sourceUrl?: string,
  ) => {
    dispatch({ type: "SET_LOADING", isLoading: true });
    dispatch({ type: "SET_ERROR", error: null });
    try {
      const res = await mcpService.registerServer({
        name,
        type,
        command,
        category,
        image_url: imageUrl,
        description,
        source_url: sourceUrl,
      });
      // Create local server state
      const now = Math.floor(Date.now() / 1000);
      const newServer: McpServer = {
        server_id: res.server_id,
        name,
        type,
        command,
        is_active: false,
        is_installed: false,
        status: "inactive",
        category,
        created_at: now,
        updated_at: now,
        image_url: imageUrl,
        description,
        source_url: sourceUrl,
        verification_state: "user_reported_url_needed",
        installability_tier: "blocked",
        risk_level: "low",
        deployment_mode: "unknown",
        platform_support: defaultPlatformSupport(),
        host_software_required: [],
        credentials_required: [],
        default_enabled: false,
        approval_gates: [],
        validation_result: {
          status: "not_tested",
          message: "Not yet validated in this environment",
          missing_dependencies: [],
        },
        install_blocked_reason:
          "Custom server pending source and install verification.",
      };
      dispatch({ type: "ADD_SERVER", server: newServer });
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to register custom server",
      });
      throw err;
    } finally {
      dispatch({ type: "SET_LOADING", isLoading: false });
    }
  };

  const toggleServerState = async (serverId: string, isActive: boolean) => {
    // Optimistic toggle update
    const previousServer = state.servers.find((s) => s.server_id === serverId);
    dispatch({
      type: "UPDATE_SERVER",
      serverId,
      updates: {
        is_active: isActive,
        status: isActive ? "active" : "inactive",
      },
    });

    try {
      const result = await mcpService.toggleServer(serverId, isActive);
      dispatch({
        type: "UPDATE_SERVER",
        serverId,
        updates: {
          is_active: result.is_active,
          status: result.status,
          error_message: result.error_message || undefined,
          ...(result.type ? { type: result.type } : {}),
        },
      });
      // Fetch tools list again since active server changes discovered tools in database
      const tools = await mcpService.getTools();
      dispatch({ type: "SET_TOOLS", tools });
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to toggle server activation",
      });
      // Revert optimistic update
      if (previousServer) {
        dispatch({
          type: "UPDATE_SERVER",
          serverId,
          updates: {
            is_active: previousServer.is_active,
            status: previousServer.status,
          },
        });
      }
      throw err;
    }
  };

  const installServerState = async (
    serverId: string,
    sessionId?: string | null,
  ) => {
    try {
      const result = await mcpService.installServer(serverId, sessionId);
      dispatch({
        type: "UPDATE_SERVER",
        serverId,
        updates: {
          is_installed: result.is_installed,
          status: result.status,
          error_message: result.error_message || undefined,
          ...(result.type ? { type: result.type } : {}),
        },
      });
      const tools = await mcpService.getTools();
      dispatch({ type: "SET_TOOLS", tools });
    } catch (err: any) {
      throw err;
    }
  };

  const uninstallServerState = async (
    serverId: string,
    sessionId?: string | null,
  ) => {
    try {
      const result = await mcpService.uninstallServer(serverId, sessionId);
      dispatch({
        type: "UPDATE_SERVER",
        serverId,
        updates: {
          is_installed: result.is_installed,
          is_active: false,
          status: result.status,
          error_message: result.error_message || undefined,
          ...(result.type ? { type: result.type } : {}),
        },
      });
      const tools = await mcpService.getTools();
      dispatch({ type: "SET_TOOLS", tools });
    } catch (err: any) {
      throw err;
    }
  };

  const deleteServerState = async (serverId: string) => {
    dispatch({ type: "SET_LOADING", isLoading: true });
    dispatch({ type: "SET_ERROR", error: null });
    try {
      await mcpService.deleteServer(serverId);
      dispatch({ type: "DELETE_SERVER", serverId });
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to delete server",
      });
      throw err;
    } finally {
      dispatch({ type: "SET_LOADING", isLoading: false });
    }
  };

  const toggleToolState = async (toolId: string, isEnabled: boolean) => {
    const previousTool = state.tools.find((t) => t.tool_id === toolId);
    dispatch({
      type: "UPDATE_TOOL",
      toolId,
      updates: { is_enabled: isEnabled },
    });

    try {
      await mcpService.toggleTool(toolId, isEnabled);
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to toggle tool enabled state",
      });
      // Revert optimistic update
      if (previousTool) {
        dispatch({
          type: "UPDATE_TOOL",
          toolId,
          updates: { is_enabled: previousTool.is_enabled },
        });
      }
      throw err;
    }
  };

  const checkServerVersion = async (
    serverId: string,
  ): Promise<VersionCheckResult> => {
    return await mcpService.checkServerVersion(serverId);
  };

  const updateServerState = async (serverId: string) => {
    dispatch({ type: "SET_LOADING", isLoading: true });
    dispatch({ type: "SET_ERROR", error: null });
    try {
      const res = await mcpService.updateServer(serverId);
      dispatch({
        type: "UPDATE_SERVER",
        serverId,
        updates: { installed_version: res.installed_version },
      });
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to update server",
      });
      throw err;
    } finally {
      dispatch({ type: "SET_LOADING", isLoading: false });
    }
  };

  const saveCredentials = async (
    serverId: string,
    credentials: Record<string, string>,
  ): Promise<CredentialStatusResponse> => {
    try {
      const result = await mcpService.saveCredentials(serverId, credentials);
      // Update the server's credentials_configured in state
      dispatch({
        type: "UPDATE_SERVER",
        serverId,
        updates: {
          credentials_configured: result.configured,
        },
      });
      return result;
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to save credentials",
      });
      throw err;
    }
  };

  const deleteCredentials = async (serverId: string): Promise<void> => {
    try {
      await mcpService.deleteCredentials(serverId);
      // Clear credentials_configured in state
      const server = state.servers.find((s) => s.server_id === serverId);
      if (server?.credentials_configured) {
        const cleared: Record<string, boolean> = {};
        for (const key of Object.keys(server.credentials_configured)) {
          cleared[key] = false;
        }
        dispatch({
          type: "UPDATE_SERVER",
          serverId,
          updates: { credentials_configured: cleared },
        });
      }
    } catch (err: any) {
      dispatch({
        type: "SET_ERROR",
        error: err.message || "Failed to delete credentials",
      });
      throw err;
    }
  };

  useEffect(() => {
    fetchServersAndTools();
  }, []);

  return (
    <ToolsContext.Provider
      value={{
        ...state,
        fetchServersAndTools,
        registerCustomServer,
        toggleServerState,
        installServerState,
        uninstallServerState,
        deleteServerState,
        toggleToolState,
        checkServerVersion,
        updateServerState,
        saveCredentials,
        deleteCredentials,
      }}
    >
      {children}
    </ToolsContext.Provider>
  );
}

export function useTools() {
  const context = useContext(ToolsContext);
  if (!context) {
    throw new Error("useTools must be used within a ToolsProvider");
  }
  return context;
}
