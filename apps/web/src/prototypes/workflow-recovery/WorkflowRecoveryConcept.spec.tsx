import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveTextContent("Current workflow version 2");
    expect(screen.getByRole("heading", { name: "Three source inputs" })).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-input-source-reference-images")).toHaveTextContent("Engineer upload");
    expect(screen.getByTestId("workflow-recovery-input-source-reference-images")).toHaveTextContent("JPG or PNG images");
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("Engineer input");
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("Typed text or common document");
    expect(screen.getByTestId("workflow-recovery-input-source-company-context")).toHaveTextContent("Company knowledge library");
    expect(screen.getByTestId("workflow-recovery-palette-context-hint")).toHaveTextContent("Tolerances come from the reviewed design specification, not this first input stage.");
    expect(screen.queryByText(/PDF brief/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest).toMatch(/^sha256:/));
    expect(missingInteractiveTestIds(container)).toEqual([]);

    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("mounting-bracket-design-intent.docx");
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-preview-artifact.design-intent"));
    const designIntentDialog = screen.getByRole("dialog", { name: "Design intent" });
    expect(designIntentDialog).toBeVisible();
    expect(within(designIntentDialog).getByText("Text or common document")).toBeVisible();
    await userEvent.click(screen.getByTestId("workflow-recovery-modal-close"));

    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.create-design-specification"));
    expect(screen.getByText("AI drafts; engineer reviews")).toBeVisible();
    expect(screen.getByText("AI prompt")).toBeVisible();
    expect(screen.getByText("Engineer checklist")).toBeVisible();
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-block-review-block.create-design-specification").value).toContain("Accept when: An engineer accepted the design specification");
    expect(screen.getByText(/These criteria come from this step's accept and revise paths/)).toBeVisible();

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
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "2");
  });
});
