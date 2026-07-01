import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "../src/components/pages/DashboardPage";

const serviceMocks = vi.hoisted(() => ({
  getRecentWorkspaces: vi.fn(),
  getAllWorkspaces: vi.fn(),
  activateWorkspace: vi.fn(),
  getBillingSubscriptions: vi.fn(),
}));

vi.mock("../src/hooks/useLogger", () => ({
  default: () => ({
    info: vi.fn(),
    error: vi.fn(),
    warn: vi.fn(),
  }),
}));

vi.mock("../src/hooks/useHealthStatus", () => ({
  default: () => [
    { serviceId: "wright-api", state: "connected" },
    { serviceId: "hermes-agent", state: "connected" },
    { serviceId: "llm-backend", state: "connected" },
  ],
}));

vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getRecentWorkspaces: serviceMocks.getRecentWorkspaces,
    getAllWorkspaces: serviceMocks.getAllWorkspaces,
    activateWorkspace: serviceMocks.activateWorkspace,
  },
}));

vi.mock("../src/services/mcp-service", () => ({
  mcpService: {
    getBillingSubscriptions: serviceMocks.getBillingSubscriptions,
  },
}));

describe("Dashboard subscriptions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    serviceMocks.getRecentWorkspaces.mockResolvedValue([]);
    serviceMocks.getAllWorkspaces.mockResolvedValue([]);
    serviceMocks.activateWorkspace.mockResolvedValue(true);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => ({
        ok: true,
        json: async () =>
          url.includes("/api/agent/sessions") ? { sessions: [] } : { logs: [] },
      })),
    );
  });

  it("shows an empty subscription panel before checkout", async () => {
    serviceMocks.getBillingSubscriptions.mockResolvedValue([]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("card-subscriptions")).toBeInTheDocument();
    expect(screen.getByTestId("subscriptions-empty")).toBeEmptyDOMElement();
    expect(screen.getByTestId("subscriptions-count")).toHaveTextContent(
      "0 active",
    );
    expect(screen.getByText("Nemotron-Nano-30B")).toBeInTheDocument();
  });

  it("shows paid MCP subscriptions with payment date, amount, and enabled state", async () => {
    serviceMocks.getBillingSubscriptions.mockResolvedValue([
      {
        subscription_id: "mp_paid_123",
        server_id: "premium-ops-intelligence-mcp",
        server_name: "Premium Ops Intelligence MCP",
        customer_id: "demo-builder",
        session_id: "billing-session",
        amount_cents: 1900,
        currency: "usd",
        interval: "month",
        payment_date: 1782820800,
        status: "active",
        mcp_enabled: true,
        mcp_status: "enabled",
      },
    ]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(
        screen.getByTestId("subscription-row-premium-ops-intelligence-mcp"),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("Premium Ops Intelligence MCP")).toBeInTheDocument();
    expect(screen.getByText("$19.00 / month")).toBeInTheDocument();
    expect(screen.getByText("Jun 30, 2026")).toBeInTheDocument();
    expect(
      screen.getByTestId(
        "subscription-mcp-status-premium-ops-intelligence-mcp",
      ),
    ).toHaveTextContent("MCP Server enabled");
    expect(screen.getByTestId("subscriptions-count")).toHaveTextContent(
      "1 active",
    );
  });
});
