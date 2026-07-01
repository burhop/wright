import { render, screen, fireEvent, within } from "@testing-library/react";
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
  const metadata = {
    verification_state: "community_mcp" as const,
    installability_tier: "might_work" as const,
    risk_level: "low" as const,
    deployment_mode: "local-only",
    platform_support: {
      linux_x64: {
        status: "likely" as const,
        tested: false,
        notes: "test fixture",
      },
    },
    host_software_required: [],
    credentials_required: [],
    default_enabled: true,
    approval_gates: [],
    validation_result: {
      status: "not_tested" as const,
      message: "Not yet validated in this environment",
      missing_dependencies: [],
    },
  };

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
      ...metadata,
      installability_tier: "might_work",
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
      ...metadata,
      installability_tier: "tested",
      verification_state: "verified_mcp",
      validation_result: {
        status: "passed",
        message: "Validated in test fixture",
        missing_dependencies: [],
      },
    },
    {
      server_id: "server-3",
      name: "Blocked Candidate",
      type: "stdio",
      command: ["uvx", "blocked"],
      is_active: false,
      is_installed: false,
      status: "inactive",
      category: "utilities",
      created_at: 1000,
      updated_at: 1000,
      ...metadata,
      installability_tier: "blocked",
      install_blocked_reason: "Source URL missing.",
      follow_up_url: "docs/mcp-catalog/followups/server-3.md",
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

    expect(screen.queryByText("uv run sim")).not.toBeInTheDocument();
    expect(
      screen.queryByText("http://127.0.0.1:9090/sse"),
    ).not.toBeInTheDocument();

    // Expand full card details for Server 1
    const serverOneCard = screen.getByTestId("server-card-server-1");
    const expandBtn = within(serverOneCard).getByTestId(
      "server-card-details-toggle-server-1",
    );
    fireEvent.click(expandBtn);

    // Server 1: stdio command display
    expect(screen.getByText("uv run sim")).toBeInTheDocument();

    const serverTwoCard = screen.getByTestId("server-card-server-2");
    fireEvent.click(
      within(serverTwoCard).getByTestId("server-card-details-toggle-server-2"),
    );

    // Server 2: URL display
    expect(screen.getByText("http://127.0.0.1:9090/sse")).toBeInTheDocument();
    expect(
      screen.getByTestId("server-card-verification-server-2"),
    ).toHaveTextContent("Verified MCP");
    expect(
      screen.getByTestId("server-card-installability-server-2"),
    ).toHaveTextContent("Launch tested");
    expect(
      screen.getByTestId("server-card-installability-server-2"),
    ).toHaveAttribute(
      "title",
      expect.stringContaining("not a security review"),
    );
  });

  it("orders tested servers before blocked servers", () => {
    render(<ToolRegistryPage />);

    const cards = screen.getAllByTestId(/server-card-server-/);
    expect(cards[0]).toHaveTextContent("CAD Extractor");
    expect(cards[1]).toHaveTextContent("Simulation Solver");
    expect(cards[2]).toHaveTextContent("Blocked Candidate");
    expect(screen.getByTestId("tool-registry-tier-tested")).toHaveTextContent(
      "1",
    );
    expect(screen.getByTestId("tool-registry-tier-blocked")).toHaveTextContent(
      "1",
    );

    const blockedCard = screen.getByTestId("server-card-server-3");
    expect(
      within(blockedCard).queryByTestId("server-card-followup-server-3"),
    ).not.toBeInTheDocument();
    fireEvent.click(
      within(blockedCard).getByTestId("server-card-details-toggle-server-3"),
    );
    expect(
      screen.getByTestId("server-card-followup-server-3"),
    ).toHaveTextContent("Follow-up record");
    expect(
      screen.getByTestId("server-card-report-missing-mcp"),
    ).toBeInTheDocument();
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
    const installBtn = screen.getByTestId("server-card-install-btn-server-1");
    expect(installBtn).toBeInTheDocument();

    fireEvent.click(installBtn);
    expect(mockInstallServerState).toHaveBeenCalledWith(
      "server-1",
      "session-1",
    );
  });
});
