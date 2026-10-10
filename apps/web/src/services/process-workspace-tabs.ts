import {
  assertProcessReference,
  ProcessClientError,
  type ProcessRef,
} from "@wright/process-client";
import type { EditorTab } from "../store/viewer";
import { sameProcessReference } from "./process-navigation";

/** Presentation locators only. No inputs, permissions or execution state live here. */
export interface ProcessWorkspaceView {
  readonly version: "1";
  readonly view_id: string;
  readonly process: ProcessRef;
  readonly run_id?: string;
  readonly interface?: ProcessInterfaceLocator;
}

export type ProcessInterfaceLocator =
  | {
      readonly kind: "working";
      readonly ui_id: string;
      readonly revision_id: string;
    }
  | {
      readonly kind: "preview";
      readonly ui_id: string;
      readonly revision_id: string;
      readonly job_id: string;
    };

export interface ProcessWorkspaceTab extends EditorTab {
  readonly type: "process";
  readonly processView: ProcessWorkspaceView;
}

const prefix = "/.wright/process-views/";
const queryKeys = [
  "processView",
  "processPath",
  "processDigest",
  "processRun",
  "processUIKind",
  "processUI",
  "processUIRevision",
  "processUIJob",
];
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
const identifier = (value: unknown): value is string =>
  typeof value === "string" && /^[a-z0-9][a-z0-9._:-]{0,159}$/i.test(value);

function invalid(): never {
  throw new ProcessClientError({
    code: "UI_INCOMPATIBLE",
    message: "This working view could not be reopened.",
    correction:
      "Open the saved workflow and choose Open working view, or reopen its recorded run. No run was started.",
  });
}

export function checkedProcessInterfaceLocator(
  value: unknown,
): ProcessInterfaceLocator {
  if (
    !object(value) ||
    !["working", "preview"].includes(String(value.kind)) ||
    typeof value.ui_id !== "string" ||
    !/^ui-[0-9a-f]{32}$/.test(value.ui_id) ||
    typeof value.revision_id !== "string" ||
    !/^revision-[0-9a-f]{32}$/.test(value.revision_id) ||
    Object.keys(value).some(
      (key) =>
        ![
          "kind",
          "ui_id",
          "revision_id",
          ...(value.kind === "preview" ? ["job_id"] : []),
        ].includes(key),
    ) ||
    (value.kind === "preview" && !identifier(value.job_id))
  )
    return invalid();
  return value.kind === "preview"
    ? {
        kind: "preview",
        ui_id: value.ui_id,
        revision_id: value.revision_id,
        job_id: value.job_id as string,
      }
    : { kind: "working", ui_id: value.ui_id, revision_id: value.revision_id };
}

export function isProcessWorkspaceTabPath(path: string | null): boolean {
  return !!path && path.startsWith(prefix);
}

export function processWorkspaceTabPath(viewId: string): string {
  if (!identifier(viewId)) return invalid();
  return `${prefix}${encodeURIComponent(viewId)}`;
}

export function checkedProcessWorkspaceView(
  value: unknown,
  workspaceId?: string,
): ProcessWorkspaceView {
  if (
    !object(value) ||
    value.version !== "1" ||
    !identifier(value.view_id) ||
    Object.keys(value).some(
      (key) =>
        !["version", "view_id", "process", "run_id", "interface"].includes(key),
    ) ||
    (value.run_id !== undefined && !identifier(value.run_id))
  )
    return invalid();
  const process = assertProcessReference(value.process);
  if (
    (workspaceId !== undefined && process.workspace_id !== workspaceId) ||
    (process.source_contract !== undefined &&
      process.source_contract !== "canonical-source")
  )
    return invalid();
  return {
    version: "1",
    view_id: value.view_id,
    process,
    ...(value.run_id !== undefined ? { run_id: value.run_id } : {}),
    ...(value.interface !== undefined
      ? { interface: checkedProcessInterfaceLocator(value.interface) }
      : {}),
  };
}

