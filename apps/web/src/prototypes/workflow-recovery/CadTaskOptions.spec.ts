import { expect, it } from "vitest";
import { cadCommands, cadPortId, type CadOptions } from "./CadTaskOptions";
import { sourceKey } from "./prompt-settings";
import { createAuthoringObject } from "./authoring-objects";
import {
  initialWorkflow,
  initialLayout,
  type RecoveryWorkflow,
  type RecoveryLayout,
} from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
  type RecoveryCommand,
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

it("offers an upstream CAD input before selection, retains its drawn connection and removes it when no longer applicable", () => {
  let workflow: RecoveryWorkflow = initialWorkflow;
  let layout: RecoveryLayout = initialLayout;
  const apply = (commands: RecoveryCommand[]) => {
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", commands),
    );
    expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
    const accepted = acceptRecoveryResult(workflow, layout, result)!;
    workflow = accepted.workflow;
    layout = accepted.layout;
  };
  const settings: CadOptions = {
    source: "new",
    save_native: true,
    native_path: "model.par",
    policy: "indexed",
    edit_mode: "in_place",
    copy_path: "copy.par",
    exports: [],
  };
  const producer = createAuthoringObject("mcp-task", workflow, layout);
  apply([producer]);
  apply(cadCommands(producer.block, workflow, settings));
  const consumer = createAuthoringObject("mcp-task", workflow, layout);
  apply([consumer]);
  const input = cadPortId(consumer.block, "input");
  const model = cadPortId(producer.block, "model");
  apply(
    cadCommands(consumer.block, workflow, { ...settings, source: "upstream" }),
  );
  expect(workflow.ports.find((p) => p.id === input)).toMatchObject({
    name: "CAD model",
    typeId: "type.geometry.brep",
    direction: "input",
  });
  const wrongType = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "graph", [
      {
        kind: "connect",
        relationship: {
          id: "rel.wrong-model",
          kind: "data",
          sourceId: producer.ports.find((p) => p.direction === "output")!.id,
          targetId: input,
          label: "Not geometry",
          condition: null,
        },
      },
    ]),
  );
  expect(wrongType.ok).toBe(false);
  expect(workflow.relationships.some((e) => e.targetId === input)).toBe(false);
  apply([
    {
      kind: "connect",
      relationship: {
        id: "rel.drawn-model",
        kind: "data",
        sourceId: model,
        targetId: input,
        label: "CAD model",
        condition: null,
      },
    },
    ...cadCommands(consumer.block, workflow, {
      ...settings,
      source: "upstream",
      from_port: sourceKey(input),
    }),
  ]);
  expect(workflow.ports.filter((p) => p.id === input)).toHaveLength(1);
  expect(
    workflow.relationships.find((e) => e.targetId === input)?.sourceId,
  ).toBe(model);
  expect(validateRecoveryAuthoringRoundTrip(workflow).ok).toBe(true);
  apply(cadCommands(consumer.block, workflow, settings));
  expect(workflow.ports.some((p) => p.id === input)).toBe(false);
  expect(workflow.relationships.some((e) => e.targetId === input)).toBe(false);
  apply(
    cadCommands(consumer.block, workflow, { ...settings, source: "upstream" }),
  );
  expect(workflow.ports.filter((p) => p.id === input)).toHaveLength(1);
  apply(cadCommands(consumer.block, workflow, null));
  expect(workflow.ports.some((p) => p.id === input)).toBe(false);
  expect(validateRecoveryAuthoringRoundTrip(workflow).ok).toBe(true);
});
