import { describe, expect, it } from "vitest";
import {
  checkedInterfaceAuthoringIntent,
  createInterfaceAuthoringRecoveryStore,
} from "./process-ui-authoring-recovery";
import { authoringProcess as process } from "../../tests/fixtures/process-ui-authoring";
const intent = {
  version: "1" as const,
  process,
  request: {
    request_id: "request-one",
    instruction: "Show findings",
    title: "Comparison",
  },
  job_id: "job-one",
};
const storage = () => {
  const data = new Map<string, string>();
  return {
    getItem: (key: string) => data.get(key) ?? null,
    setItem: (key: string, value: string) => {
      data.set(key, value);
    },
    removeItem: (key: string) => {
      data.delete(key);
    },
  };
};
describe("interface authoring request locators", () => {
  it("retains an imported source digest without adding active local authority", () => {
    const imported = {
      ...intent,
      request: {
        ...intent.request,
        imported_interface: { ui_id: "foreign-ui", sha256: "a".repeat(64) },
      },
    };
    expect(checkedInterfaceAuthoringIntent(imported, process)).toEqual(
      imported,
    );
  });
  it.each([
    { ui_id: "foreign", sha256: "bad" },
    { ui_id: "../foreign", sha256: "a".repeat(64) },
    { ui_id: "foreign", sha256: "a".repeat(64), build: "trusted" },
  ])("rejects malformed imported source selection %j", (imported_interface) => {
    expect(() =>
      checkedInterfaceAuthoringIntent(
        { ...intent, request: { ...intent.request, imported_interface } },
        process,
      ),
    ).toThrow();
  });
  it("rejects importing and updating a local revision in the same request", () => {
    expect(() =>
      checkedInterfaceAuthoringIntent(
        {
          ...intent,
          request: {
            ...intent.request,
            ui_id: "local",
            base_revision: "local-revision",
            imported_interface: { ui_id: "foreign", sha256: "a".repeat(64) },
          },
        },
        process,
      ),
    ).toThrow();
  });
  it("retains the explicit request/job locator and isolates workspace/source/session/view", () => {
    const target = storage(),
      store = createInterfaceAuthoringRecoveryStore(
        process,
        "session",
        "view",
        target,
      );
    store.write(intent);
    expect(store.read()).toEqual(intent);
    for (const [source, session, view] of [
      [{ ...process, workspace_id: "other" }, "session", "view"],
      [{ ...process, source_digest: "b".repeat(64) }, "session", "view"],
      [process, "other-session", "view"],
      [process, "session", "other-view"],
    ] as const)
      expect(
        createInterfaceAuthoringRecoveryStore(
          source,
          session,
          view,
          target,
        ).read(),
      ).toBeNull();
    store.clear();
    expect(store.read()).toBeNull();
  });
  it.each([
    { process: { ...process, workspace_id: "other" } },
    { process: { ...process, source_digest: "b".repeat(64) } },
    { job_id: "../foreign" },
    { grant: "administrator" },
    { request: { ...intent.request, invokeTool: "forbidden" } },
    { request: { ...intent.request, ui_id: "chosen" } },
    { request: { ...intent.request, instruction: "é".repeat(9000) } },
  ])("rejects malformed or widened recovery data %j", (change) => {
    expect(() =>
      checkedInterfaceAuthoringIntent({ ...intent, ...change }, process),
    ).toThrow();
  });
  it("reports unavailable storage rather than losing request identity silently", () => {
    const target = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("blocked");
      },
      removeItem: () => {
        throw new Error("blocked");
      },
    };
    const store = createInterfaceAuthoringRecoveryStore(
      process,
      "session",
      "view",
      target,
    );
    expect(() => store.read()).toThrow();
    expect(() => store.write(intent)).toThrow();
    expect(() => store.clear()).toThrow();
  });
  it("keeps the registered scope when a caller mutates its original process object", () => {
    const source = { ...process },
      target = storage(),
      store = createInterfaceAuthoringRecoveryStore(
        source,
        "session",
        "view",
        target,
      );
    store.write(intent);
    source.workspace_id = "foreign-workspace";
    expect(store.read()).toEqual(intent);
  });
});
