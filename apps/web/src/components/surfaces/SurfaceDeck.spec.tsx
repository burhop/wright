import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import { SurfaceDeck } from "./SurfaceDeck";

function live(surfaceId: string): SurfaceDescriptor {
  return {
    schemaVersion: 1,
    surfaceId,
    workspaceId: "workspace-1",
    source: {
      kind: "live_app",
      sourceId: surfaceId,
      sourceVersion: "a".repeat(64),
      manifestId: surfaceId,
    },
    title: surfaceId,
    lifecycle: "ready",
    instance: {
      instanceId: `instance-${surfaceId}`,
      generation: 1,
      sharing: "shared",
    },
    presentations: [],
    capabilities: [],
    revision: 1,
    createdAt: "2026-07-30T12:00:00Z",
    updatedAt: "2026-07-30T12:00:00Z",
  };
}

function display(surfaceId: string): SurfaceDescriptor {
  return {
    ...live(surfaceId),
    source: {
      kind: "display",
      sourceId: surfaceId,
      sourceVersion: "b".repeat(64),
      displayId: surfaceId,
      revision: 1,
    },
    instance: null,
  };
}

function Probe({
  descriptor,
  onDispose,
}: {
  readonly descriptor: SurfaceDescriptor;
  readonly onDispose: (surfaceId: string) => void;
}) {
  useEffect(
    () => () => onDispose(descriptor.surfaceId),
    [descriptor.surfaceId, onDispose],
  );
  return (
    <div data-testid={`probe-${descriptor.surfaceId}`}>{descriptor.title}</div>
  );
}

describe("SurfaceDeck", () => {
  it("retains a stateful inactive host while another tab is active", () => {
    const dispose = vi.fn();
    const descriptors = [live("app-a"), live("app-b")];
    const renderSurface = (item: SurfaceDescriptor) => (
      <Probe descriptor={item} onDispose={dispose} />
    );
    const { rerender } = render(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="app-a"
        renderSurface={renderSurface}
      />,
    );

    rerender(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="app-b"
        renderSurface={renderSurface}
      />,
    );
    const inactivePanel = screen
      .getByTestId("probe-app-a")
      .closest('[role="tabpanel"]');
    expect(inactivePanel).toHaveAttribute("aria-hidden", "true");
    expect(inactivePanel).not.toBeVisible();
    expect(dispose).not.toHaveBeenCalled();
  });

  it("bounds retained hosts after consent while always keeping the active host", async () => {
    const user = userEvent.setup();
    const dispose = vi.fn();
    const descriptors = [live("app-a"), live("app-b"), live("app-c")];
    render(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="app-c"
        maximumRetainedHosts={2}
        renderSurface={(item) => (
          <Probe descriptor={item} onDispose={dispose} />
        )}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Reload least recently used surface",
      }),
    );
    expect(screen.queryByTestId("probe-app-a")).not.toBeInTheDocument();
    expect(screen.getByTestId("probe-app-b")).toBeInTheDocument();
    expect(screen.getByTestId("probe-app-c")).toBeVisible();
  });

  it("unmounts a retained host when server reconciliation removes it", () => {
    const dispose = vi.fn();
    const descriptors = [live("app-a"), live("app-b")];
    const renderSurface = (item: SurfaceDescriptor) => (
      <Probe descriptor={item} onDispose={dispose} />
    );
    const { rerender } = render(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="app-b"
        renderSurface={renderSurface}
      />,
    );

    rerender(
      <SurfaceDeck
        descriptors={[descriptors[1]]}
        activeSurfaceId="app-b"
        renderSurface={renderSurface}
      />,
    );
    expect(dispose).toHaveBeenCalledWith("app-a");
    expect(screen.queryByTestId("probe-app-a")).not.toBeInTheDocument();
  });

  it("retains live hosts but suspends inactive static displays", () => {
    const dispose = vi.fn();
    const descriptors = [live("app-a"), display("graph-a")];
    const renderSurface = (item: SurfaceDescriptor) => (
      <Probe descriptor={item} onDispose={dispose} />
    );
    const { rerender } = render(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="graph-a"
        renderSurface={renderSurface}
      />,
    );
    rerender(
      <SurfaceDeck
        descriptors={descriptors}
        activeSurfaceId="app-a"
        renderSurface={renderSurface}
      />,
    );

    expect(screen.getByTestId("probe-app-a")).toBeVisible();
    expect(screen.queryByTestId("probe-graph-a")).not.toBeInTheDocument();
    expect(dispose).toHaveBeenCalledTimes(1);
  });

  it("warns before pressure can reload a retained stateful host", () => {
    render(
      <SurfaceDeck
        descriptors={[live("app-a"), live("app-b"), live("app-c")]}
        activeSurfaceId="app-c"
        maximumRetainedHosts={2}
        renderSurface={(item) => <div>{item.title}</div>}
      />,
    );

    expect(
      screen.getByRole("alertdialog", { name: "Surface memory limit reached" }),
    ).toBeVisible();
    expect(screen.getByText(/app-a.*reload/i)).toBeVisible();
  });

  it("disposes an evicted host exactly once and restores focus to the active panel", async () => {
    const user = userEvent.setup();
    const dispose = vi.fn();
    render(
      <SurfaceDeck
        descriptors={[live("app-a"), live("app-b"), live("app-c")]}
        activeSurfaceId="app-c"
        maximumRetainedHosts={2}
        renderSurface={(item) => (
          <Probe descriptor={item} onDispose={dispose} />
        )}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "Reload least recently used surface",
      }),
    );
    expect(dispose).toHaveBeenCalledTimes(1);
    expect(dispose).toHaveBeenCalledWith("app-a");
    expect(screen.getByRole("tabpanel", { name: "app-c" })).toHaveFocus();
  });
});
