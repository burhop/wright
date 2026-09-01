import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
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

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location-probe">{location.pathname}{location.search}</output>;
}

describe("App route compatibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    featureFlags.processDefinitionEnabled = false;
    workspaceService.getRecentWorkspaces.mockResolvedValue([]);
    workspaceService.getAllWorkspaces.mockResolvedValue([]);
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

  it("falls back to the complete workspace index and reports its real count", async () => {
    workspaceService.getRecentWorkspaces.mockResolvedValueOnce([]);
    workspaceService.getAllWorkspaces.mockResolvedValueOnce([
      {
        workspace_id: "workspace-1",
        session_id: "session-1",
        workspace_name: "Bracket Program",
        local_path: "D:\\engineering\\bracket-program",
        git_remote_url: null,
        git_username: null,
        updated_at: Math.floor(Date.now() / 1000),
      },
    ]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Bracket Program")).toBeVisible();
    expect(screen.getByTestId("card-telemetry")).toHaveTextContent(
      /Total Workspaces Indexed:\s*1/,
    );
    expect(screen.queryByText(/No workspaces yet/)).not.toBeInTheDocument();
  });

  it("keeps the complete workspace index when the recent endpoint fails", async () => {
    workspaceService.getRecentWorkspaces.mockRejectedValueOnce(
      new Error("recent index unavailable"),
    );
    workspaceService.getAllWorkspaces.mockResolvedValueOnce([
      {
        workspace_id: "workspace-2",
        session_id: "session-2",
        workspace_name: "Gearbox Program",
        local_path: "D:\\engineering\\gearbox-program",
        git_remote_url: null,
        git_username: null,
        updated_at: Math.floor(Date.now() / 1000),
      },
    ]);

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Gearbox Program")).toBeVisible();
    expect(screen.queryByText(/could not be loaded/i)).not.toBeInTheDocument();
    expect(logger.error).toHaveBeenCalledWith(
      "Failed to load recent workspaces",
      expect.objectContaining({ err: expect.any(Error) }),
    );
  });

  it("does not report an empty or complete index when the full workspace index fails", async () => {
    workspaceService.getRecentWorkspaces.mockResolvedValueOnce([]);
    workspaceService.getAllWorkspaces.mockRejectedValueOnce(
      new Error("complete index unavailable"),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/complete workspace list could not be loaded/i)).toBeVisible();
    expect(screen.queryByText(/No workspaces yet/)).not.toBeInTheDocument();
    expect(screen.getByTestId("card-telemetry")).toHaveTextContent(
      /Total Workspaces Indexed:\s*Unavailable/,
    );
    expect(screen.getByTestId("retry-workspaces-btn")).toBeVisible();
  });

  it("labels recent results as partial when the complete workspace index fails", async () => {
    workspaceService.getRecentWorkspaces.mockResolvedValueOnce([
      {
        workspace_id: "workspace-3",
        session_id: "session-3",
        workspace_name: "Pump Program",
        local_path: "D:\\engineering\\pump-program",
        git_remote_url: null,
        git_username: null,
        updated_at: Math.floor(Date.now() / 1000),
      },
    ]);
    workspaceService.getAllWorkspaces.mockRejectedValueOnce(
      new Error("complete index unavailable"),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText("Pump Program")).toBeVisible();
    expect(screen.getByTestId("workspace-index-partial")).toHaveTextContent(
      /showing recent workspaces/i,
    );
    expect(screen.getByTestId("card-telemetry")).toHaveTextContent(
      /Total Workspaces Indexed:\s*Unavailable/,
    );
    expect(screen.getByTestId("view-all-workspaces-btn")).toHaveTextContent(
      /Retry full workspace list/,
    );
  });

  it("opens the workspace first and leaves Workflows as an explicit workspace action", async () => {
    workspaceService.getRecentWorkspaces.mockResolvedValueOnce([
      {
        workspace_id: "workspace-4",
        session_id: "session-4",
        workspace_name: "Fixture Program",
        local_path: "D:\\engineering\\fixture-program",
        git_remote_url: null,
        git_username: null,
        updated_at: Math.floor(Date.now() / 1000),
      },
    ]);
    workspaceService.getAllWorkspaces.mockResolvedValueOnce([]);
    workspaceService.activateWorkspace.mockResolvedValueOnce(true);

    render(
      <MemoryRouter>
        <DashboardPage />
        <LocationProbe />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByText("Fixture Program"));
    await waitFor(() => expect(screen.getByTestId("location-probe")).toHaveTextContent("/workspace/workspace-4"));
    expect(screen.getByTestId("location-probe")).not.toHaveTextContent("workflow=canonical");
  });

  it("does not claim the workspace index is empty while it is loading", async () => {
    let resolveRecent!: (value: never[]) => void;
    let resolveAll!: (value: never[]) => void;
    workspaceService.getRecentWorkspaces.mockReturnValueOnce(
      new Promise((resolve) => { resolveRecent = resolve; }),
    );
    workspaceService.getAllWorkspaces.mockReturnValueOnce(
      new Promise((resolve) => { resolveAll = resolve; }),
    );

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("Loading workspaces…")).toBeVisible();
    expect(screen.queryByText(/No workspaces yet/)).not.toBeInTheDocument();
    resolveRecent([]);
    resolveAll([]);
    expect(await screen.findByText(/No workspaces yet/)).toBeVisible();
  });

  it("does not expose the workspace workflow editor as a global route", () => {
    expect(appSource).not.toContain('path="/workflow-recovery"');
    expect(appSource).not.toContain('path="/workflow-composer"');
    expect(appSource).not.toContain("WorkflowRecoveryPage");
    expect(appSource).not.toContain("WorkflowComposerPage");
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

  it("does not expose a global workflow navigation entry", () => {
    render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId("nav-workflow-recovery")).not.toBeInTheDocument();
    expect(screen.queryByTestId("nav-workflow-composer")).not.toBeInTheDocument();
    expect(screen.queryByText(/workflow recovery/i)).not.toBeInTheDocument();
  });
});
