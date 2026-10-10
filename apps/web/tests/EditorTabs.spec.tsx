import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import EditorTabs from "../src/components/chat/EditorTabs";
import { createProcessWorkspaceTab } from "../src/services/process-workspace-tabs";

describe("EditorTabs", () => {
  it("holds tab closure until its pending save ends", () => {
    const onCloseTab = vi.fn();
    const tab = {
      name: "design.wflow",
      path: "/workflows/design.wflow",
      type: "workflow",
      isSaving: true,
    };
    const view = render(
      <EditorTabs
        tabs={[tab]}
        activeTabPath={tab.path}
        onSelectTab={vi.fn()}
        onCloseTab={onCloseTab}
      />,
    );
    const close = screen.getByRole("button", { name: "Close design.wflow" });
    expect(close).toBeDisabled();
    expect(close).toHaveStyle({ cursor: "wait", opacity: "0.35" });
    expect(close).toHaveAttribute(
      "title",
      "Wait for saving to finish before closing this tab.",
    );
    fireEvent.click(close);
    expect(onCloseTab).not.toHaveBeenCalled();
    view.rerender(
      <EditorTabs
        tabs={[{ ...tab, isSaving: false }]}
        activeTabPath={tab.path}
        onSelectTab={vi.fn()}
        onCloseTab={onCloseTab}
      />,
    );
    fireEvent.click(close);
    expect(onCloseTab).toHaveBeenCalledWith(tab.path);
  });
  it("shows the working-view label and exact recorded-run subject in the existing strip", () => {
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace",
        source_path: "workflows/one.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "view-one", runId: "run-one" },
    );
    render(
      <EditorTabs
        tabs={[tab]}
        activeTabPath={tab.path}
        onSelectTab={vi.fn()}
        onCloseTab={vi.fn()}
      />,
    );
    const document = screen.getByRole("tab", {
      name: "Working view · one.wflow",
    });
    expect(document).toHaveAttribute(
      "title",
      "workflows/one.workflow.wflow · run run-one",
    );
    expect(document).toHaveAttribute("aria-selected", "true");
    expect(
      screen.getByRole("button", { name: "Close Working view · one.wflow" }),
    ).toBeVisible();
  });
  it("renders a visible accessible close button for each tab", () => {
    const onCloseTab = vi.fn();

    render(
      <EditorTabs
        tabs={[
          { name: "iPhone7Case2.stl", path: "/iPhone7Case2.stl", type: "stl" },
        ]}
        activeTabPath="/iPhone7Case2.stl"
        onSelectTab={vi.fn()}
        onCloseTab={onCloseTab}
      />,
    );

    const closeButton = screen.getByRole("button", {
      name: "Close iPhone7Case2.stl",
    });

    expect(closeButton).toBeVisible();
    expect(closeButton.querySelector("svg")).toBeInTheDocument();

    fireEvent.click(closeButton);
    expect(onCloseTab).toHaveBeenCalledWith("/iPhone7Case2.stl");
  });
});
