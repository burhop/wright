import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  CapabilityDialog,
  type CapabilityConsentRequest,
} from "./CapabilityDialog";

const request: CapabilityConsentRequest = {
  sourceTitle: "BREP Designer",
  sourceId: "brep",
  sourceVersion: "2.4.1",
  workspaceName: "Gearbox",
  operation: "Read selected geometry",
  dataDescription: "At most 10 selected part identifiers; no file contents",
  risk: "high",
  reason: "Use the selected parts to update the active model",
  effectivePolicy: "Allowed once for this running BREP instance",
  duration: "Until this operation finishes (maximum 60 seconds)",
  expiresAt: "2026-07-30T12:01:00Z",
  persistence: "One operation; it will not be remembered",
  denialConsequence:
    "BREP stays open, but the selected geometry will not be imported.",
  administratorOnly: false,
};

describe("CapabilityDialog", () => {
  it("discloses exact source, bounded data, risk, policy and persistence", () => {
    render(
      <CapabilityDialog
        request={request}
        actorRole="engineer"
        onDecision={vi.fn()}
      />,
    );
    const dialog = screen.getByRole("dialog", {
      name: /permission requested/i,
    });
    expect(dialog).toHaveTextContent("BREP Designer");
    expect(dialog).toHaveTextContent("brep · version 2.4.1");
    expect(dialog).toHaveTextContent("Gearbox");
    expect(dialog).toHaveTextContent("At most 10 selected part identifiers");
    expect(dialog).toHaveTextContent("High risk");
    expect(dialog).toHaveTextContent(request.reason);
    expect(dialog).toHaveTextContent(request.effectivePolicy);
    expect(dialog).toHaveTextContent("maximum 60 seconds");
    expect(dialog).toHaveTextContent(
      "One operation; it will not be remembered",
    );
    expect(dialog).toHaveTextContent(request.denialConsequence);
  });

  it("keeps allow, deny and cancel as distinct decisions", async () => {
    const user = userEvent.setup();
    const onDecision = vi.fn();
    const { rerender } = render(
      <CapabilityDialog
        request={request}
        actorRole="engineer"
        onDecision={onDecision}
      />,
    );
    await user.click(screen.getByTestId("surface-capability-allow"));
    expect(onDecision).toHaveBeenLastCalledWith("allow");
    await user.click(screen.getByTestId("surface-capability-deny"));
    expect(onDecision).toHaveBeenLastCalledWith("deny");
    await user.click(screen.getByTestId("surface-capability-cancel"));
    expect(onDecision).toHaveBeenLastCalledWith("cancel");
    rerender(
      <CapabilityDialog
        request={request}
        actorRole="engineer"
        onDecision={onDecision}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onDecision).toHaveBeenLastCalledWith("cancel");
  });

  it("shows administrator-only policy and prevents engineer broadening", () => {
    render(
      <CapabilityDialog
        request={{ ...request, administratorOnly: true }}
        actorRole="engineer"
        onDecision={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/administrator approval is required/i),
    ).toBeVisible();
    expect(screen.getByTestId("surface-capability-allow")).toBeDisabled();
    expect(screen.getByTestId("surface-capability-deny")).toBeEnabled();
    expect(screen.getByTestId("surface-capability-cancel")).toBeEnabled();
  });
});
