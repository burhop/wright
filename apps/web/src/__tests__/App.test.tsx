import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "../components/pages/DashboardPage";
import appSource from "../App.tsx?raw";

const { logger, workspaceService } = vi.hoisted(() => ({
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

describe("App route compatibility", () => {
  beforeEach(() => {
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
});
