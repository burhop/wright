import type { DraftProjection } from "../../components/workflow-composer/draft-projection";

export type RecoveryExecutionKind = "human" | "deterministic" | "ai_capable";
export type RecoveryBlockKind = "work" | "approval" | "decision" | "component";
export type RecoveryRelationshipKind = "data" | "control" | "decision" | "feedback";
export type RecoveryRunState =
  | "idle"
  | "queued"
  | "running"
  | "needs-input"
  | "succeeded"
  | "failed"
  | "blocked"
  | "stale";

export interface RecoveryPhase {
  id: string;
  name: string;
  purpose: string;
  order: number;
  blockIds: string[];
}

export interface RecoveryBlock {
  id: string;
  kind: RecoveryBlockKind;
  title: string;
  purpose: string;
  phaseId: string | null;
  executionKind: RecoveryExecutionKind;
  instructions: string;
  configuration: Record<string, string | number | boolean>;
  inputPortIds: string[];
  outputPortIds: string[];
  bindingId: string | null;
  componentRef: { componentId: string; versionRange: string } | null;
}

export interface RecoveryPort {
  id: string;
  ownerBlockId: string;
  direction: "input" | "output";
  name: string;
  typeId: string;
  required: boolean;
  cardinality: "one" | "optional" | "many";
  artifactContractId: string | null;
  description: string;
}

export interface RecoveryRelationship {
  id: string;
  kind: RecoveryRelationshipKind;
  sourceId: string;
  targetId: string;
  label: string;
  condition: string | null;
}

export interface RecoveryArtifactContract {
  id: string;
  name: string;
  typeId: string;
  mediaType: string;
  description: string;
  producerBlockId: string | null;
  requiredForBlockIds: string[];
  previewPolicy: "inline" | "metadata" | "none";
  allowedActions: ("inspect" | "preview" | "open" | "download" | "replace")[];
}

export interface RecoveryBinding {
  id: string;
  kind: "internal" | "mcp_tool" | "human";
  providerId: string | null;
  serverId: string | null;
  toolId: string | null;
  schemaDigest: string | null;
  argumentMap: { semanticSource: string; implementationTarget: string }[];
  resultMap: { semanticSource: string; implementationTarget: string }[];
  approvalPolicy: "none" | "review_before_run" | "explicit_external_write";
  capabilityName: string;
}

export interface RecoveryComponent {
  id: string;
  version: string;
  title: string;
  inputPortIds: string[];
  outputPortIds: string[];
  internalDefinitionDigest: string;
}

export interface RecoveryWorkflow {
  documentKind: "workflow-ir";
  schemaVersion: "2.0.0-recovery.1";
  workflowId: string;
  revision: number;
  parentRevision: number | null;
  semanticSha256: string | null;
  metadata: {
    title: string;
    purpose: string;
    engineeringDomain: string;
    authorship: "human" | "human_with_ai_proposal";
  };
  phases: RecoveryPhase[];
  blocks: RecoveryBlock[];
  ports: RecoveryPort[];
  relationships: RecoveryRelationship[];
  artifactContracts: RecoveryArtifactContract[];
  bindings: RecoveryBinding[];
  components: RecoveryComponent[];
}

export interface RecoveryLayout {
  positions: Record<string, { x: number; y: number }>;
  viewport: { x: number; y: number; zoom: number };
}

export interface RecoveryDiagnostic {
  code: string;
  semanticId: string | null;
  line: number | null;
  explanation: string;
  correction: string;
}

export interface RecoveryStepProjection {
  state: RecoveryRunState;
  label: string;
  detail: string;
}

export interface RecoveryRunProjection {
  runId: string;
  workflowId: string;
  workflowRevision: number;
  semanticSha256: string;
  createdAt: string;
  completedAt: string | null;
  mode: "simulated";
  state: RecoveryRunState;
  activeBlockId: string | null;
  activeRelationshipId: string | null;
  steps: Record<string, RecoveryStepProjection>;
  activity: { at: string; label: string; detail: string }[];
  artifactRecords: {
    recordId: string;
    contractId: string;
    producedByBlockId: string;
    digestSha256: string;
    origin: "static_fixture";
    upstreamContractIds: string[];
  }[];
  materialSupplied: boolean;
  outputsReady: boolean;
}

const sha = (digit: string) => `sha256:${digit.repeat(64)}`;

