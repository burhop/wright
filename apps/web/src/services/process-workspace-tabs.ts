import {
  assertProcessReference,
  ProcessClientError,
  type ProcessRef,
} from "@wright/process-client";
import type { EditorTab } from "../store/viewer";

/** Presentation locators only. No inputs, permissions or execution state live here. */
export interface ProcessWorkspaceView {
  readonly version: "1";
  readonly view_id: string;
  readonly process: ProcessRef;
  readonly run_id?: string;
}

export interface ProcessWorkspaceTab extends EditorTab {
  readonly type: "process";
  readonly processView: ProcessWorkspaceView;
}

const prefix = "/.wright/process-views/";
const queryKeys = ["processView", "processPath", "processDigest", "processRun"];
const object = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === "object" && !Array.isArray(value);
const identifier = (value: unknown): value is string =>
  typeof value === "string" && /^[a-z0-9][a-z0-9._:-]{0,159}$/i.test(value);

function invalid(): never {
  throw new ProcessClientError({
    code: "UI_INCOMPATIBLE",
    message: "This working view could not be reopened.",
    correction:
      "Open the saved process and choose Use saved process, or reopen its recorded run. No run was started.",
  });
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
      (key) => !["version", "view_id", "process", "run_id"].includes(key),
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
  };
}

export function createProcessWorkspaceTab(
  process: ProcessRef,
  options: { runId?: string; viewId?: string; name?: string } = {},
): ProcessWorkspaceTab {
  const processView = checkedProcessWorkspaceView({
    version: "1",
    view_id: options.viewId ?? crypto.randomUUID(),
    process,
    ...(options.runId !== undefined ? { run_id: options.runId } : {}),
  });
  return {
    type: "process",
    name:
      options.name ||
      `${
        process.source_path
          .split("/")
          .at(-1)
          ?.replace(/\.workflow\.wflow$/i, ".wflow") || "Process"
      } · working view`,
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
  return createProcessWorkspaceTab(
    {
      workspace_id: workspaceId,
      source_path: query.get("processPath")!,
      source_digest: query.get("processDigest")!,
    },
    {
      viewId: query.get("processView")!,
      ...(query.has("processRun") ? { runId: query.get("processRun")! } : {}),
    },
  );
}
