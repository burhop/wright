import source from "../../../../../prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow?raw";
import { expect, it } from "vitest";
import { cloneWorkflow, initialWorkflow } from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

it("opens the actual desktop handle draft and preserves its evidence and review connections on save", () => {
  const base = cloneWorkflow(initialWorkflow);
  base.workflowId = "workflow.replacement_handle_strength_draft";
  const parsed = parseRecoveryAuthoringSource(source, base);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const workflow = parsed.workflow!;
  expect(
    workflow.blocks.some(
      (block) => block.title === "Review the proposed print package",
    ),
  ).toBe(true);
  const formatted = formatRecoveryAuthoringSource(workflow);
  const reopened = parseRecoveryAuthoringSource(formatted.text, workflow);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(reopened.workflow!.relationships).toEqual(workflow.relationships);
  expect(reopened.workflow!.ports).toEqual(workflow.ports);
  expect(reopened.workflow!.blocks.map((block) => block.configuration)).toEqual(
    workflow.blocks.map((block) => block.configuration),
  );
});
