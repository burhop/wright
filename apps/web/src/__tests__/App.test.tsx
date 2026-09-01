import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "../components/pages/DashboardPage";
import Sidebar from "../components/layout/Sidebar";
import appSource from "../App.tsx?raw";

const { featureFlags, logger, workspaceService } = vi.hoisted(() => ({
  featureFlags: { processDefinitionEnabled: false, workflowComposerEnabled: false, workflowRecoveryEnabled: false },
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
vi.mock("../config/workflow-composer", () => ({
  workflowComposerEnabled: () => featureFlags.workflowComposerEnabled,
}));
vi.mock("../config/workflow-recovery", () => ({
  workflowRecoveryEnabled: () => featureFlags.workflowRecoveryEnabled,
}));

describe("App route compatibility", () => {
  beforeEach(() => {
    featureFlags.processDefinitionEnabled = false;
    featureFlags.workflowComposerEnabled = false;
    featureFlags.workflowRecoveryEnabled = false;
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

  it("guards the separate composer route with its independent browser flag", () => {
    const guard = "{composerEnabled && (";
    const route = 'path="/workflow-composer"';
    const wildcard = 'path="*"';

    expect(appSource).toContain("const composerEnabled = workflowComposerEnabled();");
    expect(appSource.indexOf(guard)).toBeGreaterThan(-1);
    expect(appSource.indexOf(route)).toBeGreaterThan(appSource.indexOf(guard));
    expect(appSource.indexOf(route)).toBeLessThan(appSource.indexOf(wildcard));
  });

  it("guards the disposable recovery route with its own default-off flag", () => {
    const guard = "{recoveryEnabled && (";
    const route = 'path="/workflow-recovery"';
    const wildcard = 'path="*"';

    expect(appSource).toContain("const recoveryEnabled = workflowRecoveryEnabled();");
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

  it("shows the composer navigation separately without changing Process Definition", () => {
    const { rerender } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId("nav-workflow-composer")).not.toBeInTheDocument();
    expect(screen.queryByTestId("nav-process-definition")).not.toBeInTheDocument();

    featureFlags.workflowComposerEnabled = true;
    rerender(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("nav-workflow-composer")).toHaveAttribute("href", "/workflow-composer");
    expect(screen.queryByTestId("nav-process-definition")).not.toBeInTheDocument();
  });

  it("shows recovery navigation only while its independent flag is enabled", () => {
    const { rerender } = render(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );
    expect(screen.queryByTestId("nav-workflow-recovery")).not.toBeInTheDocument();

    featureFlags.workflowRecoveryEnabled = true;
    rerender(
      <MemoryRouter>
        <Sidebar />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("nav-workflow-recovery")).toHaveAttribute("href", "/workflow-recovery");
    expect(screen.queryByTestId("nav-workflow-composer")).not.toBeInTheDocument();
  });
});
