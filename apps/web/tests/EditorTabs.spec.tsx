import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import EditorTabs from "../src/components/chat/EditorTabs";

describe("EditorTabs", () => {
  it("renders a visible accessible close button for each tab", () => {
    const onCloseTab = vi.fn();

    render(
      <EditorTabs
        tabs={[{ name: "iPhone7Case2.stl", path: "/iPhone7Case2.stl", type: "stl" }]}
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
