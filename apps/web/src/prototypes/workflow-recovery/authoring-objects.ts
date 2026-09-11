import type { RecoveryCommand } from "./command-system";
import {
  RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY,
  recoveryAuthoringSectionKind,
  type RecoveryBlock,
  type RecoveryDiagnostic,
  type RecoveryLayout,
  type RecoveryPort,
  type RecoveryRelationship,
  type RecoveryWorkflow,
} from "./model";
import {
  findAuthoringPosition,
  type AuthoringPoint,
} from "./authoring-positioning";

export {
  findAuthoringPosition,
  hydrateAuthoringLayout,
} from "./authoring-positioning";

export type AuthoringGroup =
  "input" | "document" | "tool" | "check3d" | "drawing" | "fdm" | "more";
export const AUTHORING_GROUPS: readonly {
  id: AuthoringGroup;
  label: string;
  description: string;
}[] = [
  {
    id: "input",
    label: "Input",
    description: "Text and existing workspace files",
  },
  {
    id: "document",
    label: "AI prompt",
    description: "Generate a response from a prompt",
  },
  {
    id: "tool",
    label: "MCP servers",
    description:
      "Add a task configured for an available application or service",
  },
  { id: "more", label: "Review", description: "Engineer review and approval" },
];

interface TemplatePort {
  key: string;
  name: string;
  typeId: string;
  direction: RecoveryPort["direction"];
  required?: boolean;
  cardinality?: RecoveryPort["cardinality"];
}
export interface AuthoringTemplate {
  id: string;
  group: AuthoringGroup;
  label: string;
  description: string;
  executionKind: RecoveryBlock["executionKind"];
  instructions: string;
  ports: readonly TemplatePort[];
  inputMode?: "text" | "workspace-file";
  applicationHint?: string;
  configuration?: Record<string, string | number | boolean>;
}
const textIn: TemplatePort = {
  key: "text-in",
  name: "Design text",
  typeId: "type.value.text",
  direction: "input",
};
const fileIn: TemplatePort = {
  key: "file-in",
  name: "Reference document",
  typeId: "type.file.workspace",
  direction: "input",
  required: false,
  cardinality: "optional",
};
const documentOut: TemplatePort = {
  key: "document-out",
  name: "Engineering document",
  typeId: "type.document.engineering",
  direction: "output",
};
const modelIn: TemplatePort = {
  key: "model-in",
  name: "CAD model",
  typeId: "type.geometry.brep",
  direction: "input",
};
const reportOut: TemplatePort = {
  key: "report-out",
  name: "Check report",
  typeId: "type.report.check",
  direction: "output",
};
const verdictOut: TemplatePort = {
  key: "verdict-out",
  name: "Check result",
  typeId: "type.verdict.check",
  direction: "output",
};
const draftInstructions =
  "Describe the required inputs, expected outputs, and acceptance criteria. This draft step is not bound to an execution tool.";

