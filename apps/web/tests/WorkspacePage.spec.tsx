import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

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

describe("WorkspacePage", () => {
  it("explains when a legacy workspace is blocked for application safety", async () => {
    getWorkspace.mockRejectedValueOnce(
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
