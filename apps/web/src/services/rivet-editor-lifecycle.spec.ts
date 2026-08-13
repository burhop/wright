import { beforeEach, describe, expect, it, vi } from "vitest";

import { workspaceService } from "./workspace-service";
import * as surfaceClient from "./surfaces/surface-client";
import type { SurfaceDescriptor } from "./surfaces/surface-contract";
import { ensureRivetEditorRunning } from "./rivet-editor-lifecycle";

const descriptor = (
  lifecycle: SurfaceDescriptor["lifecycle"],
): SurfaceDescriptor =>
  ({
    schemaVersion: 1,
    surfaceId: "surface-rivet",
    workspaceId: "workspace-1",
    source: {
      kind: "live_app",
      sourceId: "wright.rivet-editor",
      sourceVersion: "a".repeat(64),
      manifestId: "wright.rivet-editor",
    },
    title: "Rivet",
    lifecycle,
    presentations: [],
    capabilities: [],
    revision: 1,
    createdAt: "2026-07-30T12:00:00Z",
    updatedAt: "2026-07-30T12:00:00Z",
  }) as SurfaceDescriptor;

describe("managed Rivet editor lifecycle", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(workspaceService, "getRivetEditorSurface").mockResolvedValue({
      availability: "available",
      detail: null,
      manifest: { id: "wright.rivet-editor" },
    });
  });

  it("coalesces simultaneous restored tabs into one managed start", async () => {
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("declared"),
    );
    let finish!: (value: surfaceClient.LiveAppRuntime) => void;
    const operation = vi
      .spyOn(surfaceClient, "operateLiveApp")
      .mockReturnValue(new Promise((resolve) => (finish = resolve)));

    const first = ensureRivetEditorRunning("workspace-1", "session-1");
    const second = ensureRivetEditorRunning("workspace-1", "session-1");

    expect(second).toBe(first);
    await vi.waitFor(() => expect(operation).toHaveBeenCalledTimes(1));
    finish({ state: "ready" } as surfaceClient.LiveAppRuntime);
    await expect(first).resolves.toBe("surface-rivet");
    expect(operation).toHaveBeenCalledTimes(1);
    expect(operation).toHaveBeenCalledWith(
      "surface-rivet",
      "workspace-1",
      "session-1",
      "start",
    );
  });

  it("reuses an already running editor without restarting it", async () => {
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("ready"),
    );
    const operation = vi.spyOn(surfaceClient, "operateLiveApp");

    await expect(
      ensureRivetEditorRunning("workspace-1", "session-2"),
    ).resolves.toBe("surface-rivet");
    expect(operation).not.toHaveBeenCalled();
  });
});