export const AUTHORING_TEMPLATES: readonly AuthoringTemplate[] = [
  {
    id: "ai-prompt",
    group: "document",
    label: "AI prompt",
    description: "Write a prompt or use another step's response",
    executionKind: "ai_capable",
    instructions: "Describe what you want the AI to do.",
    configuration: {
      prompt_source: "inline",
      output_format: "text",
      save_output: false,
      file_policy: "indexed",
    },
    ports: [
      {
        key: "prompt-in",
        name: "Prompt",
        typeId: "type.document.engineering",
        direction: "input",
        required: false,
        cardinality: "optional",
      },
      { ...documentOut, name: "Response" },
    ],
  },
  {
    id: "text-input",
    group: "input",
    label: "Text input",
    description: "Write requirements, design intent, or notes",
    executionKind: "human",
    instructions: "Provide the engineering text used by connected steps.",
    inputMode: "text",
    ports: [
      {
        key: "text-out",
        name: "Design text",
        typeId: "type.value.text",
        direction: "output",
      },
    ],
  },
  {
    id: "file-input",
    group: "input",
    label: "Workspace file",
    description: "Reference an existing document in this workspace",
    executionKind: "human",
    instructions:
      "Select a permitted workspace file. Wright retains the reference; selecting it does not run a tool.",
    inputMode: "workspace-file",
    ports: [
      {
        key: "file-out",
        name: "Workspace file",
        typeId: "type.file.workspace",
        direction: "output",
      },
    ],
  },
  {
    id: "image-input",
    group: "input",
    label: "Image",
    description: "Select one image from this workspace",
    executionKind: "human",
    instructions:
      "Select one reference image that explains the intended design.",
    inputMode: "workspace-file",
    ports: [
      {
        key: "images-out",
        name: "Image",
        typeId: "type.image.reference-set",
        direction: "output",
        cardinality: "one",
      },
    ],
  },
  {
    id: "document",
    group: "document",
    label: "Engineering document",
    description: "Unbound document-writing step with an editable prompt",
    executionKind: "ai_capable",
    instructions:
      "Draft an engineering document from the connected design text and reference document. State assumptions and questions for engineer review.",
    ports: [textIn, fileIn, documentOut],
  },
  {
    id: "html-report",
    group: "document",
    label: "HTML report",
    description: "Create one self-contained HTML report in this workspace",
    executionKind: "ai_capable",
    instructions:
      "Write a concise engineering report. State assumptions, include any needed comparison or table, and conclude with the recommended next action.",
    configuration: { output_format: "html", output_filename: "report.html" },
    ports: [documentOut],
  },
  {
    id: "design-specification",
    group: "document",
    label: "Design specification",
    description: "Describe a design-specification drafting step",
    executionKind: "ai_capable",
    instructions:
      "Draft a design specification from the supplied design text and reference document. Separate known facts from assumptions and require engineer review.",
    ports: [
      textIn,
      fileIn,
      {
        key: "specification-out",
        name: "Design specification",
        typeId: "type.design.specification",
        direction: "output",
      },
    ],
  },
  {
    id: "work-order",
    group: "document",
    label: "Work order",
    description: "Describe work, deliverables, and acceptance criteria",
    executionKind: "ai_capable",
    instructions:
      "Draft a work order from the supplied design text and reference document, naming deliverables, constraints, and review criteria.",
    ports: [textIn, fileIn, { ...documentOut, name: "Work order" }],
  },
  {
    id: "mcp-task",
    group: "tool",
    label: "AI task with MCP",
    description:
      "Describe the task; AI chooses tools from one workspace server",
    executionKind: "ai_capable",
    instructions: "",
    configuration: {
      output_format: "text",
      save_output: false,
      file_policy: "indexed",
      max_tool_calls: 8,
      timeout_seconds: 300,
    },
    ports: [{ ...documentOut, name: "Task result" }],
  },
  {
    id: "mcp-tool",
    group: "tool",
    label: "MCP tool",
    description: "Choose a tool available to this workspace",
    executionKind: "deterministic",
    instructions: "Run the selected MCP tool with its configured inputs.",
    configuration: {
      output_format: "json",
      save_output: false,
      file_policy: "indexed",
    },
    ports: [
      {
        key: "result-out",
        name: "Result",
        typeId: "type.result.structured",
        direction: "output",
      },
      {
        key: "text-out",
        name: "Text",
        typeId: "type.value.text",
        direction: "output",
      },
    ],
  },
  {
    id: "model-check",
    group: "check3d",
    label: "Check CAD model",
    description: "Unbound model check with separate report and result",
    executionKind: "deterministic",
    instructions:
      "Define the geometric checks, units, tolerances, and acceptance criteria for the CAD model.",
    ports: [modelIn, reportOut, verdictOut],
  },
  {
    id: "dimension-check",
    group: "check3d",
    label: "Check dimensions",
    description: "Compare model dimensions with stated requirements",
    executionKind: "deterministic",
    instructions:
      "Specify the dimensions and tolerances to check. Record measured values, units, and deviations in the report.",
    ports: [
      modelIn,
      {
        key: "specification-in",
        name: "Design specification",
        typeId: "type.design.specification",
        direction: "input",
      },
      reportOut,
      verdictOut,
    ],
  },
  {
    id: "drawing-check",
    group: "drawing",
    label: "Check drawing",
    description: "Define a drawing review with a report and result",
    executionKind: "deterministic",
    instructions:
      "Check required dimensions, tolerances, notes, and revision information against the design requirements.",
    ports: [
      {
        key: "drawing-in",
        name: "Manufacturing drawing",
        typeId: "type.file.drawing",
        direction: "input",
      },
      reportOut,
      verdictOut,
    ],
  },
  {
    id: "fdm-check",
    group: "fdm",
    label: "Check FDM printability",
    description:
      "Unbound check for material, orientation, and print constraints",
    executionKind: "deterministic",
    instructions:
      "Specify printer, material, layer height, orientation, support, and wall-thickness criteria before evaluating printability.",
    ports: [modelIn, reportOut, verdictOut],
  },
  {
    id: "engineering-step",
    group: "more",
    label: "Engineering step",
    description: "Describe additional work without an execution binding",
    executionKind: "deterministic",
    instructions: draftInstructions,
    ports: [
      {
        key: "document-in",
        name: "Engineering document",
        typeId: "type.document.engineering",
        direction: "input",
      },
      documentOut,
    ],
  },
  {
    id: "manual-review",
    group: "more",
    label: "Engineer review",
    description: "Review the final document and approve or request changes",
    executionKind: "human",
    instructions:
      "Review the connected document for completeness, accuracy, assumptions, and unresolved questions. Approve it or request changes with review notes.",
    ports: [
      {
        key: "document-in",
        name: "Engineering document",
        typeId: "type.document.engineering",
        direction: "input",
      },
    ],
  },
];

