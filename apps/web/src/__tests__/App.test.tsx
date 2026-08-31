import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "../components/pages/DashboardPage";
import Sidebar from "../components/layout/Sidebar";
import appSource from "../App.tsx?raw";

const { featureFlags, logger, workspaceService } = vi.hoisted(() => ({
  featureFlags: { processDefinitionEnabled: false },
  logger: { info: vi.fn(), error: vi.fn() },
  workspaceService: {
    getRecentWorkspaces: vi.fn().mockResolvedValue([]),
    getAllWorkspaces: vi.fn().mockResolvedValue([]),
    activateWorkspace: vi.fn(),
  },
}));

vi.mock("../hooks/useLogger", () => ({ default: () => logger }));
vi.mock("../hooks/useHealthStatus", () => ({
  default: () => [
    { serviceId: "wright-api", state: "connected" },
    { serviceId: "hermes-agent", state: "connected" },
    { serviceId: "llm-backend", state: "connected" },
  ],
}));
vi.mock("../services/workspace-service", () => ({ workspaceService }));
vi.mock("../services/surfaces/feature-flags", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../services/surfaces/feature-flags")>();
  return {
    ...actual,
    processDefinitionViewEnabled: () => featureFlags.processDefinitionEnabled,
  };
});

describe("App route compatibility", () => {
  beforeEach(() => {
    featureFlags.processDefinitionEnabled = false;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ logs: [], sessions: [] }),
      }),
    );
  });

  it("keeps the workspace dashboard behavior independent of program status", async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("page-dashboard")).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Wright Design Hub" }),
    ).toBeVisible();
    await waitFor(() =>
      expect(workspaceService.getRecentWorkspaces).toHaveBeenCalled(),
    );
    fireEvent.click(screen.getByTestId("create-workspace-btn"));
    expect(
      screen.getByRole("heading", { name: "Create Workspace" }),
    ).toBeVisible();
  });

  it("retains every existing top-level route and adds program status separately", () => {
    for (const route of [
      'path="/"',
      'path="/workspace/:workspaceId"',
      'path="/tool-registry"',
      'path="/file-vault"',
      'path="/logs"',
      'path="/setup/model"',
      'path="/engineering-models"',
      'path="/settings"',
      'path="/agent-chat"',
    ]) {
      expect(appSource).toContain(route);
    }
    expect(appSource).toContain(
      '<Route path="/program-status" element={<ProgramStatusPage />} />',
    );
    expect(appSource).toContain(
      '<Route path="/" element={<DashboardPage />} />',
    );
  });

  it("guards the stable process route before the wildcard fallback", () => {
    const guard = "{processDefinitionEnabled && (";
    const route = 'path="/processes/product-definition-v1"';
    const wildcard = 'path="*"';

    expect(appSource).toContain(
      "const processDefinitionEnabled = processDefinitionViewEnabled();",
    );
    expect(appSource.indexOf(guard)).toBeGreaterThan(-1);
    expect(appSource.indexOf(route)).toBeGreaterThan(appSource.indexOf(guard));
    expect(appSource.indexOf(route)).toBeLessThan(appSource.indexOf(wildcard));
  });

  it("shows the process navigation entry only while the flag is enabled", () => {
    const { rerender } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(
      screen.queryByTestId("nav-process-definition"),
    ).not.toBeInTheDocument();

    featureFlags.processDefinitionEnabled = true;
    rerender(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("nav-process-definition")).toHaveAttribute(
      "href",
      "/processes/product-definition-v1",
    );
  });
});
