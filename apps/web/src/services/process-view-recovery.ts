import {
  assertContract,
  ProcessClientError,
  type InputSnapshot,
  type ProcessRef,
  type StartReceipt,
} from "@wright/process-client";

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
  return {
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
