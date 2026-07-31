import { describe, expect, it } from "vitest";

import {
  CHAT_MINIMUM_PX,
  NARROW_BREAKPOINT_PX,
  SEPARATOR_SIZE_PX,
  SURFACE_MINIMUM_PX,
  createWorkspaceLayout,
  resolveWorkspaceLayout,
  restoreWorkspaceLayout,
  workspaceLayoutReducer,
} from "./workspace-layout";

describe("workspace layout", () => {
  it("uses the exact wide normal defaults and container-relative minimums", () => {
    const state = createWorkspaceLayout(1200);
    const resolved = resolveWorkspaceLayout(state, 1200);

    expect(CHAT_MINIMUM_PX).toBe(320);
    expect(SURFACE_MINIMUM_PX).toBe(480);
    expect(SEPARATOR_SIZE_PX).toBe(8);
    expect(NARROW_BREAKPOINT_PX).toBe(808);
    expect(state).toMatchObject({
      version: 2,
      mode: "normal",
      wideMode: "normal",
    });
    expect(state.normalChatBasisPoints).toBe(3800);
    expect(resolved.chatPixels).toBeGreaterThanOrEqual(320);
    expect(resolved.surfacePixels).toBeGreaterThanOrEqual(480);
  });

  it("enters focus with a 360px bounded chat and restores normal ratio", () => {
    const normal = workspaceLayoutReducer(createWorkspaceLayout(1600), {
      type: "set_chat_basis_points",
      value: 4200,
      containerWidth: 1600,
    });
    const focus = workspaceLayoutReducer(normal, {
      type: "enter_focus",
      containerWidth: 1600,
    });

    expect(focus.mode).toBe("focus");
    expect(resolveWorkspaceLayout(focus, 1600).chatPixels).toBeCloseTo(360, 0);
    expect(resolveWorkspaceLayout(focus, 1600).chatPixels).toBeLessThanOrEqual(
      720,
    );

    const restored = workspaceLayoutReducer(focus, {
      type: "exit_focus",
      containerWidth: 1600,
    });
    expect(restored.mode).toBe("normal");
    expect(restored.normalChatBasisPoints).toBe(4200);

    const customized = workspaceLayoutReducer(focus, {
      type: "set_chat_basis_points",
      value: 3000,
      containerWidth: 1600,
    });
    const left = workspaceLayoutReducer(customized, {
      type: "exit_focus",
      containerWidth: 1600,
    });
    const reentered = workspaceLayoutReducer(left, {
      type: "enter_focus",
      containerWidth: 1600,
    });
    expect(reentered.focusChatBasisPoints).toBe(3000);
  });

  it("uses narrow mode below the exact minimum without losing the wide mode or ratio", () => {
    const focus = workspaceLayoutReducer(createWorkspaceLayout(1200), {
      type: "enter_focus",
      containerWidth: 1200,
    });
    const previousRatio = focus.focusChatBasisPoints;
    const narrow = workspaceLayoutReducer(focus, {
      type: "resize_container",
      containerWidth: 807,
    });
    const surface = workspaceLayoutReducer(narrow, {
      type: "select_narrow_pane",
      pane: "surface",
    });

    expect(surface).toMatchObject({
      mode: "narrow",
      wideMode: "focus",
      narrowPane: "surface",
      focusChatBasisPoints: previousRatio,
    });

    const wideAgain = workspaceLayoutReducer(surface, {
      type: "resize_container",
      containerWidth: 1200,
    });
    expect(wideAgain.mode).toBe("focus");
    expect(wideAgain.focusChatBasisPoints).toBe(previousRatio);
  });

  it("treats 200% zoom in CSS pixels and does not clip either destination", () => {
    const zoomed = workspaceLayoutReducer(createWorkspaceLayout(1400), {
      type: "resize_container",
      containerWidth: 700,
    });
    expect(zoomed.mode).toBe("narrow");
    expect(resolveWorkspaceLayout(zoomed, 700)).toMatchObject({
      chatPixels: 700,
      surfacePixels: 700,
    });
  });

  it("migrates legacy pixel state and safely defaults malformed state", () => {
    const migrated = restoreWorkspaceLayout(
      JSON.stringify({ version: 1, focus: true, chatWidth: 420 }),
      1200,
    );
    expect(migrated.version).toBe(2);
    expect(migrated.mode).toBe("focus");
    expect(resolveWorkspaceLayout(migrated, 1200).chatPixels).toBeCloseTo(
      420,
      0,
    );

    expect(restoreWorkspaceLayout("{broken", 1200)).toEqual(
      createWorkspaceLayout(1200),
    );
    expect(
      restoreWorkspaceLayout(
        JSON.stringify({
          version: 2,
          mode: "space",
          normalChatBasisPoints: -1,
        }),
        1200,
      ),
    ).toEqual(createWorkspaceLayout(1200));
  });
});
