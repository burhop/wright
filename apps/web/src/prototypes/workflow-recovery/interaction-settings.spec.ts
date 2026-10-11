import { describe, expect, it } from "vitest";
import declaredSource from "../../../../../specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow?raw";
import {
  initialWorkflow,
  initialLayout,
  cloneWorkflow,
  RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY,
  type RecoveryWorkflow,
} from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
  textEditCommands,
  type RecoveryCommand,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";
import { createAuthoringObject } from "./authoring-objects";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import {
  declarationJson,
  humanInputDeclarationCommands,
  inputDeclarationCommands,
  interactionObject,
} from "./interaction-settings";

export function declaredWorkflow() {
  const parsed = parseRecoveryAuthoringSource(declaredSource, {
    ...cloneWorkflow(initialWorkflow),
    workflowId: "workflow.test",
  });
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  return parsed.workflow!;
}
function apply(workflow: RecoveryWorkflow, commands: RecoveryCommand[]) {
  const layout = hydrateAuthoringLayout(workflow);
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  return acceptRecoveryResult(workflow, layout, result)!.workflow;
}
describe("declared input authoring", () => {
  it("edits a schema/default without changing existing text, option bindings, evidence or graph", () => {
    const workflow = declaredWorkflow(),
      input = workflow.blocks.find((item) => item.id === "block.brief")!;
    const existing = interactionObject(input, "interaction_input")!;
    const metadata = {
      ...existing,
      value_schema: { type: "number", minimum: 0 },
      unit: "mm",
      default: 0,
    };
    const next = apply(
      workflow,
      inputDeclarationCommands(input, JSON.stringify(metadata)),
    );
    expect(
      interactionObject(
        next.blocks.find((item) => item.id === input.id)!,
        "interaction_input",
      ),
    ).toEqual(metadata);
    expect(next.relationships).toEqual(workflow.relationships);
    expect(next.blocks.find((item) => item.id === "block.choice")).toEqual(
      workflow.blocks.find((item) => item.id === "block.choice"),
    );
    expect(validateRecoveryAuthoringRoundTrip(next).ok).toBe(true);
    const reopened = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(next).text,
      workflow,
    );
    expect(reopened.ok).toBe(true);
    expect(
      interactionObject(
        reopened.workflow!.blocks.find((item) => item.id === input.id)!,
        "interaction_input",
      ),
    ).toEqual(metadata);
  });
  it("preserves configured provider option fields and local definitions verbatim", () => {
    const workflow = declaredWorkflow(),
      input = workflow.blocks.find((item) => item.id === "block.brief")!;
    const metadata = {
      version: 1,
      required: true,
      value_schema: {
        type: "object",
        $defs: { size: { type: "number" } },
        properties: { size: { $ref: "#/$defs/size" } },
      },
      option_source: {
        server_id: "existing-provider",
        tool_name: "options",
        binding_revision: "a".repeat(64),
      },
      default_option_id: "configured-one",
    };
    const next = apply(
      workflow,
      inputDeclarationCommands(input, JSON.stringify(metadata)),
    );
    expect(
      interactionObject(
        next.blocks.find((item) => item.id === input.id)!,
        "interaction_input",
      ),
    ).toEqual(metadata);
  });
  it("removes optional preparation metadata through inspector and source without removing other objects", () => {
    const workflow = declaredWorkflow(),
      input = workflow.blocks.find((item) => item.id === "block.brief")!;
    const next = apply(workflow, [
      {
        kind: "set_block_object_configuration",
        blockId: input.id,
        key: "interaction_input",
        value: null,
      },
    ]);
    expect(
      interactionObject(
        next.blocks.find((item) => item.id === input.id)!,
        "interaction_input",
      ),
    ).toBeNull();
    expect(validateRecoveryAuthoringRoundTrip(next).ok).toBe(true);
    const commands = textEditCommands(workflow, next);
    expect(
      commands.some(
        (item) =>
          "kind" in item && item.kind === "set_block_object_configuration",
      ),
    ).toBe(true);
    expect(
      formatRecoveryAuthoringSource(
        apply(workflow, commands as RecoveryCommand[]),
      ).text,
    ).toBe(formatRecoveryAuthoringSource(next).text);
  });
  it("keeps the declared user instructions, object schema and exact output port together", () => {
    const workflow = declaredWorkflow(),
      human = workflow.blocks.find((item) => item.id === "block.choice")!;
    const metadata = {
      ...interactionObject(human, "human_interaction"),
      instructions: "Choose the measured candidate to continue.",
      response_schema: {
        type: "object",
        properties: { selection: { type: "string", enum: ["a", "b"] } },
        required: ["selection"],
        additionalProperties: false,
      },
    };
    const next = apply(
      workflow,
      humanInputDeclarationCommands(human, workflow, JSON.stringify(metadata)),
    );
    expect(next.blocks.find((item) => item.id === human.id)!.instructions).toBe(
      metadata.instructions,
    );
    expect(
      interactionObject(
        next.blocks.find((item) => item.id === human.id)!,
        "human_interaction",
      ),
    ).toEqual(metadata);
    expect(next.ports).toEqual(workflow.ports);
    expect(next.relationships).toEqual(workflow.relationships);
    expect(validateRecoveryAuthoringRoundTrip(next).ok).toBe(true);
  });
  it("creates a draft human step with no AI or fabricated response/default", () => {
    const created = createAuthoringObject(
      "human-input",
      initialWorkflow,
      initialLayout,
    );
    expect(created.block.executionKind).toBe("human");
    expect(created.block.configuration).toEqual({
      authoring_template: "human-input",
    });
    expect(created.ports.map((port) => [port.direction, port.typeId])).toEqual([
      ["input", "type.document.engineering"],
      ["output", "type.result.structured"],
    ]);
    const next = apply(initialWorkflow, [created]);
    expect(validateRecoveryAuthoringRoundTrip(next).ok).toBe(true);
    expect(formatRecoveryAuthoringSource(next).text).toContain(
      '"authoring_template":"human-input"',
    );
  });
  it.each([
    ["syntax", "broken"],
    ["array", "[]"],
    ["null", "null"],
    ["infinite number", '{"value":1e999}'],
    ["size", JSON.stringify({ value: "x".repeat(65536) })],
  ])("rejects malformed or unbounded declaration %s", (_label, text) => {
    expect(() => declarationJson(text)).toThrow();
  });
  it("rejects deeply nested JSON before command submission", () => {
    let value: unknown = true;
    for (let i = 0; i < 27; i++) value = { nested: value };
    expect(() => declarationJson(JSON.stringify(value))).toThrow(/nesting/);
  });
  it.each(["version", "schema", "port", "instructions"] as const)(
    "rejects changed %s on a declared response before commands",
    (field) => {
      const workflow = declaredWorkflow(),
        human = workflow.blocks.find((item) => item.id === "block.choice")!;
      const metadata = interactionObject(human, "human_interaction")!;
      if (field === "version") metadata.version = 4;
      else if (field === "schema")
        metadata.response_schema = { type: "string" };
      else if (field === "port") metadata.output_port = "another-port";
      else metadata.instructions = " ";
      expect(() =>
        humanInputDeclarationCommands(
          human,
          workflow,
          JSON.stringify(metadata),
        ),
      ).toThrow();
    },
  );
  it("does not apply input metadata to a task or mutate corrupt retained configuration", () => {
    const workflow = declaredWorkflow(),
      human = workflow.blocks.find((item) => item.id === "block.choice")!;
    expect(() =>
      inputDeclarationCommands(
        human,
        '{"version":1,"value_schema":{"type":"string"}}',
      ),
    ).toThrow();
    const corrupted = {
      ...human,
      configuration: {
        ...human.configuration,
        [RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY]: "broken",
      },
    };
    expect(() => interactionObject(corrupted, "human_interaction")).toThrow();
    const layout = hydrateAuthoringLayout(workflow);
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", [
        {
          kind: "set_block_object_configuration",
          blockId: human.id,
          key: "interaction_input",
          value: { version: 1, value_schema: {} },
        },
      ]),
    );
    expect(result.ok).toBe(false);
    expect(interactionObject(human, "human_interaction")).not.toBeNull();
  });
  it.each(["null", "[]", "broken"])(
    "contains corrupt retained objects %s without changing accepted source",
    (retained) => {
      const workflow = declaredWorkflow();
      const input = workflow.blocks.find((item) => item.id === "block.brief")!;
      input.configuration[RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY] = retained;
      const original = JSON.stringify(workflow);
      const result = applyRecoveryBatch(
        workflow,
        hydrateAuthoringLayout(workflow),
        recoveryCommandBatch(workflow.revision, "form", [
          {
            kind: "set_block_object_configuration",
            blockId: input.id,
            key: "interaction_input",
            value: { version: 1, value_schema: { type: "string" } },
          },
        ]),
      );
      expect(result.ok).toBe(false);
      expect(JSON.stringify(workflow)).toBe(original);
    },
  );
});
