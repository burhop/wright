import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { WorkflowRecoveryConcept } from "./WorkflowRecoveryConcept";

class MockResizeObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

beforeAll(() => {
  vi.stubGlobal("ResizeObserver", MockResizeObserver);
});

function missingInteractiveTestIds(root: HTMLElement): string[] {
  return [...root.querySelectorAll<HTMLElement>('button, input, textarea, select, summary, a[href], [role="button"], [tabindex]:not([tabindex="-1"])')]
    .filter((element) => !element.dataset.testid)
    .map((element) => `${element.tagName.toLowerCase()}:${element.getAttribute("aria-label") ?? element.textContent?.trim().slice(0, 40) ?? ""}`);
}

describe("WorkflowRecoveryConcept component states", () => {
  it("renders the default canonical projection and gives every visible interaction a stable test id", async () => {
    const { container } = render(<WorkflowRecoveryConcept />);
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveTextContent("Accepted definition r1");
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest).toMatch(/^sha256:/));
    expect(missingInteractiveTestIds(container)).toEqual([]);

    await userEvent.click(screen.getByTestId("workflow-recovery-port-lab-open"));
    expect(screen.getByTestId("workflow-port-lab")).toBeVisible();
    expect(missingInteractiveTestIds(container)).toEqual([]);
  });

  it("renders an explicit loading state without exposing stale editor authority", () => {
    render(<WorkflowRecoveryConcept surfaceState="loading" />);
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByTestId("workflow-recovery-canvas")).not.toBeInTheDocument();
  });

  it("renders an error state, preserves accepted-state language, and exposes a testable retry", async () => {
    const retry = vi.fn();
    render(<WorkflowRecoveryConcept surfaceState="error" onRetry={retry} />);
    expect(screen.getByRole("alert")).toHaveTextContent("accepted workflow was not changed");
    await userEvent.click(screen.getByTestId("workflow-recovery-boundary-retry"));
    expect(retry).toHaveBeenCalledOnce();
  });

  it("contains an invalid source draft with a stable diagnostic and unchanged revision", async () => {
    render(<WorkflowRecoveryConcept />);
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const editor = screen.getByTestId("workflow-recovery-source-editor");
    fireEvent.change(editor, { target: { value: "workflow malformed\nend\n" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(await screen.findByTestId(/workflow-recovery-diagnostic-WFR-/)).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "1");
  });
});
