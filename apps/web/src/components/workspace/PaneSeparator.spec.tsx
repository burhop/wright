import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PaneSeparator } from "./PaneSeparator";

describe("PaneSeparator", () => {
  it("exposes bounded container-relative ARIA values", () => {
    render(
      <PaneSeparator
        valueBasisPoints={3800}
        minimumBasisPoints={3200}
        maximumBasisPoints={5200}
        onChange={vi.fn()}
      />,
    );
    const separator = screen.getByRole("separator", {
      name: "Resize chat and surface",
    });
    expect(separator).toHaveAttribute("aria-orientation", "vertical");
    expect(separator).toHaveAttribute("aria-valuemin", "32");
    expect(separator).toHaveAttribute("aria-valuemax", "52");
    expect(separator).toHaveAttribute("aria-valuenow", "38");
  });

  it("resizes by 2%, 10%, and exact bounds from the keyboard", async () => {
    const user = userEvent.setup();
    const change = vi.fn();
    render(
      <PaneSeparator
        valueBasisPoints={3800}
        minimumBasisPoints={3200}
        maximumBasisPoints={5200}
        onChange={change}
      />,
    );
    const separator = screen.getByRole("separator");
    separator.focus();

    await user.keyboard("{ArrowRight}{ArrowLeft}{PageUp}{PageDown}{Home}{End}");
    expect(change.mock.calls.map(([value]) => value)).toEqual([
      4000, 3600, 4800, 3200, 3200, 5200,
    ]);
  });
});
