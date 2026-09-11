import { canonicalDefinitionBytes } from "./canonical-wire";
import { validateAuthoringConfiguration, validateAuthoringConnections } from "./authoring-objects";
import {
  RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY,
  cloneWorkflow,
  initialWorkflow,
  recoveryAuthoringSectionKind,
  type RecoveryArtifactContract,
  type RecoveryBlock,
  type RecoveryDiagnostic,
  type RecoveryPort,
  type RecoveryRelationship,
  type RecoveryWorkflow,
} from "./model";
import {
  formatRecoveryDsl,
  parseRecoveryDsl,
  type RecoveryParseResult,
  type RecoverySourceMapEntry,
} from "./recovery-dsl";

type AuthoringSectionKind = "workflow" | "item" | "input" | "task" | "group" | "connection";

interface AuthoringSection {
  kind: AuthoringSectionKind;
  key: string;
  fields: Record<string, unknown>;
  startLine: number;
  endLine: number;
  startOffset: number;
  endOffset: number;
}

interface FormattedSection {
  kind: AuthoringSectionKind;
  key: string;
  fields: readonly [string, unknown][];
  canonicalIds: readonly string[];
}

interface AuthoringPort {
  key: string;
  name: string;
  kind: PublicPortKind;
  item: string | null;
  required: boolean;
  quantity: RecoveryPort["cardinality"];
  description: string;
}

type PublicPortKind =
  | "reference_images"
  | "design_intent"
  | "company_context"
  | "design_specification"
  | "cad_model"
  | "manufacturing_report"
  | "approved_cad_model"
  | "step_file"
  | "handoff_package"
  | "drawing_file"
  | "approved_drawing"
  | "tolerance_report"
  | "text"
  | "workspace_file"
  | "engineering_document"
  | "structured_result"
  | "check_report"
  | "check_result";

const PUBLIC_PORT_KIND_BY_TYPE_ID = new Map<string, PublicPortKind>([
  ["type.image.reference-set", "reference_images"],
  ["type.design.intent", "design_intent"],
  ["type.context.company", "company_context"],
  ["type.design.specification", "design_specification"],
  ["type.geometry.brep", "cad_model"],
  ["type.report.manufacturability", "manufacturing_report"],
  ["type.geometry.approved", "approved_cad_model"],
  ["type.file.step", "step_file"],
  ["type.package.review", "handoff_package"],
  ["type.file.drawing", "drawing_file"],
  ["type.file.drawing.approved", "approved_drawing"],
  ["type.report.tolerance", "tolerance_report"],
  ["type.value.text", "text"],
  ["type.file.workspace", "workspace_file"],
  ["type.document.engineering", "engineering_document"],
  ["type.result.structured", "structured_result"],
  ["type.report.check", "check_report"],
  ["type.verdict.check", "check_result"],
]);

const TYPE_ID_BY_PUBLIC_PORT_KIND = new Map<PublicPortKind, string>(
  [...PUBLIC_PORT_KIND_BY_TYPE_ID].map(([typeId, kind]) => [kind, typeId] as const),
);

const RESERVED_HOST_FIELDS = new Set([
  "version",
  "schema_version",
  "revision",
  "parent",
  "parent_revision",
  "semantic_sha256",
  "digest",
  "authorship",
]);

function diagnostic(
  code: string,
  explanation: string,
  correction: string,
  semanticId: string | null = null,
  line: number | null = null,
): RecoveryDiagnostic {
  return { code, explanation, correction, semanticId, line };
}

function stableKey(id: string): string {
  const suffix = id.includes(".") ? id.slice(id.indexOf(".") + 1) : id;
  return suffix.replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "").toLowerCase();
}

function canonicalId(prefix: "block" | "port" | "rel", key: string): string {
  return `${prefix}.${key.replace(/_/g, "-")}`;
}

function stableJson(value: unknown): string {
  const normalize = (child: unknown): unknown => {
    if (Array.isArray(child)) return child.map(normalize);
    if (child !== null && typeof child === "object") {
      return Object.fromEntries(
        Object.entries(child as Record<string, unknown>)
          .sort(([left], [right]) => left.localeCompare(right))
          .map(([key, item]) => [key, normalize(item)]),
      );
    }
    return child;
  };
  return JSON.stringify(normalize(value));
}

function scalar(value: unknown): string {
  if (typeof value === "string" && /^[a-z][a-z0-9_]*$/.test(value)) return value;
  return stableJson(value);
}

function itemType(artifact: RecoveryArtifactContract): string {
  if (artifact.mediaType.startsWith("image/")) return "image_files";
  if (artifact.mediaType === "text/plain") return "text_or_document";
  if (artifact.mediaType === "text/markdown") return "design_document";
  if (artifact.mediaType === "application/vnd.wright.context+json") return "company_knowledge";
  if (artifact.mediaType === "model/step") return "step_file";
  if (artifact.mediaType.startsWith("model/")) return artifact.id.includes("approved") ? "approved_cad_model" : "cad_model";
  if (artifact.mediaType === "text/html") return "engineering_report";
  if (artifact.mediaType === "application/zip") return "archive";
  return "engineering_file";
}

function itemFormats(artifact: RecoveryArtifactContract): string[] {
  if (artifact.mediaType.startsWith("image/")) return ["jpg", "png"];
  if (artifact.mediaType === "text/plain") return ["text", "docx", "pdf"];
  if (artifact.mediaType === "text/markdown") return ["markdown"];
  if (artifact.mediaType === "application/vnd.wright.context+json") return ["company_library"];
  if (artifact.mediaType === "model/step") return ["step_ap242"];
  if (artifact.mediaType.startsWith("model/")) return ["cad_model"];
  if (artifact.mediaType === "text/html") return ["html_report"];
  if (artifact.mediaType === "application/zip") return ["zip"];
  return ["file"];
}

