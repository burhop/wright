import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import {
  cloneWorkflow,
  initialWorkflow,
  RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY,
} from "./model";
import { normalizeWorkflowInstructions } from "./workflow-instructions";
import {
  StepInstructionsEditor,
  stepInstructionOverride,
} from "./StepInstructionsEditor";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
  type RecoveryCommand,
} from "./command-system";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
const workflow = () => {
  const value = cloneWorkflow(initialWorkflow);
  value.metadata.instructions = normalizeWorkflowInstructions({
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
  return value;
};

it("saves an explicit per-step policy and guidance through portable source commands", () => {
  const current = workflow();
  const block = current.blocks.find(
    (block) => block.executionKind === "ai_capable",
  )!;
  const onApply = vi.fn((_commands: RecoveryCommand[]) => true);
  render(
    <StepInstructionsEditor
      block={block}
      workflow={current}
      readOnly={false}
      onApply={onApply}
      onOpenWorkflowInstructions={vi.fn()}
    />,
  );
  expect(onApply).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Step assumption policy"), {
    target: { value: "document_reasonable" },
  });
  fireEvent.change(screen.getByLabelText("Additional step guidance"), {
    target: { value: "Use documented finish assumptions." },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Apply step instructions" }),
  );
  const layout = hydrateAuthoringLayout(current);
  const result = applyRecoveryBatch(
    current,
    layout,
    recoveryCommandBatch(current.revision, "form", onApply.mock.calls[0]![0]),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(current, layout, result)!.workflow;
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted).text,
    current,
  );
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(
    stepInstructionOverride(
      reopened.workflow!.blocks.find((item) => item.id === block.id)!,
    ),
  ).toMatchObject({
    origin: "step-author",
    mode: "append",
    text: "Use documented finish assumptions.",
    assumption_policy: "document_reasonable",
  });
  expect(reopened.workflow!.ports).toEqual(current.ports);
});

it("requires explicit workflow migration before legacy step overrides", () => {
  const current = cloneWorkflow(initialWorkflow);
  const block = current.blocks.find(
    (block) => block.executionKind === "ai_capable",
  )!;
  const inspect = vi.fn();
  render(
    <StepInstructionsEditor
      block={block}
      workflow={current}
      readOnly={false}
      onApply={vi.fn()}
      onOpenWorkflowInstructions={inspect}
    />,
  );
  expect(screen.queryByLabelText("Step assumption policy")).toBeNull();
  fireEvent.click(
    screen.getByRole("button", { name: "Inspect workflow instructions" }),
  );
  expect(inspect).toHaveBeenCalledOnce();
});

it("rejects invalid replacement text and preserves retained object configuration", () => {
  const current = workflow();
  const block = current.blocks.find(
    (block) => block.executionKind === "ai_capable",
  )!;
  block.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY] = JSON.stringify(
    { retained_provider_config: { id: "exact" } },
  );
  const onApply = vi.fn();
  render(
    <StepInstructionsEditor
      block={block}
      workflow={current}
      readOnly={false}
      onApply={onApply}
      onOpenWorkflowInstructions={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText("Step guidance mode"), {
    target: { value: "replace" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Apply step instructions" }),
  );
  expect(screen.getByRole("alert")).toHaveTextContent("meaningful text");
  expect(onApply).not.toHaveBeenCalled();
  expect(
    JSON.parse(
      String(block.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY]),
    ),
  ).toEqual({ retained_provider_config: { id: "exact" } });
});
