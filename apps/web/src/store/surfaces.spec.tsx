import { describe, expect, it, vi } from "vitest";

import { parseSurfaceDescriptor } from "../services/surfaces/surface-contract";
import {
  SURFACE_STATE_VERSION,
  SurfacePresenterDeck,
  createSurfaceState,
  reduceSurfaceState,
  restoreSurfaceState,
  serializeSurfaceState,
} from "./surfaces";

const descriptor = (revision: number, title = `Revision ${revision}`) =>
  parseSurfaceDescriptor({
    schemaVersion: 1,
    surfaceId: "surface-1",
    workspaceId: "workspace-1",
    source: {
      kind: "display",
      sourceId: "execution-1:loads",
      sourceVersion: String(revision),
      displayId: "loads",
      revision,
    },
    title,
    lifecycle: "ready",
    presentations: [],
    capabilities: [],
    revision,
    createdAt: "2026-07-30T12:00:00Z",
    updatedAt: `2026-07-30T12:0${revision}:00Z`,
  });

describe("Workspace Surface state", () => {
  it("updates one stable tab for newer revisions and rejects stale events", () => {
    let state = createSurfaceState();
    state = reduceSurfaceState(state, {
      type: "upsert",
      descriptor: descriptor(1),
    });
    state = reduceSurfaceState(state, {
      type: "upsert",
      descriptor: descriptor(2),
    });
    state = reduceSurfaceState(state, {
      type: "upsert",
      descriptor: descriptor(1, "stale"),
    });

    expect(state.tabs).toEqual(["surface-1"]);
    expect(state.activeSurfaceId).toBe("surface-1");
    expect(state.byId["surface-1"].revision).toBe(2);
    expect(state.byId["surface-1"].title).toBe("Revision 2");
  });

  it("serializes version 2 without transient presenter state", () => {
    const state = reduceSurfaceState(createSurfaceState(), {
      type: "upsert",
      descriptor: descriptor(1),
    });
    const serialized = JSON.parse(serializeSurfaceState(state));
    expect(serialized.version).toBe(SURFACE_STATE_VERSION);
    expect(serialized.version).toBe(2);
    expect(serialized).not.toHaveProperty("presenters");
  });

  it("migrates the version-1 layout to the version-2 focus model", () => {
    const restored = restoreSurfaceState(
      JSON.stringify({
        version: 1,
        surfaces: [descriptor(1)],
        activeSurfaceId: "surface-1",
        layout: { focus: true, chatWidth: 420 },
      }),
    );
    expect(restored.version).toBe(2);
    expect(restored.layout).toEqual({
      mode: "focus",
      chatSize: { unit: "pixels", value: 420 },
    });
    expect(restored.tabs).toEqual(["surface-1"]);
  });

  it("rejects malformed persisted state instead of partially restoring it", () => {
    expect(() =>
      restoreSurfaceState(
        JSON.stringify({
          version: 2,
          descriptors: [{ ...descriptor(1), revision: 0 }],
          tabs: ["surface-1"],
          activeSurfaceId: "surface-1",
          layout: { mode: "normal", chatSize: { unit: "ratio", value: 0.4 } },
        }),
      ),
    ).toThrow(/revision/);
    expect(() => restoreSurfaceState('{"version":99}')).toThrow(/version/);
  });

  it("disposes replaced, removed, and remaining presenters exactly once", () => {
    const first = { mount: vi.fn(), update: vi.fn(), dispose: vi.fn() };
    const second = { mount: vi.fn(), update: vi.fn(), dispose: vi.fn() };
    const deck = new SurfacePresenterDeck();

    deck.set("surface-1", first);
    deck.set("surface-1", second);
    deck.remove("surface-1");
    deck.remove("surface-1");
    deck.set("surface-2", first);
    deck.dispose();
    deck.dispose();

    expect(first.dispose).toHaveBeenCalledTimes(1);
    expect(second.dispose).toHaveBeenCalledTimes(1);
  });
});
