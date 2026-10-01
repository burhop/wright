import type {
  ArtifactRef,
  InputBinding,
  InputSnapshot,
  InteractionResponse,
  InteractionSnapshot,
  JsonValue,
  NavigationTarget,
  ProcessCancellationReceipt,
  ProcessRef,
  ProcessRunEventPage,
  Readiness,
  Reason,
  StartReceipt,
  ContractName,
  ContractTypes,
} from "./contracts.generated";
import { clientError, ProcessClientError, unknownOutcome } from "./errors";
import {
  assertContract,
  checkJson,
  identifier,
  relativeLocator,
} from "./validation";
import { recordedFrames } from "./sse";

export const PROCESS_CLIENT_VERSION = "1.0.0";
export type ProcessFetch = (
  input: RequestInfo | URL,
  init?: RequestInit,
) => Promise<Response>;
export interface ReadOptions {
  readonly signal?: AbortSignal;
}
export interface SnapshotOptions extends ReadOptions {
  readonly runId?: string;
  readonly inputSnapshotId?: string;
  readonly page?: string;
}
export interface FollowOptions extends ReadOptions {
  readonly runId: string;
  readonly cursor?: string;
  readonly maxReconnects?: number;
}
export type FollowUpdate =
  | { readonly type: "snapshot"; readonly snapshot: InteractionSnapshot }
  | { readonly type: "progress"; readonly page: ProcessRunEventPage }
  | { readonly type: "reconciliation"; readonly reason: Reason }
  | {
      readonly type: "connection";
      readonly state: "connected" | "reconnecting";
      readonly attempt: number;
    };
export interface ResponseRequest {
  readonly checkpointId: string;
  readonly subjectDigest: string;
  readonly value: JsonValue;
  readonly requestId: string;
}
export interface DecisionRequest {
  readonly checkpointId: string;
  readonly subjectDigest: string;
  readonly decision: string;
  readonly reason: string;
  readonly requestId: string;
}
export interface ActionRequest {
  readonly actionId: string;
  readonly subjectDigest: string;
  readonly requestId: string;
}

/** A view of a host-bound process. The backend owns execution and all permission checks. */
export interface ProcessClient {
  readonly process: ProcessRef;
  getSnapshot(options?: SnapshotOptions): Promise<InteractionSnapshot>;
  setInputs(
    bindings: ReadonlyArray<InputBinding>,
    options?: ReadOptions,
  ): Promise<InputSnapshot>;
  checkReadiness(
    input: InputSnapshot,
    options?: ReadOptions,
  ): Promise<Readiness>;
  start(
    input: InputSnapshot,
    requestId: string,
    options?: ReadOptions,
  ): Promise<StartReceipt>;
  attach(runId: string, options?: ReadOptions): Promise<InteractionSnapshot>;
  follow(options: FollowOptions): AsyncIterable<FollowUpdate>;
  respond(
    request: ResponseRequest,
    options?: ReadOptions,
  ): Promise<InteractionResponse>;
  decide(
    request: DecisionRequest,
    options?: ReadOptions,
  ): Promise<InteractionSnapshot>;
  requestAction(
    request: ActionRequest,
    options?: ReadOptions,
  ): Promise<InteractionSnapshot>;
  cancel(
    runId: string,
    requestId: string,
    options?: ReadOptions,
  ): Promise<ProcessCancellationReceipt>;
  getRepresentation(
    reference: ArtifactRef,
    options?: ReadOptions,
  ): Promise<Blob>;
  navigate(target: NavigationTarget): Promise<void>;
}

export interface NativeProcessClientOptions {
  readonly process: ProcessRef;
  readonly sessionId: string;
  /** Host injects its browser/desktop authentication handling. No tokens belong in this package. */
  readonly fetch: ProcessFetch;
  readonly baseUrl?: string;
  readonly reconnectDelayMs?: number;
  /** Trusted native host ports. Their owning services must resolve and authorize exact references. */
  readonly readRepresentation?: (
    process: ProcessRef,
    reference: ArtifactRef,
    options: ReadOptions,
  ) => Promise<Blob>;
  readonly navigate?: (
    process: ProcessRef,
    target: NavigationTarget,
  ) => Promise<void>;
}

