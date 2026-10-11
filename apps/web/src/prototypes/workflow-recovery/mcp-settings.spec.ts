import { expect, it } from "vitest";
import acceptedManufacturingSource from "../../../tests/fixtures/corrected-manufacturing.workflow.wflow?raw";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
  type RecoveryCommand,
} from "./command-system";
import {
  initialWorkflow,
  initialLayout,
  cloneWorkflow,
  type RecoveryWorkflow,
  type RecoveryLayout,
} from "./model";
import { createAuthoringObject } from "./authoring-objects";
import {
  configureMcpTool,
  connectMcpInput,
  mcpCandidates,
  type WorkflowMcpTool,
} from "./mcp-settings";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
const tool: WorkflowMcpTool = {
  name: "docs__search",
  server_id: "docs",
  tool_name: "search",
  title: "Search docs",
  description: "Search documentation",
  schema_digest: "a".repeat(64),
  input_schema: {
    type: "object",
    properties: {
      query: { type: "string" },
      limit: { type: "integer", default: 3 },
    },
    required: ["query"],
  },
};
function apply(
  state: { workflow: RecoveryWorkflow; layout: RecoveryLayout },
  commands: RecoveryCommand[],
) {
  const result = applyRecoveryBatch(
    state.workflow,
    state.layout,
    recoveryCommandBatch(state.workflow.revision, "form", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  return acceptRecoveryResult(state.workflow, state.layout, result)!;
}
it("binds discovered tool inputs, connects a prompt response, and reconstructs from workspace source", () => {
  let state = { workflow: initialWorkflow, layout: initialLayout };
  const added = createAuthoringObject("mcp-tool", state.workflow, state.layout);
  state = apply(state, [added]);
  state = apply(state, configureMcpTool(added.block, state.workflow, tool));
  const prompt = createAuthoringObject(
    "ai-prompt",
    state.workflow,
    state.layout,
  );
  state = apply(state, [prompt]);
  const block = state.workflow.blocks.find((b) => b.id === added.block.id)!;
  const target = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "query",
  )!;
  const response = prompt.ports.find((p) => p.direction === "output")!;
  expect(
    mcpCandidates(block, state.workflow, target).some(
      (p) => p.id === response.id,
    ),
  ).toBe(true);
  expect(
    mcpCandidates(block, state.workflow, target).some(
      (p) => p.typeId === "type.image.reference-set",
    ),
  ).toBe(false);
  state = apply(
    state,
    connectMcpInput(block, state.workflow, target.id, response.id),
  );
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(state.workflow).text,
    initialWorkflow,
  );
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(
    reopened.workflow!.blocks.find((b) => b.id === block.id)!.configuration
      .mcp_tool,
  ).toBe(tool.name);
  expect(
    reopened.workflow!.relationships.some(
      (e) => e.sourceId === response.id && e.targetId === target.id,
    ),
  ).toBe(true);
  const changed = apply(
    state,
    configureMcpTool(
      state.workflow.blocks.find((b) => b.id === block.id)!,
      state.workflow,
      {
        ...tool,
        name: "docs__list",
        input_schema: { type: "object", properties: {} },
      },
    ),
  );
  expect(
    changed.workflow.ports.filter(
      (p) => p.ownerBlockId === block.id && p.direction === "input",
    ),
  ).toHaveLength(1);
  expect(
    changed.workflow.relationships.some((e) => e.targetId === target.id),
  ).toBe(false);
});
it("converts compatible text connection types atomically and rejects non-JSON whole arguments", () => {
  let state = { workflow: initialWorkflow, layout: initialLayout };
  const added = createAuthoringObject("mcp-tool", state.workflow, state.layout);
  state = apply(state, [added]);
  state = apply(state, configureMcpTool(added.block, state.workflow, tool));
  const block = state.workflow.blocks.find((b) => b.id === added.block.id)!;
  const target = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "query",
  )!;
  const textBlock = createAuthoringObject(
    "text-input",
    state.workflow,
    state.layout,
  );
  state = apply(state, [textBlock]);
  const text = state.workflow.ports.find(
    (p) =>
      p.direction === "output" &&
      p.typeId === "type.value.text" &&
      p.ownerBlockId !== block.id,
  )!;
  state = apply(
    state,
    connectMcpInput(block, state.workflow, target.id, text.id),
  );
  expect(state.workflow.ports.find((p) => p.id === target.id)!.typeId).toBe(
    text.typeId,
  );
  const args = state.workflow.ports.find(
    (p) => p.ownerBlockId === block.id && p.name === "Arguments (JSON)",
  )!;
  expect(() =>
    connectMcpInput(block, state.workflow, args.id, text.id),
  ).toThrow("matches");
});

function sourceWithFileDependencies(
  dependencies: unknown,
  template = "mcp-tool",
): string {
  let state = { workflow: initialWorkflow, layout: initialLayout };
  const added = createAuthoringObject("mcp-tool", state.workflow, state.layout);
  state = apply(state, [added]);
  state = apply(state, configureMcpTool(added.block, state.workflow, tool));
  return formatRecoveryAuthoringSource(state.workflow).text.replace(
    /(^task [^\n]+\n[\s\S]*?\n {2}settings: )([^\n]+)/gm,
    (match, prefix: string, value: string) => {
      const settings = JSON.parse(value);
      if (settings.mcp_tool !== tool.name) return match;
      return (
        prefix +
        JSON.stringify({
          ...settings,
          authoring_template: template,
          mcp_file_dependencies: dependencies,
          expected_file_ports: { model: "process-proofs/case/plate.step" },
        })
      );
    },
  );
}

