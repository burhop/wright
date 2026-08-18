import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { WorkspacePage } from "../src/components/pages/WorkspacePage";

const getWorkspace = vi.fn();
const activateWorkspace = vi.fn();

vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getWorkspace: (...args: unknown[]) => getWorkspace(...args),
    activateWorkspace: (...args: unknown[]) => activateWorkspace(...args),
  },
}));

vi.mock("../src/hooks/useLogger", () => ({
  default: () => ({ info: vi.fn(), error: vi.fn() }),
}));

vi.mock("../src/components/chat/WorkspacePanel", () => ({
  default: ({ workspace }: { workspace: { local_path: string } }) => (
    <div data-testid="workspace-panel-stub">{workspace.local_path}</div>
  ),
}));

describe("WorkspacePage", () => {
  beforeEach(() => {
    getWorkspace.mockReset();
    activateWorkspace.mockReset();
  });

  it("does not reload the workspace after activation", async () => {
    getWorkspace.mockResolvedValue({
      workspace_id: "workspace-1",
      session_id: "session-1",
      local_path: "C:/workspaces/demo",
    });
    activateWorkspace.mockResolvedValue(true);

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByTestId("workspace-panel-stub")).toHaveTextContent(
      "C:/workspaces/demo",
    );
    // Depending on the suite renderer, React may exercise a development
    // remount. Every activation must reuse the workspace from its matching
    // read; the old implementation issued one additional read per activation.
    expect(getWorkspace.mock.calls.length).toBe(
      activateWorkspace.mock.calls.length,
    );
    expect(getWorkspace.mock.calls.length).toBeGreaterThan(0);
    expect(getWorkspace.mock.calls.length).toBeLessThanOrEqual(2);
  });

  it("explains when a legacy workspace is blocked for application safety", async () => {
    getWorkspace.mockRejectedValue(
      new Error(
        "Workspace access blocked because its path overlaps Wright application files.",
      ),
    );

    render(
      <MemoryRouter
        initialEntries={["/workspace/unsafe-workspace"]}
      >
        <Routes>
          <Route path="/workspace/:workspaceId" element={<WorkspacePage />} />
        </Routes>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Workspace Blocked")).toBeInTheDocument();
    expect(screen.getByText(/overlaps Wright application files/i)).toBeVisible();
    expect(activateWorkspace).not.toHaveBeenCalled();
  });
});
