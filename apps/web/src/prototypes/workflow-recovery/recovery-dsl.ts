import type {
  RecoveryArtifactContract,
  RecoveryBinding,
  RecoveryBlock,
  RecoveryComponent,
  RecoveryDiagnostic,
  RecoveryPhase,
  RecoveryPort,
  RecoveryRelationship,
  RecoveryWorkflow,
} from "./model";

type SectionKind = "workflow" | "phase" | "block" | "port" | "relationship" | "artifact" | "binding" | "component";

interface Section {
  kind: SectionKind;
  id: string;
  fields: Record<string, unknown>;
  startLine: number;
  endLine: number;
}

export interface RecoverySourceMapEntry {
  startLine: number;
  endLine: number;
  startOffset: number;
  endOffset: number;
}

export interface RecoveryParseResult {
  ok: boolean;
  workflow: RecoveryWorkflow | null;
  diagnostics: RecoveryDiagnostic[];
  sourceMap: Record<string, RecoverySourceMapEntry>;
}

const fieldSets: Record<SectionKind, readonly string[]> = {
  workflow: ["version", "revision", "parent", "semantic_sha256", "title", "purpose", "domain", "authorship"],
  phase: ["name", "purpose", "order", "blocks"],
  block: ["kind", "title", "purpose", "phase", "execution", "instructions", "config", "inputs", "outputs", "binding", "component"],
  port: ["owner", "direction", "name", "type", "required", "cardinality", "artifact", "description"],
  relationship: ["kind", "source", "target", "label", "condition"],
  artifact: ["name", "type", "media", "description", "producer", "required_for", "preview", "actions"],
  binding: ["kind", "provider", "server", "tool", "schema", "arguments", "results", "approval", "capability"],
  component: ["version", "title", "inputs", "outputs", "digest", "addresses"],
};

function sorted(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sorted);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>).sort(([left], [right]) => left.localeCompare(right)).map(([key, child]) => [key, sorted(child)]));
  }
  return value;
}

function scalar(value: unknown): string {
  if (typeof value === "string" && /^[A-Za-z][A-Za-z0-9._\-/:]*$/.test(value) && !["null", "true", "false"].includes(value)) return value;
  return JSON.stringify(sorted(value));
}

function section(lines: string[], kind: SectionKind, id: string, fields: readonly [string, unknown][]): void {
  lines.push(`${kind} ${id}`);
  for (const [name, value] of fields) lines.push(`  ${name}: ${scalar(value)}`);
  lines.push("end", "");
}

export function formatRecoveryDsl(workflow: RecoveryWorkflow): { text: string; sourceMap: Record<string, RecoverySourceMapEntry> } {
  const lines = [
    "# Wright workflow language — recovery treatment 0.1",
    "",
  ];
  section(lines, "workflow", workflow.workflowId, [
    ["version", workflow.schemaVersion], ["revision", workflow.revision], ["parent", workflow.parentRevision], ["semantic_sha256", workflow.semanticSha256],
    ["title", workflow.metadata.title], ["purpose", workflow.metadata.purpose],
    ["domain", workflow.metadata.engineeringDomain], ["authorship", workflow.metadata.authorship],
  ]);
  for (const phase of workflow.phases) section(lines, "phase", phase.id, [
    ["name", phase.name], ["purpose", phase.purpose], ["order", phase.order], ["blocks", phase.blockIds],
  ]);
  for (const block of workflow.blocks) section(lines, "block", block.id, [
    ["kind", block.kind], ["title", block.title], ["purpose", block.purpose], ["phase", block.phaseId],
    ["execution", block.executionKind], ["instructions", block.instructions], ["config", block.configuration],
    ["inputs", block.inputPortIds], ["outputs", block.outputPortIds], ["binding", block.bindingId],
    ["component", block.componentRef === null ? null : { component_id: block.componentRef.componentId, version_range: block.componentRef.versionRange }],
  ]);
  for (const port of workflow.ports) section(lines, "port", port.id, [
    ["owner", port.ownerBlockId], ["direction", port.direction], ["name", port.name], ["type", port.typeId],
    ["required", port.required], ["cardinality", port.cardinality], ["artifact", port.artifactContractId], ["description", port.description],
  ]);
  for (const relationship of workflow.relationships) section(lines, "relationship", relationship.id, [
    ["kind", relationship.kind], ["source", relationship.sourceId], ["target", relationship.targetId],
    ["label", relationship.label], ["condition", relationship.condition],
  ]);
  for (const artifact of workflow.artifactContracts) section(lines, "artifact", artifact.id, [
    ["name", artifact.name], ["type", artifact.typeId], ["media", artifact.mediaType], ["description", artifact.description],
    ["producer", artifact.producerBlockId], ["required_for", artifact.requiredForBlockIds], ["preview", artifact.previewPolicy], ["actions", artifact.allowedActions],
  ]);
  for (const binding of workflow.bindings) section(lines, "binding", binding.id, [
    ["kind", binding.kind], ["provider", binding.providerId], ["server", binding.serverId], ["tool", binding.toolId],
    ["schema", binding.schemaDigest], ["arguments", binding.argumentMap.map((item) => ({ semantic_source: item.semanticSource, implementation_target: item.implementationTarget }))], ["results", binding.resultMap.map((item) => ({ semantic_source: item.semanticSource, implementation_target: item.implementationTarget }))],
    ["approval", binding.approvalPolicy], ["capability", binding.capabilityName],
  ]);
  for (const component of workflow.components) section(lines, "component", component.id, [
    ["version", component.version], ["title", component.title], ["inputs", component.inputPortIds],
    ["outputs", component.outputPortIds], ["digest", component.internalDefinitionDigest],
    ["addresses", component.internalAddresses.map((address) => ({ semantic_id: address.semanticId, concept_kind: address.conceptKind, relative_path: address.relativePath }))],
  ]);
  const text = `${lines.join("\n").trimEnd()}\n`;
  return { text, sourceMap: sourceMapFor(text) };
}

