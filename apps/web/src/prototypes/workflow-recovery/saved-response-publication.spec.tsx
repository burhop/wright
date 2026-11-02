import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { createAuthoringObject } from "./authoring-objects";
import { initialLayout, initialWorkflow, type RecoveryWorkflow } from "./model";
import { PromptBlockEditor } from "./PromptBlockEditor";
import { McpBlockEditor } from "./McpBlockEditor";
import { sourceKey } from "./prompt-settings";
import { configuredOutputs } from "./output-contracts";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  textEditCommands,
  type RecoveryCommand,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

afterEach(cleanup);

function fixture(kind: "ai-prompt" | "mcp-tool", policy?: string) {
  const workflow: RecoveryWorkflow = structuredClone(initialWorkflow);
  const layout = { ...structuredClone(initialLayout), positions: {} };
  workflow.blocks = [];
  workflow.ports = [];
  workflow.relationships = [];
  workflow.artifactContracts = [];
  workflow.bindings = [];
  workflow.components = [];
  for (const phase of workflow.phases) phase.blockIds = [];
  const add = createAuthoringObject(kind, workflow, layout);
  const file = {
    ...add.ports.find((port) => port.direction === "output")!,
    id: `port.${add.block.id.slice(6)}-saved-response`,
    name: "Saved response",
    typeId: "type.file.workspace",
  };
  add.block.outputPortIds.push(file.id);
  Object.assign(add.block.configuration, {
    save_output: true,
    output_format: "json",
    output_filename: "outputs/{{wright.run_id}}/response.json",
    ...(kind === "mcp-tool"
      ? { mcp_tool: "selected__inspect", mcp_server: "selected" }
      : {}),
    ...(policy
      ? {
          file_policy: policy,
          saved_response_file_port: sourceKey(file.id),
          run_path_template: "wright.run-path/1",
        }
      : {}),
  });
  workflow.blocks = [add.block];
  workflow.ports = [...add.ports, file];
  workflow.phases
    .find((phase) => phase.id === add.block.phaseId)
    ?.blockIds.push(add.block.id);
  return { workflow, layout, block: add.block, file };
}

const cases = (["ai-prompt", "mcp-tool"] as const).flatMap((kind) =>
  ["publish_indexed", "publish_overwrite"].map((policy) => ({ kind, policy })),
);

it.each(cases)(
  "preserves and displays source-authored $policy on $kind",
  ({ kind, policy }) => {
    const original = fixture(kind, policy);
    const source = formatRecoveryAuthoringSource(original.workflow).text;
    const reopened = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
    const workflow = reopened.workflow!;
    const block = workflow.blocks.find(
      (item) => item.id === original.block.id,
    )!;
    expect(block.configuration).toMatchObject({
      file_policy: policy,
      saved_response_file_port: sourceKey(original.file.id),
      run_path_template: "wright.run-path/1",
    });
    const onApply = vi.fn(() => true);
    const Editor = kind === "mcp-tool" ? McpBlockEditor : PromptBlockEditor;
    render(
      <Editor
        block={block}
        workflow={workflow}
        readOnly={false}
        onApply={onApply}
      />,
    );
    const select = screen.getByTestId(
      kind === "mcp-tool"
        ? "workflow-recovery-mcp-file-policy"
        : "workflow-recovery-file-policy",
    );
    expect(select).toHaveValue(policy);
    expect(select).toBeDisabled();
    expect(
      within(select).getByRole("option", { selected: true }),
    ).toHaveTextContent(
      policy === "publish_overwrite"
        ? "this run's configured path"
        : "indexed response file",
    );
    expect(
      screen.getByTestId("workflow-recovery-response-publication"),
    ).toHaveTextContent(sourceKey(original.file.id));
    expect(
      screen.getByTestId(
        kind === "mcp-tool"
          ? "workflow-recovery-mcp-save"
          : "workflow-recovery-save-response",
      ),
    ).toBeDisabled();
    const filename = screen.getByTestId(
      kind === "mcp-tool"
        ? "workflow-recovery-mcp-filename"
        : "workflow-recovery-output-filename",
    );
    expect(filename).not.toHaveAttribute("readonly");
    expect(onApply).not.toHaveBeenCalled();
    expect(formatRecoveryAuthoringSource(workflow).text).toContain(
      `"saved_response_file_port":"${sourceKey(original.file.id)}"`,
    );
  },
);

