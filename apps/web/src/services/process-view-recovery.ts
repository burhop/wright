import {
  assertContract,
  ProcessClientError,
  type InputSnapshot,
  type ProcessRef,
  type StartReceipt,
  type ResponseRequest,
  type DecisionRequest,
  type ActionRequest,
  type JsonValue,
} from "@wright/process-client";

/** Retained request intent supports explicit reconciliation; it never grants authority. */
export type ProcessViewMutation = { readonly runId: string } & (
  | { readonly kind: "response"; readonly request: ResponseRequest }
  | { readonly kind: "review"; readonly request: DecisionRequest }
  | {
      readonly kind: "action";
      readonly checkpointId: string;
      readonly request: ActionRequest;
    }
);

/** Browser recovery is a locator cache. Frozen values and all outcomes stay on the backend. */
export interface ProcessViewRecovery {
  readonly version: "1";
  readonly input: InputSnapshot;
  readonly start?: {
    readonly requestId: string;
    readonly receipt?: StartReceipt;
  };
  readonly cancellation?: {
    readonly requestId: string;
    readonly runId: string;
  };
}
export interface ProcessViewRecoveryStore {
  read(): ProcessViewRecovery | null;
  write(value: ProcessViewRecovery): void;
  clear(): void;
  readInteraction(runId: string): ProcessViewMutation | null;
  writeInteraction(value: ProcessViewMutation): void;
  clearInteraction(runId: string, requestId: string): void;
}
export function processViewReason(
  message = "The saved view could not be recovered.",
) {
  return new ProcessClientError({
    code: "UI_INCOMPATIBLE",
    message,
    correction:
      "Open the recorded run to reconcile its outcome before starting another run.",
  });
}
const sameProcess = (a: ProcessRef, b: ProcessRef) =>
  a.workspace_id === b.workspace_id &&
  a.source_path === b.source_path &&
  a.source_digest === b.source_digest;
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
function keys(value: Record<string, unknown>, allowed: string[]) {
  if (Object.keys(value).some((key) => !allowed.includes(key)))
    throw processViewReason();
}
function requestId(value: unknown): value is string {
  return typeof value === "string" && /^[a-z0-9-]{1,160}$/i.test(value);
}
function identifier(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.length <= 160 &&
    !/\s/.test(value) &&
    !Array.from(value).some((character) => character.charCodeAt(0) < 32)
  );
}
function jsonValue(value: unknown, depth = 0): value is JsonValue {
  if (depth > 24) return false;
  if (value === null || typeof value === "string" || typeof value === "boolean")
    return true;
  if (typeof value === "number") return Number.isFinite(value);
  if (Array.isArray(value))
    return value.every((item) => jsonValue(item, depth + 1));
  return (
    object(value) &&
    Object.values(value).every((item) => jsonValue(item, depth + 1))
  );
}
function interactionIntent(value: unknown): ProcessViewMutation {
  if (!object(value) || !identifier(value.runId) || !object(value.request))
    throw processViewReason();
  const request = value.request;
  if (
    !requestId(request.requestId) ||
    typeof request.subjectDigest !== "string" ||
    !/^[a-f0-9]{64}$/.test(request.subjectDigest)
  )
    throw processViewReason();
  if (value.kind === "action") {
    keys(value, ["kind", "runId", "checkpointId", "request"]);
    keys(request, ["actionId", "subjectDigest", "requestId"]);
    if (!identifier(value.checkpointId) || !identifier(request.actionId))
      throw processViewReason();
    return {
      kind: "action",
      runId: value.runId,
      checkpointId: value.checkpointId,
      request: {
        actionId: request.actionId,
        subjectDigest: request.subjectDigest,
        requestId: request.requestId,
      },
    };
  }
  keys(value, ["kind", "runId", "request"]);
  if (!identifier(request.checkpointId)) throw processViewReason();
  if (value.kind === "response") {
    keys(request, ["checkpointId", "subjectDigest", "requestId", "value"]);
    if (
      !jsonValue(request.value) ||
      new TextEncoder().encode(JSON.stringify(request.value)).length > 65536
    )
      throw processViewReason();
    return {
      kind: "response",
      runId: value.runId,
      request: {
        checkpointId: request.checkpointId,
        subjectDigest: request.subjectDigest,
        requestId: request.requestId,
        value: request.value,
      },
    };
  }
  if (
    value.kind !== "review" ||
    !["approved", "changes_requested"].includes(String(request.decision)) ||
    typeof request.reason !== "string" ||
    request.reason.length > 2000 ||
    (request.decision === "changes_requested" && !request.reason.trim())
  )
    throw processViewReason();
  keys(request, [
    "checkpointId",
    "subjectDigest",
    "requestId",
    "decision",
    "reason",
  ]);
  return {
    kind: "review",
    runId: value.runId,
    request: {
      checkpointId: request.checkpointId,
      subjectDigest: request.subjectDigest,
      requestId: request.requestId,
      decision: String(request.decision),
      reason: request.reason,
    },
  };
}
export function checkedRecovery(
  value: unknown,
  process: ProcessRef,
): ProcessViewRecovery {
  if (!object(value) || value.version !== "1") throw processViewReason();
  keys(value, ["version", "input", "start", "cancellation"]);
  const input = assertContract("InputSnapshot", value.input);
  if (!sameProcess(input.process, process) || input.bindings?.length)
    throw processViewReason();
  let start: ProcessViewRecovery["start"];
  if (value.start !== undefined) {
    if (!object(value.start) || !requestId(value.start.requestId))
      throw processViewReason();
    keys(value.start, ["requestId", "receipt"]);
    const receipt =
      value.start.receipt === undefined
        ? undefined
        : assertContract("StartReceipt", value.start.receipt);
    if (
      receipt &&
      (!sameProcess(receipt.process, process) ||
        receipt.request_id !== value.start.requestId ||
        receipt.input_snapshot_id !== input.snapshot_id ||
        receipt.input_digest !== input.digest)
    )
      throw processViewReason();
    start = {
      requestId: value.start.requestId,
      ...(receipt ? { receipt } : {}),
    };
  }
  let cancellation: ProcessViewRecovery["cancellation"];
  if (value.cancellation !== undefined) {
    if (
      !object(value.cancellation) ||
      !requestId(value.cancellation.requestId) ||
      typeof value.cancellation.runId !== "string" ||
      value.cancellation.runId !== start?.receipt?.run_id
    )
      throw processViewReason();
    keys(value.cancellation, ["requestId", "runId"]);
    cancellation = {
      requestId: value.cancellation.requestId,
      runId: value.cancellation.runId,
    };
  }
  return {
    version: "1",
    input,
    ...(start ? { start } : {}),
    ...(cancellation ? { cancellation } : {}),
  };
}
export function compactInput(input: InputSnapshot): InputSnapshot {
  return {
    process: input.process,
    snapshot_id: input.snapshot_id,
    digest: input.digest,
    created_at: input.created_at,
  };
}
export function createProcessViewRecoveryStore(
  process: ProcessRef,
  sessionId: string,
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem">,
): ProcessViewRecoveryStore {
  const key = `wright.process-view/1:${JSON.stringify([
    sessionId,
    process.workspace_id,
    process.source_path,
    process.source_digest,
  ])}`;
  const unavailable = () =>
    processViewReason("Wright cannot preserve this view's request identity.");
  function hostStorage() {
    try {
      return storage ?? window.localStorage;
    } catch {
      throw unavailable();
    }
  }
  function interactionKey(runId: string) {
    if (!identifier(runId)) throw processViewReason();
    return `${key}:interaction:${JSON.stringify(runId)}`;
  }
  function readInteraction(runId: string): ProcessViewMutation | null {
    try {
      const saved = hostStorage().getItem(interactionKey(runId));
      if (saved === null) return null;
      if (saved.length > 128 * 1024) throw processViewReason();
      const intent = interactionIntent(JSON.parse(saved));
      if (intent.runId !== runId) throw processViewReason();
      return intent;
    } catch (error) {
      throw error instanceof ProcessClientError ? error : unavailable();
    }
  }
  return {
    readInteraction,
    writeInteraction(value) {
      const intent = interactionIntent(value);
      const json = JSON.stringify(intent);
      if (json.length > 128 * 1024) throw processViewReason();
      try {
        const store = hostStorage();
        const existing = readInteraction(intent.runId);
        if (existing && JSON.stringify(existing) !== json)
          throw processViewReason(
            "An earlier interaction request still needs reconciliation.",
          );
        const target = interactionKey(intent.runId);
        store.setItem(target, json);
        if (store.getItem(target) !== json) throw unavailable();
      } catch (error) {
        throw error instanceof ProcessClientError ? error : unavailable();
      }
    },
    clearInteraction(runId, requestId) {
      try {
        if (readInteraction(runId)?.request.requestId === requestId)
          hostStorage().removeItem(interactionKey(runId));
      } catch (error) {
        throw error instanceof ProcessClientError ? error : unavailable();
      }
    },
    read() {
      try {
        const saved = hostStorage().getItem(key);
        if (saved === null) return null;
        if (saved.length > 16 * 1024) throw processViewReason();
        return checkedRecovery(JSON.parse(saved), process);
      } catch (error) {
        throw error instanceof ProcessClientError ? error : unavailable();
      }
    },
    write(value) {
      const json = JSON.stringify(checkedRecovery(value, process));
      if (json.length > 16 * 1024) throw processViewReason();
      try {
        const store = hostStorage();
        store.setItem(key, json);
        if (store.getItem(key) !== json) throw unavailable();
      } catch {
        throw unavailable();
      }
    },
    clear() {
      try {
        hostStorage().removeItem(key);
      } catch {
        throw unavailable();
      }
    },
  };
}
/** One immutable preparation identifies one start even if two observers lose acknowledgement. */
export async function processViewRequestId(
  kind: "start" | "cancel",
  identity: string,
): Promise<string> {
  if (!globalThis.crypto?.subtle)
    throw processViewReason("Request recovery is unavailable in this host.");
  const bytes = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(identity),
  );
  return `ui-${kind}-${Array.from(new Uint8Array(bytes), (b) => b.toString(16).padStart(2, "0")).join("")}`;
}
