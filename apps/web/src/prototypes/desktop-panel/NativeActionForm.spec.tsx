import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { NativeActionForm } from "./NativeActionForm";

afterEach(cleanup);
it("uses explicit click and Enter while retaining validation and multiline editing", () => {
  const action = vi.fn();
  render(
    <NativeActionForm onAction={action}>
      <input aria-label="Name" required />
      <textarea aria-label="Notes" />
      <button type="submit">Save</button>
      <button type="button">Other action</button>
    </NativeActionForm>,
  );
  fireEvent.click(screen.getByText("Save"));
  expect(action).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Name"), {
    target: { value: "Handle" },
  });
  fireEvent.click(screen.getByText("Save"));
  expect(action).toHaveBeenCalledTimes(1);
  fireEvent.keyDown(screen.getByLabelText("Name"), { key: "Enter" });
  expect(action).toHaveBeenCalledTimes(2);
  fireEvent.keyDown(screen.getByLabelText("Notes"), { key: "Enter" });
  fireEvent.keyDown(screen.getByLabelText("Name"), {
    key: "Enter",
    isComposing: true,
  });
  fireEvent.click(screen.getByText("Other action"));
  expect(action).toHaveBeenCalledTimes(2);
});
it("does not submit while the action is disabled", () => {
  const action = vi.fn();
  render(
    <NativeActionForm onAction={action}>
      <input aria-label="Name" defaultValue="Handle" />
      <button type="submit" disabled>
        Save
      </button>
    </NativeActionForm>,
  );
  fireEvent.keyDown(screen.getByLabelText("Name"), { key: "Enter" });
  fireEvent.click(screen.getByText("Save"));
  expect(action).not.toHaveBeenCalled();
});
