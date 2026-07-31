import { describe, expect, it } from "vitest";

import type { SurfaceDescriptor } from "../services/surfaces/surface-contract";
import {
  createSurfaceState,
  reconcileRestoredSurfaceState,
  reduceSurfaceState,
} from "./surfaces";

const live = (
  lifecycle: SurfaceDescriptor["lifecycle"],
  instance: SurfaceDescriptor["instance"],
  revision: number,
): SurfaceDescriptor => ({
  schemaVersion: 1,
  surfaceId: "surface-app",
  workspaceId: "workspace-1",
  source: {
    kind: "live_app",
    sourceId: "app",
    sourceVersion: "a".repeat(64),
    manifestId: "app",
  },
  title: "App",
  lifecycle,
  instance,
  presentations: [],
  capabilities: [],
  revision,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
});

describe("surface restore reconciliation", () => {
  it("keeps a valid current instance but takes all authority from the server", () => {
    const stale = live(
      "ready",
      { instanceId: "instance-1", generation: 2, sharing: "shared" },
      2,
    );
    const restored = reduceSurfaceState(createSurfaceState(), {
      type: "upsert",
      descriptor: stale,
    });
    const current = live(
      "ready",
      { instanceId: "instance-1", generation: 2, sharing: "shared" },
      3,
    );
    const reconciled = reconcileRestoredSurfaceState(restored, [current]);
    expect(reconciled.activeSurfaceId).toBe("surface-app");
    expect(reconciled.byId["surface-app"]).toBe(current);
  });

  it("replaces stale running state without launching a new app", () => {
    const restored = reduceSurfaceState(createSurfaceState(), {
      type: "upsert",
      descriptor: live(
        "ready",
        { instanceId: "old", generation: 1, sharing: "shared" },
        1,
      ),
    });
    const stopped = live("stopped", null, 2);
    const reconciled = reconcileRestoredSurfaceState(restored, [stopped]);
    expect(reconciled.byId["surface-app"].lifecycle).toBe("stopped");
    expect(reconciled.byId["surface-app"].instance).toBeNull();
  });

  it("drops a surface that is no longer authorized or available", () => {
    const restored = reduceSurfaceState(createSurfaceState(), {
      type: "upsert",
      descriptor: live(
        "ready",
        { instanceId: "old", generation: 1, sharing: "shared" },
        1,
      ),
    });
    const reconciled = reconcileRestoredSurfaceState(restored, []);
    expect(reconciled.tabs).toEqual([]);
    expect(reconciled.activeSurfaceId).toBeNull();
  });
});
