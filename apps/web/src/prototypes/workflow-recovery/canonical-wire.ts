import type { RecoveryLayout, RecoveryWorkflow } from "./model";

export interface CanonicalWorkflowWire {
  document_kind: "workflow-ir";
  schema_version: "2.0.0-recovery.1";
  workflow_id: string;
  revision: number;
  parent_revision: number | null;
  semantic_sha256: string | null;
  metadata: {
    title: string;
    purpose: string;
    engineering_domain: string;
    authorship: "human" | "human_with_ai_proposal";
  };
  phases: { id: string; name: string; purpose: string; order: number; block_ids: string[] }[];
  blocks: {
    id: string;
    kind: "work" | "approval" | "decision" | "component";
    title: string;
    purpose: string;
    phase_id: string | null;
    execution_kind: "human" | "deterministic" | "ai_capable";
    instructions: string;
    configuration: Record<string, string | number | boolean>;
    input_port_ids: string[];
    output_port_ids: string[];
    binding_id: string | null;
    component_ref: { component_id: string; version_range: string } | null;
  }[];
  ports: {
    id: string;
    owner_block_id: string;
    direction: "input" | "output";
    name: string;
    type_id: string;
    required: boolean;
    cardinality: "one" | "optional" | "many";
    artifact_contract_id: string | null;
    description: string;
  }[];
  relationships: { id: string; kind: "data" | "control" | "decision" | "feedback"; source_id: string; target_id: string; label: string; condition: string | null }[];
  artifact_contracts: {
    id: string;
    name: string;
    type_id: string;
    media_type: string;
    description: string;
    producer_block_id: string | null;
    required_for_block_ids: string[];
    preview_policy: "inline" | "metadata" | "none";
    allowed_actions: ("inspect" | "preview" | "open" | "download" | "replace")[];
  }[];
  bindings: {
    id: string;
    kind: "internal" | "mcp_tool" | "human";
    provider_id: string | null;
    server_id: string | null;
    tool_id: string | null;
    schema_digest: string | null;
    argument_map: { semantic_source: string; implementation_target: string }[];
    result_map: { semantic_source: string; implementation_target: string }[];
    approval_policy: "none" | "review_before_run" | "explicit_external_write";
    capability_name: string;
  }[];
  components: {
    id: string;
    version: string;
    title: string;
    input_port_ids: string[];
    output_port_ids: string[];
    internal_definition_digest: string;
    internal_addresses: {
      semantic_id: string;
      concept_kind: "block" | "port" | "relationship" | "artifact_contract" | "binding" | "component";
      relative_path: string;
    }[];
  }[];
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue);
  if (value !== null && typeof value === "object") {
    return Object.fromEntries(Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, child]) => [key, stableValue(child)]));
  }
  return value;
}

/** Object insertion order is not part of saved layout identity. */
export function canonicalLayoutBytes(layout: RecoveryLayout): string {
  return JSON.stringify(stableValue(layout));
}

export function canonicalLayoutPositionBytes(layout: RecoveryLayout): string {
  return JSON.stringify(stableValue(layout.positions));
}

export function canonicalDefinitionBytes(workflow: RecoveryWorkflow, excludeAuthority = false): string {
  const fullWire = structuredClone(toCanonicalWire(workflow));
  const wire = Object.fromEntries(
    Object.entries(fullWire).filter(([key]) => key !== "semantic_sha256"),
  ) as Omit<CanonicalWorkflowWire, "semantic_sha256">;
  wire.blocks.sort((left, right) => left.id.localeCompare(right.id));
  wire.ports.sort((left, right) => left.id.localeCompare(right.id));
  wire.relationships.sort((left, right) => left.id.localeCompare(right.id));
  wire.artifact_contracts.sort((left, right) => left.id.localeCompare(right.id));
  wire.bindings.sort((left, right) => left.id.localeCompare(right.id));
  wire.components.sort((left, right) => left.id.localeCompare(right.id));
  if (excludeAuthority) {
    wire.revision = 0;
    wire.parent_revision = null;
  }
  return JSON.stringify(stableValue(wire));
}