export function createAuthoringObject(
  templateId: string,
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  options: {
    selectedBlockId?: string | null;
    viewportCenter?: AuthoringPoint;
  } = {},
): Extract<RecoveryCommand, { kind: "add_block" }> {
  const template = AUTHORING_TEMPLATES.find((item) => item.id === templateId);
  if (!template) throw new Error(`Unknown authoring template: ${templateId}`);
  const ids = new Set(
    [
      ...workflow.blocks,
      ...workflow.ports,
      ...workflow.artifactContracts,
      ...workflow.bindings,
      ...workflow.relationships,
      ...workflow.components,
      ...workflow.phases,
    ].map((item) => item.id),
  );
  let index = 1;
  while (
    ids.has(`block.${template.id}-${index}`) ||
    template.ports.some((port) =>
      ids.has(`port.${template.id}-${index}-${port.key}`),
    )
  )
    index += 1;
  const suffix = `${template.id}-${index}`;
  const blockId = `block.${suffix}`;
  const ports: RecoveryPort[] = template.ports.map((port) => ({
    id: `port.${suffix}-${port.key}`,
    ownerBlockId: blockId,
    direction: port.direction,
    name: port.name,
    typeId: port.typeId,
    required: port.required ?? true,
    cardinality: port.cardinality ?? "one",
    artifactContractId: null,
    description: `${port.name} ${port.direction === "input" ? "used by" : "expected from"} this step; no run output is implied.`,
  }));
  const configuration: RecoveryBlock["configuration"] = {
    authoring_template: template.id,
    ...template.configuration,
  };
  if (template.id === "ai-prompt")
    configuration.prompt_input = ports[0]!.id.slice(5).replaceAll("-", "_");
  if (template.group === "input")
    Object.assign(configuration, {
      [RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY]: "input",
      input_mode: template.inputMode!,
      input_text: "",
      workspace_file: "",
    });
  else configuration.binding_state = "unbound";
  if (template.applicationHint)
    configuration.application_hint = template.applicationHint;
  const selectedPosition = options.selectedBlockId
    ? layout.positions[options.selectedBlockId]
    : undefined;
  const preferred =
    template.group === "input"
      ? { x: 40, y: 100 }
      : selectedPosition
        ? { x: selectedPosition.x + 320, y: selectedPosition.y }
        : (options.viewportCenter ?? { x: 380, y: 100 });
  return {
    kind: "add_block",
    block: {
      id: blockId,
      title: template.label,
      purpose: template.description,
      kind: "work",
      executionKind: template.executionKind,
      phaseId: null,
      instructions: template.instructions,
      configuration,
      inputPortIds: ports
        .filter((port) => port.direction === "input")
        .map((port) => port.id),
      outputPortIds: ports
        .filter((port) => port.direction === "output")
        .map((port) => port.id),
      bindingId: null,
      componentRef: null,
    },
    ports,
    position: findAuthoringPosition(workflow, layout, preferred),
  };
}

