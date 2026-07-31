import { describe, expect, it, vi } from "vitest";

import { consumeSurfaceEventStream } from "./surface-events";

const descriptor = (revision: number) => ({
  schemaVersion: 1,
  surfaceId: "surface-loads",
  workspaceId: "workspace-1",
  source: {
    kind: "display",
    sourceId: `execution-1:loads`,
    sourceVersion: String(revision),
    displayId: "loads",
    revision,
  },
  title: "Loads",
  lifecycle: "ready",
  presentations: [],
  capabilities: [],
  revision,
  createdAt: "2026-07-30T12:00:00Z",
  updatedAt: `2026-07-30T12:0${revision}:00Z`,
});

describe("Workspace Surface event stream", () => {
  it("parses split SSE records, ignores malformed data, and advances the cursor", async () => {
    const encoder = new TextEncoder();
    const payload = [
      ": keepalive\n\n",
      "id: malformed\nevent: surface.display.updated\ndata: not-json\n\n",
      `id: event-1\nevent: surface.display.created\ndata: ${JSON.stringify(descriptor(1))}\n\n`,
      `id: event-2\nevent: surface.display.deleted\ndata: ${JSON.stringify(descriptor(2))}\n\n`,
    ].join("");
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(encoder.encode(payload.slice(0, 37)));
        controller.enqueue(encoder.encode(payload.slice(37)));
        controller.close();
      },
    });
    const listener = vi.fn();

    const cursor = await consumeSurfaceEventStream(
      new Response(stream, {
        headers: { "Content-Type": "text/event-stream; charset=utf-8" },
      }),
      listener,
    );

    expect(cursor).toBe("event-2");
    expect(listener).toHaveBeenCalledTimes(2);
    expect(listener.mock.calls.map(([event]) => event.eventType)).toEqual([
      "surface.display.created",
      "surface.display.deleted",
    ]);
    expect(listener.mock.calls[1][0].descriptor.revision).toBe(2);
  });

  it("rejects a non-event-stream response", async () => {
    await expect(
      consumeSurfaceEventStream(
        new Response("{}", { headers: { "Content-Type": "application/json" } }),
        vi.fn(),
      ),
    ).rejects.toThrow(/content type/i);
  });
});
