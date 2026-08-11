import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceActivityBar } from "./WorkspaceActivityBar";

describe("WorkspaceActivityBar", () => {
  it("places BREP third and opens its Wright panel", async () => {
    const user = userEvent.setup();
    const onOpenBrepPanel = vi.fn();
    const onSelectSidebar = vi.fn();

    const { container } = render(
      <WorkspaceActivityBar
        activeSidebar="files"
        isSidebarCollapsed={false}
        onBack={vi.fn()}
        onSelectSidebar={onSelectSidebar}
        onOpenRivetEditor={vi.fn()}
        onOpenBrepPanel={onOpenBrepPanel}
        workflowsEnabled
      />,
    );

    expect(
      [...container.querySelectorAll("button.activity-bar-icon")]
        .slice(1)
        .map((button) => button.getAttribute("data-testid")),
    ).toEqual([
      "activity-bar-explorer-btn",
      "activity-bar-workflows-btn",
      "activity-bar-brep-btn",
      "activity-bar-mcp-btn",
      "activity-bar-git-btn",
      "activity-bar-settings-btn",
      "activity-bar-docs-btn",
    ]);

    await user.click(screen.getByTestId("activity-bar-brep-btn"));

    expect(onOpenBrepPanel).toHaveBeenCalledOnce();
    expect(onSelectSidebar).not.toHaveBeenCalled();
  });
});
