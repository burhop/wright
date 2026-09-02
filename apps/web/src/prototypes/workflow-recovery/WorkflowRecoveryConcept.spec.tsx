import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
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

async function openDesignIntentSettings() {
  fireEvent.click(screen.getByTestId("workflow-recovery-block-block.design-intent"));
  await userEvent.click(screen.getByTestId("workflow-recovery-inspector-tab-definition"));
}

describe("WorkflowRecoveryConcept component states", () => {
  it("opens an independently identified workflow file but rejects identity changes during contextual editing", async () => {
    const independent = savedWorkflowSource.replace(/^workflow mounting_bracket$/m, "workflow authored_inspection_plan");
    render(<WorkflowRecoveryConcept workflowSource={independent} definitionRevision={1} />);
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    const source = screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor");
    expect(source.value).toContain("workflow authored_inspection_plan");
    fireEvent.change(source, { target: { value: independent.replace("workflow authored_inspection_plan", "workflow another_document") } });
    await userEvent.click(screen.getByTestId("workflow-recovery-source-apply"));
    expect(screen.getByTestId("workflow-recovery-diagnostic-WFR-SOURCE-IDENTITY-UNKNOWN")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute("data-revision", "1");
  });

  it("adds and saves objects in a newly identified workflow without reverting to the example identity", async () => {
    const independent = savedWorkflowSource.replace(/^workflow mounting_bracket$/m, "workflow authored_new_document");
    const onSave = vi.fn(async (source: string) => ({ source, definition_revision: 2, storage_digest: "a".repeat(64) }));
    render(<WorkflowRecoveryConcept workflowSource={independent} definitionRevision={1} storageDigest={"b".repeat(64)} onSave={onSave} />);
    await userEvent.click(screen.getByTestId("workflow-recovery-create-group-input"));
    await userEvent.click(screen.getByTestId("workflow-recovery-create-template-text-input"));
    expect(screen.getByTestId("workflow-recovery-block-block.text-input-1")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("workflow-recovery-input-text-block.text-input-1"), { target: { value: "Test the new document's independent design intent." } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(onSave.mock.calls[0]![0]).toContain("workflow authored_new_document");
    expect(onSave.mock.calls[0]![0]).toContain("independent design intent");
    expect(screen.queryByTestId("workflow-recovery-diagnostic-WFR-SOURCE-IDENTITY-UNKNOWN")).not.toBeInTheDocument();
  });

  it("offers editable text and file input for company context despite its deterministic implementation binding", async () => {
    render(<WorkflowRecoveryConcept />);
    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.company-context"));
    expect(screen.getByTestId("workflow-recovery-overview-block.company-context")).toHaveTextContent("Engineer input");
    await userEvent.click(screen.getByTestId("workflow-recovery-inspector-tab-definition"));
    fireEvent.change(screen.getByTestId("workflow-recovery-input-text-block.company-context"), { target: { value: "Use company drawing standard ME-104. Prefer stock aluminum plate." } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-inputs-toggle")).toHaveTextContent("1/3 configured");
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor").value).toContain("company drawing standard ME-104");
  });

  it("creates independent text inputs by keyboard, persists real text, and cold-reopens authored input", async () => {
    let savedSource = "";
    const onSave = vi.fn(async (source: string) => { savedSource = source; return { source, definition_revision: 8, storage_digest: "a".repeat(64) }; });
    const first = render(<WorkflowRecoveryConcept onSave={onSave} />);
    screen.getByTestId("workflow-recovery-create-group-input").focus();
    await userEvent.keyboard("{Enter}");
    screen.getByTestId("workflow-recovery-create-template-text-input").focus();
    await userEvent.keyboard("{Enter}");
    expect(screen.getByTestId("workflow-recovery-block-block.text-input-1")).toBeInTheDocument();
    fireEvent.change(screen.getByTestId("workflow-recovery-input-text-block.text-input-1"), { target: { value: "Support a 400 N load. Use stainless steel. Review the mounting interface." } });
    fireEvent.change(screen.getByTestId("workflow-recovery-block-title-block.text-input-1"), { target: { value: "Pump support requirements" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-inputs-toggle")).toHaveTextContent("1/4 configured");
    await userEvent.click(screen.getByTestId("workflow-recovery-create-group-input"));
    await userEvent.click(screen.getByTestId("workflow-recovery-create-template-text-input"));
    expect(screen.getByTestId("workflow-recovery-block-block.text-input-2")).toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-block-block.text-input-1")).toHaveTextContent("Pump support requirements");
    await userEvent.click(screen.getByTestId("workflow-recovery-save"));
    await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(savedSource).toContain("Support a 400 N load");
    first.unmount();
    render(<WorkflowRecoveryConcept workflowSource={savedSource} definitionRevision={8} storageDigest={"a".repeat(64)} onSave={onSave} />);
    expect(screen.getByTestId("workflow-recovery-block-block.text-input-1")).toHaveTextContent("Pump support requirements");
    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.text-input-1"));
    expect(screen.getByTestId("workflow-recovery-overview-block.text-input-1")).toHaveTextContent("Support a 400 N load");
  });

  it("selects only actual listed workspace files, retains the reference, and reports a failed refresh", async () => {
    const onListWorkspaceFiles = vi.fn().mockResolvedValueOnce([{ path: "design/requirements.docx", name: "requirements.docx" }]).mockRejectedValueOnce(new Error("offline"));
    render(<WorkflowRecoveryConcept onListWorkspaceFiles={onListWorkspaceFiles} />);
    await userEvent.click(screen.getByTestId("workflow-recovery-create-group-input"));
    await userEvent.click(screen.getByTestId("workflow-recovery-create-template-file-input"));
    await userEvent.click(screen.getByTestId("workflow-recovery-input-files-refresh-block.file-input-1"));
    await userEvent.selectOptions(screen.getByTestId("workflow-recovery-input-file-block.file-input-1"), "design/requirements.docx");
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    expect(screen.getByTestId("workflow-recovery-inputs-toggle")).toHaveTextContent("1/4 configured");
    await userEvent.click(screen.getByTestId("workflow-recovery-input-files-refresh-block.file-input-1"));
    expect(await screen.findByTestId("workflow-recovery-settings-feedback")).toHaveTextContent("could not be read");
    expect(screen.getByTestId("workflow-recovery-input-file-block.file-input-1")).toHaveValue("design/requirements.docx");
    await userEvent.click(screen.getByTestId("workflow-recovery-view-code"));
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor").value).toContain("design/requirements.docx");
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-source-editor").value).not.toContain("mounting-bracket-design-intent.docx");
  });

  it("edits unbound prompts and parameters, confirms deletion, and restores the full object with undo", async () => {
    render(<WorkflowRecoveryConcept />);
    await userEvent.click(screen.getByTestId("workflow-recovery-create-group-document"));
    await userEvent.click(screen.getByTestId("workflow-recovery-create-template-document"));
    const id = "block.document-1";
    fireEvent.change(screen.getByTestId(`workflow-recovery-block-instructions-${id}`), { target: { value: "Draft a design note. Keep assumptions separate and list questions for review." } });
    await userEvent.click(screen.getByTestId(`workflow-recovery-settings-advanced-${id}`));
    fireEvent.change(screen.getByTestId(`workflow-recovery-parameter-name-${id}`), { target: { value: "document_format" } });
    await userEvent.click(screen.getByTestId(`workflow-recovery-parameter-add-${id}`));
    fireEvent.change(screen.getByTestId(`workflow-recovery-block-parameter-${id}-document_format`), { target: { value: "Markdown" } });
    await userEvent.click(screen.getByTestId("workflow-recovery-config-apply"));
    await userEvent.click(screen.getByTestId("workflow-recovery-delete"));
    expect(screen.getByRole("dialog", { name: "Delete workflow step" })).toHaveTextContent("0 connection(s)");
    await userEvent.click(screen.getByTestId("workflow-recovery-delete-cancel"));
    expect(screen.getByTestId(`workflow-recovery-block-${id}`)).toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-delete"));
    await userEvent.click(screen.getByTestId("workflow-recovery-delete-confirm"));
    expect(screen.queryByTestId(`workflow-recovery-block-${id}`)).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-undo"));
    fireEvent.click(screen.getByTestId(`workflow-recovery-block-${id}`));
    expect(screen.getByTestId(`workflow-recovery-overview-${id}`)).toHaveTextContent("Unbound draft");
    await userEvent.click(screen.getByTestId("workflow-recovery-inspector-tab-definition"));
    expect(screen.getByTestId(`workflow-recovery-block-instructions-${id}`)).toHaveValue("Draft a design note. Keep assumptions separate and list questions for review.");
    await userEvent.click(screen.getByTestId(`workflow-recovery-settings-advanced-${id}`));
    expect(screen.getByTestId(`workflow-recovery-block-parameter-${id}-document_format`)).toHaveValue("Markdown");
  });

  it("renders the compact Create rail, transient Inputs and contextual Inspector with stable controls", async () => {
    const { container } = render(<WorkflowRecoveryConcept />);
    expect(screen.getByTestId("workflow-recovery-canvas")).toBeVisible();
    expect(screen.getByTestId("workflow-recovery-authority")).toHaveAttribute("data-revision", "2");
    expect(screen.getByTestId("workflow-recovery-filebar")).toHaveTextContent("mounting-bracket.workflow.wflow · Local preview · not saved");
    expect(screen.queryByRole("heading", { name: "Three source inputs" })).not.toBeInTheDocument();
    expect(screen.getAllByTestId(/workflow-recovery-create-group-/)).toHaveLength(7);
    expect(screen.getByTestId("workflow-recovery-inputs-toggle")).toHaveTextContent("0/3 configured");
    expect(screen.queryByTestId("workflow-recovery-inputs-navigator")).not.toBeInTheDocument();
    await userEvent.click(screen.getByTestId("workflow-recovery-inputs-toggle"));
    expect(screen.getByTestId("workflow-recovery-inputs-navigator")).toHaveTextContent("Needs input");
    await userEvent.click(screen.getByTestId("workflow-recovery-input-navigate-block.design-intent"));
    expect(screen.queryByTestId("workflow-recovery-inputs-navigator")).not.toBeInTheDocument();
    expect(screen.getByTestId("workflow-recovery-overview-block.design-intent")).toHaveTextContent("Engineer input");
    expect(screen.queryByText(/PDF brief/i)).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("workflow-recovery-concept").dataset.semanticDigest).toMatch(/^sha256:/));
    expect(missingInteractiveTestIds(container)).toEqual([]);
    expect(screen.getByTestId("workflow-recovery-run-start")).toBeDisabled();
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveAttribute("title", expect.stringContaining("confirmed by the workspace host"));
    await userEvent.click(screen.getByTestId("workflow-recovery-inspector-close"));
    expect(screen.queryByTestId("workflow-recovery-inspector")).not.toBeInTheDocument();
    expect(container.querySelector(".recovery-workbench")).not.toHaveClass("recovery-workbench--inspecting");
    await userEvent.click(screen.getByTestId("workflow-recovery-inspector-open"));
    fireEvent.click(screen.getByTestId("workflow-recovery-block-block.create-design-specification"));
    await userEvent.click(screen.getByTestId("workflow-recovery-inspector-tab-definition"));
    expect(screen.getByText("AI prompt")).toBeVisible();
    await userEvent.click(screen.getByTestId("workflow-recovery-block-review-toggle-block.create-design-specification"));
    expect(screen.getByTestId<HTMLTextAreaElement>("workflow-recovery-block-review-block.create-design-specification").value).toContain("Accept when: An engineer accepted the design specification");
    expect(screen.getByText(/These criteria come from this step's accept and revise paths/)).toBeVisible();
    await userEvent.click(screen.getByTestId("workflow-recovery-file-technical-details"));
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
    await openDesignIntentSettings();
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
    await openDesignIntentSettings();
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
    await openDesignIntentSettings();
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

    await userEvent.click(screen.getByTestId("workflow-recovery-view-diagram"));
    await userEvent.click(screen.getByTestId("workflow-recovery-ai-request"));
    expect(screen.queryByTestId("workflow-recovery-proposal")).not.toBeInTheDocument();
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
    await openDesignIntentSettings();
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
    await openDesignIntentSettings();
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
