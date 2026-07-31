import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ExternalUrlSurface } from "./ExternalUrlSurface";

const approval = {
  approvalId: "approval-1",
  normalizedUrl: "https://docs.example.test/guide",
  displayOrigin: "docs.example.test",
  reason: "Open the vendor documentation",
  expiresAt: "2026-07-30T12:05:00Z",
};

describe("ExternalUrlSurface", () => {
  it("is browser-only and discloses the missing Wright authority", async () => {
    const user = userEvent.setup();
    const openExternal = vi.fn().mockResolvedValue(undefined);
    const { container } = render(
      <ExternalUrlSurface approval={approval} openExternal={openExternal} />,
    );
    expect(container.querySelector("iframe")).toBeNull();
    expect(
      screen.getByText(/not sent through the Wright proxy/i),
    ).toBeVisible();
    expect(
      screen.getByText(
        /no Wright credentials, tool bridge, or managed lifecycle/i,
      ),
    ).toBeVisible();
    await user.click(screen.getByTestId("surface-external-open"));
    expect(openExternal).toHaveBeenCalledWith(approval.normalizedUrl);
  });
});
