import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ManagedRivetSurface } from "./ManagedRivetSurface";

const mocks = vi.hoisted(() => ({
  closePresentation: vi.fn(),
  createPresentation: vi.fn(),
  ensureRivetEditorRunning: vi.fn(),
}));

vi.mock("../../services/rivet-editor", () => ({
  directRivetEditorUrl: () => null,
  directRivetWorkflowUrl: () => null,
}));

vi.mock("../../services/rivet-editor-lifecycle", () => ({
  ensureRivetEditorRunning: mocks.ensureRivetEditorRunning,
}));

vi.mock("../../services/surfaces/surface-client", () => ({
  closePresentation: mocks.closePresentation,
  createPresentation: mocks.createPresentation,
}));

vi.mock("./DirectRivetSurface", () => ({
  DirectRivetSurface: (props: {
    url: string;
    onEditorReady?: () => void;
    onEditorUnavailable?: (reason: string) => void;
  }) => (
    <div data-testid="direct-rivet-fixture" data-url={props.url}>
      <button type="button" onClick={() => props.onEditorReady?.()}>
        Editor ready
      </button>
      <button
        type="button"
        onClick={() =>
          props.onEditorUnavailable?.("SURFACE_PREVIEW_UNAUTHORIZED")
        }
      >
        Preview unauthorized
      </button>
    </div>
  ),
}));

const launch = (suffix: string) => ({
  presentationId: `presentation-${suffix}`,
  instanceId: "instance-1",
  generation: 1,
  kind: "panel" as const,
  absoluteBootstrapUrl: `http://s-${suffix}.localhost:8000/__wright/bootstrap#${"a".repeat(43)}`,
  expiresAt: "2026-08-12T20:00:00Z",
});

describe("ManagedRivetSurface", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.ensureRivetEditorRunning.mockResolvedValue("surface-rivet");
    mocks.closePresentation.mockResolvedValue(undefined);
  });

  it("renews an unauthorized preview once and offers Retry after a repeat", async () => {
    const user = userEvent.setup();
    mocks.createPresentation
      .mockResolvedValueOnce(launch("first"))
      .mockResolvedValueOnce(launch("second"));

    render(
      <ManagedRivetSurface
        workspaceId="workspace-1"
        sessionId="session-1"
        initialSlug="rivet"
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("direct-rivet-fixture")).toHaveAttribute(
        "data-url",
        launch("first").absoluteBootstrapUrl,
      ),
    );
    await user.click(
      screen.getByRole("button", { name: "Preview unauthorized" }),
    );

    await waitFor(() =>
      expect(screen.getByTestId("direct-rivet-fixture")).toHaveAttribute(
        "data-url",
        launch("second").absoluteBootstrapUrl,
      ),
    );
    expect(mocks.closePresentation).toHaveBeenCalledWith(
      "surface-rivet",
      "presentation-first",
      "workspace-1",
      "session-1",
    );

    await user.click(
      screen.getByRole("button", { name: "Preview unauthorized" }),
    );

    await waitFor(() =>
      expect(screen.getByTestId("managed-rivet-retry")).toBeVisible(),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Rivet preview authorization could not be renewed",
    );
    expect(mocks.createPresentation).toHaveBeenCalledTimes(2);
  });

  it("resets the automatic recovery allowance after the editor becomes ready", async () => {
    const user = userEvent.setup();
    mocks.createPresentation
      .mockResolvedValueOnce(launch("first"))
      .mockResolvedValueOnce(launch("second"))
      .mockResolvedValueOnce(launch("third"));

    render(
      <ManagedRivetSurface
        workspaceId="workspace-1"
        sessionId="session-1"
        initialSlug="rivet"
      />,
    );
    await screen.findByTestId("direct-rivet-fixture");
    await user.click(
      screen.getByRole("button", { name: "Preview unauthorized" }),
    );
    await waitFor(() =>
      expect(mocks.createPresentation).toHaveBeenCalledTimes(2),
    );
    await user.click(screen.getByRole("button", { name: "Editor ready" }));
    await user.click(
      screen.getByRole("button", { name: "Preview unauthorized" }),
    );

    await waitFor(() =>
      expect(mocks.createPresentation).toHaveBeenCalledTimes(3),
    );
    expect(screen.queryByTestId("managed-rivet-retry")).not.toBeInTheDocument();
  });
});