function performedBy(block: RecoveryBlock): string {
  if (block.kind === "approval" && block.executionKind === "ai_capable") return "ai_then_engineer";
  if (block.executionKind === "human") return "engineer";
  if (block.executionKind === "ai_capable") return "ai_assisted";
  return "configured_tool";
}

function providedBy(block: RecoveryBlock): string {
  if (block.id === "block.company-context") return "company_library";
  return block.executionKind === "human" ? "engineer" : performedBy(block);
}

function publicBlockConfiguration(block: RecoveryBlock): Record<string, string | number | boolean> {
  const configuration = structuredClone(block.configuration);
  delete configuration[RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY];
  return configuration;
}

function sourceStepType(kind: RecoveryBlock["kind"]): string {
  if (kind === "approval") return "review";
  if (kind === "component") return "reusable_step";
  return kind;
}

function recoveryStepType(value: string): RecoveryBlock["kind"] | null {
  if (value === "review") return "approval";
  if (value === "reusable_step") return "component";
  if (value === "work" || value === "decision") return value;
  return null;
}

function sourceConnectionType(kind: RecoveryRelationship["kind"]): string {
  if (kind === "data") return "item";
  if (kind === "control") return "order";
  if (kind === "decision") return "approval";
  return "revision";
}

function recoveryConnectionType(value: string): RecoveryRelationship["kind"] | null {
  if (value === "item") return "data";
  if (value === "order") return "control";
  if (value === "approval") return "decision";
  if (value === "revision") return "feedback";
  return null;
}

function sourcePort(workflow: RecoveryWorkflow, portId: string): AuthoringPort {
  const port = workflow.ports.find((entry) => entry.id === portId);
  if (!port) throw new Error(`WFR-SOURCE-PORT-MISSING:${portId}`);
  const kind = PUBLIC_PORT_KIND_BY_TYPE_ID.get(port.typeId);
  if (!kind) throw new Error(`WFR-SOURCE-PORT-KIND-UNSUPPORTED:${port.typeId}`);
  return {
    key: stableKey(port.id),
    name: port.name,
    kind,
    item: port.artifactContractId === null ? null : stableKey(port.artifactContractId),
    required: port.required,
    quantity: port.cardinality,
    description: port.description,
  };
}

function endpointKey(workflow: RecoveryWorkflow, semanticId: string): string {
  const port = workflow.ports.find((entry) => entry.id === semanticId);
  if (port) return `${stableKey(port.ownerBlockId)}.${stableKey(port.id)}`;
  const block = workflow.blocks.find((entry) => entry.id === semanticId);
  return block ? stableKey(block.id) : semanticId;
}

function formattedSections(workflow: RecoveryWorkflow): FormattedSection[] {
  const defaultGroups = new Map([
    ["phase.define", { name: "Define", order: 0 }],
    ["phase.verify", { name: "Verify", order: 1 }],
    ["phase.deliver", { name: "Deliver", order: 2 }],
  ]);
  const projectGroups = workflow.blocks.length >= 26 || workflow.phases.some((phase) => {
    const expected = defaultGroups.get(phase.id);
    return expected === undefined || phase.name !== expected.name || phase.order !== expected.order;
  });
  const sections: FormattedSection[] = [{
    kind: "workflow",
    key: stableKey(workflow.workflowId),
    fields: [
      ["name", workflow.metadata.title],
      ["purpose", workflow.metadata.purpose],
      ["discipline", workflow.metadata.engineeringDomain],
      ["reviewed_ai_suggestions", workflow.metadata.authorship === "human_with_ai_proposal"],
    ],
    canonicalIds: [workflow.workflowId],
  }];

  for (const group of projectGroups ? [...workflow.phases].sort((left, right) => left.order - right.order) : []) {
    sections.push({
      kind: "group",
      key: stableKey(group.id),
      fields: [["name", group.name], ["purpose", group.purpose], ["order", group.order]],
      canonicalIds: [group.id],
    });
  }

  for (const artifact of workflow.artifactContracts) {
    sections.push({
      kind: "item",
      key: stableKey(artifact.id),
      fields: [
        ["name", artifact.name],
        ["type", itemType(artifact)],
        ["formats", itemFormats(artifact)],
        ["description", artifact.description],
      ],
      canonicalIds: [artifact.id],
    });
  }

  for (const block of workflow.blocks) {
    const isInput = recoveryAuthoringSectionKind(block) === "input";
    const binding = block.bindingId === null ? null : workflow.bindings.find((entry) => entry.id === block.bindingId) ?? null;
    const fields: [string, unknown][] = [
      ["name", block.title],
      ["purpose", block.purpose],
      ["step_type", sourceStepType(block.kind)],
      ["group", projectGroups && block.phaseId !== null ? stableKey(block.phaseId) : null],
      ...(isInput ? [["provided_by", providedBy(block)] as [string, unknown]] : [["performed_by", performedBy(block)] as [string, unknown]]),
      ["inputs", block.inputPortIds.map((portId) => sourcePort(workflow, portId))],
      ["outputs", block.outputPortIds.map((portId) => sourcePort(workflow, portId))],
      [block.executionKind === "ai_capable" ? "prompt" : "instructions", block.instructions],
      ["settings", publicBlockConfiguration(block)],
      ["tool", binding === null ? null : { assignment: stableKey(binding.id), action: binding.toolId }],
      ["reusable_step", block.componentRef === null ? null : { key: stableKey(block.componentRef.componentId), version: block.componentRef.versionRange }],
    ];
    sections.push({
      kind: isInput ? "input" : "task",
      key: stableKey(block.id),
      fields,
      canonicalIds: [block.id, ...block.inputPortIds, ...block.outputPortIds, ...(block.bindingId ? [block.bindingId] : [])],
    });
  }

  for (const relationship of workflow.relationships) {
    sections.push({
      kind: "connection",
      key: stableKey(relationship.id),
      fields: [
        ["type", sourceConnectionType(relationship.kind)],
        ["from", endpointKey(workflow, relationship.sourceId)],
        ["to", endpointKey(workflow, relationship.targetId)],
        ["label", relationship.label],
        ["when", relationship.condition],
      ],
      canonicalIds: [relationship.id],
    });
  }
  return sections;
}

