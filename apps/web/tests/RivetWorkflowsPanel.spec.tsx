import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RivetWorkflowsPanel } from "../src/components/chat/RivetWorkflowsPanel";
import { workspaceService } from "../src/services/workspace-service";
import * as surfaceClient from "../src/services/surfaces/surface-client";

describe("RivetWorkflowsPanel", () => {
  beforeEach(() => {
    vi.spyOn(workspaceService, "listRivetWorkflowOperations").mockResolvedValue(
      [],
    );
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("discloses manual-only browser storage without a workspace save control", async () => {
    render(
      <RivetWorkflowsPanel sessionId="session-1" workspaceId="workspace-1" />,
    );

    expect(
      screen.getByText(/does not save into the Wright workspace/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /save.*workspace/i }),
    ).toBeNull();
    await waitFor(() => {
      expect(workspaceService.listRivetWorkflowOperations).toHaveBeenCalledWith(
        "session-1",
      );
    });
  });

  it("declares the server-owned isolated editor manifest and reconciles surfaces", async () => {
    const manifest = {
      schemaVersion: 1,
      id: "wright.rivet-editor",
      title: "Rivet editor (manual import/export)",
      version: "1.25.0",
      launch: { mode: "command", argv: ["python", "host.py"] },
    };
    vi.spyOn(workspaceService, "getRivetEditorSurface").mockResolvedValue({
      availability: "available",
      detail: null,
      manifest,
    });
    const declare = vi
      .spyOn(surfaceClient, "declareLiveApp")
      .mockResolvedValue({
        surfaceId: "surface-1",
      } as never);
    const reconciled = vi.fn();
    window.addEventListener("wright-surfaces-changed", reconciled);
    render(
      <RivetWorkflowsPanel sessionId="session-1" workspaceId="workspace-1" />,
    );

    fireEvent.click(screen.getByTestId("rivet-editor-open"));

    await waitFor(() => {
      expect(declare).toHaveBeenCalledWith(
        manifest,
        "workspace-1",
        "session-1",
      );
    });
    expect(reconciled).toHaveBeenCalledTimes(1);
    expect(
      screen.getByText(/opened as an isolated workspace tab/i),
    ).toBeInTheDocument();
    window.removeEventListener("wright-surfaces-changed", reconciled);
  });
});
