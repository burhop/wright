import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ToolRegistryPage } from "../components/pages/ToolRegistryPage";
import { useTools } from "../store/tools";
import {
  defaultMcpMetadata,
  type McpServer,
  type McpTool,
} from "../services/mcp-service";

const mcpServiceMocks = vi.hoisted(() => ({
  getBillingProducts: vi.fn(),
  buildMcpCheckoutUrl: vi.fn(),
  reportMissingMcp: vi.fn(),
}));

vi.mock("../services/mcp-service", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../services/mcp-service")>();
  return {
    ...actual,
    mcpService: {
      getBillingProducts: mcpServiceMocks.getBillingProducts,
      buildMcpCheckoutUrl: mcpServiceMocks.buildMcpCheckoutUrl,
      reportMissingMcp: mcpServiceMocks.reportMissingMcp,
    },
  };
});

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
      ...defaultMcpMetadata(),
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
    mcpServiceMocks.getBillingProducts.mockResolvedValue([]);
    mcpServiceMocks.buildMcpCheckoutUrl.mockImplementation(
      (serverId: string) =>
        `/api/billing/mcp-products/${serverId}/checkout?format=html`,
    );
  });

  it("renders card panels with proper data-testid values", () => {
    render(<ToolRegistryPage />);

    // Assert cards have data-testid for styling tests
    const serverCard = screen.getByTestId("server-card-server-1");
    expect(serverCard).toBeInTheDocument();

    const title = screen.getByText("CalculiX Simulation");
    expect(title).toBeInTheDocument();
  });

  it("keeps install clickable when required credentials are missing", () => {
    const saveCredentials = vi.fn().mockResolvedValue({
      server_id: "jarvis-onshape-mcp",
      env_vars: [],
      configured: {
        ONSHAPE_API_KEY: true,
        ONSHAPE_API_SECRET: true,
      },
    });
    const installServerState = vi.fn().mockResolvedValue(undefined);

    (useTools as any).mockReturnValue({
      servers: [
        {
          server_id: "jarvis-onshape-mcp",
          name: "Jarvis OnShape MCP",
          type: "stdio",
          command: ["uv", "run", "onshape-mcp"],
          is_active: false,
          is_installed: false,
          status: "inactive",
          category: "cad",
          created_at: 1000,
          updated_at: 1000,
          description: "AI copilot for Onshape CAD.",
          env_vars: [
            {
              name: "ONSHAPE_API_KEY",
              label: "Access Key",
              required: true,
              secret: false,
            },
            {
              name: "ONSHAPE_API_SECRET",
              label: "Secret Key",
              required: true,
              secret: true,
            },
          ],
          credentials_configured: {
            ONSHAPE_API_KEY: false,
            ONSHAPE_API_SECRET: false,
          },
          ...defaultMcpMetadata(),
        },
      ],
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
      installServerState,
      uninstallServerState: vi.fn(),
      deleteServerState: vi.fn(),
      toggleToolState: vi.fn(),
      saveCredentials,
      deleteCredentials: vi.fn(),
    });

    render(<ToolRegistryPage />);

    expect(
      screen.getByTestId("server-card-install-btn-jarvis-onshape-mcp"),
    ).toBeEnabled();
  });

  it("collects missing credentials during install and then installs", async () => {
    const saveCredentials = vi.fn().mockResolvedValue({
      server_id: "jarvis-onshape-mcp",
      env_vars: [],
      configured: {
        ONSHAPE_API_KEY: true,
        ONSHAPE_API_SECRET: true,
      },
    });
    const installServerState = vi.fn().mockResolvedValue(undefined);

    (useTools as any).mockReturnValue({
      servers: [
        {
          server_id: "jarvis-onshape-mcp",
          name: "Jarvis OnShape MCP",
          type: "stdio",
          command: ["uv", "run", "onshape-mcp"],
          is_active: false,
          is_installed: false,
          status: "inactive",
          category: "cad",
          created_at: 1000,
          updated_at: 1000,
          description: "AI copilot for Onshape CAD.",
          env_vars: [
            {
              name: "ONSHAPE_API_KEY",
              label: "Access Key",
              required: true,
              secret: false,
            },
            {
              name: "ONSHAPE_API_SECRET",
              label: "Secret Key",
              required: true,
              secret: true,
            },
          ],
          credentials_configured: {
            ONSHAPE_API_KEY: false,
            ONSHAPE_API_SECRET: false,
          },
          ...defaultMcpMetadata(),
        },
      ],
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
      installServerState,
      uninstallServerState: vi.fn(),
      deleteServerState: vi.fn(),
      toggleToolState: vi.fn(),
      saveCredentials,
      deleteCredentials: vi.fn(),
    });

    render(<ToolRegistryPage />);

    const installBtn = screen.getByTestId(
      "server-card-install-btn-jarvis-onshape-mcp",
    );
    fireEvent.click(installBtn);

    expect(
      screen.getByTestId("server-card-credentials-form-jarvis-onshape-mcp"),
    ).toBeInTheDocument();
    expect(installServerState).not.toHaveBeenCalled();

    fireEvent.change(
      screen.getByTestId("server-card-credential-input-ONSHAPE_API_KEY"),
      { target: { value: "access-key" } },
    );
    fireEvent.change(
      screen.getByTestId("server-card-credential-input-ONSHAPE_API_SECRET"),
      { target: { value: "secret-key" } },
    );
    fireEvent.click(installBtn);

    await waitFor(() => {
      expect(saveCredentials).toHaveBeenCalledWith("jarvis-onshape-mcp", {
        ONSHAPE_API_KEY: "access-key",
        ONSHAPE_API_SECRET: "secret-key",
      });
      expect(installServerState).toHaveBeenCalledWith(
        "jarvis-onshape-mcp",
        "session-1",
      );
    });
  });

  it("prompts for credentials on installed servers that are missing required keys", () => {
    const saveCredentials = vi.fn().mockResolvedValue({
      server_id: "jarvis-onshape-mcp",
      env_vars: [],
      configured: {
        ONSHAPE_API_KEY: true,
        ONSHAPE_API_SECRET: true,
      },
    });

    (useTools as any).mockReturnValue({
      servers: [
        {
          server_id: "jarvis-onshape-mcp",
          name: "Jarvis OnShape MCP",
          type: "stdio",
          command: ["uv", "run", "onshape-mcp"],
          is_active: false,
          is_installed: true,
          status: "inactive",
          category: "cad",
          created_at: 1000,
          updated_at: 1000,
          description: "AI copilot for Onshape CAD.",
          env_vars: [
            {
              name: "ONSHAPE_API_KEY",
              label: "Access Key",
              required: true,
              secret: false,
            },
            {
              name: "ONSHAPE_API_SECRET",
              label: "Secret Key",
              required: true,
              secret: true,
            },
          ],
          credentials_configured: {
            ONSHAPE_API_KEY: false,
            ONSHAPE_API_SECRET: false,
          },
          ...defaultMcpMetadata(),
        },
      ],
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
      installServerState: vi.fn(),
      uninstallServerState: vi.fn(),
      deleteServerState: vi.fn(),
      toggleToolState: vi.fn(),
      saveCredentials,
      deleteCredentials: vi.fn(),
    });

    render(<ToolRegistryPage />);

    const addCredentialsBtn = screen.getByTestId(
      "server-card-add-credentials-btn-jarvis-onshape-mcp",
    );
    expect(addCredentialsBtn).toBeInTheDocument();

    fireEvent.click(addCredentialsBtn);

    expect(
      screen.getByTestId("server-card-credentials-form-jarvis-onshape-mcp"),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("server-card-notice-jarvis-onshape-mcp"),
    ).toHaveTextContent("Enter the required credentials");
  });

  it("shows price and purchase link for paid MCP servers", async () => {
    const paidServer: McpServer = {
      server_id: "premium-ops-intelligence-mcp",
      name: "Premium Ops Intelligence MCP",
      type: "stdio",
      command: ["uv", "run", "premium"],
      is_active: false,
      is_installed: false,
      status: "inactive",
      category: "business",
      created_at: 1000,
      updated_at: 1000,
      description: "Mock paid MCP server.",
      ...defaultMcpMetadata(),
      installability_tier: "blocked",
      default_enabled: false,
      install_blocked_reason: "Subscription required.",
    };
    mcpServiceMocks.getBillingProducts.mockResolvedValue([
      {
        server_id: "premium-ops-intelligence-mcp",
        name: "Premium Ops Intelligence MCP",
        description: "Mock paid MCP server.",
        price_cents: 1900,
        currency: "usd",
        interval: "month",
        payment_mode: "stripe_billing_subscription_mock",
        requires_payment: true,
        purchased: false,
        install_state: "locked",
        latest_purchase_status: null,
        checkout_url: null,
      },
    ]);

    (useTools as any).mockReturnValue({
      servers: [paidServer],
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
      installServerState: vi.fn(),
      uninstallServerState: vi.fn(),
      deleteServerState: vi.fn(),
      toggleToolState: vi.fn(),
      saveCredentials: vi.fn(),
      deleteCredentials: vi.fn(),
    });

    render(<ToolRegistryPage />);

    expect(
      await screen.findByTestId(
        "server-card-billing-premium-ops-intelligence-mcp",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByTestId("server-card-price-premium-ops-intelligence-mcp"),
    ).toHaveTextContent("$19.00 / month");
    expect(
      screen.getByTestId("server-card-billing-premium-ops-intelligence-mcp"),
    ).toHaveTextContent("Stripe Billing MCP");
    expect(
      screen.getByTestId(
        "server-card-purchase-link-premium-ops-intelligence-mcp",
      ),
    ).toHaveTextContent("Purchase with Stripe");
    expect(
      screen.getByTestId(
        "server-card-purchase-link-premium-ops-intelligence-mcp",
      ),
    ).toHaveAttribute(
      "href",
      "/api/billing/mcp-products/premium-ops-intelligence-mcp/checkout?format=html",
    );
  });

  it("keeps the paid MCP purchase link visible when billing products fail to load", async () => {
    const paidServer: McpServer = {
      server_id: "premium-ops-intelligence-mcp",
      name: "Premium Ops Intelligence MCP",
      type: "stdio",
      command: ["uv", "run", "premium"],
      is_active: false,
      is_installed: false,
      status: "inactive",
      category: "business",
      created_at: 1000,
      updated_at: 1000,
      description: "Mock paid MCP server.",
      ...defaultMcpMetadata(),
      installability_tier: "blocked",
      default_enabled: false,
      approval_gates: ["stripe_link_approval"],
      install_blocked_reason: "Subscription required.",
    };
    mcpServiceMocks.getBillingProducts.mockRejectedValue(
      new Error("Billing API not ready"),
    );

    (useTools as any).mockReturnValue({
      servers: [paidServer],
      tools: mockTools,
      isLoading: false,
      error: null,
      fetchServersAndTools: vi.fn(),
      installServerState: vi.fn(),
      uninstallServerState: vi.fn(),
      deleteServerState: vi.fn(),
      toggleToolState: vi.fn(),
      saveCredentials: vi.fn(),
      deleteCredentials: vi.fn(),
    });

    render(<ToolRegistryPage />);

    expect(
      await screen.findByTestId(
        "server-card-billing-premium-ops-intelligence-mcp",
      ),
    ).toHaveTextContent("Stripe Billing MCP");
    expect(
      screen.getByTestId(
        "server-card-purchase-link-premium-ops-intelligence-mcp",
      ),
    ).toHaveAttribute(
      "href",
      "/api/billing/mcp-products/premium-ops-intelligence-mcp/checkout?format=html",
    );
  });
});