export function formatRecoveryAuthoringSource(workflow: RecoveryWorkflow): { text: string; sourceMap: Record<string, RecoverySourceMapEntry> } {
  const lines = [
    "# Wright engineering workflow source",
    "# Stable names identify engineering items, steps, connection points, and routes.",
    "# Versions, history, integrity digests, canvas layout, and run state are managed by Wright.",
    "# Optional groups are shown only when they improve a larger or explicitly grouped workflow.",
    "",
  ];
  const sourceMap: Record<string, RecoverySourceMapEntry> = {};
  let offset = lines.reduce((total, line) => total + line.length + 1, 0);
  for (const entry of formattedSections(workflow)) {
    const startLine = lines.length + 1;
    const startOffset = offset;
    const sectionLines = [`${entry.kind} ${entry.key}`, ...entry.fields.map(([name, value]) => `  ${name}: ${scalar(value)}`), "end", ""];
    lines.push(...sectionLines);
    offset += sectionLines.reduce((total, line) => total + line.length + 1, 0);
    const span = { startLine, endLine: startLine + sectionLines.length - 2, startOffset, endOffset: offset - 2 };
    for (const id of entry.canonicalIds) sourceMap[id] = span;
  }
  return { text: `${lines.join("\n").trimEnd()}\n`, sourceMap };
}

function parseValue(raw: string): unknown {
  if (raw.startsWith("\"") || raw.startsWith("[") || raw.startsWith("{") || raw === "true" || raw === "false" || raw === "null" || /^-?\d+(\.\d+)?$/.test(raw)) {
    return JSON.parse(raw);
  }
  if (/^[a-z][a-z0-9_]*$/.test(raw)) return raw;
  throw new Error("WFR-SOURCE-VALUE-INVALID");
}

function parseSections(text: string): { sections: AuthoringSection[]; diagnostics: RecoveryDiagnostic[] } {
  const lines = text.split("\n");
  const sections: AuthoringSection[] = [];
  const diagnostics: RecoveryDiagnostic[] = [];
  let offset = 0;
  let current: Omit<AuthoringSection, "endLine" | "endOffset"> | null = null;
  const keys = new Set<string>();
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]!;
    const lineNumber = index + 1;
    const trimmed = line.trim();
    if (current === null) {
      if (trimmed === "" || trimmed.startsWith("#")) {
        offset += line.length + 1;
        continue;
      }
      const header = /^(workflow|item|input|task|group|connection)\s+([a-z][a-z0-9_]*)$/.exec(trimmed);
      if (!header) {
        diagnostics.push(diagnostic("WFR-SOURCE-SECTION-INVALID", `Line ${lineNumber} is not a workflow, item, input, task, optional group, or connection declaration.`, "Use '<kind> <stable_name>', indented fields, and 'end'.", null, lineNumber));
        offset += line.length + 1;
        continue;
      }
      const sectionKey = `${header[1]}:${header[2]}`;
      if (keys.has(sectionKey)) diagnostics.push(diagnostic("WFR-SOURCE-KEY-DUPLICATE", `The stable name ${header[2]} is declared twice as ${header[1]}.`, "Keep one declaration for each stable name.", null, lineNumber));
      keys.add(sectionKey);
      current = { kind: header[1] as AuthoringSectionKind, key: header[2]!, fields: {}, startLine: lineNumber, startOffset: offset };
      offset += line.length + 1;
      continue;
    }
    if (trimmed === "end") {
      sections.push({ ...current, endLine: lineNumber, endOffset: offset + line.length });
      current = null;
      offset += line.length + 1;
      continue;
    }
    const field = /^\s{2}([a-z][a-z0-9_]*):\s*(.+)$/.exec(line);
    if (!field) {
      diagnostics.push(diagnostic("WFR-SOURCE-FIELD-INVALID", `Line ${lineNumber} is not an indented name/value field.`, "Indent two spaces and write 'field: value', or close the section with 'end'.", null, lineNumber));
      offset += line.length + 1;
      continue;
    }
    if (RESERVED_HOST_FIELDS.has(field[1]!)) {
      diagnostics.push(diagnostic("WFR-SOURCE-FIELD-MANAGED", `${field[1]} is managed by Wright and cannot be assigned in engineering source.`, "Remove the field; Wright records accepted version, ancestry, and integrity after validation.", null, lineNumber));
      offset += line.length + 1;
      continue;
    }
    if (Object.hasOwn(current.fields, field[1]!)) {
      diagnostics.push(diagnostic("WFR-SOURCE-FIELD-DUPLICATE", `${field[1]} is repeated in ${current.kind} ${current.key}.`, "Keep one value for each field.", null, lineNumber));
      offset += line.length + 1;
      continue;
    }
    try {
      current.fields[field[1]!] = parseValue(field[2]!);
    } catch {
      diagnostics.push(diagnostic("WFR-SOURCE-VALUE-INVALID", `Line ${lineNumber} has an invalid value.`, "Use a quoted string, JSON array/object, number, boolean, null, or lower_snake_case name.", null, lineNumber));
    }
    offset += line.length + 1;
  }
  if (current !== null) diagnostics.push(diagnostic("WFR-SOURCE-SECTION-UNTERMINATED", `${current.kind} ${current.key} is missing 'end'.`, "Add 'end' before the next declaration.", null, current.startLine));
  return { sections, diagnostics };
}

