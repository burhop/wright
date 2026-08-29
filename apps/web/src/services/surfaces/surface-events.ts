import { hostAdapter } from "../host-adapter";
import {
  parseSurfaceDescriptor,
  type SurfaceDescriptor,
} from "./surface-contract";
import { listSurfaces } from "./surface-client";

const MAXIMUM_EVENT_BUFFER = 1024 * 1024;
const RETRY_MILLISECONDS = 1000;

export interface SurfaceDescriptorEvent {
  readonly eventId: string | null;
  readonly eventType: string;
  readonly descriptor: SurfaceDescriptor;
}

export type SurfaceEventListener = (event: SurfaceDescriptorEvent) => void;

function parseEventBlock(
  block: string,
  fallbackEventId: string | null,
): SurfaceDescriptorEvent | null {
  let eventId = fallbackEventId;
  let eventType = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line === "" || line.startsWith(":")) continue;
    const separator = line.indexOf(":");
    const field = separator < 0 ? line : line.slice(0, separator);
    const raw = separator < 0 ? "" : line.slice(separator + 1);
    const value = raw.startsWith(" ") ? raw.slice(1) : raw;
    if (field === "id" && !value.includes("\0")) eventId = value;
    else if (field === "event") eventType = value || "message";
    else if (field === "data") data.push(value);
  }
  if (data.length === 0) return null;
  try {
    return {
      eventId,
      eventType,
      descriptor: parseSurfaceDescriptor(JSON.parse(data.join("\n"))),
    };
  } catch {
    return null;
  }
}

export async function consumeSurfaceEventStream(
  response: Response,
  listener: SurfaceEventListener,
  lastEventId: string | null = null,
): Promise<string | null> {
  if (!response.ok || !response.body) {
    throw new Error(
      `Workspace Surface event stream failed with HTTP ${response.status}`,
    );
  }
  const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
  if (!contentType.startsWith("text/event-stream")) {
    throw new Error(
      "Workspace Surface event stream returned an invalid content type",
    );
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let cursor = lastEventId;
  const emit = (block: string) => {
    const event = parseEventBlock(block, cursor);
    if (!event) return;
    cursor = event.eventId;
    listener(event);
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll("\r\n", "\n");
    if (buffer.length > MAXIMUM_EVENT_BUFFER) {
      await reader.cancel("Workspace Surface event exceeded the buffer limit");
      throw new Error("Workspace Surface event exceeded the buffer limit");
    }
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      emit(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      boundary = buffer.indexOf("\n\n");
    }
    if (done) break;
  }
  if (buffer.trim()) emit(buffer);
  return cursor;
}

function retryDelay(): Promise<void> {
  return new Promise((resolve) =>
    window.setTimeout(resolve, RETRY_MILLISECONDS),
  );
}

function subscribeBrowserStream(
  workspaceId: string,
  sessionId: string,
  listener: SurfaceEventListener,
): () => void {
  const controller = new AbortController();
  let stopped = false;
  let lastEventId: string | null = null;
  const run = async () => {
    while (!stopped) {
      try {
        const response = await hostAdapter.fetch(
          `${hostAdapter.getApiBaseUrl()}/api/workspace/surfaces/events`,
          {
            headers: {
              "X-Wright-Workspace-ID": workspaceId,
              "X-Wright-Session-ID": sessionId,
              ...(lastEventId ? { "Last-Event-ID": lastEventId } : {}),
            },
            signal: controller.signal,
          },
        );
        lastEventId = await consumeSurfaceEventStream(
          response,
          listener,
          lastEventId,
        );
      } catch (error) {
        if (controller.signal.aborted) return;
        console.debug("Workspace Surface event stream reconnecting", error);
      }
      if (!stopped) await retryDelay();
    }
  };
  void run();
  return () => {
    stopped = true;
    controller.abort();
  };
}

function subscribeDesktopPolling(
  workspaceId: string,
  sessionId: string,
  listener: SurfaceEventListener,
): () => void {
  let stopped = false;
  let timer: number | undefined;
  let previous = new Map<string, SurfaceDescriptor>();
  const poll = async () => {
    try {
      const descriptors = await listSurfaces(workspaceId, sessionId);
      if (stopped) return;
      const current = new Map(
        descriptors.map((item) => [item.surfaceId, item]),
      );
      for (const descriptor of descriptors) {
        const known = previous.get(descriptor.surfaceId);
        if (!known || descriptor.revision > known.revision) {
          listener({
            eventId: null,
            eventType: "surface.snapshot",
            descriptor,
          });
        }
      }
      for (const descriptor of previous.values()) {
        if (!current.has(descriptor.surfaceId)) {
          listener({ eventId: null, eventType: "surface.deleted", descriptor });
        }
      }
      previous = current;
    } catch (error) {
      console.debug("Workspace Surface polling retrying", error);
    } finally {
      if (!stopped) timer = window.setTimeout(poll, RETRY_MILLISECONDS);
    }
  };
  void poll();
  return () => {
    stopped = true;
    if (timer !== undefined) window.clearTimeout(timer);
  };
}

export function subscribeSurfaceUpdates(
  workspaceId: string,
  sessionId: string,
  listener: SurfaceEventListener,
): () => void {
  return hostAdapter.mode === "desktop"
    ? subscribeDesktopPolling(workspaceId, sessionId, listener)
    : subscribeBrowserStream(workspaceId, sessionId, listener);
}
