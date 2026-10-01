import { describe, expect, it } from "vitest";
import type { ProcessRef } from "@wright/process-client";
import {
  checkedProcessWorkspaceTab,
  checkedProcessWorkspaceView,
  createProcessWorkspaceTab,
  isProcessWorkspaceTabPath,
  processWorkspaceQuery,
  processWorkspaceTabFromQuery,
} from "./process-workspace-tabs";

const process: ProcessRef = {
  workspace_id: "workspace-one",
  source_path: "workflows/thermal.workflow.wflow",
  source_digest: "a".repeat(64),
};
const tab = createProcessWorkspaceTab(process, {
  viewId: "view-one",
  runId: "run-one",
});

describe("workspace process locators", () => {
  it("creates a typed tab with no user input, credentials or browser run state", () => {
    expect(tab).toEqual({
      type: "process",
      path: "/.wright/process-views/view-one",
      name: "thermal.wflow · working view",
      isDirty: false,
      processView: {
        version: "1",
        view_id: "view-one",
        process,
        run_id: "run-one",
      },
    });
    expect(isProcessWorkspaceTabPath(tab.path)).toBe(true);
    expect(isProcessWorkspaceTabPath("/workflows/thermal.workflow.wflow")).toBe(
      false,
    );
  });

  it("preserves source identity and accepts only a current-workspace restoration", () => {
    expect(
      checkedProcessWorkspaceTab(
        JSON.parse(JSON.stringify(tab)),
        process.workspace_id,
      ),
    ).toEqual(tab);
    expect(() => checkedProcessWorkspaceTab(tab, "other-workspace")).toThrow();
  });

  it("discards the generic dirty marker when reopening a process view", () => {
    expect(checkedProcessWorkspaceTab({ ...tab, isDirty: true }).isDirty).toBe(
      false,
    );
  });

  it.each([
    { version: "2" },
    { view_id: "../other" },
    { view_id: "" },
    { run_id: "" },
    { run_id: "../outside" },
    { state: "completed" },
    { inputs: [{ value: "secret" }] },
    { permissions: ["admin"] },
    { process: { ...process, source_contract: "another-executor" } },
    { process: { ...process, source_path: "../outside.wflow" } },
    { process: { ...process, source_digest: "not-a-hash" } },
    { process: { ...process, token: "secret" } },
  ])("rejects malformed or authority-bearing locators %j", (extra) => {
    expect(() =>
      checkedProcessWorkspaceView({ ...tab.processView, ...extra }),
    ).toThrow();
  });

  it.each([
    { type: "code" },
    { path: "/.wright/process-views/another-view" },
    { name: "" },
    { name: "a".repeat(257) },
    { token: "secret" },
    { last_modified: 42 },
  ])("rejects incompatible persisted tabs %j", (extra) => {
    expect(() => checkedProcessWorkspaceTab({ ...tab, ...extra })).toThrow();
  });

  it("round-trips links while preserving editor/file context", () => {
    const search = processWorkspaceQuery(
      "?workflow=canonical&workflowPath=workflows%2Fthermal.workflow.wflow&other=keep",
      tab,
    );
    const query = new URLSearchParams(search);
    expect(query.get("other")).toBe("keep");
    expect(query.get("workflow")).toBe("canonical");
    expect(processWorkspaceTabFromQuery(search, process.workspace_id)).toEqual(
      tab,
    );
    expect(processWorkspaceQuery(search)).toBe(
      "?workflow=canonical&workflowPath=workflows%2Fthermal.workflow.wflow&other=keep",
    );
  });

  it("derives workspace scope from the host rather than a query parameter", () => {
    const search = `${processWorkspaceQuery("", tab)}&workspace_id=attacker-workspace`;
    expect(
      processWorkspaceTabFromQuery(search, "host-workspace")?.processView
        .process.workspace_id,
    ).toBe("host-workspace");
  });

  it("does not invent a run identifier for a preparation view", () => {
    const prepare = createProcessWorkspaceTab(process, {
      viewId: "view-prepare",
    });
    const restored = processWorkspaceTabFromQuery(
      processWorkspaceQuery("", prepare),
      process.workspace_id,
    )!;
    expect(restored.processView.run_id).toBeUndefined();
    expect(restored.path).toBe(prepare.path);
  });

  it("replaces only process locators when switching views", () => {
    const other = createProcessWorkspaceTab(process, {
      viewId: "another-view",
    });
    const search = processWorkspaceQuery(
      processWorkspaceQuery("?workflow=canonical", tab),
      other,
    );
    expect(processWorkspaceTabFromQuery(search, process.workspace_id)).toEqual(
      other,
    );
    expect(new URLSearchParams(search).has("processRun")).toBe(false);
  });

  it.each([
    "?processView=view-one",
    "?processRun=run-one",
    "?processPath=workflows%2Fone.wflow&processDigest=" + "a".repeat(64),
    processWorkspaceQuery("", tab) + "&processRun=another-run",
    processWorkspaceQuery("", tab) + "&processView=another-view",
    processWorkspaceQuery("", tab).replace("processRun=run-one", "processRun="),
  ])("rejects incomplete/ambiguous query locators %s", (search) => {
    expect(() =>
      processWorkspaceTabFromQuery(search, process.workspace_id),
    ).toThrow();
  });

  it("leaves normal file/editor navigation alone", () => {
    expect(
      processWorkspaceTabFromQuery("?workflow=canonical", process.workspace_id),
    ).toBeNull();
    expect(processWorkspaceQuery("")).toBe("");
  });
});