function diagnostic(
  code: string,
  explanation: string,
  correction: string,
  semanticId: string | null = null,
  line: number | null = null,
): RecoveryDiagnostic {
  return { code, explanation, correction, semanticId, line };
}

function sourceMapFor(text: string): Record<string, RecoverySourceMapEntry> {
  const map: Record<string, RecoverySourceMapEntry> = {};
  const lines = text.split("\n");
  let offset = 0;
  let active: { id: string; line: number; offset: number } | null = null;
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    if (active === null) {
      const match = /^(workflow|phase|block|port|relationship|artifact|binding|component)\s+([a-z0-9._-]+)$/.exec(line.trim());
      if (match?.[2]) active = { id: match[2], line: lineNumber, offset };
    } else if (line.trim() === "end") {
      map[active.id] = { startLine: active.line, endLine: lineNumber, startOffset: active.offset, endOffset: offset + line.length };
      active = null;
    }
    offset += line.length + 1;
  });
  const unterminated = active as { id: string; line: number; offset: number } | null;
  if (unterminated !== null) {
    map[unterminated.id] = { startLine: unterminated.line, endLine: lines.length, startOffset: unterminated.offset, endOffset: text.length };
  }
  return map;
}

function asString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  return value;
}

function asNullableString(value: unknown, field: string): string | null {
  if (value === null) return null;
  return asString(value, field);
}

function asNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  return value;
}

function asBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  return value;
}

function asStringArray(value: unknown, field: string): string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  return [...value];
}

function asActionArray(value: unknown): RecoveryArtifactContract["allowedActions"] {
  const actions = asStringArray(value, "actions");
  const allowed = new Set(["inspect", "preview", "open", "download", "replace"]);
  if (actions.some((action) => !allowed.has(action)) || new Set(actions).size !== actions.length) throw new Error("WFR-TEXT-FIELD-ENUM:actions");
  return actions as RecoveryArtifactContract["allowedActions"];
}

function asRecord(value: unknown, field: string): Record<string, string | number | boolean> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  const row = value as Record<string, unknown>;
  if (Object.values(row).some((item) => !["string", "number", "boolean"].includes(typeof item) || (typeof item === "number" && !Number.isFinite(item)))) {
    throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  }
  return { ...row } as Record<string, string | number | boolean>;
}

function asComponentRef(value: unknown): RecoveryBlock["componentRef"] {
  if (value === null) return null;
  if (typeof value !== "object" || Array.isArray(value)) throw new Error("WFR-TEXT-FIELD-TYPE:component");
  const row = value as Record<string, unknown>;
  if (Object.keys(row).sort().join(",") !== "component_id,version_range") throw new Error("WFR-TEXT-FIELD-TYPE:component");
  return { componentId: asString(row.component_id, "component_id"), versionRange: asString(row.version_range, "version_range") };
}

function asBindingMaps(value: unknown, field: string): RecoveryBinding["argumentMap"] {
  if (!Array.isArray(value)) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
  return value.map((item) => {
    if (item === null || typeof item !== "object" || Array.isArray(item)) throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
    const row = item as Record<string, unknown>;
    if (Object.keys(row).sort().join(",") !== "implementation_target,semantic_source") throw new Error(`WFR-TEXT-FIELD-TYPE:${field}`);
    return { semanticSource: asString(row.semantic_source, "semantic_source"), implementationTarget: asString(row.implementation_target, "implementation_target") };
  });
}

