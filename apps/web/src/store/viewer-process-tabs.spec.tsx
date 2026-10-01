import { act, render } from "@testing-library/react";
import { useEffect } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createProcessWorkspaceTab } from "../services/process-workspace-tabs";
import {
  dedupeEditorTabs,
  useViewerPanel,
  ViewerPanelProvider,
} from "./viewer";

vi.mock("./sessions", () => ({
  useChat: () => ({ state: { activeSessionId: "session-one" } }),
}));
const process = {
  workspace_id: "workspace-one",
  source_path: "workflows/one.workflow.wflow",
  source_digest: "a".repeat(64),
};
const working = createProcessWorkspaceTab(process, { viewId: "view-one" });
const document = { type: "md", path: "/notes.md", name: "notes.md" };
let viewer: ReturnType<typeof useViewerPanel>;
function Probe() {
  const current = useViewerPanel();
  useEffect(() => {
    viewer = current;
  }, [current]);
  return null;
}

describe("process documents in the existing viewer store", () => {
  beforeEach(() => {
    render(
      <ViewerPanelProvider>
        <Probe />
      </ViewerPanelProvider>,
    );
  });

  it("shares the existing strip with normal files and deduplicates the same view", () => {
    act(() => {
      viewer.openTransientTab(document);
      viewer.openTransientTab(working);
      viewer.openTransientTab(working);
    });
    expect(viewer.openTabs.map((tab) => tab.path)).toEqual([
      document.path,
      working.path,
    ]);
    expect(viewer.activeTabPath).toBe(working.path);
    expect(dedupeEditorTabs(viewer.openTabs)).toHaveLength(2);
  });

  it("records an accepted run without changing tab identity or focus", () => {
    act(() => {
      viewer.openTransientTab(working);
      viewer.openTransientTab(document);
    });
    act(() => viewer.attachProcessTabRun(working.path, process, "run-one"));
    expect(
      viewer.openTabs.find((tab) => tab.path === working.path)?.processView
        ?.run_id,
    ).toBe("run-one");
    expect(viewer.activeTabPath).toBe(document.path);
  });

  it("ignores a late receipt after a tab closes", () => {
    act(() => {
      viewer.openTransientTab(document);
      viewer.openTransientTab(working);
    });
    act(() => viewer.closeTab(working.path));
    act(() => viewer.attachProcessTabRun(working.path, process, "late-run"));
    expect(viewer.openTabs.map((tab) => tab.path)).toEqual([document.path]);
    expect(viewer.activeTabPath).toBe(document.path);
  });

  it.each([
    { ...process, workspace_id: "other" },
    { ...process, source_path: "workflows/other.workflow.wflow" },
    { ...process, source_digest: "b".repeat(64) },
  ])("cannot attach a receipt for a different process %j", (other) => {
    act(() => viewer.openTransientTab(working));
    act(() => viewer.attachProcessTabRun(working.path, other, "other-run"));
    expect(viewer.openTabs[0]?.processView?.run_id).toBeUndefined();
  });

  it("keeps a recorded view attached to its original run", () => {
    act(() => viewer.openTransientTab(working));
    act(() => viewer.attachProcessTabRun(working.path, process, "run-one"));
    act(() => viewer.attachProcessTabRun(working.path, process, "run-two"));
    expect(viewer.openTabs[0]?.processView?.run_id).toBe("run-one");
  });

  it("cannot overwrite a recorded view with a preparation locator or another process", () => {
    act(() => viewer.openTransientTab(working));
    act(() => viewer.attachProcessTabRun(working.path, process, "run-one"));
    act(() => viewer.openTransientTab(working));
    act(() =>
      viewer.openTransientTab(
        createProcessWorkspaceTab(
          { ...process, source_digest: "b".repeat(64) },
          { viewId: "view-one", runId: "run-one" },
        ),
      ),
    );
    expect(viewer.openTabs[0]?.processView?.run_id).toBe("run-one");
    expect(viewer.openTabs[0]?.processView?.process.source_digest).toBe(
      process.source_digest,
    );
  });

  it("rejects reserved virtual paths presented as ordinary files", () => {
    expect(() =>
      viewer.openTransientTab({ ...document, path: working.path }),
    ).toThrow();
    expect(viewer.openTabs).toEqual([]);
  });

  it("can close one view without disturbing another view of the process", () => {
    const other = createProcessWorkspaceTab(process, {
      viewId: "view-two",
      runId: "run-two",
    });
    act(() => {
      viewer.openTransientTab(working);
      viewer.openTransientTab(other);
    });
    act(() => viewer.closeTab(working.path));
    expect(viewer.openTabs[0]?.processView?.run_id).toBe("run-two");
    expect(viewer.activeTabPath).toBe(other.path);
  });

  it("clears view locators on workspace reset without calling an executor", () => {
    act(() => viewer.openTransientTab(working));
    act(() => viewer.resetViewer());
    expect(viewer.openTabs).toEqual([]);
    expect(viewer.activeTabPath).toBeNull();
  });
});