export function toCanonicalWire(workflow: RecoveryWorkflow): CanonicalWorkflowWire {
  return {
    document_kind: workflow.documentKind,
    schema_version: workflow.schemaVersion,
    workflow_id: workflow.workflowId,
    revision: workflow.revision,
    parent_revision: workflow.parentRevision,
    semantic_sha256: workflow.semanticSha256,
    metadata: {
      title: workflow.metadata.title,
      purpose: workflow.metadata.purpose,
      engineering_domain: workflow.metadata.engineeringDomain,
      authorship: workflow.metadata.authorship,
    },
    phases: workflow.phases.map((phase) => ({ id: phase.id, name: phase.name, purpose: phase.purpose, order: phase.order, block_ids: [...phase.blockIds] })),
    blocks: workflow.blocks.map((block) => ({
      id: block.id,
      kind: block.kind,
      title: block.title,
      purpose: block.purpose,
      phase_id: block.phaseId,
      execution_kind: block.executionKind,
      instructions: block.instructions,
      configuration: { ...block.configuration },
      input_port_ids: [...block.inputPortIds],
      output_port_ids: [...block.outputPortIds],
      binding_id: block.bindingId,
      component_ref: block.componentRef === null ? null : { component_id: block.componentRef.componentId, version_range: block.componentRef.versionRange },
    })),
    ports: workflow.ports.map((port) => ({ id: port.id, owner_block_id: port.ownerBlockId, direction: port.direction, name: port.name, type_id: port.typeId, required: port.required, cardinality: port.cardinality, artifact_contract_id: port.artifactContractId, description: port.description })),
    relationships: workflow.relationships.map((relationship) => ({ id: relationship.id, kind: relationship.kind, source_id: relationship.sourceId, target_id: relationship.targetId, label: relationship.label, condition: relationship.condition })),
    artifact_contracts: workflow.artifactContracts.map((artifact) => ({ id: artifact.id, name: artifact.name, type_id: artifact.typeId, media_type: artifact.mediaType, description: artifact.description, producer_block_id: artifact.producerBlockId, required_for_block_ids: [...artifact.requiredForBlockIds], preview_policy: artifact.previewPolicy, allowed_actions: [...artifact.allowedActions] })),
    bindings: workflow.bindings.map((binding) => ({
      id: binding.id,
      kind: binding.kind,
      provider_id: binding.providerId,
      server_id: binding.serverId,
      tool_id: binding.toolId,
      schema_digest: binding.schemaDigest,
      argument_map: binding.argumentMap.map((item) => ({ semantic_source: item.semanticSource, implementation_target: item.implementationTarget })),
      result_map: binding.resultMap.map((item) => ({ semantic_source: item.semanticSource, implementation_target: item.implementationTarget })),
      approval_policy: binding.approvalPolicy,
      capability_name: binding.capabilityName,
    })),
    components: workflow.components.map((component) => ({
      id: component.id,
      version: component.version,
      title: component.title,
      input_port_ids: [...component.inputPortIds],
      output_port_ids: [...component.outputPortIds],
      internal_definition_digest: component.internalDefinitionDigest,
      internal_addresses: component.internalAddresses.map((address) => ({ semantic_id: address.semanticId, concept_kind: address.conceptKind, relative_path: address.relativePath })),
    })),
  };
}

export function fromCanonicalWire(wire: CanonicalWorkflowWire): RecoveryWorkflow {
  return {
    documentKind: wire.document_kind,
    schemaVersion: wire.schema_version,
    workflowId: wire.workflow_id,
    revision: wire.revision,
    parentRevision: wire.parent_revision,
    semanticSha256: wire.semantic_sha256,
    metadata: { title: wire.metadata.title, purpose: wire.metadata.purpose, engineeringDomain: wire.metadata.engineering_domain, authorship: wire.metadata.authorship },
    phases: wire.phases.map((phase) => ({ id: phase.id, name: phase.name, purpose: phase.purpose, order: phase.order, blockIds: [...phase.block_ids] })),
    blocks: wire.blocks.map((block) => ({
      id: block.id,
      kind: block.kind,
      title: block.title,
      purpose: block.purpose,
      phaseId: block.phase_id,
      executionKind: block.execution_kind,
      instructions: block.instructions,
      configuration: { ...block.configuration },
      inputPortIds: [...block.input_port_ids],
      outputPortIds: [...block.output_port_ids],
      bindingId: block.binding_id,
      componentRef: block.component_ref === null ? null : { componentId: block.component_ref.component_id, versionRange: block.component_ref.version_range },
    })),
    ports: wire.ports.map((port) => ({ id: port.id, ownerBlockId: port.owner_block_id, direction: port.direction, name: port.name, typeId: port.type_id, required: port.required, cardinality: port.cardinality, artifactContractId: port.artifact_contract_id, description: port.description })),
    relationships: wire.relationships.map((relationship) => ({ id: relationship.id, kind: relationship.kind, sourceId: relationship.source_id, targetId: relationship.target_id, label: relationship.label, condition: relationship.condition })),
    artifactContracts: wire.artifact_contracts.map((artifact) => ({ id: artifact.id, name: artifact.name, typeId: artifact.type_id, mediaType: artifact.media_type, description: artifact.description, producerBlockId: artifact.producer_block_id, requiredForBlockIds: [...artifact.required_for_block_ids], previewPolicy: artifact.preview_policy, allowedActions: [...artifact.allowed_actions] })),
    bindings: wire.bindings.map((binding) => ({
      id: binding.id,
      kind: binding.kind,
      providerId: binding.provider_id,
      serverId: binding.server_id,
      toolId: binding.tool_id,
      schemaDigest: binding.schema_digest,
      argumentMap: binding.argument_map.map((item) => ({ semanticSource: item.semantic_source, implementationTarget: item.implementation_target })),
      resultMap: binding.result_map.map((item) => ({ semanticSource: item.semantic_source, implementationTarget: item.implementation_target })),
      approvalPolicy: binding.approval_policy,
      capabilityName: binding.capability_name,
    })),
    components: wire.components.map((component) => ({
      id: component.id,
      version: component.version,
      title: component.title,
      inputPortIds: [...component.input_port_ids],
      outputPortIds: [...component.output_port_ids],
      internalDefinitionDigest: component.internal_definition_digest,
      internalAddresses: component.internal_addresses.map((address) => ({ semanticId: address.semantic_id, conceptKind: address.concept_kind, relativePath: address.relative_path })),
    })),
  };
}