function asComponentAddresses(value: unknown): RecoveryComponent["internalAddresses"] {
  if (!Array.isArray(value)) throw new Error("WFR-TEXT-FIELD-TYPE:addresses");
  return value.map((item) => {
    if (item === null || typeof item !== "object" || Array.isArray(item)) throw new Error("WFR-TEXT-FIELD-TYPE:addresses");
    const row = item as Record<string, unknown>;
    if (Object.keys(row).sort().join(",") !== "concept_kind,relative_path,semantic_id") throw new Error("WFR-TEXT-FIELD-TYPE:addresses");
    return {
      semanticId: asString(row.semantic_id, "semantic_id"),
      conceptKind: oneOf(row.concept_kind, ["block", "port", "relationship", "artifact_contract", "binding", "component"] as const, "concept_kind"),
      relativePath: asString(row.relative_path, "relative_path"),
    };
  });
}

function oneOf<T extends string>(value: unknown, options: readonly T[], field: string): T {
  if (typeof value !== "string" || !options.includes(value as T)) throw new Error(`WFR-TEXT-FIELD-ENUM:${field}`);
  return value as T;
}

function componentVersionMatches(version: string, range: string): boolean {
  if (range === version) return true;
  const versionMatch = /^(\d+)\.(\d+)\.(\d+)$/.exec(version);
  const rangeMatch = /^\^(\d+)\.(\d+)\.(\d+)$/.exec(range);
  if (!versionMatch || !rangeMatch) return false;
  const current = versionMatch.slice(1).map(Number);
  const minimum = rangeMatch.slice(1).map(Number);
  if (current[0] !== minimum[0]) return false;
  return current[1]! > minimum[1]! || (current[1] === minimum[1] && current[2]! >= minimum[2]!);
}

function exactFields(sectionValue: Section): void {
  const expected = new Set(fieldSets[sectionValue.kind]);
  for (const field of Object.keys(sectionValue.fields)) {
    if (!expected.has(field)) throw new Error(`WFR-TEXT-FIELD-UNKNOWN:${field}`);
  }
  for (const field of expected) {
    if (!(field in sectionValue.fields)) throw new Error(`WFR-TEXT-FIELD-MISSING:${field}`);
  }
}