function same(left: unknown, right: unknown): boolean {
  return stableJson(left) === stableJson(right);
}

function requireFields(section: AuthoringSection, required: readonly string[], optional: readonly string[] = []): RecoveryDiagnostic[] {
  const diagnostics: RecoveryDiagnostic[] = [];
  const allowed = new Set([...required, ...optional]);
  for (const field of required) {
    if (!Object.hasOwn(section.fields, field)) diagnostics.push(diagnostic("WFR-SOURCE-FIELD-MISSING", `${section.kind} ${section.key} is missing '${field}'.`, `Add '${field}' to the section.`, null, section.startLine));
  }
  for (const field of Object.keys(section.fields)) {
    if (!allowed.has(field)) diagnostics.push(diagnostic("WFR-SOURCE-FIELD-UNKNOWN", `${section.kind} ${section.key} contains unknown field '${field}'.`, "Use only documented engineering-source fields.", null, section.startLine));
  }
  return diagnostics;
}

function stringField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): string | null {
  const value = section.fields[field];
  if (typeof value !== "string" || value.trim() === "") {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be a non-empty string or stable name.`, "Provide a quoted string or lower_snake_case name.", null, section.startLine));
    return null;
  }
  return value;
}

function nullableStringField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): string | null | undefined {
  const value = section.fields[field];
  if (value === null) return null;
  if (typeof value !== "string" || value.trim() === "") {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be a string or null.`, "Provide a quoted string, lower_snake_case name, or null.", null, section.startLine));
    return undefined;
  }
  return value;
}

function stringArrayField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): string[] | null {
  const value = section.fields[field];
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be an array of stable names.`, "Use a JSON string array.", null, section.startLine));
    return null;
  }
  return value as string[];
}

function booleanField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): boolean | null {
  const value = section.fields[field];
  if (typeof value !== "boolean") {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be true or false.`, "Use an unquoted boolean.", null, section.startLine));
    return null;
  }
  return value;
}

function numberField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): number | null {
  const value = section.fields[field];
  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be a non-negative integer.`, "Use an unquoted whole number.", null, section.startLine));
    return null;
  }
  return value;
}

function objectOrNullField(section: AuthoringSection, field: string, diagnostics: RecoveryDiagnostic[]): Record<string, unknown> | null | undefined {
  const value = section.fields[field];
  if (value === null) return null;
  if (value === undefined || typeof value !== "object" || Array.isArray(value)) {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be an object or null.`, "Use a JSON object or null.", null, section.startLine));
    return undefined;
  }
  return value as Record<string, unknown>;
}

function sourceMapForResolved(section: AuthoringSection, canonicalIds: readonly string[], map: Record<string, RecoverySourceMapEntry>): void {
  const span = { startLine: section.startLine, endLine: section.endLine, startOffset: section.startOffset, endOffset: section.endOffset };
  for (const id of canonicalIds) map[id] = span;
}

