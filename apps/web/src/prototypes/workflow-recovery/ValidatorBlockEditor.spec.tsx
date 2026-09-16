import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ValidatorBlockEditor } from "./ValidatorBlockEditor";
import { createAuthoringObject } from "./authoring-objects";
import {
  cloneWorkflow,
  initialWorkflow,
  initialLayout,
  type RecoveryPort,
} from "./model";
import { validationProfiles } from "./validation-settings";
import { sourceKey } from "./prompt-settings";

it("selects the actual packaged profile through normal editing commands", () => {
  const add = createAuthoringObject(
    "process-validator",
    initialWorkflow,
    initialLayout,
  );
  const apply = vi.fn(() => true);
  render(
    <ValidatorBlockEditor
      block={add.block}
      workflow={initialWorkflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  fireEvent.change(
    screen.getByRole("combobox", { name: "Validation profile" }),
    { target: { value: "structured-demo" } },
  );
  expect(apply).toHaveBeenCalledOnce();
  const commands = apply.mock.calls[0] as unknown as [
    { kind: string; key?: string; value?: string }[],
  ];
  const configuration = commands[0].find((item) => item.key === "validation")!;
  const value = JSON.parse(configuration.value!);
  expect(value.profile.name).toBe("structured-demo");
  expect(value.profile.reference.sha256).toMatch(/^[a-f0-9]{64}$/);
  expect(value.baseline.id).toBe("structured-demo");
  expect(screen.queryByLabelText("MCP server")).toBeNull();
});

it("preserves the running/read-only authoring boundary", () => {
  const add = createAuthoringObject(
    "process-validator",
    initialWorkflow,
    initialLayout,
  );
  render(
    <ValidatorBlockEditor
      block={add.block}
      workflow={initialWorkflow}
      readOnly
      onApply={() => false}
    />,
  );
  expect(
    screen.getByRole("combobox", { name: "Validation profile" }),
  ).toBeDisabled();
});

it("offers the exact connected safe producer and applies a bounded revision path", () => {
  const producer = createAuthoringObject(
    "ai-prompt",
    initialWorkflow,
    initialLayout,
  );
  const validator = createAuthoringObject(
    "process-validator",
    initialWorkflow,
    initialLayout,
  );
  const workflow = cloneWorkflow(initialWorkflow);
  const profile = validationProfiles.find(
    (item) => item.name === "structured-demo",
  )!;
  const input: RecoveryPort = {
    id: `port.${validator.block.id.slice(6)}-subject-result`,
    ownerBlockId: validator.block.id,
    direction: "input",
    name: "result",
    typeId: "type.document.engineering",
    required: true,
    cardinality: "one",
    artifactContractId: null,
    description: "Exact output",
  };
  validator.block.inputPortIds = [input.id];
  validator.block.configuration.validation = JSON.stringify({
    profile: {
      source: "packaged",
      name: profile.name,
      reference: profile.profile_ref,
    },
    baseline: profile.baseline_ref,
    subjects: { result: sourceKey(input.id) },
  });
  workflow.blocks.push(producer.block, validator.block);
  workflow.ports.push(...producer.ports, ...validator.ports, input);
  workflow.relationships.push({
    id: "rel.validator-subject",
    kind: "data",
    sourceId: producer.block.outputPortIds[0]!,
    targetId: input.id,
    label: "Validate output",
    condition: null,
  });
  const apply = vi.fn(() => true);
  render(
    <ValidatorBlockEditor
      block={validator.block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );

  fireEvent.change(
    screen.getByRole("combobox", { name: "Validation revision target" }),
    { target: { value: producer.block.id } },
  );
  const commands = (
    apply.mock.calls[0] as unknown as [
      Array<{
        kind: string;
        key?: string;
        value?: number;
        relationship?: Record<string, unknown>;
      }>,
    ]
  )[0];
  expect(commands).toContainEqual(
    expect.objectContaining({
      kind: "connect",
      relationship: expect.objectContaining({
        kind: "feedback",
        sourceId: validator.block.id,
        targetId: producer.block.id,
      }),
    }),
  );
  expect(commands).toContainEqual(
    expect.objectContaining({ key: "max_revisions", value: 1 }),
  );
  expect(
    screen.getByRole("spinbutton", { name: "Maximum corrected revisions" }),
  ).toBeDisabled();
});
