import {
  assertProcessReference,
  ProcessClientError,
  type ProcessRef,
} from "@wright/process-client";
import type { InterfaceAuthoringRequest } from "./process-ui-authoring";
import { sameProcessReference } from "./process-navigation";

/** Untrusted request locators only. Jobs/builds/permissions stay with Wright. */
export interface InterfaceAuthoringIntent {
  readonly version: "1";
  readonly process: ProcessRef;
  readonly request: InterfaceAuthoringRequest;
  readonly job_id?: string;
}
export interface InterfaceAuthoringRecoveryStore {
  read(): InterfaceAuthoringIntent | null;
  write(value: InterfaceAuthoringIntent): void;
  clear(): void;
}
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
const identifier = (value: unknown): value is string =>
  typeof value === "string" && /^[a-z0-9][a-z0-9._:-]{0,159}$/i.test(value);
function unavailable(): never {
  throw new ProcessClientError({
    code: "UI_INCOMPATIBLE",
    message: "This interface request could not be recovered safely.",
    correction:
      "Open its recorded job or clear the local request locator. No new generation was requested.",
  });
}
export function checkedInterfaceAuthoringIntent(
  value: unknown,
  process: ProcessRef,
): InterfaceAuthoringIntent {
  if (
    !object(value) ||
    value.version !== "1" ||
    Object.keys(value).some(
      (key) => !["version", "process", "request", "job_id"].includes(key),
    ) ||
    (value.job_id !== undefined && !identifier(value.job_id)) ||
    !object(value.request)
  )
    return unavailable();
  const source = assertProcessReference(value.process),
    request = value.request;
  if (
    !sameProcessReference(source, process) ||
    !identifier(request.request_id) ||
    typeof request.instruction !== "string" ||
    !request.instruction.trim() ||
    new TextEncoder().encode(request.instruction).byteLength > 16_384 ||
    typeof request.title !== "string" ||
    !request.title.trim() ||
    request.title.length > 512 ||
    Object.keys(request).some(
      (key) =>
        ![
          "request_id",
          "instruction",
          "title",
          "ui_id",
          "base_revision",
          "imported_interface",
        ].includes(key),
    ) ||
    (request.ui_id === undefined) !== (request.base_revision === undefined) ||
    (request.ui_id !== undefined &&
      (!identifier(request.ui_id) || !identifier(request.base_revision)))
  )
    return unavailable();
  const imported = request.imported_interface;
  if (
    imported !== undefined &&
    (request.ui_id !== undefined ||
      !object(imported) ||
      Object.keys(imported).some((key) => !["ui_id", "sha256"].includes(key)) ||
      !identifier(imported.ui_id) ||
      typeof imported.sha256 !== "string" ||
      !/^[a-f0-9]{64}$/.test(imported.sha256))
  )
    return unavailable();
  return {
    version: "1",
    process: source,
    request: {
      request_id: request.request_id,
      instruction: request.instruction,
      title: request.title,
      ...(object(imported)
        ? {
            imported_interface: {
              ui_id: imported.ui_id as string,
              sha256: imported.sha256 as string,
            },
          }
        : {}),
      ...(request.ui_id !== undefined
        ? {
            ui_id: request.ui_id as string,
            base_revision: request.base_revision as string,
          }
        : {}),
    },
    ...(value.job_id !== undefined ? { job_id: value.job_id } : {}),
  };
}
export function createInterfaceAuthoringRecoveryStore(
  process: ProcessRef,
  sessionId: string,
  viewId: string,
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem">,
): InterfaceAuthoringRecoveryStore {
  const source = Object.freeze({ ...assertProcessReference(process) });
  if (!identifier(sessionId) || !identifier(viewId)) return unavailable();
  const key =
    "wright.process-ui-authoring/1:" +
    JSON.stringify([
      source.workspace_id,
      source.source_path,
      source.source_digest,
      sessionId,
      viewId,
    ]);
  const target = () => storage ?? window.localStorage;
  return {
    read() {
      try {
        const raw = target().getItem(key);
        if (raw === null) return null;
        if (raw.length > 131_072) return unavailable();
        return checkedInterfaceAuthoringIntent(JSON.parse(raw), source);
      } catch {
        return unavailable();
      }
    },
    write(value) {
      try {
        target().setItem(
          key,
          JSON.stringify(checkedInterfaceAuthoringIntent(value, source)),
        );
      } catch {
        return unavailable();
      }
    },
    clear() {
      try {
        target().removeItem(key);
      } catch {
        return unavailable();
      }
    },
  };
}
