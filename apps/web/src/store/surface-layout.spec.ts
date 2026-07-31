import { describe, expect, it } from "vitest";

import { createWorkspaceLayout } from "../components/workspace/workspace-layout";
import {
  loadSurfaceLayout,
  saveSurfaceLayout,
  surfaceLayoutStorageKey,
} from "./surface-layout";

class MemoryStorage implements Pick<Storage, "getItem" | "setItem"> {
  readonly values = new Map<string, string>();

  getItem(key: string): string | null {
    return this.values.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value);
  }
}

describe("surface layout persistence", () => {
  it("keys versioned preferences by exact user and workspace", () => {
    expect(surfaceLayoutStorageKey("user/a", "workspace b")).toBe(
      "wright.workspaceSurfaces.layout.v2.user%2Fa.workspace%20b",
    );
  });

  it("round-trips basis-point state and safely handles unavailable storage", () => {
    const storage = new MemoryStorage();
    const state = {
      ...createWorkspaceLayout(1200),
      normalChatBasisPoints: 4100,
    };
    saveSurfaceLayout(storage, "layout", state);
    expect(loadSurfaceLayout(storage, "layout", 1200)).toEqual(state);

    const denied = {
      getItem: () => {
        throw new DOMException("denied");
      },
    };
    expect(loadSurfaceLayout(denied, "layout", 1200)).toEqual(
      createWorkspaceLayout(1200),
    );
  });
});
