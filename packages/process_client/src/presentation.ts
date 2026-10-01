/** Cookie-bound isolated presentation transport. No native token crosses this boundary. */
import {
  createNativeProcessClient,
  type ProcessClient,
  type ProcessFetch,
} from "./client";
import type {
  ProcessRef,
  StartReceipt,
  NavigationResolution,
} from "./contracts.generated";
import { clientError } from "./errors";
import { assertProcessReference, checkJson, identifier } from "./validation";

const capabilities = [
  "process.read",
  "process.inputs",
  "process.start",
  "process.respond",
  "process.review",
  "process.action",
  "process.cancel",
  "process.results",
  "process.navigate",
] as const;
export type PresentationCapability = (typeof capabilities)[number];
export interface ProcessPresentationContext {
  readonly schema_version: "wright.process-presentation/1";
  readonly process: ProcessRef;
  readonly session_id: string;
  readonly ui_id: string;
  readonly revision_id: string;
  readonly run_id: string | null;
  readonly read_only: boolean;
  readonly capabilities: readonly PresentationCapability[];
  readonly presentation_id: string;
  readonly generation: number;
}

function denied(): never {
  throw clientError(
    "SCOPE_DENIED",
    "This interface is not authorized for that process operation.",
    "Open the exact process and run in Wright or use its common working view.",
  );
}

export function assertPresentationContext(
  raw: unknown,
): ProcessPresentationContext {
  checkJson(raw);
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return denied();
  const value = raw as Record<string, unknown>;
  const fields = [
    "schema_version",
    "process",
    "session_id",
    "ui_id",
    "revision_id",
    "run_id",
    "read_only",
    "capabilities",
    "presentation_id",
    "generation",
  ];
  if (
    Object.keys(value).length !== fields.length ||
    fields.some((key) => !Object.hasOwn(value, key)) ||
    value.schema_version !== "wright.process-presentation/1" ||
    typeof value.read_only !== "boolean" ||
    !Number.isInteger(value.generation) ||
    (value.generation as number) < 1 ||
    (value.generation as number) > 2147483647
  )
    return denied();
  if (
    typeof value.ui_id !== "string" ||
    !/^ui-[0-9a-f]{32}$/.test(value.ui_id) ||
    typeof value.revision_id !== "string" ||
    !/^revision-[0-9a-f]{32}$/.test(value.revision_id)
  )
    return denied();
  if (
    typeof value.session_id !== "string" ||
    typeof value.presentation_id !== "string" ||
    (value.run_id !== null && typeof value.run_id !== "string")
  )
    return denied();
  if (
    !Array.isArray(value.capabilities) ||
    value.capabilities.some(
      (capability) => !capabilities.includes(capability),
    ) ||
    new Set(value.capabilities).size !== value.capabilities.length ||
    !value.capabilities.includes("process.read")
  )
    return denied();
  const allowed = Object.freeze([
    ...value.capabilities,
  ]) as readonly PresentationCapability[];
  if (
    value.read_only &&
    allowed.some(
      (capability) =>
        !["process.read", "process.results", "process.navigate"].includes(
          capability,
        ),
    )
  )
    return denied();
  return Object.freeze({
    schema_version: "wright.process-presentation/1",
    process: Object.freeze({ ...assertProcessReference(value.process) }),
    session_id: identifier(value.session_id, "presentation session"),
    ui_id: value.ui_id,
    revision_id: value.revision_id,
    run_id:
      value.run_id === null ? null : identifier(value.run_id, "bound run"),
    read_only: value.read_only,
    capabilities: allowed,
    presentation_id: identifier(value.presentation_id, "presentation"),
    generation: value.generation as number,
  });
}

export interface PresentationClientPorts {
  readonly fetch: ProcessFetch;
  /** Trusted host replaces/reopens the tab with a fresh exact run presentation. */
  readonly onRunStarted?: (receipt: StartReceipt) => void | Promise<void>;
  readonly navigate?: (
    resolution: NavigationResolution,
  ) => void | Promise<void>;
}

export function createPresentationProcessClient(
  raw: unknown,
  ports: PresentationClientPorts,
): ProcessClient {
  const context = assertPresentationContext(raw);
  const allowed = (capability: PresentationCapability) => {
    if (!context.capabilities.includes(capability)) denied();
  };
  const run = (runId: string | undefined) => {
    if ((runId ?? null) !== context.run_id) denied();
  };
  const draft = () => {
    if (context.run_id !== null) denied();
  };
  const attached = () => {
    if (context.run_id === null) denied();
  };
  const client = createNativeProcessClient({
    process: context.process,
    sessionId: context.session_id,
    baseUrl: "/__wright/process",
    fetch: (input, init) =>
      ports.fetch(input, {
        ...init,
        credentials: "same-origin",
        mode: "same-origin",
        redirect: "error",
      }),
    ...(ports.navigate
      ? {
          navigate: async (_process, _target, resolution) => {
            await ports.navigate!(resolution);
          },
        }
      : {}),
  });
  return Object.freeze({
    process: client.process,
    async getSnapshot(options = {}) {
      allowed("process.read");
      const runId = options.runId ?? context.run_id ?? undefined;
      run(runId);
      return client.getSnapshot({ ...options, runId });
    },
    async setInputs(bindings, options) {
      allowed("process.inputs");
      draft();
      return client.setInputs(bindings, options);
    },
    async uploadInput(inputId, file, options) {
      allowed("process.inputs");
      draft();
      return client.uploadInput(inputId, file, options);
    },
    async checkReadiness(input, options) {
      allowed("process.read");
      draft();
      return client.checkReadiness(input, options);
    },
    async start(input, requestId, options) {
      allowed("process.start");
      draft();
      const receipt = await client.start(input, requestId, options);
      // A presentation stays bound to its original run. Only the native host
      // may create a fresh binding from this durable receipt. A host failure
      // does not turn a known accepted start into permission to replay work.
      try {
        void Promise.resolve(ports.onRunStarted?.(receipt)).catch(
          () => undefined,
        );
      } catch {
        /* receipt remains authoritative */
      }
      return receipt;
    },
    async attach(runId, options) {
      allowed("process.read");
      attached();
      run(runId);
      return client.attach(runId, options);
    },
    async *follow(options) {
      allowed("process.read");
      attached();
      run(options.runId);
      yield* client.follow(options);
    },
    async respond(request, options) {
      allowed("process.respond");
      attached();
      return client.respond(request, options);
    },
    async decide(request, options) {
      allowed("process.review");
      attached();
      return client.decide(request, options);
    },
    async requestAction(request, options) {
      allowed("process.action");
      attached();
      return client.requestAction(request, options);
    },
    async cancel(runId, requestId, options) {
      allowed("process.cancel");
      attached();
      run(runId);
      return client.cancel(runId, requestId, options);
    },
    async getRepresentation(reference, options = {}) {
      allowed("process.results");
      const runId = options.runId ?? context.run_id ?? undefined;
      run(runId);
      return client.getRepresentation(reference, { ...options, runId });
    },
    async navigate(target) {
      allowed("process.navigate");
      if (target.run_id) run(target.run_id);
      return client.navigate(target);
    },
  } satisfies ProcessClient);
}
