import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import { SurfaceToolbar } from "./SurfaceToolbar";

const descriptor = (
  lifecycle: SurfaceDescriptor["lifecycle"] = "ready",
): SurfaceDescriptor => ({
  schemaVersion: 1,
  surfaceId: "surface-app",
  workspaceId: "workspace-1",
  source: {
    kind: "live_app",
    sourceId: "shareable-app",
    sourceVersion: "a".repeat(64),
    manifestId: "shareable-app",
  },
  title: "Shareable app",
  lifecycle,
  instance: {
    instanceId: "instance-shared",
    generation: 3,
    sharing: "shared",
  },
  presentations: [
    { kind: "panel", eligible: true },
    { kind: "browser", eligible: true },
  ],
  capabilities: [],
  revision: 4,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
});

function callbacks() {
  return {
    onOpen: vi.fn(),
    onOpenBoth: vi.fn(),
    onFocus: vi.fn(),
    onClosePresentation: vi.fn(),
    onStopApplication: vi.fn(),
    onDiagnostics: vi.fn(),
    onRememberPreferenceChange: vi.fn(),
  };
}

describe("SurfaceToolbar", () => {
  it("offers panel, browser, and both for one shareable ready instance", async () => {
    const user = userEvent.setup();
    const actions = callbacks();
    render(
      <SurfaceToolbar
        descriptor={descriptor()}
        activeKinds={[]}
        rememberPreference={false}
        preferredKind="browser"
        {...actions}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent(/ready/i);
    expect(screen.getByText(/same running instance/i)).toBeVisible();
    expect(screen.getByText(/preferred presentation: browser/i)).toBeVisible();
    expect(screen.getByTestId("surface-open-browser")).toHaveTextContent(
      /preferred/i,
    );
    await user.click(screen.getByTestId("surface-open-panel"));
    await user.click(screen.getByTestId("surface-open-browser"));
    await user.click(screen.getByTestId("surface-open-both"));
    expect(actions.onOpen).toHaveBeenNthCalledWith(1, "panel");
    expect(actions.onOpen).toHaveBeenNthCalledWith(2, "browser");
    expect(actions.onOpenBoth).toHaveBeenCalledOnce();

    await user.click(
      screen.getByLabelText("Remember this presentation choice"),
    );
    expect(actions.onRememberPreferenceChange).toHaveBeenCalledWith(true);
  });

  it("keeps close-presentation and stop-application consequences distinct", async () => {
    const user = userEvent.setup();
    const actions = callbacks();
    render(
      <SurfaceToolbar
        descriptor={descriptor()}
        activeKinds={["panel"]}
        rememberPreference
        {...actions}
      />,
    );
    await user.click(screen.getByTestId("surface-close-panel"));
    expect(actions.onClosePresentation).toHaveBeenCalledWith("panel");
    expect(screen.getByTestId("surface-stop-application")).toHaveAccessibleName(
      /stop application/i,
    );
    expect(screen.getByText(/closing this view keeps.*running/i)).toBeVisible();
  });

  it("shows truthful lifecycle and recovery actions instead of a blank frame", async () => {
    const user = userEvent.setup();
    const actions = callbacks();
    const { rerender } = render(
      <SurfaceToolbar
        descriptor={descriptor("starting")}
        activeKinds={[]}
        rememberPreference={false}
        {...actions}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      /starting.*not ready/i,
    );
    expect(screen.queryByTestId("surface-open-panel")).not.toBeInTheDocument();
    await user.click(screen.getByTestId("surface-diagnostics"));
    expect(actions.onDiagnostics).toHaveBeenCalledOnce();

    rerender(
      <SurfaceToolbar
        descriptor={descriptor("unhealthy")}
        activeKinds={[]}
        rememberPreference={false}
        frameStatus="unknown"
        {...actions}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/embedding.*blocked/i);
    expect(screen.getByTestId("surface-open-browser")).toBeVisible();
  });
});
