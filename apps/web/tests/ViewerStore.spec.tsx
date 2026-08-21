import { render, screen, waitFor } from "@testing-library/react";
import { useEffect, useRef } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  dedupeEditorTabs,
  normalizeEditorTabPath,
  useViewerPanel,
  ViewerPanelProvider,
} from "../src/store/viewer";

const mockUseChat = vi.fn();

vi.mock("../src/store/sessions", () => ({
  useChat: () => mockUseChat(),
}));

function OpenDuplicateTabsHarness() {
  const viewer = useViewerPanel();

  useEffect(() => {
    void viewer.openTab({
      id: "specification.md",
      uri: "specification.md",
      name: "specification.md",
      extension: "unknown",
      mimeType: "text/plain",
    });
    void viewer.openTab({
      id: "/specification.md",
      uri: "/specification.md",
      name: "specification.md",
      extension: "unknown",
      mimeType: "text/plain",
    });
  }, [viewer]);

  return (
    <div>
      <span data-testid="tab-count">{viewer.openTabs.length}</span>
      <span data-testid="active-tab">{viewer.activeTabPath}</span>
      {viewer.openTabs.map((tab) => (
        <span key={tab.path}>{tab.name}</span>
      ))}
    </div>
  );
}

function OpenSingleTabHarness() {
  const viewer = useViewerPanel();

  useEffect(() => {
    void viewer.openTab({
      id: "lessons.viewer",
      uri: "lessons.viewer",
      name: "lessons.viewer",
      extension: "unknown",
      mimeType: "text/plain",
    });
  }, [viewer]);

  return (
    <div>
      <span data-testid="tab-count">{viewer.openTabs.length}</span>
      <span data-testid="active-tab">{viewer.activeTabPath}</span>
    </div>
  );
}

function RenameTransientTabHarness() {
  const viewer = useViewerPanel();
  const initialUpdateTabPath = useRef(viewer.updateTabPath);

  return (
    <div>
      <button
        type="button"
        onClick={() => {
          viewer.openTransientTab({
            name: "rivet.rivet-project",
            path: "/.wright/rivet-workflows/rivet/workflow.rivet-project",
            type: "rivet",
          });
          queueMicrotask(() =>
            initialUpdateTabPath.current(
              "/.wright/rivet-workflows/rivet/workflow.rivet-project",
              "/.wright/rivet-workflows/ai-agent/workflow.rivet-project",
              "ai-agent.rivet-project",
            ),
          );
        }}
      >
        Open Rivet
      </button>
      <span data-testid="active-tab">{viewer.activeTabPath}</span>
    </div>
  );
}

describe("ViewerPanelProvider tab state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChat.mockReturnValue({
      state: {
        activeSessionId: "session-1",
      },
    });
  });

  it("normalizes and deduplicates persisted editor tabs", () => {
    expect(normalizeEditorTabPath("specification.md")).toBe(
      "/specification.md",
    );
    expect(normalizeEditorTabPath("\\tmp\\specification.md")).toBe(
      "/tmp/specification.md",
    );

    const tabs = dedupeEditorTabs([
      { name: "specification.md", path: "specification.md", type: "md" },
      {
        name: "specification.md",
        path: "/specification.md",
        type: "md",
        isDirty: true,
        last_modified: 2,
      },
      {
        name: "specification.md",
        path: "//specification.md",
        type: "md",
        last_modified: 1,
      },
    ]);

    expect(tabs).toEqual([
      {
        name: "specification.md",
        path: "/specification.md",
        type: "md",
        isDirty: true,
        last_modified: 2,
      },
    ]);
  });

  it("keeps duplicate opens from creating multiple visible tabs", async () => {
    render(
      <ViewerPanelProvider>
        <OpenDuplicateTabsHarness />
      </ViewerPanelProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("tab-count")).toHaveTextContent("1");
    });
    expect(screen.getByTestId("active-tab")).toHaveTextContent(
      "/specification.md",
    );
    expect(screen.getAllByText("specification.md")).toHaveLength(1);
  });

  it("keeps viewer tabs open when switching sessions in the same workspace", async () => {
    const { rerender } = render(
      <ViewerPanelProvider>
        <OpenSingleTabHarness />
      </ViewerPanelProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("tab-count")).toHaveTextContent("1");
    });
    expect(screen.getByTestId("active-tab")).toHaveTextContent(
      "/lessons.viewer",
    );

    mockUseChat.mockReturnValue({
      state: {
        activeSessionId: "session-2",
      },
    });

    rerender(
      <ViewerPanelProvider>
        <OpenSingleTabHarness />
      </ViewerPanelProvider>,
    );

    expect(screen.getByTestId("tab-count")).toHaveTextContent("1");
    expect(screen.getByTestId("active-tab")).toHaveTextContent(
      "/lessons.viewer",
    );
  });

  it("keeps an asynchronously renamed transient tab active", async () => {
    render(
      <ViewerPanelProvider>
        <RenameTransientTabHarness />
      </ViewerPanelProvider>,
    );

    screen.getByRole("button", { name: "Open Rivet" }).click();

    await waitFor(() =>
      expect(screen.getByTestId("active-tab")).toHaveTextContent(
        "/.wright/rivet-workflows/ai-agent/workflow.rivet-project",
      ),
    );
  });
});