function parseSections(text: string): Section[] {
  const sections: Section[] = [];
  let current: Omit<Section, "endLine"> | null = null;
  for (const [index, raw] of text.split("\n").entries()) {
    const line = index + 1;
    const value = raw.trim();
    if (!value || value.startsWith("#")) continue;
    if (current === null) {
      const match = /^(workflow|phase|block|port|relationship|artifact|binding|component)\s+([a-z0-9._-]+)$/.exec(value);
      if (!match?.[1] || !match[2]) throw new Error(`WFR-TEXT-SECTION:${line}`);
      current = { kind: match[1] as SectionKind, id: match[2], fields: {}, startLine: line };
      continue;
    }
    if (value === "end") {
      const completed: Section = { ...current, endLine: line };
      exactFields(completed);
      sections.push(completed);
      current = null;
      continue;
    }
    const separator = value.indexOf(":");
    if (separator < 1) throw new Error(`WFR-TEXT-FIELD:${line}`);
    const name = value.slice(0, separator).trim();
    if (name in current.fields) throw new Error(`WFR-TEXT-FIELD-DUPLICATE:${line}:${name}`);
    const rawValue = value.slice(separator + 1).trim();
    try {
      current.fields[name] = /^["[{]|^(?:null|true|false|-?\d)/.test(rawValue) ? JSON.parse(rawValue) : rawValue;
    } catch {
      throw new Error(`WFR-TEXT-VALUE:${line}:${name}`);
    }
  }
  if (current !== null) throw new Error(`WFR-TEXT-SECTION-UNTERMINATED:${current.startLine}`);
  return sections;
}

function validateModel(workflow: RecoveryWorkflow): RecoveryDiagnostic[] {
  const diagnostics: RecoveryDiagnostic[] = [];
  const all = [...workflow.phases, ...workflow.blocks, ...workflow.ports, ...workflow.relationships, ...workflow.artifactContracts, ...workflow.bindings, ...workflow.components];
  const seen = new Set<string>();
  for (const item of all) {
    if (seen.has(item.id)) diagnostics.push(diagnostic("WFR-ID-DUPLICATE", `Stable identity ${item.id} is duplicated.`, "Assign one globally unique identity.", item.id));
    seen.add(item.id);
  }
  const blocks = new Map(workflow.blocks.map((block) => [block.id, block]));
  const phases = new Set(workflow.phases.map((phase) => phase.id));
  const ports = new Map(workflow.ports.map((port) => [port.id, port]));
  const bindings = new Set(workflow.bindings.map((binding) => binding.id));
  const components = new Map(workflow.components.map((component) => [component.id, component]));
  const artifacts = new Set(workflow.artifactContracts.map((artifact) => artifact.id));
  const blockOrder = new Map<string, number>();
  for (const phase of [...workflow.phases].sort((left, right) => left.order - right.order)) {
    phase.blockIds.forEach((blockId, index) => blockOrder.set(blockId, phase.order * 10000 + index));
  }
  if (!Number.isInteger(workflow.revision) || workflow.revision < 1 || (workflow.parentRevision !== null && (!Number.isInteger(workflow.parentRevision) || workflow.parentRevision < 1))) {
    diagnostics.push(diagnostic("WFR-REVISION-INVALID", "Revision identities must be positive integers.", "Use a positive revision and parent revision."));
  }
  if (workflow.semanticSha256 !== null && !/^[a-f0-9]{64}$/.test(workflow.semanticSha256)) diagnostics.push(diagnostic("WFR-DIGEST-INVALID", "semantic_sha256 must be 64 lowercase hexadecimal characters.", "Recompute the semantic digest or use null before acceptance."));
  const phaseMembership = new Map<string, string[]>();
  for (const phase of workflow.phases) {
    if (new Set(phase.blockIds).size !== phase.blockIds.length) diagnostics.push(diagnostic("WFR-ID-DUPLICATE", `${phase.id} lists a block more than once.`, "Keep each block identity once.", phase.id));
    for (const blockId of phase.blockIds) {
      if (!blocks.has(blockId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${phase.id} references missing block ${blockId}.`, "Choose an existing block.", phase.id));
      phaseMembership.set(blockId, [...(phaseMembership.get(blockId) ?? []), phase.id]);
    }
  }
  for (const block of workflow.blocks) {
    if (block.phaseId !== null && !phases.has(block.phaseId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${block.id} references missing phase ${block.phaseId}.`, "Choose an existing phase.", block.id));
    const memberships = phaseMembership.get(block.id) ?? [];
    if (block.phaseId === null ? memberships.length !== 0 : memberships.length !== 1 || memberships[0] !== block.phaseId) diagnostics.push(diagnostic("WFR-PHASE-MEMBERSHIP", `${block.id} and its declared phase are not exactly reciprocal.`, "List the block exactly once in its declared phase, or in no phase when phase is null.", block.id));
    if (block.bindingId !== null && !bindings.has(block.bindingId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${block.id} references missing binding ${block.bindingId}.`, "Choose an existing binding.", block.id));
    if (block.kind === "component" && block.componentRef === null) diagnostics.push(diagnostic("WFR-COMPONENT-REFERENCE-REQUIRED", `${block.id} is a component instance without a component reference.`, "Reference an existing component and compatible version range.", block.id));
    if (block.kind !== "component" && block.componentRef !== null) diagnostics.push(diagnostic("WFR-COMPONENT-BLOCK-KIND", `${block.id} references a reusable component but is not kind component.`, "Use kind component for reusable component instances.", block.id));
    if (block.componentRef !== null) {
      const component = components.get(block.componentRef.componentId);
      if (!component) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${block.id} references missing component ${block.componentRef.componentId}.`, "Choose an existing component.", block.id));
      else {
        if (!componentVersionMatches(component.version, block.componentRef.versionRange)) diagnostics.push(diagnostic("WFR-COMPONENT-VERSION-INCOMPATIBLE", `${block.id} requests ${block.componentRef.versionRange}, but ${component.id} is ${component.version}.`, "Select a compatible component version or update the reviewed range.", block.id));
        if (block.inputPortIds.join("\n") !== component.inputPortIds.join("\n") || block.outputPortIds.join("\n") !== component.outputPortIds.join("\n")) diagnostics.push(diagnostic("WFR-COMPONENT-INTERFACE-MISMATCH", `${block.id} does not expose the exact reviewed interface of ${component.id}.`, "Use the component's ordered input and output port identities.", block.id));
      }
    }
    for (const [portIds, direction] of [[block.inputPortIds, "input"], [block.outputPortIds, "output"]] as const) {
      if (new Set(portIds).size !== portIds.length) diagnostics.push(diagnostic("WFR-ID-DUPLICATE", `${block.id} lists a ${direction} port more than once.`, "Keep each port identity once.", block.id));
      for (const portId of portIds) {
        const port = ports.get(portId);
        if (!port || port.ownerBlockId !== block.id || port.direction !== direction) diagnostics.push(diagnostic("WFR-PORT-OWNERSHIP", `${portId} is not a ${direction} owned by ${block.id}.`, "Use a reciprocal owned port with the declared direction.", block.id));
      }
    }
  }
  for (const port of workflow.ports) {
    const owner = blocks.get(port.ownerBlockId);
    if (!owner) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${port.id} references missing owner ${port.ownerBlockId}.`, "Choose an existing block.", port.id));
    else if (!(port.direction === "input" ? owner.inputPortIds : owner.outputPortIds).includes(port.id)) diagnostics.push(diagnostic("WFR-PORT-OWNERSHIP", `${port.id} is not reciprocally listed by ${owner.id}.`, "Add the port to the owning block's matching direction list.", port.id));
    if (port.artifactContractId !== null && !artifacts.has(port.artifactContractId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${port.id} references missing artifact ${port.artifactContractId}.`, "Choose an existing artifact contract.", port.id));
  }
  const endpointPairs = new Map<string, string>();
  const incomingData = new Map<string, string[]>();
  const adjacency = new Map<string, { target: string; relationshipId: string }[]>();
  for (const relationship of workflow.relationships) {
    const endpointKey = `${relationship.sourceId}\u0000${relationship.targetId}`;
    const priorEndpoint = endpointPairs.get(endpointKey);
    if (priorEndpoint) diagnostics.push(diagnostic("WFR-RELATIONSHIP-DUPLICATE", `${relationship.id} duplicates the endpoints of ${priorEndpoint}.`, "Keep one relationship for an endpoint pair or introduce a distinct semantic target.", relationship.id));
    else endpointPairs.set(endpointKey, relationship.id);
    const source = ports.get(relationship.sourceId);
    const target = ports.get(relationship.targetId);
    let sourceBlockId: string | null = null;
    let targetBlockId: string | null = null;
    if (relationship.kind === "data") {
      if (!source || !target) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${relationship.id} has a missing port endpoint.`, "Choose existing ports.", relationship.id));
      else if (source.direction !== "output" || target.direction !== "input") diagnostics.push(diagnostic("WFR-DATA-ENDPOINTS", `${relationship.id} must connect output to input.`, "Connect a right output handle to a left input handle.", relationship.id));
      else if (source.typeId !== target.typeId) diagnostics.push(diagnostic("WFR-PORT-TYPE-MISMATCH", `${source.typeId} cannot feed ${target.typeId}.`, "Choose identical types or an explicit adapter.", relationship.id));
      if (source && target) {
        sourceBlockId = source.ownerBlockId;
        targetBlockId = target.ownerBlockId;
        incomingData.set(target.id, [...(incomingData.get(target.id) ?? []), relationship.id]);
      }
    } else {
      sourceBlockId = relationship.sourceId;
      targetBlockId = relationship.targetId;
      const sourceBlock = blocks.get(relationship.sourceId);
      if (!sourceBlock || !blocks.has(relationship.targetId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${relationship.id} has a missing block endpoint.`, "Choose existing blocks.", relationship.id));
      const isReviewComponent = sourceBlock?.kind === "component" && sourceBlock.componentRef?.componentId === "component.review-cell";
      if ((relationship.kind === "decision" || relationship.kind === "feedback") && sourceBlock && sourceBlock.kind !== "decision" && sourceBlock.kind !== "approval" && !isReviewComponent) {
        diagnostics.push(diagnostic("WFR-RELATIONSHIP-SOURCE-KIND", `${relationship.id} must originate at a decision or approval block.`, "Choose a decision/approval source or use data/control flow.", relationship.id));
      }
      if (relationship.kind === "feedback") {
        const sourceOrder = blockOrder.get(relationship.sourceId);
        const targetOrder = blockOrder.get(relationship.targetId);
        if (sourceOrder !== undefined && targetOrder !== undefined && targetOrder >= sourceOrder) diagnostics.push(diagnostic("WFR-FEEDBACK-DIRECTION", `${relationship.id} must return to an earlier block or component.`, "Choose an earlier revision target or use forward control flow.", relationship.id));
      }
    }
    if (relationship.kind !== "feedback" && sourceBlockId && targetBlockId) {
      adjacency.set(sourceBlockId, [...(adjacency.get(sourceBlockId) ?? []), { target: targetBlockId, relationshipId: relationship.id }]);
    }
  }
  for (const [portId, relationshipIds] of incomingData) {
    const port = ports.get(portId)!;
    if (port.cardinality !== "many" && relationshipIds.length > 1) diagnostics.push(diagnostic("WFR-PORT-CARDINALITY", `${port.id} accepts ${port.cardinality} but has ${relationshipIds.length} incoming data relationships.`, "Remove extra connections or declare many cardinality.", port.id));
  }
  const visitState = new Map<string, 0 | 1 | 2>();
  let cycleReported = false;
  const visit = (blockId: string): void => {
    if (cycleReported) return;
    visitState.set(blockId, 1);
    for (const edge of adjacency.get(blockId) ?? []) {
      if ((visitState.get(edge.target) ?? 0) === 1) {
        diagnostics.push(diagnostic("WFR-CYCLE-NON-FEEDBACK", `${edge.relationshipId} closes a cycle without an explicit feedback relationship.`, "Mark the intentional revision back-edge as feedback or remove the cycle.", edge.relationshipId));
        cycleReported = true;
        return;
      }
      if ((visitState.get(edge.target) ?? 0) === 0) visit(edge.target);
    }
    visitState.set(blockId, 2);
  };
  for (const blockId of blocks.keys()) if ((visitState.get(blockId) ?? 0) === 0) visit(blockId);
  for (const artifact of workflow.artifactContracts) {
    if (artifact.producerBlockId !== null && !blocks.has(artifact.producerBlockId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${artifact.id} references missing producer ${artifact.producerBlockId}.`, "Choose an existing producer block.", artifact.id));
    for (const blockId of artifact.requiredForBlockIds) if (!blocks.has(blockId)) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${artifact.id} references missing consumer ${blockId}.`, "Choose an existing consumer block.", artifact.id));
  }
  for (const binding of workflow.bindings) {
    const owners = new Set(workflow.blocks.filter((block) => block.bindingId === binding.id).map((block) => block.id));
    for (const map of binding.argumentMap) {
      const port = ports.get(map.semanticSource);
      const configOwner = [...owners].find((ownerId) => {
        const prefix = `${ownerId}.configuration.`;
        return map.semanticSource.startsWith(prefix) && map.semanticSource.slice(prefix.length) in (blocks.get(ownerId)?.configuration ?? {});
      });
      if (!port && !configOwner) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${binding.id} maps missing argument source ${map.semanticSource}.`, "Map an owned input port or declared configuration value.", binding.id));
      else if (port && (port.direction !== "input" || (owners.size > 0 && !owners.has(port.ownerBlockId)))) diagnostics.push(diagnostic("WFR-BINDING-MAP-DIRECTION", `${binding.id} argument source ${map.semanticSource} is not an owned input.`, "Map an input port owned by a block using this binding.", binding.id));
    }
    for (const map of binding.resultMap) {
      const port = ports.get(map.semanticSource);
      const artifact = workflow.artifactContracts.find((item) => item.id === map.semanticSource);
      if (!port && !artifact) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${binding.id} maps missing result target ${map.semanticSource}.`, "Map an owned output port or produced artifact contract.", binding.id));
      else if (port && (port.direction !== "output" || (owners.size > 0 && !owners.has(port.ownerBlockId)))) diagnostics.push(diagnostic("WFR-BINDING-MAP-DIRECTION", `${binding.id} result target ${map.semanticSource} is not an owned output.`, "Map an output port owned by a block using this binding.", binding.id));
      else if (artifact && owners.size > 0 && (artifact.producerBlockId === null || !owners.has(artifact.producerBlockId))) diagnostics.push(diagnostic("WFR-BINDING-MAP-DIRECTION", `${binding.id} result artifact ${map.semanticSource} is not produced by an owning block.`, "Map an artifact produced by a block using this binding.", binding.id));
    }
  }
  for (const component of workflow.components) {
    for (const [portIds, direction] of [[component.inputPortIds, "input"], [component.outputPortIds, "output"]] as const) for (const portId of portIds) {
      const port = ports.get(portId);
      if (!port) diagnostics.push(diagnostic("WFR-REFERENCE-DANGLING", `${component.id} exposes missing port ${portId}.`, "Expose an existing typed port.", component.id));
      else if (port.direction !== direction) diagnostics.push(diagnostic("WFR-COMPONENT-PORT-DIRECTION", `${component.id} exposes ${portId} as ${direction}, but the port is ${port.direction}.`, "Use a component interface port with the matching direction.", component.id));
    }
    if (!/^sha256:[a-f0-9]{64}$/.test(component.internalDefinitionDigest)) diagnostics.push(diagnostic("WFR-DIGEST-INVALID", `${component.id} has an invalid internal definition digest.`, "Use a sha256-prefixed 64-hex digest.", component.id));
    const semanticIds = new Set<string>();
    const relativePaths = new Set<string>();
    const pathRoots: Record<RecoveryComponent["internalAddresses"][number]["conceptKind"], string> = { block: "blocks/", port: "ports/", relationship: "relationships/", artifact_contract: "artifact-contracts/", binding: "bindings/", component: "components/" };
    if (component.internalAddresses.length === 0) diagnostics.push(diagnostic("WFR-COMPONENT-ADDRESS-EMPTY", `${component.id} has no stable internal semantic addresses.`, "Address each internal concept required by diagnostics and historical run lineage.", component.id));
    for (const address of component.internalAddresses) {
      if (!address.semanticId.startsWith(`${component.id}.`)) diagnostics.push(diagnostic("WFR-COMPONENT-ADDRESS-SCOPE", `${address.semanticId} is outside ${component.id}.`, "Prefix every internal semantic address with the component identity.", component.id));
      if (semanticIds.has(address.semanticId) || relativePaths.has(address.relativePath)) diagnostics.push(diagnostic("WFR-COMPONENT-ADDRESS-DUPLICATE", `${component.id} repeats an internal semantic identity or relative path.`, "Assign one stable identity and one relative path per internal concept.", component.id));
      if (!address.relativePath.startsWith(pathRoots[address.conceptKind]) || address.relativePath.split("/").some((segment) => segment === "." || segment === "..")) diagnostics.push(diagnostic("WFR-COMPONENT-ADDRESS-PATH", `${address.relativePath} does not match ${address.conceptKind}.`, "Use the matching collection root and no dot traversal segments.", component.id));
      semanticIds.add(address.semanticId);
      relativePaths.add(address.relativePath);
    }
  }
  return diagnostics;
}

