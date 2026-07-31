import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
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
  return <div data-testid={`probe-${descriptor.surfaceId}`}>{descriptor.title}</div>;
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

  it("bounds retained hosts while always keeping the active host", () => {
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
});
