import { afterEach, expect, it, vi } from "vitest";
import {
  navigationState,
  readNavigationState,
  rememberNavigationState,
  workflowLocation,
} from "./native-navigation-state";
const state = {
  schema_version: "wright.native-navigation/1" as const,
  workspace_id: "workspace-a",
  session_id: "chat-a",
  view: "connections" as const,
};
afterEach(() => {
  delete (window as unknown as { openai?: unknown }).openai;
});
it("retains an exact workflow/run read target without status or approval authority", () => {
  const location = {
    path: "workflows/part__one.workflow.wflow",
    source_digest: "a".repeat(64),
    view: "working" as const,
    run_id: "recorded-run",
  };
  expect(navigationState({ ...state, workflow: location })?.workflow).toEqual(
    location,
  );
  for (const patch of [
    { path: "workflows/../private.wflow" },
    { path: "workflows\\part.wflow" },
    { source_digest: "" },
    { run_id: "../other" },
    { status: "completed" },
    { approved: true },
    { view: "execute" },
  ]) {
    expect(workflowLocation({ ...location, ...patch })).toBeUndefined();
    expect(
      navigationState({ ...state, workflow: { ...location, ...patch } }),
    ).toBeUndefined();
  }
});
function host(value: unknown) {
  Object.defineProperty(window, "openai", { configurable: true, value });
}
it("stores only validated navigation in widget-private state and preserves other widget fields", () => {
  const api = {
    widgetState: {
      modelContent: "existing context",
      privateContent: { other: "kept" },
    },
    setWidgetState: vi.fn(),
  };
  host(api);
  expect(rememberNavigationState(state)).toBe(true);
  expect(api.setWidgetState).toHaveBeenCalledExactlyOnceWith({
    modelContent: "existing context",
    privateContent: { other: "kept", wrightNavigation: state },
  });
  api.widgetState = api.setWidgetState.mock.calls[0][0];
  expect(readNavigationState()).toEqual(state);
});
it("does not claim persistence for an absent, throwing or read-only optional host API", () => {
  expect(rememberNavigationState(state)).toBe(false);
  expect(readNavigationState()).toBeUndefined();
  host({ widgetState: { privateContent: { wrightNavigation: state } } });
  expect(readNavigationState()).toBeUndefined();
  expect(rememberNavigationState(state)).toBe(false);
  host({
    setWidgetState() {
      throw Error("unsupported");
    },
  });
  expect(rememberNavigationState(state)).toBe(false);
});
it.each([
  { run_id: "forbidden" },
  { source: "not UI state" },
  { approval: true },
  { workspace_id: "../escape" },
  { session_id: "" },
  { view: "run" },
  { schema_version: "unknown" },
])("rejects unsupported or authority-bearing snapshot fields %j", (patch) => {
  const api = {
    widgetState: {
      privateContent: { wrightNavigation: { ...state, ...patch } },
    },
    setWidgetState: vi.fn(),
  };
  host(api);
  expect(readNavigationState()).toBeUndefined();
  expect(navigationState({ ...state, ...patch })).toBeUndefined();
  expect(rememberNavigationState({ ...state, ...patch } as typeof state)).toBe(
    false,
  );
  expect(api.setWidgetState).not.toHaveBeenCalled();
});