function parsePortList(
  section: AuthoringSection,
  field: "inputs" | "outputs",
  ownerBlockId: string,
  base: RecoveryWorkflow,
  artifactsByKey: ReadonlyMap<string, RecoveryArtifactContract>,
  diagnostics: RecoveryDiagnostic[],
): RecoveryPort[] {
  const value = section.fields[field];
  if (!Array.isArray(value)) {
    diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.${field} must be an array of connection-point objects.`, "Use the connection points emitted by Diagram or add a complete object with key, name, kind, item, required, quantity, and description.", ownerBlockId, section.startLine));
    return [];
  }
  const direction: RecoveryPort["direction"] = field === "inputs" ? "input" : "output";
  const basePortsByKey = new Map(base.ports.map((port) => [stableKey(port.id), port]));
  const seen = new Set<string>();
  const ports: RecoveryPort[] = [];
  for (const raw of value) {
    if (raw === null || typeof raw !== "object" || Array.isArray(raw)) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-INVALID", `${section.kind} ${section.key}.${field} contains an invalid connection point.`, "Use a JSON object for each connection point.", ownerBlockId, section.startLine));
      continue;
    }
    const port = raw as Record<string, unknown>;
    const requiredFields = ["key", "name", "kind", "item", "required", "quantity", "description"];
    if (requiredFields.some((key) => !Object.hasOwn(port, key)) || Object.keys(port).some((key) => !requiredFields.includes(key))) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-FIELDS", `${section.kind} ${section.key}.${field} has incomplete or unknown connection-point fields.`, "Use exactly key, name, kind, item, required, quantity, and description.", ownerBlockId, section.startLine));
      continue;
    }
    const key = port.key;
    const name = port.name;
    const kind = port.kind;
    const item = port.item;
    const required = port.required;
    const quantity = port.quantity;
    const description = port.description;
    if (typeof key !== "string" || !/^[a-z][a-z0-9_]*$/.test(key) || typeof name !== "string" || !name.trim() || typeof kind !== "string" || !kind.trim() || typeof description !== "string" || !description.trim() || typeof required !== "boolean" || !["one", "optional", "many"].includes(String(quantity)) || (item !== null && (typeof item !== "string" || !/^[a-z][a-z0-9_]*$/.test(item)))) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-INVALID", `${section.kind} ${section.key}.${field} contains an invalid connection-point value.`, "Use a stable key, clear names/types/descriptions, true or false, one/optional/many, and an item stable name or null.", ownerBlockId, section.startLine));
      continue;
    }
    const mappedTypeId = TYPE_ID_BY_PUBLIC_PORT_KIND.get(kind as PublicPortKind);
    if (!mappedTypeId) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-KIND", `Connection point '${key}' uses unknown engineering kind '${kind}'.`, `Use a supported kind: ${[...TYPE_ID_BY_PUBLIC_PORT_KIND.keys()].join(", ")}.`, ownerBlockId, section.startLine));
      continue;
    }
    if (seen.has(key)) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-DUPLICATE", `${section.kind} ${section.key} repeats connection point '${key}'.`, "Keep each connection point once.", ownerBlockId, section.startLine));
      continue;
    }
    seen.add(key);
    const artifact = item === null ? null : artifactsByKey.get(item);
    if (item !== null && !artifact) diagnostics.push(diagnostic("WFR-SOURCE-ITEM-UNKNOWN", `Connection point '${key}' refers to unknown engineering item '${item}'.`, "Declare the item or select an existing item stable name.", ownerBlockId, section.startLine));
    const basePort = basePortsByKey.get(key);
    if (basePort && basePort.typeId !== mappedTypeId) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-KIND", `Connection point '${key}' is '${PUBLIC_PORT_KIND_BY_TYPE_ID.get(basePort.typeId) ?? "an unsupported internal kind"}', not '${kind}'.`, "Restore the accepted engineering kind; changing a connection-point kind requires a reviewed structural operation.", ownerBlockId, section.startLine));
      continue;
    }
    const typeId = basePort?.typeId ?? mappedTypeId;
    if (artifact && artifact.typeId !== typeId) {
      diagnostics.push(diagnostic("WFR-SOURCE-PORT-ITEM-TYPE", `Connection point '${key}' kind '${kind}' does not match engineering item '${item}'.`, "Select an item with the same engineering kind, or correct the connection-point kind.", ownerBlockId, section.startLine));
      continue;
    }
    ports.push({
      id: basePort?.id ?? canonicalId("port", key),
      ownerBlockId,
      direction,
      name: name.trim(),
      typeId,
      required,
      cardinality: quantity as RecoveryPort["cardinality"],
      artifactContractId: artifact?.id ?? null,
      description: description.trim(),
    });
  }
  return ports;
}

function executionKindForActor(actor: string): RecoveryBlock["executionKind"] | null {
  if (actor === "engineer") return "human";
  if (actor === "configured_tool" || actor === "company_library") return "deterministic";
  if (actor === "ai_assisted" || actor === "ai_then_engineer") return "ai_capable";
  return null;
}

export function parseRecoveryAuthoringSource(text: string, base: RecoveryWorkflow): RecoveryParseResult {
  const parsed = parseSections(text);
  const diagnostics = [...parsed.diagnostics];
  const sourceMap: Record<string, RecoverySourceMapEntry> = {};
  const candidate = cloneWorkflow(base);
  const sectionsByKind = (kind: AuthoringSectionKind) => parsed.sections.filter((section) => section.kind === kind);

  const workflowSections = sectionsByKind("workflow");
  if (workflowSections.length !== 1) diagnostics.push(diagnostic("WFR-SOURCE-WORKFLOW-COUNT", `Engineering source must contain exactly one workflow section; found ${workflowSections.length}.`, "Keep one workflow declaration."));
  const workflowSection = workflowSections[0];
  if (workflowSection) {
    diagnostics.push(...requireFields(workflowSection, ["name", "purpose", "discipline", "reviewed_ai_suggestions"]));
    if (workflowSection.key !== stableKey(base.workflowId)) diagnostics.push(diagnostic("WFR-SOURCE-IDENTITY-UNKNOWN", `Workflow stable name '${workflowSection.key}' does not match this workflow.`, `Keep '${stableKey(base.workflowId)}'; rename the displayed name instead.`, base.workflowId, workflowSection.startLine));
    const name = stringField(workflowSection, "name", diagnostics);
    const purpose = stringField(workflowSection, "purpose", diagnostics);
    const discipline = stringField(workflowSection, "discipline", diagnostics);
    const reviewedAi = booleanField(workflowSection, "reviewed_ai_suggestions", diagnostics);
    if (name) candidate.metadata.title = name;
    if (purpose) candidate.metadata.purpose = purpose;
    if (discipline) candidate.metadata.engineeringDomain = discipline;
    if (reviewedAi !== null) candidate.metadata.authorship = reviewedAi ? "human_with_ai_proposal" : "human";
    sourceMapForResolved(workflowSection, [base.workflowId], sourceMap);
  }

  const groupSections = sectionsByKind("group");
  const groupsByKey = new Map(candidate.phases.map((phase) => [stableKey(phase.id), phase]));
  for (const group of groupSections) {
    diagnostics.push(...requireFields(group, ["name", "purpose", "order"]));
    const phase = groupsByKey.get(group.key);
    if (!phase) {
      diagnostics.push(diagnostic("WFR-SOURCE-GROUP-UNKNOWN", `Optional group '${group.key}' is not part of this workflow.`, "Remove it; group creation is a separate reviewed structural operation.", null, group.startLine));
      continue;
    }
    const name = stringField(group, "name", diagnostics);
    const purpose = stringField(group, "purpose", diagnostics);
    const order = numberField(group, "order", diagnostics);
    if (name) phase.name = name;
    if (purpose) phase.purpose = purpose;
    if (order !== null) phase.order = order;
    sourceMapForResolved(group, [phase.id], sourceMap);
  }

  const itemSections = new Map(sectionsByKind("item").map((section) => [section.key, section]));
  // The reconstruction base supplies vocabulary only. Source controls which
  // item contracts are retained, so a small workflow need not inherit the demo.
  candidate.artifactContracts = candidate.artifactContracts.filter((artifact) =>
    itemSections.has(stableKey(artifact.id)),
  );
  const artifactsByKey = new Map(candidate.artifactContracts.map((artifact) => [stableKey(artifact.id), artifact]));
  for (const artifact of candidate.artifactContracts) {
    const key = stableKey(artifact.id);
    const section = itemSections.get(key);
    if (!section) continue;
    diagnostics.push(...requireFields(section, ["name", "type", "formats", "description"]));
    const name = stringField(section, "name", diagnostics);
    const type = stringField(section, "type", diagnostics);
    const formats = stringArrayField(section, "formats", diagnostics);
    const description = stringField(section, "description", diagnostics);
    if (type && type !== itemType(artifact)) diagnostics.push(diagnostic("WFR-SOURCE-TYPE-CHANGE-UNSUPPORTED", `Item '${key}' is '${itemType(artifact)}', not '${type}'.`, "Restore the accepted engineering item type.", artifact.id, section.startLine));
    if (formats && !same(formats, itemFormats(artifact))) diagnostics.push(diagnostic("WFR-SOURCE-FORMAT-CHANGE-UNSUPPORTED", `Item '${key}' formats do not match its accepted file contract.`, `Restore ${stableJson(itemFormats(artifact))}.`, artifact.id, section.startLine));
    if (name) artifact.name = name;
    if (description) artifact.description = description;
    sourceMapForResolved(section, [artifact.id], sourceMap);
    itemSections.delete(key);
  }
  for (const section of itemSections.values()) diagnostics.push(diagnostic("WFR-SOURCE-IDENTITY-UNKNOWN", `Unknown engineering item '${section.key}'.`, "Create new item contracts through a reviewed structural command.", null, section.startLine));

  const baseBlocksByKey = new Map(base.blocks.map((block) => [stableKey(block.id), block]));
  const blockSections = parsed.sections.filter((section) => section.kind === "input" || section.kind === "task");
  const blockKeys = new Set<string>();
  const nextBlocks: RecoveryBlock[] = [];
  const nextPorts: RecoveryPort[] = [];
  const bindingByKey = new Map(candidate.bindings.map((binding) => [stableKey(binding.id), binding]));
  const componentByKey = new Map(candidate.components.map((component) => [stableKey(component.id), component]));
  for (const section of blockSections) {
    if (blockKeys.has(section.key)) {
      diagnostics.push(diagnostic("WFR-SOURCE-KEY-DUPLICATE", `Workflow step '${section.key}' is declared more than once.`, "Keep exactly one input or task section for each stable step name.", null, section.startLine));
      continue;
    }
    blockKeys.add(section.key);
    const baseBlock = baseBlocksByKey.get(section.key);
    const expectedKind: AuthoringSectionKind = baseBlock ? recoveryAuthoringSectionKind(baseBlock) : section.kind;
    if (baseBlock && section.kind !== expectedKind) diagnostics.push(diagnostic("WFR-SOURCE-STEP-KIND", `'${section.key}' must be declared as ${expectedKind}, not ${section.kind}.`, `Change the section keyword to '${expectedKind}'.`, baseBlock.id, section.startLine));
    const instructionField = section.fields.prompt !== undefined ? "prompt" : "instructions";
    diagnostics.push(...requireFields(section, ["name", "purpose", "step_type", "group", section.kind === "input" ? "provided_by" : "performed_by", "inputs", "outputs", instructionField, "settings", "tool", "reusable_step"]));
    const name = stringField(section, "name", diagnostics);
    const purpose = stringField(section, "purpose", diagnostics);
    const stepTypeValue = stringField(section, "step_type", diagnostics);
    const actor = stringField(section, section.kind === "input" ? "provided_by" : "performed_by", diagnostics);
    const instructions = instructionField === "prompt" && typeof section.fields[instructionField] === "string"
      ? section.fields[instructionField] as string : stringField(section, instructionField, diagnostics);
    const groupKey = nullableStringField(section, "group", diagnostics);
    const stepType = stepTypeValue ? recoveryStepType(stepTypeValue) : null;
    const executionKind = actor ? executionKindForActor(actor) : null;
    if (stepTypeValue && !stepType) diagnostics.push(diagnostic("WFR-SOURCE-STEP-TYPE", `Workflow step '${section.key}' has unknown step_type '${stepTypeValue}'.`, "Use work, review, decision, or reusable_step.", baseBlock?.id ?? null, section.startLine));
    if (actor && !executionKind) diagnostics.push(diagnostic("WFR-SOURCE-ACTOR", `Workflow step '${section.key}' has unknown performer '${actor}'.`, "Use engineer, configured_tool, company_library, ai_assisted, or ai_then_engineer.", baseBlock?.id ?? null, section.startLine));
    const phase = groupKey === null || groupKey === undefined ? null : groupsByKey.get(groupKey);
    if (groupKey && !phase) diagnostics.push(diagnostic("WFR-SOURCE-GROUP-UNKNOWN", `Workflow step '${section.key}' refers to unknown group '${groupKey}'.`, "Use an existing optional group stable name or null.", baseBlock?.id ?? null, section.startLine));
    const settings = section.fields.settings;
    if (settings === null || typeof settings !== "object" || Array.isArray(settings) || Object.values(settings as Record<string, unknown>).some((value) => !["string", "number", "boolean"].includes(typeof value))) diagnostics.push(diagnostic("WFR-SOURCE-FIELD-TYPE", `${section.kind} ${section.key}.settings must be a JSON object of string, number, or boolean values.`, "Use settings: {\"name\":\"value\"}.", baseBlock?.id ?? null, section.startLine));
    if (settings !== null && typeof settings === "object" && !Array.isArray(settings) && Object.hasOwn(settings, RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY)) diagnostics.push(diagnostic("WFR-SOURCE-FIELD-MANAGED", `${section.kind} ${section.key}.settings contains a Wright-managed authoring classification.`, "Remove the managed setting; use the input or task section keyword.", baseBlock?.id ?? null, section.startLine));
    const blockId = baseBlock?.id ?? canonicalId("block", section.key);
    const inputs = parsePortList(section, "inputs", blockId, base, artifactsByKey, diagnostics);
    const outputs = parsePortList(section, "outputs", blockId, base, artifactsByKey, diagnostics);
    const tool = objectOrNullField(section, "tool", diagnostics);
    let bindingId: string | null = null;
    if (tool) {
      if (Object.keys(tool).some((key) => !["assignment", "action"].includes(key)) || typeof tool.assignment !== "string" || (tool.action !== null && typeof tool.action !== "string")) diagnostics.push(diagnostic("WFR-SOURCE-TOOL-INVALID", `Workflow step '${section.key}' has an invalid tool assignment.`, "Use {\"assignment\":\"stable_name\",\"action\":\"tool.action\"} or null.", blockId, section.startLine));
      else {
        const binding = bindingByKey.get(tool.assignment);
        if (!binding) diagnostics.push(diagnostic("WFR-SOURCE-TOOL-UNKNOWN", `Workflow step '${section.key}' refers to unknown tool assignment '${tool.assignment}'.`, "Select a configured assignment from Technical details.", blockId, section.startLine));
        else {
          bindingId = binding.id;
          binding.toolId = tool.action as string | null;
        }
      }
    }
    const reusable = objectOrNullField(section, "reusable_step", diagnostics);
    let componentRef: RecoveryBlock["componentRef"] = null;
    if (reusable) {
      if (Object.keys(reusable).some((key) => !["key", "version"].includes(key)) || typeof reusable.key !== "string" || typeof reusable.version !== "string") diagnostics.push(diagnostic("WFR-SOURCE-REUSABLE-INVALID", `Workflow step '${section.key}' has an invalid reusable_step reference.`, "Use {\"key\":\"stable_name\",\"version\":\"range\"} or null.", blockId, section.startLine));
      else {
        const component = componentByKey.get(reusable.key);
        if (!component) diagnostics.push(diagnostic("WFR-SOURCE-REUSABLE-UNKNOWN", `Workflow step '${section.key}' refers to unknown reusable step '${reusable.key}'.`, "Select an installed reusable step.", blockId, section.startLine));
        else componentRef = { componentId: component.id, versionRange: reusable.version };
      }
    }
    const configuration = settings && typeof settings === "object" && !Array.isArray(settings)
      ? structuredClone(settings as Record<string, string | number | boolean>)
      : {};
    delete configuration[RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY];
    if (section.kind === "input" && (baseBlock === undefined || baseBlock.configuration[RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY] === "input")) {
      configuration[RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY] = "input";
    }
    const block: RecoveryBlock = {
      id: blockId,
      kind: stepType ?? baseBlock?.kind ?? "work",
      title: name ?? baseBlock?.title ?? section.key,
      purpose: purpose ?? baseBlock?.purpose ?? section.key,
      phaseId: phase?.id ?? (groupSections.length === 0 && baseBlock ? baseBlock.phaseId : null),
      executionKind: executionKind ?? baseBlock?.executionKind ?? "human",
      instructions: instructions ?? baseBlock?.instructions ?? section.key,
      configuration,
      inputPortIds: inputs.map((port) => port.id),
      outputPortIds: outputs.map((port) => port.id),
      bindingId,
      componentRef,
    };
    diagnostics.push(...validateAuthoringConfiguration(block).map((item) => ({ ...item, line: section.startLine })));
    nextBlocks.push(block);
    nextPorts.push(...inputs, ...outputs);
    sourceMapForResolved(section, [block.id, ...block.inputPortIds, ...block.outputPortIds, ...(bindingId ? [bindingId] : [])], sourceMap);
  }
  candidate.blocks = nextBlocks;
  candidate.ports = nextPorts;
  const retainedBindings = new Set(nextBlocks.flatMap((block) => block.bindingId ? [block.bindingId] : []));
  const retainedComponents = new Set(nextBlocks.flatMap((block) => block.componentRef ? [block.componentRef.componentId] : []));
  candidate.bindings = candidate.bindings.filter((binding) => retainedBindings.has(binding.id));
  candidate.components = candidate.components.filter((component) => retainedComponents.has(component.id));
  for (const phase of candidate.phases) phase.blockIds = nextBlocks.filter((block) => block.phaseId === phase.id).map((block) => block.id);

  const blocksByKey = new Map(candidate.blocks.map((block) => [stableKey(block.id), block]));
  const portsByOwnerAndKey = new Map(candidate.ports.map((port) => [`${stableKey(port.ownerBlockId)}.${stableKey(port.id)}`, port]));
  const baseRelationshipsByKey = new Map(base.relationships.map((relationship) => [stableKey(relationship.id), relationship]));
  const resolveEndpoint = (value: string, section: AuthoringSection): string | null => {
    const port = portsByOwnerAndKey.get(value);
    if (port) return port.id;
    const endpointBlock = blocksByKey.get(value);
    if (endpointBlock) return endpointBlock.id;
    diagnostics.push(diagnostic("WFR-SOURCE-ENDPOINT-UNKNOWN", `Connection '${section.key}' refers to unknown endpoint '${value}'.`, "Use task_name.connection_point for items or task_name for approval/order/revision paths.", null, section.startLine));
    return null;
  };
  const nextRelationships: RecoveryRelationship[] = [];
  for (const section of sectionsByKind("connection")) {
    diagnostics.push(...requireFields(section, ["type", "from", "to", "label", "when"]));
    const typeValue = stringField(section, "type", diagnostics);
    const fromValue = stringField(section, "from", diagnostics);
    const toValue = stringField(section, "to", diagnostics);
    const label = stringField(section, "label", diagnostics);
    const when = nullableStringField(section, "when", diagnostics);
    const kind = typeValue ? recoveryConnectionType(typeValue) : null;
    if (typeValue && !kind) diagnostics.push(diagnostic("WFR-SOURCE-CONNECTION-TYPE", `Connection '${section.key}' has unknown type '${typeValue}'.`, "Use item, order, approval, or revision.", null, section.startLine));
    const sourceId = fromValue ? resolveEndpoint(fromValue, section) : null;
    const targetId = toValue ? resolveEndpoint(toValue, section) : null;
    const existing = baseRelationshipsByKey.get(section.key);
    const relationshipId = existing?.id ?? canonicalId("rel", section.key);
    if (kind && sourceId && targetId && label && when !== undefined) nextRelationships.push({ id: relationshipId, kind, sourceId, targetId, label, condition: when });
    sourceMapForResolved(section, [relationshipId], sourceMap);
  }
  candidate.relationships = nextRelationships;
  diagnostics.push(...validateAuthoringConnections(candidate));

  if (diagnostics.length > 0) return { ok: false, workflow: null, diagnostics, sourceMap };
  const validated = parseRecoveryDsl(formatRecoveryDsl(candidate).text);
  if (!validated.ok || validated.workflow === null) return { ok: false, workflow: null, diagnostics: validated.diagnostics, sourceMap };
  return { ok: true, workflow: validated.workflow, diagnostics: [], sourceMap };
}

export function validateRecoveryAuthoringRoundTrip(
  workflow: RecoveryWorkflow,
  reconstructionBase: RecoveryWorkflow = initialWorkflow,
): RecoveryParseResult {
  const formatted = formatRecoveryAuthoringSource(workflow);
  const base = cloneWorkflow(reconstructionBase);
  // The reconstruction seed supplies retained schema/binding vocabulary, not a
  // different document identity. The public workflow declaration carries this.
  base.workflowId = workflow.workflowId;
  base.revision = workflow.revision;
  base.parentRevision = workflow.parentRevision;
  base.semanticSha256 = workflow.semanticSha256;
  const parsed = parseRecoveryAuthoringSource(formatted.text, base);
  if (!parsed.ok || parsed.workflow === null) return parsed;
  if (canonicalDefinitionBytes(parsed.workflow, true) !== canonicalDefinitionBytes(workflow, true)) {
    return {
      ok: false,
      workflow: null,
      diagnostics: [diagnostic("WFR-SOURCE-ROUNDTRIP-LOSS", "The engineering source cannot reconstruct every semantic fact in this candidate.", "The accepted workflow was kept unchanged. Add a lossless source representation before accepting or saving this change.")],
      sourceMap: formatted.sourceMap,
    };
  }
  return parsed;
}

export function recoveryAuthoringSourceSelection(
  sourceMap: Readonly<Record<string, RecoverySourceMapEntry>>,
  semanticId: string | null,
): RecoverySourceMapEntry | null {
  return semanticId === null ? null : sourceMap[semanticId] ?? null;
}

function sourceSelectionPriority(semanticId: string): number {
  if (semanticId.startsWith("block.")) return 0;
  if (semanticId.startsWith("artifact.")) return 1;
  if (semanticId.startsWith("rel.")) return 2;
  if (semanticId.startsWith("phase.")) return 3;
  if (semanticId.startsWith("binding.")) return 4;
  if (semanticId.startsWith("port.")) return 5;
  return 6;
}

export function recoveryAuthoringSemanticIdAtOffset(
  sourceMap: Readonly<Record<string, RecoverySourceMapEntry>>,
  offset: number,
): string | null {
  const matches = Object.entries(sourceMap)
    .filter(([, span]) => span.startOffset <= offset && offset <= span.endOffset)
    .sort(([leftId, leftSpan], [rightId, rightSpan]) => {
      const spanLength = (leftSpan.endOffset - leftSpan.startOffset) - (rightSpan.endOffset - rightSpan.startOffset);
      if (spanLength !== 0) return spanLength;
      const priority = sourceSelectionPriority(leftId) - sourceSelectionPriority(rightId);
      return priority !== 0 ? priority : leftId.localeCompare(rightId);
    });
  return matches[0]?.[0] ?? null;
}