it.each(["ai-prompt", "mcp-tool"] as const)(
  "keeps ordinary %s save choices editable without offering an unbound publication",
  (kind) => {
    const { workflow, block } = fixture(kind);
    const onApply = vi.fn(() => true);
    const Editor = kind === "mcp-tool" ? McpBlockEditor : PromptBlockEditor;
    render(
      <Editor
        block={block}
        workflow={workflow}
        readOnly={false}
        onApply={onApply}
      />,
    );
    const select = screen.getByTestId(
      kind === "mcp-tool"
        ? "workflow-recovery-mcp-file-policy"
        : "workflow-recovery-file-policy",
    );
    expect(select).toBeEnabled();
    expect(
      within(select)
        .getAllByRole("option")
        .map((option) => (option as HTMLOptionElement).value),
    ).toEqual(["indexed", "overwrite"]);
    expect(
      screen.queryByTestId("workflow-recovery-response-publication"),
    ).toBeNull();
    fireEvent.change(select, { target: { value: "overwrite" } });
    expect(onApply).toHaveBeenCalledWith([
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "file_policy",
        value: "overwrite",
      },
    ]);
  },
);

it("keeps an incomplete source-authored publication visible without inventing its file port", () => {
  const { workflow, block } = fixture("ai-prompt", "publish_overwrite");
  delete block.configuration.saved_response_file_port;
  const onApply = vi.fn(() => true);
  render(
    <PromptBlockEditor
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={onApply}
    />,
  );
  expect(
    screen.getByTestId("workflow-recovery-response-publication"),
  ).toHaveTextContent("not configured");
  expect(screen.getByTestId("workflow-recovery-file-policy")).toBeDisabled();
  expect(onApply).not.toHaveBeenCalled();
});

it.each([
  { key: "output_filename", value: "outputs/{{wright.run_id}}/different.json" },
  { key: "output_format", value: "text" },
  { key: "saved_response_file_port", value: "" },
  { key: "save_output", value: false },
  { key: "file_policy", value: "indexed" },
])(
  "protects connected saved response files from $key changes through forms and Source",
  ({ key, value }) => {
    const { workflow, layout, block, file } = fixture(
      "ai-prompt",
      "publish_overwrite",
    );
    const consumer = createAuthoringObject("ai-prompt", workflow, layout);
    consumer.block.title = "Inspect exact saved response";
    const target = consumer.ports.find((port) => port.direction === "input")!;
    target.typeId = "type.file.workspace";
    workflow.blocks.push(consumer.block);
    workflow.ports.push(...consumer.ports);
    workflow.relationships.push({
      id: "rel.saved-response",
      kind: "data",
      sourceId: file.id,
      targetId: target.id,
      label: "Exact saved response",
      condition: null,
    });
    expect(
      configuredOutputs(block, workflow).get(sourceKey(file.id)),
    ).toMatchObject({
      format: "json",
      path: "outputs/{{wright.run_id}}/response.json",
    });
    const commands: RecoveryCommand[] = [
      { kind: "set_block_configuration", blockId: block.id, key, value },
    ];
    const form = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", commands),
    );
    expect(form.ok).toBe(false);
    expect(form.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-CONNECTED-OUTPUT-CHANGE" }),
    );
    const changed = structuredClone(workflow);
    changed.blocks.find((item) => item.id === block.id)!.configuration[key] =
      value;
    const parsed = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(changed).text,
      workflow,
    );
    expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
    const source = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(
        workflow.revision,
        "text",
        textEditCommands(
          workflow,
          parsed.workflow!,
          layout,
        ) as RecoveryCommand[],
      ),
    );
    expect(source.ok).toBe(false);
    expect(source.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-CONNECTED-OUTPUT-CHANGE" }),
    );
    expect(
      workflow.relationships.some((edge) => edge.sourceId === file.id),
    ).toBe(true);
  },
);