export interface AuthoringInputState {
  status: "missing" | "configured" | "unavailable";
  summary: string;
  reason?: string;
}

export function isSafeWorkspaceInputPath(value: string): boolean {
  // eslint-disable-next-line no-control-regex -- reject ASCII control characters in workspace paths
  const hasUnsafeCharacter = /[\\%<>:"|?*\u0000-\u001f\u007f]/.test(value);
  if (
    value.length === 0 ||
    value.length > 1024 ||
    value !== value.trim() ||
    hasUnsafeCharacter ||
    value.startsWith("/") ||
    /^[a-z]+:/i.test(value)
  )
    return false;
  return value
    .split("/")
    .every(
      (part) =>
        part.length > 0 &&
        part !== "." &&
        part !== ".." &&
        !/[. ]$/.test(part) &&
        !/^\.(?:git|wright)$/i.test(part) &&
        !/^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(part),
    );
}

/** Shared by every command and source parse, not only the file-picker UI. */
export function validateAuthoringConfiguration(
  block: RecoveryBlock,
): RecoveryDiagnostic[] {
  const diagnostics: RecoveryDiagnostic[] = [];
  const fail = (code: string, explanation: string, correction: string) =>
    diagnostics.push({
      code,
      explanation,
      correction,
      semanticId: block.id,
      line: null,
    });
  const configuration = block.configuration;
  if (
    configuration.authoring_template === "mcp-task" &&
    configuration.max_tool_calls !== undefined &&
    (typeof configuration.max_tool_calls !== "number" ||
      !Number.isInteger(configuration.max_tool_calls) ||
      configuration.max_tool_calls < 1 ||
      configuration.max_tool_calls > 32)
  ) {
    fail(
      "WFR-MCP-TASK-LIMIT-INVALID",
      "Maximum tool calls must be a whole number from 1 to 32.",
      "Choose 1–32 calls; the default is 8 and the task time limit still applies.",
    );
  }
  if (
    Object.keys(configuration).some((key) =>
      ["__proto__", "prototype", "constructor"].includes(key),
    )
  )
    fail(
      "WFR-INPUT-CONFIGURATION-INVALID",
      "The setting name is reserved and cannot be authored.",
      "Choose an ordinary engineering setting name.",
    );
  if (
    Object.values(configuration).some(
      (value) =>
        !["string", "number", "boolean"].includes(typeof value) ||
        (typeof value === "number" && !Number.isFinite(value)),
    )
  )
    fail(
      "WFR-INPUT-CONFIGURATION-INVALID",
      "Step settings must contain finite numbers, text, or true/false values.",
      "Correct the invalid setting; the previous workflow remains unchanged.",
    );
  if (
    configuration.workspace_file !== undefined &&
    (typeof configuration.workspace_file !== "string" ||
      (configuration.workspace_file !== "" &&
        !isSafeWorkspaceInputPath(configuration.workspace_file)))
  )
    fail(
      "WFR-INPUT-PATH-INVALID",
      "The input file must be a regular relative path inside this workspace.",
      "Choose a file from this workspace; absolute paths, parent traversal, encoded paths, and managed directories are not allowed.",
    );
  if (
    configuration.input_text !== undefined &&
    (typeof configuration.input_text !== "string" ||
      configuration.input_text.length > 65_536)
  )
    fail(
      "WFR-INPUT-TEXT-INVALID",
      "Input text must be text no longer than 65,536 characters.",
      "Shorten the text or reference a workspace document.",
    );
  if (
    configuration.input_mode !== undefined &&
    !["text", "workspace-file", "text-or-document"].includes(
      String(configuration.input_mode),
    )
  )
    fail(
      "WFR-INPUT-MODE-INVALID",
      "The input mode is not supported.",
      "Use text or workspace-file.",
    );
  return diagnostics;
}

export function canConnectAuthoringPorts(
  source:
    | Pick<
        RecoveryPort,
        "direction" | "typeId" | "cardinality" | "ownerBlockId"
      >
    | undefined,
  target:
    | Pick<
        RecoveryPort,
        "direction" | "typeId" | "cardinality" | "ownerBlockId"
      >
    | undefined,
): boolean {
  return Boolean(
    source &&
    target &&
    source.direction === "output" &&
    target.direction === "input" &&
    source.ownerBlockId !== target.ownerBlockId &&
    source.typeId === target.typeId &&
    (source.cardinality !== "many" || target.cardinality === "many"),
  );
}

/** The old image-input template marked its single file as a collection.
 * Repair only that template; genuinely authored collection inputs stay intact. */
export function singleImageInputCorrections(
  workflow: RecoveryWorkflow,
): RecoveryCommand[] {
  const singleFileBlocks = new Set(
    workflow.blocks
      .filter(
        (block) =>
          block.configuration.authoring_template === "image-input" &&
          block.configuration.input_mode === "workspace-file",
      )
      .map((block) => block.id),
  );
  return workflow.ports
    .filter(
      (port) =>
        singleFileBlocks.has(port.ownerBlockId) &&
        port.direction === "output" &&
        port.typeId === "type.image.reference-set" &&
        port.cardinality === "many",
    )
    .map((port) => ({
      kind: "set_port_contract",
      portId: port.id,
      required: port.required,
      cardinality: "one",
    }));
}

/** Do not silently narrow a collection value to one item. The retained
 * contract still permits a single producer to feed a many-valued input. */
export function validateAuthoringConnections(
  workflow: RecoveryWorkflow,
): RecoveryDiagnostic[] {
  const ports = new Map(workflow.ports.map((port) => [port.id, port]));
  return workflow.relationships.flatMap(
    (relationship): RecoveryDiagnostic[] => {
      if (relationship.kind !== "data") return [];
      const source = ports.get(relationship.sourceId);
      const target = ports.get(relationship.targetId);
      if (
        source?.cardinality !== "many" ||
        !target ||
        target.cardinality === "many"
      )
        return [];
      return [
        {
          code: "WFR-PORT-COLLECTION-MISMATCH",
          semanticId: relationship.id,
          line: null,
          explanation: `${source.name} supplies a collection but ${target.name} accepts one item.`,
          correction:
            "Use a collection input or an explicit step that selects an item from the collection.",
        },
      ];
    },
  );
}

export function authoringInputState(
  block: RecoveryBlock,
  permittedFiles?: readonly string[],
): AuthoringInputState {
  const diagnostics = validateAuthoringConfiguration(block);
  if (diagnostics.length > 0)
    return {
      status: "unavailable",
      summary: "Input needs correction",
      reason: diagnostics[0]!.explanation,
    };
  const mode = block.configuration.input_mode;
  const text =
    typeof block.configuration.input_text === "string"
      ? block.configuration.input_text
      : "";
  const path =
    typeof block.configuration.workspace_file === "string"
      ? block.configuration.workspace_file
      : "";
  if (mode === "workspace-file" || (mode !== "text" && path)) {
    if (!path)
      return {
        status: "missing",
        summary: "No file path",
        reason: "Enter a workspace-relative file path.",
      };
    if (permittedFiles && !permittedFiles.includes(path))
      return {
        status: "unavailable",
        summary: path,
        reason:
          "This file is not available in the current workspace. Choose another file.",
      };
    return {
      status: "configured",
      summary: path,
      reason:
        "A file reference is configured; it is checked again before opening. This is not an execution result.",
    };
  }
  if (text.trim())
    return {
      status: "configured",
      summary: `${text.trim().length.toLocaleString("en-US")} characters`,
      reason: "Engineer-authored text is configured, not executed or approved.",
    };
  return {
    status: "missing",
    summary: "Not configured",
    reason: "Enter text or a workspace-relative file path.",
  };
}

export function authoringReadiness(
  workflow: RecoveryWorkflow,
  permittedFiles?: readonly string[],
) {
  const inputs = workflow.blocks
    .filter((block) => recoveryAuthoringSectionKind(block) === "input")
    .map((block) => ({
      blockId: block.id,
      title: block.title,
      ...authoringInputState(block, permittedFiles),
    }));
  return {
    inputs,
    configuredCount: inputs.filter((input) => input.status === "configured")
      .length,
    totalCount: inputs.length,
  };
}

export function authoringConfigurationCommands(
  block: RecoveryBlock,
  patch: Record<string, string | number | boolean>,
): RecoveryCommand[] {
  if (
    Object.hasOwn(patch, RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY) ||
    Object.keys(patch).some((key) =>
      ["__proto__", "prototype", "constructor"].includes(key),
    )
  )
    throw new Error(
      "Wright-managed settings cannot be changed from the input editor.",
    );
  const diagnostics = validateAuthoringConfiguration({
    ...block,
    configuration: { ...block.configuration, ...patch },
  });
  if (diagnostics.length)
    throw new Error(`${diagnostics[0]!.code}: ${diagnostics[0]!.explanation}`);
  return Object.entries(patch)
    .filter(([key, value]) => block.configuration[key] !== value)
    .map(([key, value]) => ({
      kind: "set_block_configuration",
      blockId: block.id,
      key,
      value,
    }));
}

export function authoringDeletionImpact(
  workflow: RecoveryWorkflow,
  blockId: string,
): { relationships: RecoveryRelationship[]; blockedReason?: string } {
  const block = workflow.blocks.find((item) => item.id === blockId);
  if (!block)
    return { relationships: [], blockedReason: "This step no longer exists." };
  const endpoints = new Set([
    block.id,
    ...block.inputPortIds,
    ...block.outputPortIds,
  ]);
  const relationships = workflow.relationships.filter(
    (item) => endpoints.has(item.sourceId) || endpoints.has(item.targetId),
  );
  const artifact = workflow.artifactContracts.find(
    (item) =>
      item.producerBlockId === blockId ||
      item.requiredForBlockIds.includes(blockId),
  );
  const binding = workflow.bindings.find((item) =>
    [...item.argumentMap, ...item.resultMap].some(
      (mapping) =>
        endpoints.has(mapping.semanticSource) ||
        mapping.semanticSource.startsWith(`${blockId}.configuration.`),
    ),
  );
  const component = workflow.components.find((item) =>
    [...item.inputPortIds, ...item.outputPortIds].some((id) =>
      endpoints.has(id),
    ),
  );
  const blockedReason = artifact
    ? `This step is referenced by the ${artifact.name} file contract. Review that contract before deleting the step.`
    : binding
      ? `This step has a configured assignment (${binding.capabilityName}). Remove the assignment before deleting the step.`
      : component
        ? `This step owns interfaces of ${component.title}. Review the grouped step before deleting it.`
        : undefined;
  return { relationships, ...(blockedReason ? { blockedReason } : {}) };
}

export function buildDeletionCommands(
  workflow: RecoveryWorkflow,
  blockId: string,
): RecoveryCommand[] {
  const impact = authoringDeletionImpact(workflow, blockId);
  if (impact.blockedReason) throw new Error(impact.blockedReason);
  return [
    ...impact.relationships.map((relationship): RecoveryCommand => ({
      kind: "disconnect",
      relationshipId: relationship.id,
    })),
    { kind: "delete_block", blockId },
  ];
}
