import {
  createNativeProcessClient,
  ProcessClientError,
  type ProcessClient,
  type ProcessFetch,
  type ProcessRef,
  type Reason,
  type FollowOptions,
} from "@wright/process-client";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import {
  desktopReasoningWait,
  type WorkflowReasoningStatusReader,
} from "../../services/desktop-reasoning-status";

export type NativeProcessTool =
  "wright_process_ui_read" | "wright_process_ui_update";
export type NativeProcessCall = (
  tool: NativeProcessTool,
  request: Record<string, unknown>,
  signal?: AbortSignal,
) => Promise<CallToolResult>;
const base = "https://wright-process.invalid";
const unavailable: Reason = {
  code: "CAPABILITY_UNAVAILABLE",
  message: "This native view does not expose that process operation.",
  correction:
    "Use an enabled Wright process capability. No operation was sent.",
};
const response = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "content-type": "application/json" },
  });
const denied = (reason: Reason, status = 403) =>
  response({ detail: { reason } }, status);
function envelope(result: CallToolResult): {
  ok?: boolean;
  document?: unknown;
  http_status?: number;
  reason?: Reason;
} {
  if (result.isError)
    throw new Error("Wright did not acknowledge the process request.");
  if (result.structuredContent) return result.structuredContent;
  const content = result.content.find((item) => item.type === "text");
  if (!content || content.type !== "text")
    throw new Error("Wright returned no process record.");
  return JSON.parse(content.text);
}

export function encodeFile(file: File, signal?: AbortSignal): Promise<string> {
  signal?.throwIfAborted();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    const abort = () => reader.abort();
    const cleanup = () => signal?.removeEventListener("abort", abort);
    reader.onload = () => {
      cleanup();
      const value = reader.result;
      if (typeof value !== "string" || !value.includes(";base64,"))
        reject(new Error("The selected file could not be encoded."));
      else resolve(value.slice(value.indexOf(",") + 1));
    };
    reader.onerror = () => {
      cleanup();
      reject(new Error("The selected file could not be read."));
    };
    reader.onabort = () => {
      cleanup();
      reject(new DOMException("Input read cancelled", "AbortError"));
    };
    signal?.addEventListener("abort", abort, { once: true });
    reader.readAsDataURL(file);
  });
}

/** Existing public client validation/recovery, with a closed MCP transport.
 * The synthetic address is never fetched. Only the named operations below can
 * cross the host bridge; no arbitrary URL, method, model or tool is forwarded.
 */
