import { expect, it } from "vitest";
import { cadCommands, type CadOptions } from "./CadTaskOptions";
import { createAuthoringObject } from "./authoring-objects";
import { initialWorkflow, initialLayout } from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
} from "./command-system";
import {
  validateRecoveryAuthoringRoundTrip,
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

it("persists an initially blank export row without losing authoring semantics", () => {
  const add = createAuthoringObject("mcp-task", initialWorkflow, initialLayout);
  const created = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    applyRecoveryBatch(
      initialWorkflow,
      initialLayout,
      recoveryCommandBatch(initialWorkflow.revision, "form", [add]),
    ),
  )!;
  const block = created.workflow.blocks.find((b) => b.id === add.block.id)!;
  const settings: CadOptions = {
    source: "new",
    save_native: true,
    native_path: "part.psm",
    policy: "indexed",
    edit_mode: "in_place",
    copy_path: "copy.psm",
    exports: [{ id: "export-123", format: "", path: "", policy: "indexed" }],
  };
  const result = applyRecoveryBatch(
    created.workflow,
    created.layout,
    recoveryCommandBatch(
      created.workflow.revision,
      "form",
      cadCommands(block, created.workflow, settings),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(
    created.workflow,
    created.layout,
    result,
  )!;
  expect(validateRecoveryAuthoringRoundTrip(accepted.workflow).ok).toBe(true);
  const parsed = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(parsed.ok).toBe(true);
  expect(
    JSON.parse(
      String(
        parsed.workflow!.blocks.find((b) => b.id === block.id)!.configuration
          .cad,
      ),
    ).exports[0].format,
  ).toBe("");
});
