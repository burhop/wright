import { describe, expect, it } from "vitest";

import type { SurfaceDescriptor } from "./surface-contract";
import { visibleWorkspaceSurfaces } from "./surface-visibility";

const descriptor = (
  surfaceId: string,
  sourceId: string,
  lifecycle: SurfaceDescriptor["lifecycle"],
): SurfaceDescriptor => ({
  schemaVersion: 1,
  surfaceId,
  workspaceId: "workspace-1",
  source: {
    kind: "live_app",
    sourceId,
    sourceVersion: "a".repeat(64),
    manifestId: sourceId,
  },
  title: "Rivet",
  lifecycle,
  presentations: [],
  capabilities: [],
  revision: 1,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
});

describe("workspace surface visibility", () => {
  it("hides failed retained Rivet editor surfaces from the deck", () => {
    const visible = visibleWorkspaceSurfaces([
      descriptor("failed-rivet", "wright.rivet-editor", "failed"),
      descriptor("ready-rivet", "wright.rivet-editor", "ready"),
      descriptor("failed-other", "other.app", "failed"),
    ]);

    expect(visible.map((item) => item.surfaceId)).toEqual([
      "ready-rivet",
      "failed-other",
    ]);
  });
});
