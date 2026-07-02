import { render, screen, waitFor } from "@testing-library/react";
import { useEffect } from "react";
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
});
