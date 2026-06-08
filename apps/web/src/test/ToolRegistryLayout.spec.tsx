import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ToolRegistryPage } from "../components/pages/ToolRegistryPage";
import { useTools } from "../store/tools";
import type { McpServer, McpTool } from "../services/mcp-service";

// Mock the useTools hook
vi.mock("../store/tools", () => ({
  useTools: vi.fn(),
  ToolsProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

// Mock useChat to control store states
const mockUseChat = vi.fn();
vi.mock("../store/sessions", () => ({
  useChat: () => mockUseChat(),
  ChatProvider: ({ children }: any) => <div>{children}</div>,
}));

// Mock workspace-service
vi.mock("../services/workspace-service", () => ({
  workspaceService: {
    getAllWorkspaces: vi.fn().mockResolvedValue([]),
    toggleWorkspaceTool: vi.fn().mockResolvedValue(true),
  },
}));

// Mock logger hook
vi.mock("../hooks/useLogger", () => ({
  default: () => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  }),
}));

describe("ToolRegistryPage Visual Layout", () => {
  const mockServers: McpServer[] = [
    {
      server_id: "server-1",
      name: "CalculiX Simulation",
      type: "stdio",
      command: ["uv", "run", "calculix-mcp"],
      is_active: false,
      is_installed: false,
      status: "inactive",
      category: "simulation",
      created_at: 1000,
      updated_at: 1000,
      description: "Finite element analysis solver.",
    },
  ];

  const mockTools: McpTool[] = [];

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChat.mockReturnValue({
      state: {
        activeSessionId: "session-1",
      },
    });
    (useTools as any).mockReturnValue({
      servers: mockServers,
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
    });
  });

  it("renders card panels with proper data-testid values", () => {
    render(<ToolRegistryPage />);

    // Assert cards have data-testid for styling tests
    const serverCard = screen.getByTestId("server-card-server-1");
    expect(serverCard).toBeInTheDocument();

    const title = screen.getByText("CalculiX Simulation");
    expect(title).toBeInTheDocument();
  });
});
