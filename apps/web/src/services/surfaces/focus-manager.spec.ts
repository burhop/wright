import { describe, expect, it, vi } from "vitest";

import {
  SurfaceFocusManager,
  installElectronReturnAccelerator,
  nextHostFocusRegion,
} from "./focus-manager";

describe("surface focus manager", () => {
  it("cycles host regions in both directions with wrapping", () => {
    expect(nextHostFocusRegion("chat")).toBe("tabs");
    expect(nextHostFocusRegion("frame-return")).toBe("chat");
    expect(nextHostFocusRegion("chat", true)).toBe("frame-return");
  });

  it("restores the initiating control and uses a fallback if it was removed", () => {
    const manager = new SurfaceFocusManager();
    const initiator = document.createElement("button");
    const fallback = document.createElement("button");
    document.body.append(initiator, fallback);
    manager.rememberInitiator(initiator);
    manager.restoreInitiator(fallback);
    expect(initiator).toHaveFocus();

    manager.rememberInitiator(initiator);
    initiator.remove();
    manager.restoreInitiator(fallback);
    expect(fallback).toHaveFocus();
    fallback.remove();
  });

  it("subscribes to and removes the desktop return bridge", () => {
    const callback = vi.fn();
    const unsubscribe = vi.fn();
    const original = window.wrightDesktop;
    window.wrightDesktop = {
      onReturnToHost: (handler: () => void) => {
        handler();
        return unsubscribe;
      },
    } as unknown as NonNullable<typeof window.wrightDesktop>;

    const remove = installElectronReturnAccelerator(callback);
    expect(callback).toHaveBeenCalledTimes(1);
    window.dispatchEvent(new Event("wright:return-to-host"));
    expect(callback).toHaveBeenCalledTimes(2);
    remove();
    expect(unsubscribe).toHaveBeenCalledOnce();
    window.wrightDesktop = original;
  });
});