function scopedProcess(expected: ProcessRef, actual: ProcessRef): void {
  if (
    expected.workspace_id !== actual.workspace_id ||
    expected.source_path !== actual.source_path ||
    expected.source_digest !== actual.source_digest
  ) {
    throw clientError(
      "SCOPE_DENIED",
      "The reply belongs to another process or source revision.",
      "Open the intended process again. This view cannot adopt another process.",
    );
  }
}

function scopedRun(
  expected: string | undefined,
  actual: string | null | undefined,
): void {
  if (expected !== undefined && expected !== actual)
    throw clientError(
      "SCOPE_DENIED",
      "The reply belongs to another run.",
      "Reopen the intended saved run.",
    );
}

function cursor(value: string | undefined): string | undefined {
  if (
    value !== undefined &&
    (typeof value !== "string" ||
      value.length === 0 ||
      value.length > 256 ||
      /[\x00-\x1f]/.test(value))
  ) {
    throw clientError(
      "SUBJECT_STALE",
      "The saved progress cursor is not supported.",
      "Attach to the current run without that cursor.",
    );
  }
  return value;
}

function unavailable(capability: string): never {
  throw clientError(
    "CAPABILITY_UNAVAILABLE",
    `This host has not enabled ${capability}.`,
    "Use an available process view or configure the owning capability before proceeding.",
  );
}

async function jsonBody(
  response: Response,
  signal?: AbortSignal,
): Promise<unknown> {
  const maximum = 64 * 1024 * 1024;
  const length = Number(response.headers.get("content-length"));
  if (Number.isFinite(length) && length > maximum)
    throw clientError(
      "UI_INCOMPATIBLE",
      "The process reply exceeds the supported size.",
      "Read a smaller page or use referenced artifacts.",
    );
  if (!response.body)
    throw clientError(
      "UI_INCOMPATIBLE",
      "The process reply is empty.",
      "Refresh the current process snapshot.",
    );
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let bytes = 0,
    text = "";
  const abort = () => {
    void reader.cancel().catch(() => undefined);
  };
  signal?.addEventListener("abort", abort, { once: true });
  try {
    signal?.throwIfAborted();
    while (true) {
      const chunk = await reader.read();
      signal?.throwIfAborted();
      if (chunk.done) break;
      bytes += chunk.value.byteLength;
      if (bytes > maximum)
        throw clientError(
          "UI_INCOMPATIBLE",
          "The process reply exceeds the supported size.",
          "Read a smaller page or use referenced artifacts.",
        );
      text += decoder.decode(chunk.value, { stream: true });
    }
    text += decoder.decode();
    try {
      return JSON.parse(text);
    } catch {
      throw clientError(
        "UI_INCOMPATIBLE",
        "Wright did not return supported process data.",
        "Refresh the view and check client/server compatibility.",
      );
    }
  } finally {
    signal?.removeEventListener("abort", abort);
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

async function httpFailure(
  response: Response,
  requestId?: string,
): Promise<never> {
  let reason: Reason | undefined;
  try {
    const value = (await jsonBody(response)) as {
      detail?: { reason?: unknown };
    };
    if (value && typeof value === "object" && value.detail?.reason)
      reason = assertContract("Reason", value.detail.reason);
  } catch {
    /* No arbitrary raw error payload is shown as user-facing text. */
  }
  if (!reason && requestId && response.status >= 500)
    throw unknownOutcome(requestId);
  throw new ProcessClientError(
    reason ?? {
      code:
        response.status === 401 || response.status === 403
          ? "SCOPE_DENIED"
          : "CAPABILITY_UNAVAILABLE",
      message:
        response.status === 401 || response.status === 403
          ? "This view is not authorized to access the process."
          : "Wright could not provide the requested process operation.",
      correction:
        response.status === 401 || response.status === 403
          ? "Sign in again or reopen the process from its workspace."
          : "Refresh the view and check the owning service.",
    },
    { httpStatus: response.status, requestId },
  );
}

async function delay(
  milliseconds: number,
  signal?: AbortSignal,
): Promise<void> {
  signal?.throwIfAborted();
  if (milliseconds === 0) return;
  await new Promise<void>((resolve, reject) => {
    const abort = () => {
      clearTimeout(timer);
      reject(signal?.reason);
    };
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", abort);
      resolve();
    }, milliseconds);
    signal?.addEventListener("abort", abort, { once: true });
  });
}

