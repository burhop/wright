import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, describe, expect, it, vi } from "vitest";

import { WorkflowRecoveryConcept, type WorkflowRecoveryPersistedSource } from "./WorkflowRecoveryConcept";
import savedWorkflowSource from "../../../../../specs/080-canonical-workflow-recovery/fixtures/mounting-bracket.workflow.wflow?raw";

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
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute("data-revision", "2");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("mounting-bracket.workflow.wflow · Local preview · not saved");
    expect(screen.queryByText(/Build and review the work as a diagram/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Three source inputs" })).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-input-source-reference-images")).toHaveTextContent("Engineer upload");
    expect(screen.getByTestId("workflow-recovery-input-source-reference-images")).toHaveTextContent("JPG or PNG images");
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("Engineer input");
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("Typed text or common document");
    expect(screen.getByTestId("workflow-recovery-attachment-artifact.design-intent")).toHaveTextContent("Demo input for this session · not saved by this concept");
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
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute("title", expect.stringContaining("confirmed by the workspace host"));

    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.create-design-specification"));
    expect(screen.getByText("AI drafts; engineer reviews")).toBeVisible();
    expect(screen.getByText("AI prompt")).toBeVisible();
    expect(screen.getByText("Engineer approval checklist")).toBeVisible();
    await userEvent.click(screen.getByTestId("workflow-recovery-block-review-toggle-block.create-design-specification"));
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

  it("fails closed on invalid persisted source instead of substituting the built-in workflow", () => {
    render(<WorkflowRecoveryConcept workflowSource={"workflow malformed\nend\n"} definitionRevision={19} />);
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-surface-state", "invalid-source");
    expect(screen.getByRole("alert")).toHaveTextContent("accepted diagram was not replaced with fallback content");
    expect(screen.queryByTestId("workflow-recovery-canvas")).not.toBeInTheDocument();
  });

  it("contains an invalid source draft with a stable diagnostic and unchanged revision", async () => {
    render(<WorkflowRecoveryConcept />);
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const editor = screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor");
    expect(editor.value).toContain("input design_intent");
    expect(editor.value).toContain("task generate_geometry");
    expect(editor.value).not.toMatch(/^\s*(revision|parent|semantic_sha256):/m);
    fireEvent.change(editor, { target: { value: "workflow malformed\nend\n" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect((await screen.findAllByTestId(/workflow-recovery-diagnostic-WFR-/))[0]).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "2");
  });

  it("loads a workspace source, marks semantic edits unsaved, and marks them saved only after success", async () => {
    let finishSave: () => void = () => undefined;
    const onSave = vi.fn((source: string) => new Promise<WorkflowRecoveryPersistedSource>((resolve) => {
      finishSave = () => resolve({ source, definition_revision: 37, storage_digest: "b".repeat(64) });
    }));
    render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} definitionRevision={2} storageDigest={"a".repeat(64)} workflowFilePath="workflows/bracket.workflow.wflow" onSave={onSave} />);

    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("bracket.workflow.wflow · Saved in workspace");
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled();
    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Design intent and loads" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("Unsaved changes");
    expect(screen.getByTestId("workflow-recovery-save-status")).toHaveTextContent("Unsaved workflow changes");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();

    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(onSave.mock.calls[0]?.[0]).toContain('name: "Design intent and loads"');
    await act(async () => finishSave());
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "37"));
    expect(screen.getByTestId("workflow-recovery-save-status")).toHaveTextContent("Saved in workspace");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("Saved in workspace");
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute("data-revision", "37");
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute("title", expect.stringContaining("exact mounting-bracket fixture facts"));
  });

  it("runs the host-confirmed revision with its semantic digest and separate storage proof after undo", async () => {
    const onSave = vi.fn(async (source: string) => ({ source, definition_revision: 38, storage_digest: "c".repeat(64) }));
    const storageDigest = "b".repeat(64);
    render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} definitionRevision={37} storageDigest={storageDigest} onSave={onSave} />);
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest).toMatch(/^sha256:[a-f0-9]{64}$/));
    const semanticSha256 = screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest!.replace("sha256:", "");
    expect(semanticSha256).not.toBe(storageDigest);
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled());

    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Temporary local title" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    expect(screen.getByTestId("workflow-recovery-concept")).not.toHaveAttribute("data-revision", "37");
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled());
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute("data-subject-revision", "37");
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute("data-subject-semantic-digest", semanticSha256);
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveAttribute("data-subject-storage-digest", storageDigest);
    await userEvent.click(screen.getByTestId("workflow-recovery-run-subject-details"));
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveTextContent(`Definition semantic SHA-256 ${semanticSha256}`);
    expect(screen.getByTestId("workflow-recovery-run-mode")).toHaveTextContent(`Stored file SHA-256 ${storageDigest}`);
    expect(onSave).not.toHaveBeenCalled();
  });

  it("locks semantic edits and candidate previews to an active run subject while leaving layout interaction available", async () => {
    render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} definitionRevision={2} storageDigest={"b".repeat(64)} onSave={vi.fn()} />);
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled());

    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Temporary design intent" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled());
    expect(screen.getByTestId("workflow-recovery-redo")).toBeEnabled();

    const revision = screen.getByTestId("workflow-recovery-authority").getAttribute("data-revision");
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    expect(screen.getByTestId("workflow-recovery-run-definition-lock")).toHaveTextContent("Canvas layout moves remain available");

    await userEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(screen.getByTestId("workflow-recovery-diagnostic-WFR-RUN-DEFINITION-LOCKED")).toHaveTextContent("End the current test");
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute("data-revision", revision);
    expect(screen.getByTestId("workflow-recovery-block-block.design-intent")).toHaveTextContent("Design intent");
    expect(screen.getByTestId("workflow-recovery-block-block.design-intent")).not.toHaveTextContent("Temporary design intent");
    expect(screen.getByTestId("workflow-recovery-redo")).toBeEnabled();

    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Form edit during run" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-block-block.design-intent")).not.toHaveTextContent("Form edit during run");

    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const source = screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor");
    fireEvent.change(source, {
      target: {
        value: source.value.replace(
          'input design_intent\n  name: "Design intent"',
          'input design_intent\n  name: "Source edit during run"',
        ),
      },
    });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute("data-revision", revision);

    await userEvent.click(screen.getByTestId("workflow-recovery-ai-request"));
    expect(screen.queryByTestId("workflow-recovery-proposal")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-view-diagram"));
    const flowNode = screen.getByTestId("workflow-recovery-block-block.design-intent").closest(".react-flow__node");
    expect(flowNode).toHaveClass("draggable");

    await userEvent.click(screen.getByTestId("workflow-recovery-run-end"));
    expect(screen.queryByTestId("workflow-recovery-run-mode")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-redo"));
    expect(screen.getByTestId("workflow-recovery-block-block.design-intent")).toHaveTextContent("Temporary design intent");
  });

  it("saves and cold-reopens accepted AI steps from only the public workflow file", async () => {
    let persistedSource = "";
    const onSave = vi.fn(async (source: string) => {
      persistedSource = source;
      return { source, definition_revision: 12, storage_digest: "c".repeat(64) };
    });
    const first = render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} definitionRevision={2} storageDigest={"a".repeat(64)} onSave={onSave} />);

    await userEvent.click(screen.getByTestId("workflow-recovery-ai-request"));
    const friendlyChanges = screen.getByTestId("workflow-recovery-proposal-change-list");
    expect(friendlyChanges).toHaveTextContent("Add step: Create manufacturing drawing");
    expect([...friendlyChanges.querySelectorAll("p")].map((item) => item.textContent).join(" ")).not.toMatch(/\b(?:block|port|rel)\./);
    await userEvent.click(screen.getByTestId("workflow-recovery-proposal-accept"));
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(persistedSource).toContain("task create_inspection_drawing");
    expect(persistedSource).toContain("connection approved_to_drawing");

    first.unmount();
    render(<WorkflowRecoveryConcept workflowSource={persistedSource} definitionRevision={12} storageDigest={"c".repeat(64)} onSave={vi.fn()} />);
    expect(screen.getByTestId("workflow-recovery-block-block.create-inspection-drawing")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-block-block.review-inspection-drawing")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "12");
  });

  it("retains local semantic edits when an ordinary save fails", async () => {
    const onSave = vi.fn().mockRejectedValue(new Error("Unable to save this workflow file. Your local edits were kept."));
    render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} storageDigest={"a".repeat(64)} onSave={onSave} />);
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled();
    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Unsaved load definition" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));

    expect(await screen.findByRole("alert")).toHaveTextContent("local edits were kept");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("Unsaved changes");
    expect(screen.getByTestId("workflow-recovery-save")).toBeEnabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute("title", expect.stringContaining("Save workflow changes successfully"));
  });

  it("protects local source on stale saves until the engineer explicitly compares, copies, or reloads", async () => {
    const conflict = Object.assign(new Error("server detail must not be shown"), { code: "workflow_source_conflict" });
    const onSave = vi.fn().mockRejectedValue(conflict);
    const storedSource = savedWorkflowSource.replace('name: "Design intent"', 'name: "Stored design intent"');
    const onReadStoredSource = vi.fn().mockResolvedValue({ source: storedSource, definition_revision: 8, storage_revision: 11, storage_digest: "b".repeat(64) });
    const onReloadStoredSource = vi.fn().mockResolvedValue(undefined);
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    render(<WorkflowRecoveryConcept workflowSource={savedWorkflowSource} storageDigest={"a".repeat(64)} onSave={onSave} onReadStoredSource={onReadStoredSource} onReloadStoredSource={onReloadStoredSource} />);
    await userEvent.click(screen.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent"));
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeEnabled();
    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Local design requirements" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("workspace file changed elsewhere");
    expect(alert).toHaveTextContent("local edits are still here");
    expect(alert).not.toHaveTextContent("server detail");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("Unsaved changes");
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-conflict-actions")).toBeVisible();

    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.design-intent"), { target: { value: "Local requirements retained after conflict" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-save")).toBeDisabled();

    await userEvent.click(screen.getByTestId("workflow-recovery-conflict-copy-local"));
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining('name: "Local requirements retained after conflict"'));
    expect(screen.getByTestId("workflow-recovery-conflict-action-message")).toHaveTextContent("editor and stored file were not changed");

    await userEvent.click(screen.getByTestId("workflow-recovery-conflict-compare"));
    const comparison = await screen.findByRole("dialog", { name: "Compare workflow sources" });
    expect(onReadStoredSource).toHaveBeenCalledOnce();
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-comparison-local").value).toContain('name: "Local requirements retained after conflict"');
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-comparison-stored").value).toContain('name: "Stored design intent"');
    expect(comparison).toHaveTextContent("neither version has been applied or saved");
    expect(screen.getByTestId("workflow-recovery-modal-close")).toHaveFocus();
    await userEvent.click(screen.getByTestId("workflow-recovery-modal-close"));
    expect(screen.getByTestId("workflow-recovery-conflict-compare")).toHaveFocus();

    await userEvent.click(screen.getByTestId("workflow-recovery-conflict-reload"));
    expect(await screen.findByRole("dialog", { name: "Reload stored workflow?" })).toHaveTextContent("discard the unsaved local workflow edits");
    expect(onReloadStoredSource).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("workflow-recovery-conflict-reload-confirm"));
    await waitFor(() => expect(onReloadStoredSource).toHaveBeenCalledOnce());
    expect(onSave).toHaveBeenCalledOnce();
  });
});
