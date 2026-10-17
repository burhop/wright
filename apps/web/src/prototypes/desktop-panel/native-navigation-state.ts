/** Optional, widget-scoped navigation hints. Never process or permission state. */
export type HomeView = "workflows" | "connections" | "files" | "runs";
export interface NativeNavigationState {
  schema_version: "wright.native-navigation/1";
  workspace_id: string;
  session_id: string;
  view: HomeView;
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
export function navigationState(
  value: unknown,
): NativeNavigationState | undefined {
  const data = object(value);
  if (
    !data ||
    data.schema_version !== "wright.native-navigation/1" ||
    Object.keys(data).some(
      (key) =>
        !["schema_version", "workspace_id", "session_id", "view"].includes(key),
    ) ||
    typeof data.workspace_id !== "string" ||
    typeof data.session_id !== "string" ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(data.workspace_id) ||
    !/^[A-Za-z0-9._:-]{1,128}$/.test(data.session_id) ||
    !["workflows", "connections", "files", "runs"].includes(String(data.view))
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
