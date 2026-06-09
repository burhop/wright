import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ToolRegistryPage } from "../src/components/pages/ToolRegistryPage";
import { useTools } from "../src/store/tools";
import type { McpServer, McpTool } from "../src/services/mcp-service";

// Mock the useTools hook
vi.mock("../src/store/tools", () => ({
  useTools: vi.fn(),
  ToolsProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

// Mock useChat to control store states
const mockUseChat = vi.fn();
vi.mock("../src/store/sessions", () => ({
  useChat: () => mockUseChat(),
  ChatProvider: ({ children }: any) => <div>{children}</div>,
}));

// Mock workspace-service
vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getAllWorkspaces: vi.fn().mockResolvedValue([
      {
        workspace_id: "ws-1",
        session_id: "session-1",
        local_path: "/path/to/ws-1",
        git_remote_url: null,
        git_username: null,
        enabled_tools: ["Simulation Solver"],
        updated_at: 1000,
      },
    ]),
    toggleWorkspaceTool: vi.fn().mockResolvedValue(true),
  },
}));

// Mock logger hook to avoid logging output clutter
vi.mock("../src/hooks/useLogger", () => ({
  default: () => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  }),
}));

describe("ToolRegistryPage", () => {
  const mockServers: McpServer[] = [
    {
      server_id: "server-1",
      name: "Simulation Solver",
      type: "stdio",
      command: ["uv", "run", "sim"],
      is_active: false,
      is_installed: false,
      status: "inactive",
      category: "simulation",
      created_at: 1000,
      updated_at: 1000,
    },
    {
      server_id: "server-2",
      name: "CAD Extractor",
      type: "sse",
      command: "http://127.0.0.1:9090/sse",
      is_active: true,
      is_installed: true,
      status: "active",
      category: "cad",
      created_at: 1000,
      updated_at: 1000,
    },
  ];

  const mockTools: McpTool[] = [
    {
      tool_id: "server-2:get_layers",
      server_id: "server-2",
      name: "get_layers",
      description: "Get CAD layers",
      input_schema: { type: "object" },
      is_enabled: true,
      created_at: 1000,
    },
  ];

  const mockToggleServerState = vi.fn();
  const mockInstallServerState = vi.fn();
  const mockUninstallServerState = vi.fn();
  const mockDeleteServerState = vi.fn();
  const mockToggleToolState = vi.fn();
  const mockRegisterCustomServer = vi.fn();
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChat.mockReturnValue({
      state: {
        activeSessionId: "session-1",
      },
      refreshSessions: vi.fn(),
    });
    (useTools as any).mockReturnValue({
      servers: mockServers,
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: mockFetch,
      registerCustomServer: mockRegisterCustomServer,
      toggleServerState: mockToggleServerState,
      installServerState: mockInstallServerState,
      uninstallServerState: mockUninstallServerState,
      deleteServerState: mockDeleteServerState,
      toggleToolState: mockToggleToolState,
    });
  });

  it("renders registered servers and tools list", () => {
    render(<ToolRegistryPage />);

    expect(screen.getByText("Simulation Solver")).toBeInTheDocument();
    expect(screen.getByText("CAD Extractor")).toBeInTheDocument();

    // Expand connection details for Server 1
    const expandBtn = screen.getByRole("button", {
      name: /Show connection details/i,
    });
    fireEvent.click(expandBtn);

    // Server 1: stdio command display
    expect(screen.getByText("uv run sim")).toBeInTheDocument();
    // Server 2: URL display
    expect(screen.getByText("http://127.0.0.1:9090/sse")).toBeInTheDocument();
  });

  it("filters servers by search query input", () => {
    render(<ToolRegistryPage />);

    const searchInput = screen.getByTestId("tool-registry-search-input");
    fireEvent.change(searchInput, { target: { value: "Simulation" } });

    expect(screen.getByText("Simulation Solver")).toBeInTheDocument();
    expect(screen.queryByText("CAD Extractor")).not.toBeInTheDocument();
  });

  it("filters servers by category sidebar selection", () => {
    render(<ToolRegistryPage />);

    const cadBtn = screen.getByTestId("tool-registry-category-cad");
    fireEvent.click(cadBtn);

    expect(screen.queryByText("Simulation Solver")).not.toBeInTheDocument();
    expect(screen.getByText("CAD Extractor")).toBeInTheDocument();
  });

  it("installs a server when install button is clicked", async () => {
    render(<ToolRegistryPage />);

    // Click to install server 1 (which is not installed)
    const installBtn = screen.getByRole("button", { name: "Install" });
    expect(installBtn).toBeInTheDocument();

    fireEvent.click(installBtn);
    expect(mockInstallServerState).toHaveBeenCalledWith(
      "server-1",
      "session-1",
    );
  });
});