export function createNativePanelProcessClient(options: {
  readonly process: ProcessRef;
  readonly sessionId: string;
  readonly call: NativeProcessCall;
  readonly workspaceName: string;
  readonly navigate?: Parameters<
    typeof createNativeProcessClient
  >[0]["navigate"];
}): {
  client: ProcessClient;
  readReasoningStatus: WorkflowReasoningStatusReader;
} {
  const process = Object.freeze({ ...options.process });
  const sessionId = options.sessionId,
    workspaceName = options.workspaceName,
    call = options.call;
  const scope = Object.freeze({
    workspace_id: process.workspace_id,
    session_id: sessionId,
    path: process.source_path,
    expected_storage_digest: process.source_digest,
  });
  const invoke = async (
    tool: NativeProcessTool,
    request: Record<string, unknown>,
    signal?: AbortSignal,
  ) => {
    signal?.throwIfAborted();
    const result = envelope(await call(tool, request, signal));
    signal?.throwIfAborted();
    if (result.ok === true && result.document !== undefined) {
      if (request.operation !== "representation")
        return response(result.document);
      const file = result.document as {
        bytes_base64?: string;
        sha256?: string;
        media_type?: string;
        size_bytes?: number;
      };
      const reference = request.reference as { sha256?: string };
      if (
        typeof file.bytes_base64 !== "string" ||
        file.bytes_base64.length > 1_398_104 ||
        file.sha256 !== reference.sha256 ||
        !Number.isInteger(file.size_bytes) ||
        !file.media_type ||
        ![
          "text/plain",
          "text/markdown",
          "text/csv",
          "application/json",
          "image/png",
          "image/jpeg",
        ].includes(file.media_type)
      )
        throw new Error(
          "Wright did not confirm a bounded text or image representation.",
        );
      const bytes = Uint8Array.from(atob(file.bytes_base64), (character) =>
        character.charCodeAt(0),
      );
      if (bytes.byteLength !== file.size_bytes || bytes.byteLength > 1_048_576)
        throw new Error("Wright representation size differs.");
      return new Response(bytes, {
        headers: {
          "content-type": file.media_type,
          "content-length": String(bytes.byteLength),
          "x-wright-artifact-sha256": file.sha256!,
          "x-content-type-options": "nosniff",
        },
      });
    }
    if (
      result.ok === false &&
      result.reason &&
      Number.isInteger(result.http_status) &&
      result.http_status! >= 400 &&
      result.http_status! <= 599
    )
      return denied(result.reason, result.http_status);
    throw new Error("Wright did not confirm the process operation.");
  };
  const fetch: ProcessFetch = async (input, init = {}) => {
    const url = new URL(String(input));
    const method = init.method ?? "GET";
    if (url.origin !== base || url.hash) return denied(unavailable);
    if (method === "POST" && url.pathname === "/inputs/upload" && !url.search) {
      const form = init.body;
      if (
        !(form instanceof FormData) ||
        [...form.keys()].sort().join(",") !==
          "expected_storage_digest,file,input_id,path,session_id" ||
        Object.entries(scope).some(
          ([key, value]) => key !== "workspace_id" && form.get(key) !== value,
        )
      )
        return denied({
          code: "SCOPE_DENIED",
          message: "The upload changed its bound process scope.",
          correction: "Reopen the exact saved process. No upload was sent.",
        });
      const file = form.get("file");
      const inputId = form.get("input_id");
      if (
        !(file instanceof File) ||
        typeof inputId !== "string" ||
        file.size < 1 ||
        file.size > 33_554_432
      )
        return denied(
          {
            code: "RESPONSE_INVALID",
            message: "Choose an input file of at most 32 MiB.",
            correction: "Use a file supported by the declared input.",
          },
          422,
        );
      const signal = init.signal ?? undefined;
      const encoded = await encodeFile(file, signal);
      return invoke(
        "wright_process_ui_update",
        {
          ...scope,
          operation: "upload",
          input_id: inputId,
          filename: file.name,
          bytes_base64: encoded,
        },
        signal,
      );
    }
    const data =
      method === "GET"
        ? Object.fromEntries(url.searchParams)
        : typeof init.body === "string"
          ? (JSON.parse(init.body) as Record<string, unknown>)
          : undefined;
    if (
      !data ||
      Object.entries(scope).some(
        ([key, value]) => key !== "workspace_id" && data[key] !== value,
      )
    )
      return denied({
        code: "SCOPE_DENIED",
        message: "The process request changed its bound scope.",
        correction: "Reopen the exact saved process. No operation was sent.",
      });
    const request: Record<string, unknown> = {
      ...data,
      workspace_id: scope.workspace_id,
    };
    let tool: NativeProcessTool = "wright_process_ui_update";
    if (method === "GET") {
      tool = "wright_process_ui_read";
      if (url.pathname === "/interaction") request.operation = "snapshot";
      else {
        const run = /^\/runs\/([^/]+)$/.exec(url.pathname);
        if (!run) return denied(unavailable, 501);
        request.operation = "snapshot";
        request.run_id = decodeURIComponent(run[1]);
      }
    } else if (method === "POST" && !url.search) {
      const simple: Record<string, string> = {
        "/inputs": "inputs",
        "/readiness": "readiness",
        "/runs": "start",
      };
      if (url.pathname === "/navigation") {
        request.operation = "navigation";
        tool = "wright_process_ui_read";
      } else if (url.pathname === "/representations/read") {
        request.operation = "representation";
        tool = "wright_process_ui_read";
      } else if (simple[url.pathname]) request.operation = simple[url.pathname];
      else {
        const answer = /^\/interactions\/([^/]+)\/response$/.exec(url.pathname);
        const decision = /^\/interactions\/([^/]+)\/decision$/.exec(
          url.pathname,
        );
        const cancel = /^\/runs\/([^/]+)\/cancel$/.exec(url.pathname);
        const continuation = /^\/actions\/(continue-[^/]+)$/.exec(url.pathname);
        if (answer) {
          request.operation = "respond";
          request.checkpoint_id = decodeURIComponent(answer[1]);
        } else if (decision) {
          request.operation = "decide";
          request.checkpoint_id = decodeURIComponent(decision[1]);
        } else if (cancel) {
          request.operation = "cancel";
          request.run_id = decodeURIComponent(cancel[1]);
        } else if (continuation) {
          request.operation = "continue";
          request.action_id = decodeURIComponent(continuation[1]);
        } else return denied(unavailable, 501);
      }
    } else return denied(unavailable, 501);
    return invoke(tool, request, init.signal ?? undefined);
  };
  const validated = createNativeProcessClient({
    process,
    sessionId,
    baseUrl: base,
    fetch,
    navigate: options.navigate,
  });
  // MCP tool results are snapshots, not an SSE/LLM stream. Poll only the durable
  // reader while this observer is open. Closing it never cancels or restarts a run.
  const client: ProcessClient = Object.freeze({
    ...validated,
    async *follow(read: FollowOptions) {
      if (read.cursor !== undefined)
        throw new ProcessClientError({
          code: "CAPABILITY_UNAVAILABLE",
          message:
            "Recorded event cursors are unavailable in this native snapshot view.",
          correction:
            "Reattach to the same durable run snapshot. No work was restarted.",
        });
      let failures = 0;
      const maximum = read.maxReconnects ?? 3;
      if (!Number.isInteger(maximum) || maximum < 0 || maximum > 5)
        throw new ProcessClientError({
          code: "RESPONSE_INVALID",
          message: "The read reconnect bound is unsupported.",
          correction: "Use at most five read reconnections.",
        });
      while (!read.signal?.aborted) {
        try {
          const snapshot = await validated.getSnapshot({
            runId: read.runId,
            signal: read.signal,
          });
          if (read.signal?.aborted) return;
          failures = 0;
          yield {
            type: "connection" as const,
            state: "connected" as const,
            attempt: 0,
          };
          yield { type: "snapshot" as const, snapshot };
          if (["completed", "failed", "cancelled"].includes(snapshot.state))
            return;
        } catch (error) {
          if (read.signal?.aborted) return;
          if (
            !(error instanceof ProcessClientError) ||
            error.reason.code !== "CAPABILITY_UNAVAILABLE" ||
            ++failures > maximum
          )
            throw error;
          yield {
            type: "connection" as const,
            state: "reconnecting" as const,
            attempt: failures,
          };
        }
        await new Promise<void>((resolve) => {
          const finish = () => {
            clearTimeout(timer);
            read.signal?.removeEventListener("abort", finish);
            resolve();
          };
          const timer = setTimeout(finish, 2000);
          read.signal?.addEventListener("abort", finish, { once: true });
          if (read.signal?.aborted) finish();
        });
      }
    },
  });
  const readReasoningStatus: WorkflowReasoningStatusReader = async (
    runId,
    signal,
  ) => {
    const reply = await invoke(
      "wright_process_ui_read",
      { ...scope, operation: "reasoning", run_id: runId },
      signal,
    );
    if (!reply.ok)
      throw new Error("Wright could not read the exact run's chat wait.");
    return desktopReasoningWait(await reply.json(), {
      workspaceId: process.workspace_id,
      sessionId,
      runId,
      workspaceName,
    });
  };
  return { client, readReasoningStatus };
}