it("preserves connected-output bindings and explicit attempt templates on save and reopen", () => {
  const source = sourceWithFileDependencies(
    { authored_source: { source: "connected_output" } },
    "mcp-task",
  ).replace(
    '"expected_file_ports":{"model":"process-proofs/case/plate.step"}',
    '"run_path_template":"wright.run-path/2","expected_file_ports":{"model":"outputs/{{wright.run_id}}/create/{{wright.producer_attempt}}/plate.step"}',
  );
  const parsed = parseRecoveryAuthoringSource(source, initialWorkflow);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const formatted = formatRecoveryAuthoringSource(parsed.workflow!).text;
  expect(formatted).toContain('"source":"connected_output"');
  expect(formatted).toContain('"run_path_template":"wright.run-path/2"');
  expect(formatted).toContain("{{wright.producer_attempt}}");
  const reopened = parseRecoveryAuthoringSource(formatted, initialWorkflow);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(formatRecoveryAuthoringSource(reopened.workflow!).text).toBe(
    formatted,
  );
});

it.each(["mcp-tool", "mcp-task"])(
  "cold-round-trips %s file dependencies alongside produced file ports",
  (template) => {
    const dependencies = {
      authored_source: "process-proofs/case/plate-source.py",
    };
    const source = sourceWithFileDependencies(dependencies, template);
    expect(source).toContain('"mcp_file_dependencies":');
    const parsed = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
    const formatted = formatRecoveryAuthoringSource(parsed.workflow!).text;
    expect(formatted).toContain(
      '"mcp_file_dependencies":{"authored_source":"process-proofs/case/plate-source.py"}',
    );
    expect(formatted).toContain(
      '"expected_file_ports":{"model":"process-proofs/case/plate.step"}',
    );
    const reopened = parseRecoveryAuthoringSource(formatted, initialWorkflow);
    expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
    expect(formatRecoveryAuthoringSource(reopened.workflow!).text).toBe(
      formatted,
    );
  },
);

it("rejects tool file dependencies on a plain AI task", () => {
  const parsed = parseRecoveryAuthoringSource(
    sourceWithFileDependencies({ source: "native.stl" }, "ai-prompt"),
    initialWorkflow,
  );
  expect(parsed.ok).toBe(false);
});

it.each([
  null,
  [],
  { source: 42 },
  { source: { path: "plate.py" } },
  { source: "../plate.py" },
  { source: "C:/plate.py" },
  { source: "plate\\source.py" },
])("rejects malformed tool file-dependency maps (%#)", (dependencies) => {
  const parsed = parseRecoveryAuthoringSource(
    sourceWithFileDependencies(dependencies),
    initialWorkflow,
  );
  expect(parsed.ok).toBe(false);
  expect(
    parsed.diagnostics.some((item) => item.code === "WFR-SOURCE-FIELD-TYPE"),
  ).toBe(true);
});

function sourceWithTaskTools(tools: unknown, template = "mcp-task"): string {
  return sourceWithFileDependencies({}, template).replace(
    /(^task [^\n]+\n[\s\S]*?\n {2}settings: )([^\n]+)/gm,
    (match, prefix: string, value: string) => {
      const settings = JSON.parse(value);
      if (settings.mcp_tool !== tool.name) return match;
      return prefix + JSON.stringify({ ...settings, mcp_task_tools: tools });
    },
  );
}

it.each(
  [[], ["inspect_file"], ["inspect_file", "measure"]].map((tools) => ({
    tools,
  })),
)(
  "cold-round-trips a bounded distinct MCP task allowlist (%#)",
  ({ tools }) => {
    const parsed = parseRecoveryAuthoringSource(
      sourceWithTaskTools(tools),
      initialWorkflow,
    );
    expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
    const formatted = formatRecoveryAuthoringSource(parsed.workflow!).text;
    expect(formatted).toContain('"mcp_task_tools":' + JSON.stringify(tools));
    const reopened = parseRecoveryAuthoringSource(formatted, initialWorkflow);
    expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
    expect(formatRecoveryAuthoringSource(reopened.workflow!).text).toBe(
      formatted,
    );
  },
);

it.each(
  [
    null,
    {},
    [42],
    [""],
    ["inspect_file", "inspect_file"],
    Array.from({ length: 33 }, (_, i) => "tool_" + i),
  ].map((tools) => ({ tools })),
)("rejects malformed MCP task tool lists (%#)", ({ tools }) => {
  const parsed = parseRecoveryAuthoringSource(
    sourceWithTaskTools(tools),
    initialWorkflow,
  );
  expect(parsed.ok).toBe(false);
  expect(
    parsed.diagnostics.some((d) => d.code === "WFR-SOURCE-FIELD-TYPE"),
  ).toBe(true);
});

it("rejects a nonempty task allowlist on an exact configured tool step", () => {
  expect(
    parseRecoveryAuthoringSource(
      sourceWithTaskTools(["inspect_file"], "mcp-tool"),
      initialWorkflow,
    ).ok,
  ).toBe(false);
});

it("opens the actual accepted manufacturing source with its read-only report allowlist", () => {
  const source = acceptedManufacturingSource;
  const base = cloneWorkflow(initialWorkflow);
  base.workflowId = "workflow.retained_consumer_003";
  const parsed = parseRecoveryAuthoringSource(source, base);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const formatted = formatRecoveryAuthoringSource(parsed.workflow!).text;
  expect(formatted).toContain('"mcp_task_tools":["inspect_file"]');
  const reopened = parseRecoveryAuthoringSource(formatted, base);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
});