export function createProcessWorkspaceTab(
  process: ProcessRef,
  options: {
    runId?: string;
    viewId?: string;
    name?: string;
    interface?: ProcessInterfaceLocator;
  } = {},
): ProcessWorkspaceTab {
  const processView = checkedProcessWorkspaceView({
    version: "1",
    view_id: options.viewId ?? crypto.randomUUID(),
    process,
    ...(options.runId !== undefined ? { run_id: options.runId } : {}),
    ...(options.interface !== undefined
      ? { interface: options.interface }
      : {}),
  });
  return {
    type: "process",
    name:
      options.name ||
      `${options.interface?.kind === "preview" ? "Interface preview" : "Working view"} · ${
        process.source_path
          .split("/")
          .at(-1)
          ?.replace(/\.workflow\.wflow$/i, ".wflow") || "Process"
      }`,
    path: processWorkspaceTabPath(processView.view_id),
    isDirty: false,
    processView,
  };
}

/** Restore into the current workspace, never into a locator-supplied workspace. */
export function checkedProcessWorkspaceTab(
  value: unknown,
  workspaceId?: string,
): ProcessWorkspaceTab {
  if (!object(value) || value.type !== "process") return invalid();
  const processView = checkedProcessWorkspaceView(
    value.processView,
    workspaceId,
  );
  if (
    value.path !== processWorkspaceTabPath(processView.view_id) ||
    typeof value.name !== "string" ||
    value.name.length === 0 ||
    value.name.length > 256 ||
    value.last_modified !== undefined ||
    Object.keys(value).some(
      (key) =>
        ![
          "type",
          "name",
          "path",
          "isDirty",
          "last_modified",
          "processView",
        ].includes(key),
    )
  )
    return invalid();
  return {
    type: "process",
    name: value.name,
    path: value.path,
    isDirty: false,
    processView,
  };
}

/** Evidence navigation needs the common reader, not an arbitrary tailored tab. */
export function findCommonProcessWorkspaceTab(
  tabs: readonly EditorTab[],
  process: ProcessRef,
  runId: string | undefined,
): ProcessWorkspaceTab | undefined {
  const candidate = tabs.find(
    (tab) =>
      tab.type === "process" &&
      tab.processView &&
      !tab.processView.interface &&
      sameProcessReference(tab.processView.process, process) &&
      tab.processView.run_id === runId,
  );
  return candidate
    ? checkedProcessWorkspaceTab(candidate, process.workspace_id)
    : undefined;
}

/** Preserve the other workspace/file/editor query parameters. */
export function processWorkspaceQuery(
  search: string,
  tab?: ProcessWorkspaceTab,
): string {
  const query = new URLSearchParams(search);
  for (const key of queryKeys) query.delete(key);
  if (tab) {
    const view = checkedProcessWorkspaceTab(tab).processView;
    query.set("processView", view.view_id);
    query.set("processPath", view.process.source_path);
    query.set("processDigest", view.process.source_digest);
    if (view.run_id) query.set("processRun", view.run_id);
    if (view.interface) {
      query.set("processUIKind", view.interface.kind);
      query.set("processUI", view.interface.ui_id);
      query.set("processUIRevision", view.interface.revision_id);
      if (view.interface.kind === "preview")
        query.set("processUIJob", view.interface.job_id);
    }
  }
  return query.size ? `?${query.toString()}` : "";
}

/** Parse untrusted locators. The normal scoped read still authorizes every reply. */
export function processWorkspaceTabFromQuery(
  search: string,
  workspaceId: string,
): ProcessWorkspaceTab | null {
  const query = new URLSearchParams(search);
  if (!queryKeys.some((key) => query.has(key))) return null;
  if (
    queryKeys.some((key) => query.getAll(key).length > 1) ||
    !identifier(query.get("processView")) ||
    !query.has("processPath") ||
    !query.has("processDigest")
  )
    return invalid();
  const hasInterface = [
    "processUIKind",
    "processUI",
    "processUIRevision",
    "processUIJob",
  ].some((key) => query.has(key));
  const app = hasInterface
    ? checkedProcessInterfaceLocator({
        kind: query.get("processUIKind"),
        ui_id: query.get("processUI"),
        revision_id: query.get("processUIRevision"),
        ...(query.has("processUIJob")
          ? { job_id: query.get("processUIJob") }
          : {}),
      })
    : undefined;
  return createProcessWorkspaceTab(
    {
      workspace_id: workspaceId,
      source_path: query.get("processPath")!,
      source_digest: query.get("processDigest")!,
    },
    {
      viewId: query.get("processView")!,
      ...(query.has("processRun") ? { runId: query.get("processRun")! } : {}),
      ...(app ? { interface: app } : {}),
    },
  );
}
