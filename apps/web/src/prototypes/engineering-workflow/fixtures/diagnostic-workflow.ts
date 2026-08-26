import type { DiagnosticScenario } from "../domain/diagnostic-demo";
import type { WorkflowPreview } from "../workflow-preview-model";

export const diagnosticWorkflow: WorkflowPreview = {
  schemaVersion: "0.1-visual-slice",
  workflowId: "four-block-diagnostic-demo",
  revision: 1,
  title: "Four-Block Diagnostic Workflow",
  purpose:
    "Test a valid workflow that completes successfully but produces an unacceptable result.",
  phases: [
    {
      phaseId: "diagnose",
      index: 1,
      label: "Run and Diagnose",
      description:
        "Follow evidence backward, revise one input, and compare the rerun.",
      tone: "verify",
      height: 270,
    },
  ],
  blocks: [
    {
      blockId: "diagnostic-input",
      phaseId: "diagnose",
      sequence: "1",
      role: "input",
      title: "Prompt / Request",
      purpose: "Runtime text, images, and readable files for this run.",
      badge: "MULTIMODAL INPUT",
      outputPorts: [
        { portId: "request", label: "Complete request", dataType: "request" },
        { portId: "text", label: "Instructions", dataType: "text" },
        { portId: "images", label: "Images", dataType: "images", count: 0 },
        {
          portId: "documents",
          label: "Documents",
          dataType: "documents",
          count: 0,
        },
      ],
      position: { x: 42, y: 92, width: 190, height: 98 },
      inspector: {
        summary:
          "Supply the runtime prompt, images, and readable files required by this workflow.",
        fields: [],
      },
    },
    {
      blockId: "diagnostic-ai-task",
      phaseId: "diagnose",
      sequence: "2",
      role: "ai-task",
      title: "Interpret Request",
      purpose:
        "Use a configured AI to interpret the request and prepare a typed result.",
      badge: "SELECT MODEL",
      outputPorts: [
        { portId: "text", label: "Produced text", dataType: "text" },
      ],
      position: { x: 338, y: 92, width: 190, height: 98 },
      inspector: {
        summary:
          "Select a configured model and thinking level. Wright does not activate workspace MCP tools for this AI task.",
        fields: [
          { label: "Executor", value: "Configured at run time" },
          { label: "Output", value: "None · task did not run" },
        ],
      },
    },
    {
      blockId: "diagnostic-mcp-action",
      phaseId: "diagnose",
      sequence: "3",
      role: "mcp-action",
      title: "Run Selected MCP Tool",
      purpose: "Execute one exact, schema-valid generic MCP call.",
      badge: "NOT RUN",
      position: { x: 634, y: 92, width: 190, height: 98 },
      inspector: {
        summary:
          "After AI output exists, select one exact catalog tool and map its declared input schema.",
        fields: [
          { label: "Binding", value: "No exact tool selected" },
          { label: "Tool result", value: "Not run" },
        ],
      },
    },
    {
      blockId: "diagnostic-evaluation",
      phaseId: "diagnose",
      sequence: "4",
      role: "decision",
      title: "Outcome Acceptable?",
      purpose: "Evidence-based evaluation",
      position: { x: 950, y: 80, width: 122, height: 122 },
      inspector: {
        summary:
          "No artifact exists to evaluate because upstream execution stopped at the AI task.",
        fields: [
          { label: "Definition", value: "Valid" },
          { label: "Evaluation status", value: "Not reached" },
        ],
      },
    },
  ],
  connections: [
    {
      connectionId: "diagnostic-input-to-ai",
      sourceBlockId: "diagnostic-input",
      targetBlockId: "diagnostic-ai-task",
      semantics: "data",
      label: "context",
      sourcePortId: "request",
    },
    {
      connectionId: "diagnostic-ai-to-mcp",
      sourceBlockId: "diagnostic-ai-task",
      targetBlockId: "diagnostic-mcp-action",
      semantics: "control",
      label: "instruction",
      sourcePortId: "text",
    },
    {
      connectionId: "diagnostic-mcp-to-evaluation",
      sourceBlockId: "diagnostic-mcp-action",
      targetBlockId: "diagnostic-evaluation",
      semantics: "data",
      label: "result + evidence",
    },
    {
      connectionId: "diagnostic-feedback",
      sourceBlockId: "diagnostic-evaluation",
      targetBlockId: "diagnostic-input",
      semantics: "feedback",
      label: "revise and rerun",
    },
  ],
};

export const diagnosticScenario: DiagnosticScenario = {
  scenarioId: "unconnected-ai-boundary",
  request: {
    blockId: "diagnostic-input",
    initialPrompt:
      "Create a 100 x 60 x 8 mm editable mounting plate with four 8 mm through holes whose centers are 10 mm from the nearest X and Z edges.",
    requirements: {
      promptRequired: true,
      minImages: 0,
      minDocuments: 0,
    },
  },
  executorBlockId: "diagnostic-ai-task",
  mcpBlockId: "diagnostic-mcp-action",
  mcpBindingDefault: {
    serverName: "BREP MCP",
    toolName: "brep.model.apply_history",
    reason:
      "This diagnostic test explicitly uses BREP MCP and its apply-history operation. The installed catalog identity is resolved at runtime and remains reviewable.",
  },
  evaluationBlockId: "diagnostic-evaluation",
  blockIds: diagnosticWorkflow.blocks.map(({ blockId }) => blockId),
  finding: {
    code: "MCP_TOOL_NOT_SELECTED",
    severity: "medium",
    evaluationBlockId: "diagnostic-mcp-action",
    title: "Exact MCP tool not selected",
    criterion:
      "An MCP action must bind one catalog tool and validate arguments against its exact input schema.",
    expected:
      "An exact MCP server, tool, schema identity, and validated argument mapping.",
    actual:
      "The AI output is reviewable, but no MCP tool or schema mapping has been selected.",
    evidence: [
      {
        nodeId: "diagnostic-mcp-action",
        observation:
          "There is no exact catalog identity or input schema for argument validation.",
      },
    ],
  },
  corrections: [],
};