export const initialWorkflow: RecoveryWorkflow = {
  documentKind: "workflow-ir",
  schemaVersion: "2.0.0-recovery.1",
  workflowId: "workflow.mounting-bracket",
  revision: 1,
  parentRevision: null,
  semanticSha256: null,
  metadata: {
    title: "Mounting bracket development",
    purpose: "Turn bracket requirements into a reviewed manufacturable STEP package.",
    engineeringDomain: "mechanical.design",
    authorship: "human_with_ai_proposal",
  },
  phases: [
    { id: "phase.define", name: "Define", purpose: "Capture the design basis and create geometry.", order: 0, blockIds: ["block.capture-brief", "block.generate-geometry"] },
    { id: "phase.verify", name: "Verify", purpose: "Check manufacturability and approve the design.", order: 1, blockIds: ["block.check-manufacturability", "block.review-design"] },
    { id: "phase.deliver", name: "Deliver", purpose: "Export and package the approved design.", order: 2, blockIds: ["block.export-step", "block.release-package"] },
  ],
  blocks: [
    {
      id: "block.capture-brief", kind: "work", title: "Capture bracket brief",
      purpose: "Attach the requirement package and record the material basis.", phaseId: "phase.define",
      executionKind: "human", instructions: "Confirm dimensions, hole pattern, loads, material, and source revision.",
      configuration: { material: "6061-T6", units: "mm" }, inputPortIds: [], outputPortIds: ["port.brief-out"], bindingId: null, componentRef: null,
    },
    {
      id: "block.generate-geometry", kind: "work", title: "Generate bracket geometry",
      purpose: "Create a parametric L-bracket from the approved brief.", phaseId: "phase.define",
      executionKind: "deterministic", instructions: "Create the bracket with two mounting holes and one slotted interface.",
      configuration: { thickness_mm: 6, inside_radius_mm: 4 }, inputPortIds: ["port.brief-in"], outputPortIds: ["port.geometry-out"], bindingId: "binding.generate-geometry", componentRef: null,
    },
    {
      id: "block.check-manufacturability", kind: "work", title: "Check manufacturability",
      purpose: "Evaluate bend radius, edge distance, thickness, and tool access.", phaseId: "phase.verify",
      executionKind: "ai_capable", instructions: "Explain every warning and cite the geometry and material fact that caused it.",
      configuration: { process: "machined-and-bent", minimum_edge_ratio: 1.5 }, inputPortIds: ["port.geometry-check-in", "port.material-in"], outputPortIds: ["port.report-out"], bindingId: "binding.check-manufacturability", componentRef: null,
    },
    {
      id: "block.review-design", kind: "approval", title: "Review bracket design",
      purpose: "Approve the geometry and manufacturability findings or return them for revision.", phaseId: "phase.verify",
      executionKind: "human", instructions: "Approve only when all required inputs are present and every warning is dispositioned.",
      configuration: { required_role: "design-reviewer" }, inputPortIds: ["port.geometry-review-in", "port.report-in"], outputPortIds: ["port.approved-geometry-out"], bindingId: null, componentRef: null,
    },
    {
      id: "block.export-step", kind: "work", title: "Export STEP",
      purpose: "Export the approved bracket to a neutral STEP file.", phaseId: "phase.deliver",
      executionKind: "deterministic", instructions: "Export AP242 with millimetre units and preserve the exact source revision.",
      configuration: { format: "STEP AP242", overwrite: false }, inputPortIds: ["port.approved-geometry-in"], outputPortIds: ["port.step-out"], bindingId: "binding.export-step", componentRef: null,
    },
    {
      id: "block.release-package", kind: "work", title: "Assemble review package",
      purpose: "Package the STEP model and manufacturability report for downstream review.", phaseId: "phase.deliver",
      executionKind: "deterministic", instructions: "Create a local package only; do not publish or send it.",
      configuration: { classification: "internal", publish: false }, inputPortIds: ["port.step-in", "port.report-package-in"], outputPortIds: ["port.package-out"], bindingId: "binding.release-package", componentRef: null,
    },
  ],
  ports: [
    { id: "port.brief-out", ownerBlockId: "block.capture-brief", direction: "output", name: "Bracket brief", typeId: "type.requirements.bundle", required: true, cardinality: "one", artifactContractId: "artifact.brief", description: "The attached dimensions, loads, material, and reference images." },
    { id: "port.brief-in", ownerBlockId: "block.generate-geometry", direction: "input", name: "Bracket brief", typeId: "type.requirements.bundle", required: true, cardinality: "one", artifactContractId: "artifact.brief", description: "Approved bracket requirements." },
    { id: "port.geometry-out", ownerBlockId: "block.generate-geometry", direction: "output", name: "Bracket geometry", typeId: "type.geometry.brep", required: true, cardinality: "one", artifactContractId: "artifact.geometry", description: "Parametric bracket geometry." },
    { id: "port.geometry-check-in", ownerBlockId: "block.check-manufacturability", direction: "input", name: "Geometry", typeId: "type.geometry.brep", required: true, cardinality: "one", artifactContractId: "artifact.geometry", description: "Geometry to evaluate." },
    { id: "port.material-in", ownerBlockId: "block.check-manufacturability", direction: "input", name: "Material", typeId: "type.material.spec", required: true, cardinality: "one", artifactContractId: "artifact.material", description: "Material and temper needed for manufacturing rules." },
    { id: "port.report-out", ownerBlockId: "block.check-manufacturability", direction: "output", name: "Manufacturability report", typeId: "type.report.manufacturability", required: true, cardinality: "one", artifactContractId: "artifact.manufacturability-report", description: "Findings, evidence, and recovery guidance." },
    { id: "port.geometry-review-in", ownerBlockId: "block.review-design", direction: "input", name: "Geometry", typeId: "type.geometry.brep", required: true, cardinality: "one", artifactContractId: "artifact.geometry", description: "Geometry presented for approval." },
    { id: "port.report-in", ownerBlockId: "block.review-design", direction: "input", name: "Report", typeId: "type.report.manufacturability", required: true, cardinality: "one", artifactContractId: "artifact.manufacturability-report", description: "Manufacturability evidence presented for approval." },
    { id: "port.approved-geometry-out", ownerBlockId: "block.review-design", direction: "output", name: "Approved geometry", typeId: "type.geometry.approved", required: true, cardinality: "one", artifactContractId: "artifact.approved-geometry", description: "Exact approved geometry revision." },
    { id: "port.approved-geometry-in", ownerBlockId: "block.export-step", direction: "input", name: "Approved geometry", typeId: "type.geometry.approved", required: true, cardinality: "one", artifactContractId: "artifact.approved-geometry", description: "Approved source for export." },
    { id: "port.step-out", ownerBlockId: "block.export-step", direction: "output", name: "STEP model", typeId: "type.file.step", required: true, cardinality: "one", artifactContractId: "artifact.step", description: "Neutral bracket model." },
    { id: "port.step-in", ownerBlockId: "block.release-package", direction: "input", name: "STEP model", typeId: "type.file.step", required: true, cardinality: "one", artifactContractId: "artifact.step", description: "Approved exported model." },
    { id: "port.report-package-in", ownerBlockId: "block.release-package", direction: "input", name: "Report", typeId: "type.report.manufacturability", required: true, cardinality: "one", artifactContractId: "artifact.manufacturability-report", description: "Report to include in the package." },
    { id: "port.package-out", ownerBlockId: "block.release-package", direction: "output", name: "Review package", typeId: "type.package.review", required: true, cardinality: "one", artifactContractId: "artifact.release-package", description: "Local review package." },
  ],
  relationships: [
    { id: "rel.brief-to-geometry", kind: "data", sourceId: "port.brief-out", targetId: "port.brief-in", label: "requirements", condition: null },
    { id: "rel.geometry-to-check", kind: "data", sourceId: "port.geometry-out", targetId: "port.geometry-check-in", label: "geometry", condition: null },
    { id: "rel.geometry-to-review", kind: "data", sourceId: "port.geometry-out", targetId: "port.geometry-review-in", label: "geometry", condition: null },
    { id: "rel.report-to-review", kind: "data", sourceId: "port.report-out", targetId: "port.report-in", label: "findings", condition: null },
    { id: "rel.review-to-export", kind: "data", sourceId: "port.approved-geometry-out", targetId: "port.approved-geometry-in", label: "approved geometry", condition: "decision.accepted" },
    { id: "rel.step-to-package", kind: "data", sourceId: "port.step-out", targetId: "port.step-in", label: "STEP", condition: null },
    { id: "rel.report-to-package", kind: "data", sourceId: "port.report-out", targetId: "port.report-package-in", label: "report", condition: null },
    { id: "rel.review-accepted", kind: "decision", sourceId: "block.review-design", targetId: "block.export-step", label: "Accepted", condition: "All required inputs present and warnings dispositioned" },
    { id: "rel.review-revise", kind: "feedback", sourceId: "block.review-design", targetId: "block.generate-geometry", label: "Revise geometry", condition: "A requirement or manufacturability warning is unresolved" },
  ],
  artifactContracts: [
    { id: "artifact.brief", name: "Bracket requirement package", typeId: "type.requirements.bundle", mediaType: "application/pdf", description: "Input dimensions, loads, material, and reference images.", producerBlockId: null, requiredForBlockIds: ["block.generate-geometry"], previewPolicy: "inline", allowedActions: ["inspect", "preview", "replace"] },
    { id: "artifact.material", name: "Material specification", typeId: "type.material.spec", mediaType: "application/vnd.wright.material+json", description: "Material and temper properties used by the check.", producerBlockId: null, requiredForBlockIds: ["block.check-manufacturability"], previewPolicy: "metadata", allowedActions: ["inspect", "replace"] },
    { id: "artifact.geometry", name: "Bracket geometry", typeId: "type.geometry.brep", mediaType: "model/vnd.wright.brep", description: "Parametric bracket model before approval.", producerBlockId: "block.generate-geometry", requiredForBlockIds: ["block.check-manufacturability", "block.review-design"], previewPolicy: "inline", allowedActions: ["inspect", "preview"] },
    { id: "artifact.manufacturability-report", name: "Manufacturability report", typeId: "type.report.manufacturability", mediaType: "text/html", description: "Findings and recovery guidance.", producerBlockId: "block.check-manufacturability", requiredForBlockIds: ["block.review-design", "block.release-package"], previewPolicy: "inline", allowedActions: ["inspect", "preview", "open", "download"] },
    { id: "artifact.approved-geometry", name: "Approved geometry", typeId: "type.geometry.approved", mediaType: "model/vnd.wright.brep", description: "Geometry plus review identity.", producerBlockId: "block.review-design", requiredForBlockIds: ["block.export-step"], previewPolicy: "inline", allowedActions: ["inspect", "preview"] },
    { id: "artifact.step", name: "Mounting bracket STEP", typeId: "type.file.step", mediaType: "model/step", description: "AP242 neutral geometry file.", producerBlockId: "block.export-step", requiredForBlockIds: ["block.release-package"], previewPolicy: "inline", allowedActions: ["inspect", "preview", "open", "download"] },
    { id: "artifact.release-package", name: "Bracket review package", typeId: "type.package.review", mediaType: "application/zip", description: "Local internal package containing the STEP model and report.", producerBlockId: "block.release-package", requiredForBlockIds: [], previewPolicy: "metadata", allowedActions: ["inspect", "download"] },
  ],
  bindings: [
    { id: "binding.generate-geometry", kind: "mcp_tool", providerId: "provider.wright-local", serverId: "server.solid-edge", toolId: "tool.create-mounting-bracket", schemaDigest: sha("1"), argumentMap: [{ semanticSource: "port.brief-in", implementationTarget: "arguments.requirements" }], resultMap: [{ semanticSource: "port.geometry-out", implementationTarget: "result.geometry" }], approvalPolicy: "review_before_run", capabilityName: "Create mounting bracket geometry" },
    { id: "binding.check-manufacturability", kind: "internal", providerId: "provider.wright-local", serverId: null, toolId: "check.bracket-manufacturability", schemaDigest: sha("2"), argumentMap: [{ semanticSource: "port.geometry-check-in", implementationTarget: "geometry" }, { semanticSource: "port.material-in", implementationTarget: "material" }], resultMap: [{ semanticSource: "port.report-out", implementationTarget: "report" }], approvalPolicy: "none", capabilityName: "Check bracket manufacturability" },
    { id: "binding.export-step", kind: "mcp_tool", providerId: "provider.wright-local", serverId: "server.solid-edge", toolId: "tool.export-step-ap242", schemaDigest: sha("3"), argumentMap: [{ semanticSource: "port.approved-geometry-in", implementationTarget: "arguments.model" }], resultMap: [{ semanticSource: "port.step-out", implementationTarget: "result.step_file" }], approvalPolicy: "review_before_run", capabilityName: "Export approved model as STEP AP242" },
    { id: "binding.release-package", kind: "internal", providerId: "provider.wright-local", serverId: null, toolId: "package.local-review-bundle", schemaDigest: sha("4"), argumentMap: [{ semanticSource: "port.step-in", implementationTarget: "files.step" }, { semanticSource: "port.report-package-in", implementationTarget: "files.report" }], resultMap: [{ semanticSource: "port.package-out", implementationTarget: "package" }], approvalPolicy: "none", capabilityName: "Assemble local design review package" },
  ],
  components: [],
};

