import { clientError } from "./errors";

export interface RecordedFrame {
  readonly event: string;
  readonly id?: string;
  readonly data: string;
}

/** Fetch-based SSE supports the host's authenticated browser/desktop transport. */
export async function* recordedFrames(
  response: Response,
  signal?: AbortSignal,
): AsyncGenerator<RecordedFrame> {
  if (
    !response.body ||
    !response.headers
      .get("content-type")
      ?.toLowerCase()
      .startsWith("text/event-stream")
  ) {
    throw clientError(
      "UI_INCOMPATIBLE",
      "Wright did not return a supported progress stream.",
      "Refresh the view and check client/server compatibility.",
    );
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  const encoder = new TextEncoder();
  let buffer = "",
    event = "",
    id: string | undefined;
  let data: string[] = [],
    bytes = 0;
  const abort = () => {
    void reader.cancel().catch(() => undefined);
  };
  signal?.addEventListener("abort", abort, { once: true });
  try {
    while (!signal?.aborted) {
      const next = await reader.read();
      if (next.done) break; // Do not accept an incomplete frame after disconnection.
      try {
        buffer += decoder.decode(next.value, { stream: true });
      } catch {
        throw clientError(
          "UI_INCOMPATIBLE",
          "The progress message is not valid UTF-8.",
          "Reopen the current run snapshot.",
        );
      }
      while (true) {
        const newline = buffer.search(/[\r\n]/);
        if (
          newline < 0 ||
          (buffer[newline] === "\r" && newline === buffer.length - 1)
        )
          break;
        const line = buffer.slice(0, newline);
        const separator =
          buffer[newline] === "\r" && buffer[newline + 1] === "\n" ? 2 : 1;
        buffer = buffer.slice(newline + separator);
        bytes += encoder.encode(line).byteLength + separator;
        if (bytes > 66_560)
          throw clientError(
            "UI_INCOMPATIBLE",
            "The progress message exceeds its supported size.",
            "Reopen the run to read its current snapshot.",
          );
        if (line === "") {
          if (encoder.encode(data.join("\n")).byteLength > 65_536)
            throw clientError(
              "UI_INCOMPATIBLE",
              "The progress data exceeds its supported size.",
              "Reopen the current run snapshot.",
            );
          if (data.length)
            yield { event: event || "message", id, data: data.join("\n") };
          event = "";
          id = undefined;
          data = [];
          bytes = 0;
          continue;
        }
        if (line.startsWith(":")) continue;
        const colon = line.indexOf(":");
        const field = colon < 0 ? line : line.slice(0, colon);
        let value = colon < 0 ? "" : line.slice(colon + 1);
        if (value.startsWith(" ")) value = value.slice(1);
        if (field === "data") data.push(value);
        if (field === "event") event = value;
        if (field === "id" && !value.includes("\0")) id = value;
      }
      if (bytes + encoder.encode(buffer).byteLength > 66_560)
        throw clientError(
          "UI_INCOMPATIBLE",
          "The progress message exceeds its supported size.",
          "Reopen the run to read its current snapshot.",
        );
    }
  } finally {
    signal?.removeEventListener("abort", abort);
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
