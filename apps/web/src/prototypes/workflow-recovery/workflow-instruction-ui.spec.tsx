import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeAll, expect, it, vi } from "vitest";
import { WorkflowRecoveryConcept } from "./WorkflowRecoveryConcept";
import { cloneWorkflow, initialWorkflow } from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import { normalizeWorkflowInstructions } from "./workflow-instructions";

beforeAll(() =>
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  ),
);
const instructions = normalizeWorkflowInstructions({
  profile_id: "default",
  profile_version: "1",
  assets: [
    {
      id: "task",
      role: "workflow-task",
      version: "1",
      body: "Explicit instructions",
      body_digest: "a".repeat(64),
      origin: "packaged",
    },
  ],
  bindings: [{ role: "workflow-task", asset_ids: ["task"] }],
});

it("applies visible instruction edits through normal source, undo and accepted save", async () => {
  const workflow = cloneWorkflow(initialWorkflow);
  workflow.metadata.instructions = instructions;
  const source = formatRecoveryAuthoringSource(workflow).text;
  const onSave = vi.fn(async (value: string) => ({
    source: value,
    definition_revision: 3,
    storage_digest: "c".repeat(64),
  }));
  const onExportSource = vi.fn();
  render(
    <WorkflowRecoveryConcept
      workflowSource={source}
      definitionRevision={2}
      storageDigest={"b".repeat(64)}
      onSave={onSave}
      onExportSource={onExportSource}
    />,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-instructions"));
  expect(
    screen.getByRole("button", { name: "Export saved workflow source" }),
  ).not.toBeDisabled();
  fireEvent.change(screen.getByLabelText("Unspecified design choices"), {
    target: { value: "document_reasonable" },
  });
  fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
    target: { value: "Record dimensional assumptions." },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Apply workflow instructions" }),
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Export saved workflow source" }),
    ).toBeDisabled(),
  );
  expect(
    await screen.findByText(/Instructions applied to the draft/),
  ).toBeVisible();
  fireEvent.click(screen.getByTestId("workflow-recovery-modal-close"));
  fireEvent.click(screen.getByTestId("workflow-recovery-undo"));
  fireEvent.click(screen.getByTestId("workflow-recovery-instructions"));
  expect(screen.getByLabelText("Unspecified design choices")).toHaveValue(
    "require_specified",
  );
  expect(screen.getByLabelText("Additional workflow guidance")).toHaveValue("");
  fireEvent.change(screen.getByLabelText("Unspecified design choices"), {
    target: { value: "document_reasonable" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Apply workflow instructions" }),
  );
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Export saved workflow source" }),
    ).toBeDisabled(),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-modal-close"));
  fireEvent.click(screen.getByTestId("workflow-recovery-save"));
  await waitFor(() => expect(onSave).toHaveBeenCalledOnce());
  const parsed = parseRecoveryAuthoringSource(
    onSave.mock.calls[0]![0],
    workflow,
  );
  expect(parsed.ok).toBe(true);
  expect(parsed.workflow!.metadata.instructions?.policy.assumption_policy).toBe(
    "document_reasonable",
  );
  expect(onExportSource).not.toHaveBeenCalled();
});

it("opening legacy instructions leaves source unchanged until explicitly reviewed migration", async () => {
  const source = formatRecoveryAuthoringSource(initialWorkflow).text;
  const onLoadInstructionDefaults = vi.fn(async () => ({
    instructions,
    digest: "a".repeat(64),
    revision: "r1",
    origin: "packaged" as const,
  }));
  render(
    <WorkflowRecoveryConcept
      workflowSource={source}
      onLoadInstructionDefaults={onLoadInstructionDefaults}
      onExportSource={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-instructions"));
  expect(onLoadInstructionDefaults).not.toHaveBeenCalled();
  expect(
    screen.getByRole("button", { name: "Export saved workflow source" }),
  ).toBeDisabled();
  fireEvent.click(
    screen.getByRole("button", { name: "Make instructions explicit…" }),
  );
  await screen.findByLabelText("Proposed instructions");
  fireEvent.click(
    screen.getByRole("button", { name: "Cancel instruction update" }),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-modal-close"));
  expect(screen.getByTestId("workflow-recovery-undo")).toBeDisabled();
});
