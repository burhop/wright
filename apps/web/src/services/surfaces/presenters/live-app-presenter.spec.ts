import { describe, expect, it, vi } from "vitest";

import type { HostAdapter } from "../../host-adapter";
import type { SurfaceDescriptor } from "../surface-contract";
import type { PresentationLaunch } from "../surface-client";
import { LiveAppPresenter } from "./live-app-presenter";

const launch: PresentationLaunch = {
  presentationId: "presentation-1",
  instanceId: "instance-1",
  generation: 3,
  kind: "panel",
  absoluteBootstrapUrl:
    "https://s-opaque.preview.test/__wright/bootstrap#abcdefghijklmnopqrstuvwxyz123456",
  expiresAt: "2026-07-30T12:05:00Z",
};

function descriptor(
  title = "Shared dashboard",
  instanceId = "instance-1",
  generation = 3,
): SurfaceDescriptor {
  return {
    schemaVersion: 1,
    surfaceId: "surface-app",
    workspaceId: "workspace-1",
    source: {
      kind: "live_app",
      sourceId: "shared-dashboard",
      sourceVersion: "a".repeat(64),
      manifestId: "shared-dashboard",
    },
    title,
    lifecycle: "ready",
    instance: { instanceId, generation, sharing: "shared" },
    presentations: [],
    capabilities: [],
    revision: 4,
    createdAt: "2026-07-30T12:00:00Z",
    updatedAt: "2026-07-30T12:00:00Z",
  };
}

function adapter(validate = vi.fn((value: string) => value)): HostAdapter {
  return {
    mode: "browser",
    surfaceCapabilities: { absolutePreviewUrls: true, externalOpen: true },
    fetch: vi.fn(),
    readFile: vi.fn(),
    writeFile: vi.fn(),
    listDirectory: vi.fn(),
    selectFiles: vi.fn(),
    getApiBaseUrl: () => "http://control.test",
    resolveBackendUrl: (path) => `http://control.test${path}`,
    validateIssuedPreviewUrl: validate,
    openExternal: vi.fn(),
    getRouterType: () => "browser",
    notify: vi.fn(),
    hasTerminal: () => false,
    dispose: vi.fn(),
  };
}

describe("LiveAppPresenter", () => {
  it("mounts only a validated backend-issued URL in a restricted frame", () => {
    const validate = vi.fn((value: string) => value);
    const statuses: string[] = [];
    const host = document.createElement("div");
    const presenter = new LiveAppPresenter(
      launch,
      descriptor(),
      (status) => statuses.push(status),
      adapter(validate),
    );

    presenter.mount(host);
    const frame = host.querySelector("iframe");
    expect(validate).toHaveBeenCalledWith(launch.absoluteBootstrapUrl);
    expect(frame).not.toBeNull();
    expect(frame).toHaveAttribute("sandbox", "allow-scripts allow-forms allow-same-origin");
    expect(frame).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(frame).toHaveAttribute("allow", expect.stringContaining("camera 'none'"));
    expect(statuses).toEqual(["loading"]);

    frame?.dispatchEvent(new Event("load"));
    expect(statuses).toEqual(["loading", "unknown"]);
    presenter.dispose();
  });

  it("updates only the presentation's current instance generation", () => {
    const host = document.createElement("div");
    const presenter = new LiveAppPresenter(
      launch,
      descriptor(),
      vi.fn(),
      adapter(),
    );
    presenter.mount(host);

    presenter.update(descriptor("Renamed dashboard"));
    expect(host.querySelector("iframe")).toHaveAttribute(
      "title",
      "Renamed dashboard",
    );
    expect(() =>
      presenter.update(descriptor("Stale dashboard", "instance-2", 4)),
    ).toThrow(/stale instance generation/i);
    presenter.dispose();
  });

  it("disposes its exact frame once and refuses remount", () => {
    const host = document.createElement("div");
    const presenter = new LiveAppPresenter(
      launch,
      descriptor(),
      vi.fn(),
      adapter(),
    );
    presenter.mount(host);
    presenter.dispose();
    presenter.dispose();

    expect(host.querySelector("iframe")).toBeNull();
    expect(() => presenter.mount(host)).toThrow(/disposed/i);
  });
});