/** Create once per accepted revision. Reopening uses reads; only start() can submit work. */
export function createNativeProcessClient(
  options: NativeProcessClientOptions,
): ProcessClient {
  const process = Object.freeze({
    ...assertContract("ProcessRef", options.process),
  });
  identifier(process.workspace_id, "workspace ID");
  relativeLocator(process.source_path);
  const sessionId = identifier(options.sessionId, "session ID");
  const fetch = options.fetch;
  const base = options.baseUrl ?? "/api/workspace/process-interfaces";
  if (
    !base ||
    base.startsWith("//") ||
    base.endsWith("/") ||
    /[?#]/.test(base) ||
    (!base.startsWith("/") && !/^https?:\/\//.test(base))
  ) {
    throw clientError(
      "RESPONSE_INVALID",
      "The host process service address is not supported.",
      "Configure the native process service base address.",
    );
  }
  const reconnectDelay = options.reconnectDelayMs ?? 500;
  if (
    !Number.isInteger(reconnectDelay) ||
    reconnectDelay < 0 ||
    reconnectDelay > 5000
  )
    throw clientError(
      "RESPONSE_INVALID",
      "The reconnection delay is outside the supported bound.",
      "Use a delay from zero to five seconds.",
    );
  const navigate = options.navigate,
    readRepresentation = options.readRepresentation;
  const source = () => ({
    session_id: sessionId,
    path: process.source_path,
    expected_storage_digest: process.source_digest,
  });
  const url = (
    path: string,
    query: Readonly<Record<string, string | undefined>> = {},
  ) => {
    const params = new URLSearchParams(source());
    for (const [key, value] of Object.entries(query))
      if (value !== undefined) params.set(key, value);
    return `${base}${path}?${params}`;
  };
  async function request<K extends ContractName>(
    path: string,
    name: K,
    read: ReadOptions,
    body?: Record<string, unknown>,
    requestId?: string,
  ): Promise<ContractTypes[K]> {
    read.signal?.throwIfAborted();
    let response: Response;
    try {
      response = await fetch(body ? `${base}${path}` : url(path), {
        method: body ? "POST" : "GET",
        cache: "no-store",
        signal: read.signal,
        headers: body
          ? { "content-type": "application/json", accept: "application/json" }
          : { accept: "application/json" },
        ...(body ? { body: JSON.stringify({ ...source(), ...body }) } : {}),
      });
    } catch {
      if (requestId) throw unknownOutcome(requestId);
      read.signal?.throwIfAborted();
      throw clientError(
        "CAPABILITY_UNAVAILABLE",
        "The connection to Wright was interrupted.",
        "Refresh the current process view.",
      );
    }
    if (!response.ok) return httpFailure(response, requestId);
    try {
      return assertContract(name, await jsonBody(response, read.signal));
    } catch (error) {
      if (requestId) throw unknownOutcome(requestId);
      throw error;
    }
  }
  function checkedInput(value: InputSnapshot): InputSnapshot {
    const input = assertContract("InputSnapshot", value);
    scopedProcess(process, input.process);
    return input;
  }
  async function getSnapshot(
    read: SnapshotOptions = {},
  ): Promise<InteractionSnapshot> {
    const runId =
      read.runId === undefined ? undefined : identifier(read.runId, "run ID");
    const inputId =
      read.inputSnapshotId === undefined
        ? undefined
        : identifier(read.inputSnapshotId, "input snapshot ID");
    const page = cursor(read.page);
    read.signal?.throwIfAborted();
    let response: Response;
    try {
      response = await fetch(
        url(runId ? `/runs/${encodeURIComponent(runId)}` : "/interaction", {
          input_snapshot_id: inputId,
          page,
        }),
        {
          method: "GET",
          cache: "no-store",
          signal: read.signal,
          headers: { accept: "application/json" },
        },
      );
    } catch {
      read.signal?.throwIfAborted();
      throw clientError(
        "CAPABILITY_UNAVAILABLE",
        "The connection to Wright was interrupted.",
        "Reattach to the saved run or refresh the process view.",
      );
    }
    if (!response.ok) return httpFailure(response);
    const reply = assertContract(
      "InteractionSnapshot",
      await jsonBody(response, read.signal),
    );
    scopedProcess(process, reply.context.process);
    scopedRun(runId, reply.context.run_id);
    if (inputId && inputId !== reply.context.input_snapshot_id)
      throw clientError(
        "SCOPE_DENIED",
        "The reply belongs to another input snapshot.",
        "Reopen the intended prepared inputs.",
      );
    return reply;
  }
  async function* follow(read: FollowOptions): AsyncGenerator<FollowUpdate> {
    const runId = identifier(read.runId, "run ID"); // Captured: subsequent views cannot redirect an existing observer.
    let savedCursor = cursor(read.cursor),
      attempts = 0;
    const maxReconnects = read.maxReconnects ?? 3;
    if (
      !Number.isInteger(maxReconnects) ||
      maxReconnects < 0 ||
      maxReconnects > 5
    )
      throw clientError(
        "RESPONSE_INVALID",
        "The reconnect limit is outside the supported bound.",
        "Use at most five consecutive reconnection attempts.",
      );
    let lastState: InteractionSnapshot["state"] | undefined;
    if (read.signal?.aborted) return;
    try {
      yield {
        type: "snapshot",
        snapshot: await getSnapshot({ runId, signal: read.signal }),
      };
      while (!read.signal?.aborted) {
        try {
          const response = await fetch(
            url(`/runs/${encodeURIComponent(runId)}/events`, {
              cursor: savedCursor,
            }),
            {
              method: "GET",
              cache: "no-store",
              signal: read.signal,
              headers: { accept: "text/event-stream" },
            },
          );
          if (!response.ok) await httpFailure(response);
          yield { type: "connection", state: "connected", attempt: attempts };
          for await (const frame of recordedFrames(response, read.signal)) {
            let value: unknown;
            try {
              value = JSON.parse(frame.data);
            } catch {
              throw clientError(
                "UI_INCOMPATIBLE",
                "Wright returned an unreadable progress message.",
                "Reopen the current run snapshot.",
              );
            }
            if (frame.event === "reconciliation") {
              const reason = assertContract("Reason", value);
              yield { type: "reconciliation", reason };
              if (reason.code === "SUBJECT_STALE") {
                savedCursor = undefined;
                break;
              }
              throw new ProcessClientError(reason);
            }
            if (frame.event !== "progress")
              throw clientError(
                "UI_INCOMPATIBLE",
                "Wright returned an unsupported progress event.",
                "Refresh the current run snapshot.",
              );
            const page = assertContract("ProcessRunEventPage", value);
            scopedRun(runId, page.run_id);
            cursor(page.cursor);
            if (frame.id !== page.cursor)
              throw clientError(
                "UI_INCOMPATIBLE",
                "The recorded progress cursor does not match its event.",
                "Reopen the current run snapshot.",
              );
            savedCursor = page.cursor;
            attempts = 0;
            yield { type: "progress", page };
            if (
              (page.events?.length ?? 0) > 0 ||
              page.state !== lastState ||
              !page.following
            ) {
              yield {
                type: "snapshot",
                snapshot: await getSnapshot({ runId, signal: read.signal }),
              };
              lastState = page.state;
            }
            if (!page.following && !page.has_more) return;
          }
          if (read.signal?.aborted) return;
          throw clientError(
            "CAPABILITY_UNAVAILABLE",
            "The progress connection was interrupted.",
            "Reattach to the saved run.",
          );
        } catch (error) {
          if (read.signal?.aborted) return;
          if (
            error instanceof ProcessClientError &&
            !["CAPABILITY_UNAVAILABLE", "SUBJECT_STALE"].includes(
              error.reason.code,
            )
          )
            throw error;
          if (++attempts > maxReconnects)
            throw clientError(
              "CAPABILITY_UNAVAILABLE",
              "Wright could not reconnect to the saved progress stream.",
              "Reopen the run to reconcile its current status. No work has been restarted.",
            );
          if (
            error instanceof ProcessClientError &&
            error.reason.code === "SUBJECT_STALE"
          )
            savedCursor = undefined;
          yield {
            type: "connection",
            state: "reconnecting",
            attempt: attempts,
          };
          yield {
            type: "snapshot",
            snapshot: await getSnapshot({ runId, signal: read.signal }),
          };
          await delay(Math.min(reconnectDelay * attempts, 5000), read.signal);
        }
      }
    } catch (error) {
      if (!read.signal?.aborted) throw error;
    }
  }
  return Object.freeze({
    process,
    getSnapshot,
    follow,
    async setInputs(
      bindings: ReadonlyArray<InputBinding>,
      read: ReadOptions = {},
    ) {
      if (!Array.isArray(bindings) || bindings.length > 256)
        throw clientError(
          "RESPONSE_INVALID",
          "The prepared input list exceeds its supported size.",
          "Prepare at most 256 input bindings.",
        );
      const checked = bindings.map((binding) => {
        checkJson(binding);
        if (!["value", "file", "option"].includes(binding.kind))
          throw clientError(
            "RESPONSE_INVALID",
            "Each input binding needs its declared kind.",
            "Supply a value, file or configured option binding.",
          );
        return assertContract(
          binding.kind === "file"
            ? "FileBinding"
            : binding.kind === "option"
              ? "OptionBinding"
              : "ValueBinding",
          binding,
        );
      });
      const reply = await request("/inputs", "InputSnapshot", read, {
        bindings: checked,
      });
      scopedProcess(process, reply.process);
      return reply;
    },
    async checkReadiness(value: InputSnapshot, read: ReadOptions = {}) {
      const input = checkedInput(value);
      const reply = await request("/readiness", "Readiness", read, {
        input_snapshot_id: input.snapshot_id,
      });
      scopedProcess(process, reply.process);
      if (reply.input_digest !== input.digest)
        throw clientError(
          "SUBJECT_STALE",
          "Readiness belongs to different prepared inputs.",
          "Check readiness again for the intended input snapshot.",
        );
      return reply;
    },
    async start(
      value: InputSnapshot,
      requestId: string,
      read: ReadOptions = {},
    ) {
      const input = checkedInput(value);
      identifier(requestId, "request ID");
      const reply = await request(
        "/runs",
        "StartReceipt",
        read,
        {
          input_snapshot_id: input.snapshot_id,
          expected_input_digest: input.digest,
          request_id: requestId,
        },
        requestId,
      );
      try {
        scopedProcess(process, reply.process);
        if (
          reply.request_id !== requestId ||
          reply.input_snapshot_id !== input.snapshot_id ||
          reply.input_digest !== input.digest
        )
          throw unknownOutcome(requestId);
      } catch (error) {
        if (error instanceof ProcessClientError)
          throw new ProcessClientError(error.reason, {
            requestId,
            uncertain: true,
          });
        throw error;
      }
      return reply;
    },
    attach: (runId: string, read: ReadOptions = {}) =>
      getSnapshot({ runId, signal: read.signal }),
    // These categories are part of the public contract. Their backend routes and
    // scoped presentation transport are implemented by subsequent feature tasks.
    async respond(
      _request: ResponseRequest,
      _read?: ReadOptions,
    ): Promise<InteractionResponse> {
      return unavailable("declared input responses");
    },
    async decide(
      _request: DecisionRequest,
      _read?: ReadOptions,
    ): Promise<InteractionSnapshot> {
      return unavailable("process review decisions");
    },
    async requestAction(
      _request: ActionRequest,
      _read?: ReadOptions,
    ): Promise<InteractionSnapshot> {
      return unavailable("process actions");
    },
    async cancel(runId: string, requestId: string, read: ReadOptions = {}) {
      identifier(runId, "run ID");
      identifier(requestId, "request ID");
      const reply = await request(
        `/runs/${encodeURIComponent(runId)}/cancel`,
        "ProcessCancellationReceipt",
        read,
        { request_id: requestId },
        requestId,
      );
      if (reply.run_id !== runId || reply.request_id !== requestId)
        throw unknownOutcome(requestId);
      return reply;
    },
    async getRepresentation(reference: ArtifactRef, read: ReadOptions = {}) {
      const checked = assertContract("ArtifactRef", reference);
      relativeLocator(checked.artifact_ref);
      if (!readRepresentation) return unavailable("representation reads");
      return readRepresentation(process, checked, read);
    },
    async navigate(target: NavigationTarget) {
      const checked = assertContract("NavigationTarget", target);
      if (!navigate) return unavailable("workspace navigation");
      await navigate(process, checked);
    },
  });
}