export const initialLayout: RecoveryLayout = {
  positions: {
    "block.capture-brief": { x: 20, y: 30 },
    "block.generate-geometry": { x: 365, y: 55 },
    "block.check-manufacturability": { x: 365, y: 390 },
    "block.review-design": { x: 720, y: 360 },
    "block.export-step": { x: 720, y: 30 },
    "block.release-package": { x: 1060, y: 80 },
  },
  viewport: { x: 0, y: 0, zoom: 0.72 },
};

export function cloneWorkflow(workflow: RecoveryWorkflow): RecoveryWorkflow {
  return structuredClone(workflow);
}

export function cloneLayout(layout: RecoveryLayout): RecoveryLayout {
  return structuredClone(layout);
}

export function findBlock(workflow: RecoveryWorkflow, id: string | null): RecoveryBlock | null {
  return id === null ? null : workflow.blocks.find((block) => block.id === id) ?? null;
}

export function findPort(workflow: RecoveryWorkflow, id: string): RecoveryPort | null {
  return workflow.ports.find((port) => port.id === id) ?? null;
}

export function phaseName(workflow: RecoveryWorkflow, id: string | null): string {
  return workflow.phases.find((phase) => phase.id === id)?.name ?? id ?? "Reusable component";
}

function roleFor(block: RecoveryBlock): "input" | "work" | "review" | "release" {
  if (block.id === "block.capture-brief") return "input";
  if (block.kind === "approval") return "review";
  if (block.id.includes("release") || block.id.includes("export")) return "release";
  return "work";
}

