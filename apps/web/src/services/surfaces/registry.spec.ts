import { describe, expect, it, vi } from "vitest";

import { parseSurfaceDescriptor } from "./surface-contract";
import { SurfacePresenterRegistry } from "./registry";

const descriptor = parseSurfaceDescriptor({
  schemaVersion: 1,
  surfaceId: "surface-1",
  workspaceId: "workspace-1",
  source: {
    kind: "display",
    sourceId: "execution-1:loads",
    sourceVersion: "1",
    displayId: "loads",
    revision: 1,
  },
  title: "Loads",
  lifecycle: "ready",
  presentations: [],
  capabilities: [],
  revision: 1,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: "2026-07-30T12:00:00Z",
});

const contribution = (id: string, priority: number) => ({
  id,
  priority,
  sourceKinds: ["display" as const],
  create: vi.fn(),
});

describe("SurfacePresenterRegistry", () => {
  it("resolves deterministically by priority and ID", () => {
    const registry = new SurfacePresenterRegistry();
    registry.register(contribution("z-low", 1));
    registry.register(contribution("b-high", 10));
    registry.register(contribution("a-high", 10));

    expect(registry.resolve(descriptor)?.id).toBe("a-high");
  });

  it("rejects duplicate IDs and deregisters idempotently", () => {
    const registry = new SurfacePresenterRegistry();
    const registration = registry.register(contribution("display", 1));
    expect(() => registry.register(contribution("display", 2))).toThrow(
      /already registered/,
    );
    registration.dispose();
    registration.dispose();
    expect(registry.resolve(descriptor)).toBeNull();
  });

  it("applies contribution capability predicates", () => {
    const registry = new SurfacePresenterRegistry();
    registry.register({
      ...contribution("unavailable", 10),
      canPresent: () => false,
    });
    registry.register(contribution("fallback", 1));
    expect(registry.resolve(descriptor)?.id).toBe("fallback");
  });
});
