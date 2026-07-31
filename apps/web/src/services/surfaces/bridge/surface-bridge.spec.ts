import { describe, expect, it, vi } from "vitest";

import { SurfaceBridge, type SurfaceBridgeEnvelope } from "./surface-bridge";

class FakeHostWindow {
  listener: ((event: MessageEvent) => void) | undefined;

  addEventListener(_kind: "message", listener: (event: MessageEvent) => void) {
    this.listener = listener;
  }

  removeEventListener(
    _kind: "message",
    listener: (event: MessageEvent) => void,
  ) {
    if (this.listener === listener) this.listener = undefined;
  }

  dispatch(event: MessageEvent) {
    this.listener?.(event);
  }
}

const binding = {
  workspaceId: "workspace-1",
  sessionId: "session-1",
  surfaceId: "surface-1",
  instanceId: "instance-1",
  presentationId: "presentation-1",
  generation: 3,
  documentOrigin: "https://s-presentation-1.preview.test",
};

function envelope(
  overrides: Partial<SurfaceBridgeEnvelope> = {},
): SurfaceBridgeEnvelope {
  return {
    protocolVersion: "1.0",
    kind: "event",
    messageId: "00000000-0000-4000-8000-000000000001",
    correlationId: "00000000-0000-4000-8000-000000000002",
    binding,
    operation: "surface.updated",
    sequence: 1,
    createdAt: "2026-07-30T12:00:00.000Z",
    deadlineAt: "2026-07-30T12:00:10.000Z",
    payload: { revision: 2 },
    ...overrides,
  };
}

function fixture(maximumMessageBytes = 4096) {
  const host = new FakeHostWindow();
  const target = { postMessage: vi.fn() };
  const received = vi.fn();
  const rejected = vi.fn();
  const bridge = new SurfaceBridge({
    hostWindow: host,
    targetWindow: target,
    targetOrigin: binding.documentOrigin,
    binding,
    maximumMessageBytes,
    idFactory: () => "00000000-0000-4000-8000-000000000010",
    now: () => new Date("2026-07-30T12:00:00.000Z"),
    onMessage: received,
    onSecurityEvent: rejected,
  });
  bridge.start();
  return { host, target, received, rejected, bridge };
}

describe("SurfaceBridge", () => {
  it("accepts only the exact event origin and iframe window source", () => {
    const { host, target, received, rejected } = fixture();
    host.dispatch(
      new MessageEvent("message", {
        origin: "https://sibling.preview.test",
        source: target as unknown as Window,
        data: envelope(),
      }),
    );
    host.dispatch(
      new MessageEvent("message", {
        origin: binding.documentOrigin,
        source: {} as Window,
        data: envelope(),
      }),
    );
    expect(received).not.toHaveBeenCalled();
    expect(rejected.mock.calls.map(([code]) => code)).toEqual([
      "SURFACE_BRIDGE_ORIGIN_MISMATCH",
      "SURFACE_BRIDGE_SOURCE_MISMATCH",
    ]);

    host.dispatch(
      new MessageEvent("message", {
        origin: binding.documentOrigin,
        source: target as unknown as Window,
        data: envelope(),
      }),
    );
    expect(received).toHaveBeenCalledOnce();
  });

  it("never permits wildcard outbound authority", () => {
    const { target, bridge } = fixture();
    bridge.send("request", "tool.call", { value: 4 });
    expect(target.postMessage).toHaveBeenCalledOnce();
    expect(target.postMessage.mock.calls[0][1]).toBe(binding.documentOrigin);
    expect(target.postMessage.mock.calls[0][1]).not.toBe("*");
    expect(
      () =>
        new SurfaceBridge({
          hostWindow: new FakeHostWindow(),
          targetWindow: target,
          targetOrigin: "*",
          binding,
          onMessage: vi.fn(),
        }),
    ).toThrow(/exact target origin/i);
  });

  it("rejects stale generation, malformed and oversized messages", () => {
    const { host, target, received, rejected } = fixture(800);
    for (const data of [
      envelope({ binding: { ...binding, generation: 2 } }),
      { protocolVersion: "1.0", unexpected: true },
      envelope({ payload: { text: "x".repeat(2000) } }),
    ]) {
      host.dispatch(
        new MessageEvent("message", {
          origin: binding.documentOrigin,
          source: target as unknown as Window,
          data,
        }),
      );
    }
    expect(received).not.toHaveBeenCalled();
    expect(rejected.mock.calls.map(([code]) => code)).toEqual([
      "SURFACE_BRIDGE_STALE_GENERATION",
      "SURFACE_BRIDGE_INVALID_MESSAGE",
      "SURFACE_BRIDGE_MESSAGE_TOO_LARGE",
    ]);
  });

  it("removes authority before teardown races can deliver messages", () => {
    const { host, target, received, bridge } = fixture();
    const queued = host.listener;
    bridge.dispose();
    queued?.(
      new MessageEvent("message", {
        origin: binding.documentOrigin,
        source: target as unknown as Window,
        data: envelope(),
      }),
    );
    expect(received).not.toHaveBeenCalled();
    expect(host.listener).toBeUndefined();
    expect(() => bridge.send("request", "tool.call", {})).toThrow(/disposed/i);
    bridge.dispose();
  });
});