export function parseRecoveryDsl(text: string): RecoveryParseResult {
  try {
    const sections = parseSections(text);
    const workflowSections = sections.filter((item) => item.kind === "workflow");
    if (workflowSections.length !== 1) throw new Error("WFR-TEXT-WORKFLOW-COUNT");
    const root = workflowSections[0];
    if (!root) throw new Error("WFR-TEXT-WORKFLOW-COUNT");
    const phase = (item: Section): RecoveryPhase => ({
      id: item.id, name: asString(item.fields.name, "name"), purpose: asString(item.fields.purpose, "purpose"),
      order: asNumber(item.fields.order, "order"), blockIds: asStringArray(item.fields.blocks, "blocks"),
    });
    const block = (item: Section): RecoveryBlock => ({
      id: item.id, kind: oneOf(item.fields.kind, ["work", "approval", "decision", "component"] as const, "kind"),
      title: asString(item.fields.title, "title"), purpose: asString(item.fields.purpose, "purpose"), phaseId: asNullableString(item.fields.phase, "phase"),
      executionKind: oneOf(item.fields.execution, ["human", "deterministic", "ai_capable"] as const, "execution"),
      instructions: asString(item.fields.instructions, "instructions"), configuration: asRecord(item.fields.config, "config"),
      inputPortIds: asStringArray(item.fields.inputs, "inputs"), outputPortIds: asStringArray(item.fields.outputs, "outputs"),
      bindingId: asNullableString(item.fields.binding, "binding"),
      componentRef: asComponentRef(item.fields.component),
    });
    const port = (item: Section): RecoveryPort => ({
      id: item.id, ownerBlockId: asString(item.fields.owner, "owner"), direction: oneOf(item.fields.direction, ["input", "output"] as const, "direction"),
      name: asString(item.fields.name, "name"), typeId: asString(item.fields.type, "type"), required: asBoolean(item.fields.required, "required"),
      cardinality: oneOf(item.fields.cardinality, ["one", "optional", "many"] as const, "cardinality"),
      artifactContractId: asNullableString(item.fields.artifact, "artifact"), description: asString(item.fields.description, "description"),
    });
    const relationship = (item: Section): RecoveryRelationship => ({
      id: item.id, kind: oneOf(item.fields.kind, ["data", "control", "decision", "feedback"] as const, "kind"),
      sourceId: asString(item.fields.source, "source"), targetId: asString(item.fields.target, "target"),
      label: asString(item.fields.label, "label"), condition: asNullableString(item.fields.condition, "condition"),
    });
    const artifact = (item: Section): RecoveryArtifactContract => ({
      id: item.id, name: asString(item.fields.name, "name"), typeId: asString(item.fields.type, "type"), mediaType: asString(item.fields.media, "media"),
      description: asString(item.fields.description, "description"), producerBlockId: asNullableString(item.fields.producer, "producer"),
      requiredForBlockIds: asStringArray(item.fields.required_for, "required_for"), previewPolicy: oneOf(item.fields.preview, ["inline", "metadata", "none"] as const, "preview"),
      allowedActions: asActionArray(item.fields.actions),
    });
    const binding = (item: Section): RecoveryBinding => {
      return {
        id: item.id, kind: oneOf(item.fields.kind, ["internal", "mcp_tool", "human"] as const, "kind"),
        providerId: asNullableString(item.fields.provider, "provider"), serverId: asNullableString(item.fields.server, "server"),
        toolId: asNullableString(item.fields.tool, "tool"), schemaDigest: asNullableString(item.fields.schema, "schema"),
        argumentMap: asBindingMaps(item.fields.arguments, "arguments"), resultMap: asBindingMaps(item.fields.results, "results"),
        approvalPolicy: oneOf(item.fields.approval, ["none", "review_before_run", "explicit_external_write"] as const, "approval"),
        capabilityName: asString(item.fields.capability, "capability"),
      };
    };
    const component = (item: Section): RecoveryComponent => ({
      id: item.id,
      version: asString(item.fields.version, "version"),
      title: asString(item.fields.title, "title"),
      inputPortIds: asStringArray(item.fields.inputs, "inputs"),
      outputPortIds: asStringArray(item.fields.outputs, "outputs"),
      internalDefinitionDigest: asString(item.fields.digest, "digest"),
      internalAddresses: asComponentAddresses(item.fields.addresses),
    });
    const workflow: RecoveryWorkflow = {
      documentKind: "workflow-ir", schemaVersion: oneOf(root.fields.version, ["2.0.0-recovery.1"] as const, "version"),
      workflowId: root.id, revision: asNumber(root.fields.revision, "revision"),
      parentRevision: root.fields.parent === null ? null : asNumber(root.fields.parent, "parent"),
      semanticSha256: asNullableString(root.fields.semantic_sha256, "semantic_sha256"),
      metadata: {
        title: asString(root.fields.title, "title"), purpose: asString(root.fields.purpose, "purpose"),
        engineeringDomain: asString(root.fields.domain, "domain"),
        authorship: oneOf(root.fields.authorship, ["human", "human_with_ai_proposal"] as const, "authorship"),
      },
      phases: sections.filter((item) => item.kind === "phase").map(phase),
      blocks: sections.filter((item) => item.kind === "block").map(block),
      ports: sections.filter((item) => item.kind === "port").map(port),
      relationships: sections.filter((item) => item.kind === "relationship").map(relationship),
      artifactContracts: sections.filter((item) => item.kind === "artifact").map(artifact),
      bindings: sections.filter((item) => item.kind === "binding").map(binding),
      components: sections.filter((item) => item.kind === "component").map(component),
    };
    const diagnostics = validateModel(workflow);
    return { ok: diagnostics.length === 0, workflow: diagnostics.length === 0 ? workflow : null, diagnostics, sourceMap: sourceMapFor(text) };
  } catch (error) {
    const message = error instanceof Error ? error.message : "WFR-TEXT-UNKNOWN";
    const parts = message.split(":");
    const line = parts.find((part) => /^\d+$/.test(part));
    const code = parts[0]?.startsWith("WFR-") ? parts[0] : "WFR-TEXT-UNKNOWN";
    const map = sourceMapFor(text);
    const lineNumber = line ? Number(line) : null;
    const semanticId = lineNumber === null ? null : Object.entries(map)
      .filter(([, span]) => span.startLine <= lineNumber)
      .sort(([, left], [, right]) => right.startLine - left.startLine)[0]?.[0] ?? null;
    return {
      ok: false,
      workflow: null,
      diagnostics: [diagnostic(code ?? "WFR-TEXT-UNKNOWN", message, "Correct the reported source field; the last-valid diagram is unchanged.", semanticId, lineNumber)],
      sourceMap: map,
    };
  }
}

export function semanticJson(workflow: RecoveryWorkflow): string {
  return JSON.stringify(workflow);
}

export function sourceSelection(sourceMap: Record<string, RecoverySourceMapEntry>, semanticId: string | null): RecoverySourceMapEntry | null {
  return semanticId === null ? null : sourceMap[semanticId] ?? null;
}
