import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { BlockNameHeading, WorkflowNameHeading } from "./BlockNameHeading";

describe.each(["workflow", "block"] as const)("%s name heading", (kind) => {
  const Component =
    kind === "workflow" ? WorkflowNameHeading : BlockNameHeading;
  const label = kind === "workflow" ? "Workflow name" : "Block name";

  it("applies a trimmed name on Enter and exposes the accepted heading", async () => {
    const onRename = vi.fn(() => true);
    const props = {
      title: "Original",
      readOnly: false,
      onRename,
      fileTitle: "File · Saved",
    };
    const view = render(<Component {...props} />);
    const input = screen.getByRole("textbox", { name: label });
    await userEvent.click(input);
    await userEvent.keyboard("  Engineering review  {Enter}");
    expect(onRename).toHaveBeenCalledExactlyOnceWith("Engineering review");
    expect(input).toHaveValue("Engineering review");
    view.rerender(<Component {...props} title="Engineering review" />);
    expect(
      screen.getByRole("heading", { name: "Engineering review" }),
    ).toBeVisible();
    view.rerender(<Component {...props} title="Restored by Undo" />);
    expect(input).toHaveValue("Restored by Undo");
  });

  it("discards Escape and blank edits without issuing a command", async () => {
    const onRename = vi.fn(() => true);
    render(
      <Component
        title="Original"
        readOnly={false}
        onRename={onRename}
        fileTitle="File"
      />,
    );
    const input = screen.getByRole("textbox", { name: label });
    await userEvent.click(input);
    await userEvent.keyboard("Discard{Escape}");
    expect(input).toHaveValue("Original");
    await userEvent.clear(input);
    await userEvent.tab();
    expect(input).toHaveValue("Original");
    expect(onRename).not.toHaveBeenCalled();
  });

  it("restores the accepted name when the command is rejected", async () => {
    const onRename = vi.fn(() => false);
    render(
      <Component
        title="Original"
        readOnly={false}
        onRename={onRename}
        fileTitle="File"
      />,
    );
    await userEvent.click(screen.getByRole("textbox", { name: label }));
    await userEvent.keyboard("Rejected{Enter}");
    expect(screen.getByRole("textbox", { name: label })).toHaveValue(
      "Original",
    );
    expect(onRename).toHaveBeenCalledExactlyOnceWith("Rejected");
  });

  it("keeps a locked name readable without authoring commands", async () => {
    const onRename = vi.fn(() => true);
    render(
      <Component
        title="Original"
        readOnly
        onRename={onRename}
        fileTitle="File"
      />,
    );
    const input = screen.getByRole("textbox", { name: label });
    expect(input).toHaveAttribute("readonly");
    await userEvent.click(input);
    await userEvent.keyboard("Replacement{Enter}");
    expect(input).toHaveValue("Original");
    expect(onRename).not.toHaveBeenCalled();
  });
});
