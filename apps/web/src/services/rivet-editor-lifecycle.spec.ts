import { beforeEach, describe, expect, it, vi } from "vitest";

import { workspaceService } from "./workspace-service";
import * as surfaceClient from "./surfaces/surface-client";
import type { SurfaceDescriptor } from "./surfaces/surface-contract";
import {
  ensureRivetEditorRunning,
  retryRivetEditorRunning,
} from "./rivet-editor-lifecycle";

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

  it("leaves a failed editor on its explicit audited Retry control", async () => {
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("failed"),
    );
    const operation = vi.spyOn(surfaceClient, "operateLiveApp");

    await expect(
      ensureRivetEditorRunning("workspace-1", "session-failed"),
    ).rejects.toThrow("Rivet editor cannot start from failed");
    expect(operation).not.toHaveBeenCalled();
  });

  it("performs one lifecycle retry only after explicit user recovery", async () => {
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("failed"),
    );
    const operation = vi
      .spyOn(surfaceClient, "operateLiveApp")
      .mockResolvedValue({ state: "ready" } as surfaceClient.LiveAppRuntime);

    await expect(
      ensureRivetEditorRunning("workspace-1", "session-explicit"),
    ).rejects.toThrow("Rivet editor cannot start from failed");
    expect(operation).not.toHaveBeenCalled();

    await expect(
      retryRivetEditorRunning("workspace-1", "session-explicit"),
    ).resolves.toBe("surface-rivet");
    expect(operation).toHaveBeenCalledTimes(1);
    expect(operation).toHaveBeenCalledWith(
      "surface-rivet",
      "workspace-1",
      "session-explicit",
      "retry",
    );
  });

  it("does not coalesce explicit Retry behind an in-flight passive mount", async () => {
    let releasePassive!: (value: {
      availability: "available";
      detail: null;
      manifest: { id: string };
    }) => void;
    vi.spyOn(workspaceService, "getRivetEditorSurface")
      .mockReturnValueOnce(
        new Promise((resolve) => {
          releasePassive = resolve;
        }),
      )
      .mockResolvedValue({
        availability: "available",
        detail: null,
        manifest: { id: "wright.rivet-editor" },
      });
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("failed"),
    );
    const operation = vi
      .spyOn(surfaceClient, "operateLiveApp")
      .mockResolvedValue({ state: "ready" } as surfaceClient.LiveAppRuntime);

    const passive = ensureRivetEditorRunning(
      "workspace-1",
      "session-overlapping-retry",
    );
    await vi.waitFor(() =>
      expect(workspaceService.getRivetEditorSurface).toHaveBeenCalledTimes(1),
    );
    const explicit = retryRivetEditorRunning(
      "workspace-1",
      "session-overlapping-retry",
    );

    expect(explicit).not.toBe(passive);
    await expect(explicit).resolves.toBe("surface-rivet");
    expect(operation).toHaveBeenCalledTimes(1);
    expect(operation).toHaveBeenCalledWith(
      "surface-rivet",
      "workspace-1",
      "session-overlapping-retry",
      "retry",
    );

    releasePassive({
      availability: "available",
      detail: null,
      manifest: { id: "wright.rivet-editor" },
    });
    await expect(passive).rejects.toThrow("cannot start from failed");
    expect(operation).toHaveBeenCalledTimes(1);
  });

  it("does not spend one explicit Retry authorization more than once", async () => {
    vi.spyOn(surfaceClient, "declareLiveApp").mockResolvedValue(
      descriptor("failed"),
    );
    vi.spyOn(surfaceClient, "listSurfaces").mockResolvedValue([
      descriptor("failed"),
    ]);
    const operation = vi
      .spyOn(surfaceClient, "operateLiveApp")
      .mockResolvedValue({ state: "failed" } as surfaceClient.LiveAppRuntime);

    await expect(
      retryRivetEditorRunning("workspace-1", "session-still-failed"),
    ).rejects.toThrow("Rivet editor remained failed after Retry");
    expect(operation).toHaveBeenCalledTimes(1);
  });
});
