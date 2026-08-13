import { StrictMode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DirectBrepSurface } from "./DirectBrepSurface";

const mocks = vi.hoisted(() => ({
  openBrepPanel: vi.fn(),
  openExternal: vi.fn(),
}));

vi.mock("../../services/workspace-service", () => ({
  workspaceService: { openBrepPanel: mocks.openBrepPanel },
}));

vi.mock("../../services/host-adapter", () => ({
  hostAdapter: { openExternal: mocks.openExternal },
}));

describe("DirectBrepSurface", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.openBrepPanel.mockResolvedValue({
      server_id: "brep-server",
      control_url: "http://127.0.0.1:61234/?token=test-secret-token-012345",
      module_url: "http://127.0.0.1:5190/src/CAD.ts",
      connected: false,
    });
  });

  it("loads the BREP MCP control page inside the retained Wright panel", async () => {
    render(
      <StrictMode>
        <DirectBrepSurface sessionId="session-1" />
      </StrictMode>,
    );

    await waitFor(() =>
      expect(screen.getByTitle("BREP canvas")).toHaveAttribute(
        "src",
        expect.stringContaining("127.0.0.1:61234"),
      ),
    );
    expect(mocks.openBrepPanel).toHaveBeenCalledOnce();
    expect(mocks.openBrepPanel).toHaveBeenCalledWith("session-1");
  });

  it("offers a retry when BREP startup fails", async () => {
    const user = userEvent.setup();
    mocks.openBrepPanel
      .mockRejectedValueOnce(new Error("Port unavailable"))
      .mockResolvedValueOnce({
        server_id: "brep-server",
        control_url: "http://127.0.0.1:61234/?token=test-secret-token-012345",
        module_url: "http://127.0.0.1:5190/src/CAD.ts",
        connected: false,
      });

    render(<DirectBrepSurface sessionId="session-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Port unavailable",
    );
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByTitle("BREP canvas")).toBeVisible();
  });
});