export function toDraftProjection(workflow: RecoveryWorkflow, layout: RecoveryLayout): DraftProjection {
  const port = (identity: string) => {
    const source = workflow.ports.find((item) => item.id === identity);
    if (!source) throw new Error(`RECOVERY_PORT_MISSING:${identity}`);
    return {
      id: source.id,
      owner_block_id: source.ownerBlockId,
      direction: source.direction,
      name: source.name,
      value_type_id: source.typeId,
      required: source.required,
      cardinality: source.cardinality === "many" ? "many" as const : "one" as const,
      semanticId: source.id,
    };
  };
  const blocks = new Map(workflow.blocks.map((block) => [block.id, block]));
  const gatesByOwner = new Map<string, {
    id: string;
    owner_block_id: string;
    condition: string;
    proceed_target_block_id: string;
    revise_target_block_id: string;
    feedback_path_id: string;
    semanticId: string;
  }>();
  for (const block of workflow.blocks) {
    if (block.kind !== "approval") continue;
    const decision = workflow.relationships
      .filter((relationship) => relationship.kind === "decision" && relationship.sourceId === block.id)
      .sort((left, right) => left.id.localeCompare(right.id))[0];
    const feedback = workflow.relationships
      .filter((relationship) => relationship.kind === "feedback" && relationship.sourceId === block.id)
      .sort((left, right) => left.id.localeCompare(right.id))[0];
    if (!decision || !feedback) continue;
    const gateId = block.id === "block.review-design" ? "gate.review-decision" : `gate.${block.id.replace(/^block\./, "")}-decision`;
    gatesByOwner.set(block.id, {
      id: gateId,
      owner_block_id: block.id,
      condition: decision.condition ?? block.instructions,
      proceed_target_block_id: decision.targetId,
      revise_target_block_id: feedback.targetId,
      feedback_path_id: feedback.id,
      semanticId: gateId,
    });
  }
  const artifactsByProducer = new Map<string, RecoveryArtifactContract[]>();
  for (const artifact of workflow.artifactContracts) {
    if (artifact.producerBlockId) {
      artifactsByProducer.set(artifact.producerBlockId, [...(artifactsByProducer.get(artifact.producerBlockId) ?? []), artifact]);
    }
  }
  const projectedBlocks = new Map(workflow.blocks.map((block) => {
    const gate = gatesByOwner.get(block.id);
    const gates = gate ? [gate] : [];
    return [block.id, {
      id: block.id,
      title: block.title,
      purpose: block.purpose,
      role: roleFor(block),
      phase_id: block.phaseId ?? "phase.unassigned-component",
      input_port_ids: [...block.inputPortIds],
      output_port_ids: [...block.outputPortIds],
      gate_ids: gates.map((gate) => gate.id),
      intended_artifact_ids: (artifactsByProducer.get(block.id) ?? []).map((item) => item.id),
      semanticId: block.id,
      position: { semantic_id: block.id, ...(layout.positions[block.id] ?? { x: 40, y: 40 }) },
      inputs: block.inputPortIds.map(port),
      outputs: block.outputPortIds.map(port),
      gates,
      artifacts: (artifactsByProducer.get(block.id) ?? []).map((artifact) => ({
        id: artifact.id,
        title: artifact.name,
        artifact_type_id: artifact.typeId,
        description: artifact.description,
        produced_by_block_id: block.id,
        semanticId: artifact.id,
      })),
    }];
  }));
  const portOwners = new Map(workflow.ports.map((item) => [item.id, item.ownerBlockId]));
  const unphasedBlockIds = workflow.blocks.filter((block) => block.phaseId === null).map((block) => block.id);
  const projectedPhases = workflow.phases.map((phase) => ({
    id: phase.id,
    name: phase.name,
    purpose: phase.purpose,
    order: phase.order,
    block_ids: [...phase.blockIds],
    semanticId: phase.id,
    blocks: phase.blockIds.map((id) => {
      const projected = projectedBlocks.get(id);
      if (!projected || !blocks.has(id)) throw new Error(`RECOVERY_BLOCK_MISSING:${id}`);
      return projected;
    }),
  }));
  if (unphasedBlockIds.length > 0) {
    projectedPhases.push({
      id: "phase.unassigned-component",
      name: "Reusable components",
      purpose: "Projection-only grouping for canonical component blocks that are not assigned to an execution phase.",
      order: projectedPhases.length,
      block_ids: unphasedBlockIds,
      semanticId: "phase.unassigned-component",
      blocks: unphasedBlockIds.map((id) => projectedBlocks.get(id)!),
    });
  }
  return {
    draftId: workflow.workflowId,
    revision: workflow.revision,
    title: workflow.metadata.title,
    purpose: workflow.metadata.purpose,
    phases: projectedPhases,
    connections: workflow.relationships.filter((relationship) => relationship.kind === "data").map((relationship) => ({
      id: relationship.id,
      source_port_id: relationship.sourceId,
      target_port_id: relationship.targetId,
      semanticId: relationship.id,
      sourceBlockId: portOwners.get(relationship.sourceId) ?? relationship.sourceId,
      targetBlockId: portOwners.get(relationship.targetId) ?? relationship.targetId,
    })),
    feedbackPaths: workflow.relationships.flatMap((relationship) => {
      if (relationship.kind !== "feedback") return [];
      const gate = gatesByOwner.get(relationship.sourceId);
      return [{
        id: relationship.id,
        from_gate_id: gate?.id ?? relationship.sourceId,
        to_block_id: relationship.targetId,
        reason: relationship.condition ?? relationship.label,
        semanticId: relationship.id,
        label: relationship.label,
      }];
    }),
  };
}

export function initialRunProjection(
  subject: RecoveryWorkflow = initialWorkflow,
  semanticSha256 = "",
  createdAt = "",
): RecoveryRunProjection {
  return {
    runId: "run.demo-001",
    workflowId: subject.workflowId,
    workflowRevision: subject.revision,
    semanticSha256,
    createdAt,
    completedAt: null,
    mode: "simulated",
    state: "idle",
    activeBlockId: null,
    activeRelationshipId: null,
    steps: Object.fromEntries(subject.blocks.map((block) => [block.id, { state: "idle", label: "Not started", detail: "Waiting for the simulated run." }])),
    activity: [],
    artifactRecords: [],
    materialSupplied: false,
    outputsReady: false,
  };
}
