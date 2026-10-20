/** Optional, widget-scoped navigation hints. Never process or permission state. */
export type HomeView = "workflows" | "connections" | "files" | "runs";
/** Exact read target, not a saved run status or a grant to resume execution. */
export interface NativeWorkflowLocation {
  path: string;
  source_digest: string;
  view: "editor" | "working";
  run_id?: string;
}
export interface NativeNavigationState {
  schema_version: "wright.native-navigation/1";
  workspace_id: string;
  session_id: string;
  view: HomeView;
  workflow?: NativeWorkflowLocation;
}
interface WidgetApi {
  widgetState?: unknown;
  setWidgetState?: (state: Record<string, unknown>) => void;
}
const object = (value: unknown): Record<string, unknown> | undefined =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
function widget(): WidgetApi | undefined {
  return (window as unknown as { openai?: WidgetApi }).openai;
}
export function workflowLocation(
  value: unknown,
): NativeWorkflowLocation | undefined {
  const data = object(value);
  if (
    !data ||
    Object.keys(data).some(
      (key) => !["path", "source_digest", "view", "run_id"].includes(key),
    ) ||
    typeof data.path !== "string" ||
    data.path.length > 1024 ||
    !data.path.startsWith("workflows/") ||
    !data.path.endsWith(".wflow") ||
    [...data.path].some(
      (character) => character === "\\" || character.charCodeAt(0) < 32,
    ) ||
    data.path
      .split("/")
      .some((part) => !part || part === "." || part === "..") ||
    typeof data.source_digest !== "string" ||
    !/^[a-f0-9]{64}$/.test(data.source_digest) ||
    !["editor", "working"].includes(String(data.view)) ||
    (data.run_id !== undefined &&
      (typeof data.run_id !== "string" ||
        !/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(data.run_id)))
  )
    return;
  return data as unknown as NativeWorkflowLocation;
}
export function navigationState(
  value: unknown,
): NativeNavigationState | undefined {
  const data = object(value);
  if (
    !data ||
    data.schema_version !== "wright.native-navigation/1" ||
    Object.keys(data).some(
      (key) =>
        ![
          "schema_version",
          "workspace_id",
          "session_id",
          "view",
          "workflow",
        ].includes(key),
    ) ||
    typeof data.workspace_id !== "string" ||
    typeof data.session_id !== "string" ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(data.workspace_id) ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(data.session_id) ||
    !["workflows", "connections", "files", "runs"].includes(
      String(data.view),
    ) ||
    (data.workflow !== undefined && !workflowLocation(data.workflow))
  )
    return;
  return data as unknown as NativeNavigationState;
}
export function readNavigationState(): NativeNavigationState | undefined {
  try {
    const api = widget();
    if (typeof api?.setWidgetState !== "function") return;
    const saved = object(api.widgetState);
    return navigationState(object(saved?.privateContent)?.wrightNavigation);
  } catch {
    return;
  }
}
export function rememberNavigationState(state: NativeNavigationState): boolean {
  try {
    const api = widget();
    if (typeof api?.setWidgetState !== "function" || !navigationState(state))
      return false;
    const previous = object(api.widgetState) ?? {};
    api.setWidgetState({
      ...previous,
      privateContent: {
        ...(object(previous.privateContent) ?? {}),
        wrightNavigation: state,
      },
    });
    return true;
  } catch {
    return false;
  }
}
