import type { DraftProjection } from "../../components/workflow-composer/draft-projection";

export type RecoveryExecutionKind = "human" | "deterministic" | "ai_capable";
export type RecoveryBlockKind = "work" | "approval" | "decision" | "component";
export type RecoveryRelationshipKind =
  "data" | "control" | "decision" | "feedback";
export const RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY =
  "__wright_authoring_section";
export const RECOVERY_AUTHORING_INSTRUCTION_FIELD_KEY =
  "__wright_authoring_instruction_field";
export const RECOVERY_AUTHORING_SECONDARY_INSTRUCTION_KEY =
  "__wright_authoring_secondary_instruction";
export const RECOVERY_AUTHORING_APPROVAL_OBJECTS_KEY =
  "__wright_authoring_approval_objects";
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
  internalAddresses: {
    semanticId: string;
    conceptKind:
      | "block"
      | "port"
      | "relationship"
      | "artifact_contract"
      | "binding"
      | "component";
    relativePath: string;
  }[];
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
  documentKind: "workflow-layout";
  schemaVersion: "1.0.0-recovery.1";
  workflowId: string;
  semanticRevision: number;
  layoutRevision: number;
  positions: Record<string, { x: number; y: number }>;
  viewport: { x: number; y: number; zoom: number };
}

export interface RecoveryDiagnostic {
  code: string;
  semanticId: string | null;
  line: number | null;
  explanation: string;
  correction: string;
  componentScope?: RecoveryComponentScope;
}

export interface RecoveryComponentScope {
  componentInstanceId: string;
  componentId: string;
  componentVersion: string;
  internalSemanticId: string;
}

export interface RecoveryStepProjection {
  state: RecoveryRunState;
  label: string;
  detail: string;
  componentScope?: RecoveryComponentScope;
}

export interface RecoveryRunProjection {
  documentKind: "workflow-run";
  schemaVersion: "1.0.0-recovery.1";
  runId: string;
  workflowId: string;
  workflowRevision: number;
  semanticSha256: string;
  createdAt: string;
  completedAt: string | null;
  mode: "simulated" | "native";
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

export interface RecoveryRunSubject {
  workflowId: string;
  workflowRevision: number;
  semanticSha256: string;
}

const sha = (digit: string) => `sha256:${digit.repeat(64)}`;

export const initialWorkflow: RecoveryWorkflow = {
  documentKind: "workflow-ir",
  schemaVersion: "2.0.0-recovery.1",
  workflowId: "workflow.mounting-bracket",
  revision: 2,
  parentRevision: 1,
  semanticSha256: null,
  metadata: {
    title: "Mounting bracket development",
    purpose:
      "Turn bracket requirements into a reviewed manufacturable STEP package.",
    engineeringDomain: "mechanical.design",
    authorship: "human_with_ai_proposal",
  },
  phases: [
    {
      id: "phase.define",
      name: "Define",
      purpose:
        "Combine design intent, reference images, and company context into a reviewed design specification, then create the CAD model.",
      order: 0,
      blockIds: [
        "block.reference-images",
        "block.design-intent",
        "block.company-context",
        "block.create-design-specification",
        "block.generate-geometry",
      ],
    },
    {
      id: "phase.verify",
      name: "Verify",
      purpose: "Check manufacturability and approve the design.",
      order: 1,
      blockIds: ["block.check-manufacturability", "block.review-design"],
    },
    {
      id: "phase.deliver",
      name: "Deliver",
      purpose: "Export and package the approved design.",
      order: 2,
      blockIds: ["block.export-step", "block.release-package"],
    },
  ],
  blocks: [
    {
      id: "block.reference-images",
      kind: "work",
      title: "Reference images",
      purpose:
        "Add sketches, photographs, or marked-up images that show the intended bracket and interfaces.",
      phaseId: "phase.define",
      executionKind: "human",
      instructions:
        "Add one or more JPG or PNG images and identify any dimensions or interfaces that must be preserved.",
      configuration: { accepted_formats: "JPG, PNG" },
      inputPortIds: [],
      outputPortIds: ["port.reference-images-out"],
      bindingId: null,
      componentRef: null,
    },
    {
      id: "block.design-intent",
      kind: "work",
      title: "Design intent",
      purpose:
        "Describe how the bracket will be used, its loads, interfaces, constraints, and success criteria in text or a common document.",
      phaseId: "phase.define",
      executionKind: "human",
      instructions:
        "Enter design intent as text or add a common document. Include use, loads, interfaces, constraints, units, and known material requirements.",
      configuration: { input_mode: "text-or-document", units: "mm" },
      inputPortIds: [],
      outputPortIds: ["port.design-intent-out"],
      bindingId: null,
      componentRef: null,
    },
    {
      id: "block.company-context",
      kind: "work",
      title: "Company standards and context",
      purpose:
        "Bring in approved standards, preferred materials and processes, and relevant past designs.",
      phaseId: "phase.define",
      executionKind: "deterministic",
      instructions:
        "Retrieve the company standards and prior-design guidance relevant to brackets, material selection, tolerancing, and manufacturing.",
      configuration: { source: "approved-company-library" },
      inputPortIds: [],
      outputPortIds: ["port.company-context-out"],
      bindingId: "binding.company-context",
      componentRef: null,
    },
    {
      id: "block.create-design-specification",
      kind: "approval",
      title: "Create and review design specification",
      purpose:
        "Combine the three input sources into an editable, reviewable source of truth before CAD work begins.",
      phaseId: "phase.define",
      executionKind: "ai_capable",
      instructions:
        "Draft a concise engineering design specification from the design intent, reference images, and company context. Separate supplied facts from assumptions, flag conflicts and missing information, and require engineer review before release to CAD.",
      configuration: { review_status: "needs-review" },
      inputPortIds: [
        "port.design-intent-in",
        "port.reference-images-in",
        "port.company-context-in",
      ],
      outputPortIds: ["port.design-specification-out"],
      bindingId: "binding.create-design-specification",
      componentRef: null,
    },
    {
      id: "block.generate-geometry",
      kind: "work",
      title: "Create bracket CAD model",
      purpose:
        "Create a parametric L-bracket from the reviewed design specification.",
      phaseId: "phase.define",
      executionKind: "deterministic",
      instructions:
        "Create the bracket with two mounting holes and one slotted interface.",
      configuration: { thickness_mm: 6, inside_radius_mm: 4 },
      inputPortIds: ["port.design-specification-in"],
      outputPortIds: ["port.geometry-out"],
      bindingId: "binding.generate-geometry",
      componentRef: null,
    },
    {
      id: "block.check-manufacturability",
      kind: "work",
      title: "Run manufacturing checks",
      purpose: "Check bend radius, edge distance, thickness, and tool access.",
      phaseId: "phase.verify",
      executionKind: "ai_capable",
      instructions:
        "Check bend radius, edge distance, thickness, and tool access. For each issue, cite the CAD feature and material property that triggered it.",
      configuration: { process: "machined-and-bent", minimum_edge_ratio: 1.5 },
      inputPortIds: [
        "port.geometry-check-in",
        "port.design-specification-check-in",
      ],
      outputPortIds: ["port.report-out"],
      bindingId: "binding.check-manufacturability",
      componentRef: null,
    },
    {
      id: "block.review-design",
      kind: "component",
      title: "Review CAD model for approval",
      purpose:
        "Approve the CAD model and manufacturing report or return the design for revision.",
      phaseId: "phase.verify",
      executionKind: "human",
      instructions:
        "Approve only when the reviewed design specification, CAD model, and manufacturing check report agree and every issue has a recorded resolution.",
      configuration: { required_role: "design-reviewer" },
      inputPortIds: [
        "port.design-specification-review-in",
        "port.geometry-review-in",
        "port.report-in",
      ],
      outputPortIds: ["port.approved-geometry-out"],
      bindingId: null,
      componentRef: {
        componentId: "component.review-cell",
        versionRange: "^1.0.0",
      },
    },
    {
      id: "block.export-step",
      kind: "work",
      title: "Export approved STEP file",
      purpose: "Export the approved bracket CAD model as a neutral STEP file.",
      phaseId: "phase.deliver",
      executionKind: "deterministic",
      instructions:
        "Export STEP AP242 in millimetres from the approved CAD model and record its source revision.",
      configuration: { format: "STEP AP242", overwrite: false },
      inputPortIds: ["port.approved-geometry-in"],
      outputPortIds: ["port.step-out"],
      bindingId: "binding.export-step",
      componentRef: null,
    },
    {
      id: "block.release-package",
      kind: "work",
      title: "Create design handoff package",
      purpose:
        "Place the STEP file and manufacturing report in one local handoff package.",
      phaseId: "phase.deliver",
      executionKind: "deterministic",
      instructions:
        "Create a local ZIP containing the approved STEP file and manufacturing report. Do not publish or send it.",
      configuration: { classification: "internal", publish: false },
      inputPortIds: ["port.step-in", "port.report-package-in"],
      outputPortIds: ["port.package-out"],
      bindingId: "binding.release-package",
      componentRef: null,
    },
  ],
  ports: [
    {
      id: "port.reference-images-out",
      ownerBlockId: "block.reference-images",
      direction: "output",
      name: "Reference images",
      typeId: "type.image.reference-set",
      required: true,
      cardinality: "many",
      artifactContractId: "artifact.reference-images",
      description:
        "Sketches, photographs, or marked-up JPG and PNG images supplied by the engineer.",
    },
    {
      id: "port.design-intent-out",
      ownerBlockId: "block.design-intent",
      direction: "output",
      name: "Design intent",
      typeId: "type.design.intent",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-intent",
      description:
        "Engineer-entered text or a common document describing use, loads, interfaces, constraints, units, and known material requirements.",
    },
    {
      id: "port.company-context-out",
      ownerBlockId: "block.company-context",
      direction: "output",
      name: "Company standards and context",
      typeId: "type.context.company",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.company-context",
      description:
        "Approved standards, preferred practices, and relevant prior-design guidance.",
    },
    {
      id: "port.design-intent-in",
      ownerBlockId: "block.create-design-specification",
      direction: "input",
      name: "Design intent",
      typeId: "type.design.intent",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-intent",
      description:
        "The engineer's text or document describing what the bracket must do.",
    },
    {
      id: "port.reference-images-in",
      ownerBlockId: "block.create-design-specification",
      direction: "input",
      name: "Reference images",
      typeId: "type.image.reference-set",
      required: true,
      cardinality: "many",
      artifactContractId: "artifact.reference-images",
      description:
        "Visual references used to clarify shape, interfaces, and constraints.",
    },
    {
      id: "port.company-context-in",
      ownerBlockId: "block.create-design-specification",
      direction: "input",
      name: "Company standards and context",
      typeId: "type.context.company",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.company-context",
      description: "Approved company rules and reusable design knowledge.",
    },
    {
      id: "port.design-specification-out",
      ownerBlockId: "block.create-design-specification",
      direction: "output",
      name: "Reviewed design specification",
      typeId: "type.design.specification",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-specification",
      description:
        "Editable source of truth that separates supplied facts, assumptions, decisions, and unresolved questions.",
    },
    {
      id: "port.design-specification-in",
      ownerBlockId: "block.generate-geometry",
      direction: "input",
      name: "Reviewed design specification",
      typeId: "type.design.specification",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-specification",
      description:
        "The reviewed source of truth used to create the bracket CAD model.",
    },
    {
      id: "port.geometry-out",
      ownerBlockId: "block.generate-geometry",
      direction: "output",
      name: "Bracket CAD model",
      typeId: "type.geometry.brep",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.geometry",
      description: "Parametric bracket CAD model.",
    },
    {
      id: "port.geometry-check-in",
      ownerBlockId: "block.check-manufacturability",
      direction: "input",
      name: "Bracket CAD model",
      typeId: "type.geometry.brep",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.geometry",
      description: "CAD model to check for manufacturing issues.",
    },
    {
      id: "port.design-specification-check-in",
      ownerBlockId: "block.check-manufacturability",
      direction: "input",
      name: "Reviewed design specification",
      typeId: "type.design.specification",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-specification",
      description:
        "Approved dimensions, material, process, tolerances, and acceptance criteria used by the manufacturing checks.",
    },
    {
      id: "port.report-out",
      ownerBlockId: "block.check-manufacturability",
      direction: "output",
      name: "Manufacturing check report",
      typeId: "type.report.manufacturability",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.manufacturability-report",
      description:
        "Manufacturing issues, supporting evidence, and recommended corrections.",
    },
    {
      id: "port.design-specification-review-in",
      ownerBlockId: "block.review-design",
      direction: "input",
      name: "Reviewed design specification",
      typeId: "type.design.specification",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.design-specification",
      description:
        "Accepted design criteria used to judge the CAD model and manufacturing report.",
    },
    {
      id: "port.geometry-review-in",
      ownerBlockId: "block.review-design",
      direction: "input",
      name: "Bracket CAD model",
      typeId: "type.geometry.brep",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.geometry",
      description: "CAD model presented for design approval.",
    },
    {
      id: "port.report-in",
      ownerBlockId: "block.review-design",
      direction: "input",
      name: "Manufacturing check report",
      typeId: "type.report.manufacturability",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.manufacturability-report",
      description: "Manufacturing evidence presented for design approval.",
    },
    {
      id: "port.approved-geometry-out",
      ownerBlockId: "block.review-design",
      direction: "output",
      name: "Approved CAD model",
      typeId: "type.geometry.approved",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.approved-geometry",
      description: "Exact CAD model revision approved by design review.",
    },
    {
      id: "port.approved-geometry-in",
      ownerBlockId: "block.export-step",
      direction: "input",
      name: "Approved CAD model",
      typeId: "type.geometry.approved",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.approved-geometry",
      description: "Approved CAD model used for the STEP export.",
    },
    {
      id: "port.step-out",
      ownerBlockId: "block.export-step",
      direction: "output",
      name: "STEP AP242 file",
      typeId: "type.file.step",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.step",
      description: "Neutral bracket CAD file for downstream use.",
    },
    {
      id: "port.step-in",
      ownerBlockId: "block.release-package",
      direction: "input",
      name: "STEP AP242 file",
      typeId: "type.file.step",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.step",
      description: "Approved STEP file to include in the handoff package.",
    },
    {
      id: "port.report-package-in",
      ownerBlockId: "block.release-package",
      direction: "input",
      name: "Manufacturing check report",
      typeId: "type.report.manufacturability",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.manufacturability-report",
      description: "Manufacturing report to include in the handoff package.",
    },
    {
      id: "port.package-out",
      ownerBlockId: "block.release-package",
      direction: "output",
      name: "Design handoff package",
      typeId: "type.package.review",
      required: true,
      cardinality: "one",
      artifactContractId: "artifact.release-package",
      description:
        "Local ZIP containing the approved STEP file and manufacturing report.",
    },
  ],
  relationships: [
    {
      id: "rel.design-intent-to-specification",
      kind: "data",
      sourceId: "port.design-intent-out",
      targetId: "port.design-intent-in",
      label: "design intent",
      condition: null,
    },
    {
      id: "rel.reference-to-specification",
      kind: "data",
      sourceId: "port.reference-images-out",
      targetId: "port.reference-images-in",
      label: "reference images",
      condition: null,
    },
    {
      id: "rel.context-to-specification",
      kind: "data",
      sourceId: "port.company-context-out",
      targetId: "port.company-context-in",
      label: "company context",
      condition: null,
    },
    {
      id: "rel.specification-to-geometry",
      kind: "data",
      sourceId: "port.design-specification-out",
      targetId: "port.design-specification-in",
      label: "reviewed design specification",
      condition: "decision.specification-accepted",
    },
    {
      id: "rel.specification-to-check",
      kind: "data",
      sourceId: "port.design-specification-out",
      targetId: "port.design-specification-check-in",
      label: "design criteria",
      condition: "decision.specification-accepted",
    },
    {
      id: "rel.geometry-to-check",
      kind: "data",
      sourceId: "port.geometry-out",
      targetId: "port.geometry-check-in",
      label: "CAD model",
      condition: null,
    },
    {
      id: "rel.specification-to-review",
      kind: "data",
      sourceId: "port.design-specification-out",
      targetId: "port.design-specification-review-in",
      label: "design criteria",
      condition: "decision.specification-accepted",
    },
    {
      id: "rel.geometry-to-review",
      kind: "data",
      sourceId: "port.geometry-out",
      targetId: "port.geometry-review-in",
      label: "CAD model",
      condition: null,
    },
    {
      id: "rel.report-to-review",
      kind: "data",
      sourceId: "port.report-out",
      targetId: "port.report-in",
      label: "manufacturing report",
      condition: null,
    },
    {
      id: "rel.review-to-export",
      kind: "data",
      sourceId: "port.approved-geometry-out",
      targetId: "port.approved-geometry-in",
      label: "approved CAD model",
      condition: "decision.accepted",
    },
    {
      id: "rel.step-to-package",
      kind: "data",
      sourceId: "port.step-out",
      targetId: "port.step-in",
      label: "STEP file",
      condition: null,
    },
    {
      id: "rel.report-to-package",
      kind: "data",
      sourceId: "port.report-out",
      targetId: "port.report-package-in",
      label: "manufacturing report",
      condition: null,
    },
    {
      id: "rel.specification-accepted",
      kind: "decision",
      sourceId: "block.create-design-specification",
      targetId: "block.generate-geometry",
      label: "Specification reviewed",
      condition:
        "An engineer accepted the design specification and resolved or explicitly recorded all open questions",
    },
    {
      id: "rel.specification-revise",
      kind: "feedback",
      sourceId: "block.create-design-specification",
      targetId: "block.design-intent",
      label: "Revise design inputs",
      condition:
        "The design specification contains a conflict, unsupported assumption, or missing decision",
    },
    {
      id: "rel.review-accepted",
      kind: "decision",
      sourceId: "block.review-design",
      targetId: "block.export-step",
      label: "Accepted",
      condition: "All required inputs present and warnings dispositioned",
    },
    {
      id: "rel.review-revise",
      kind: "feedback",
      sourceId: "block.review-design",
      targetId: "block.generate-geometry",
      label: "Revise CAD model",
      condition: "A design requirement or manufacturing issue is unresolved",
    },
  ],
  artifactContracts: [
    {
      id: "artifact.reference-images",
      name: "Reference images",
      typeId: "type.image.reference-set",
      mediaType: "image/*",
      description:
        "Engineer-supplied sketches, photographs, and marked-up JPG or PNG images.",
      producerBlockId: null,
      requiredForBlockIds: ["block.create-design-specification"],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview", "replace"],
    },
    {
      id: "artifact.design-intent",
      name: "Design intent",
      typeId: "type.design.intent",
      mediaType: "text/plain",
      description:
        "Typed text or text from a common document describing use, loads, interfaces, constraints, units, and known material requirements.",
      producerBlockId: null,
      requiredForBlockIds: ["block.create-design-specification"],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview", "replace"],
    },
    {
      id: "artifact.company-context",
      name: "Company standards and context",
      typeId: "type.context.company",
      mediaType: "application/vnd.wright.context+json",
      description:
        "Approved company standards, preferred practices, and relevant prior-design guidance.",
      producerBlockId: "block.company-context",
      requiredForBlockIds: ["block.create-design-specification"],
      previewPolicy: "metadata",
      allowedActions: ["inspect", "preview"],
    },
    {
      id: "artifact.design-specification",
      name: "Reviewed design specification",
      typeId: "type.design.specification",
      mediaType: "text/markdown",
      description:
        "Editable, reviewable source of truth for CAD and downstream engineering work.",
      producerBlockId: "block.create-design-specification",
      requiredForBlockIds: [
        "block.generate-geometry",
        "block.check-manufacturability",
        "block.review-design",
      ],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview", "open", "download"],
    },
    {
      id: "artifact.geometry",
      name: "Bracket CAD model",
      typeId: "type.geometry.brep",
      mediaType: "model/vnd.wright.brep",
      description: "Parametric bracket CAD model before design approval.",
      producerBlockId: "block.generate-geometry",
      requiredForBlockIds: [
        "block.check-manufacturability",
        "block.review-design",
      ],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview"],
    },
    {
      id: "artifact.manufacturability-report",
      name: "Manufacturing check report",
      typeId: "type.report.manufacturability",
      mediaType: "text/html",
      description:
        "Manufacturing issues, evidence, and recommended corrections.",
      producerBlockId: "block.check-manufacturability",
      requiredForBlockIds: ["block.review-design", "block.release-package"],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview", "open", "download"],
    },
    {
      id: "artifact.approved-geometry",
      name: "Approved CAD model",
      typeId: "type.geometry.approved",
      mediaType: "model/vnd.wright.brep",
      description: "CAD model plus its design-review decision.",
      producerBlockId: "block.review-design",
      requiredForBlockIds: ["block.export-step"],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview"],
    },
    {
      id: "artifact.step",
      name: "Mounting bracket STEP AP242 file",
      typeId: "type.file.step",
      mediaType: "model/step",
      description: "Neutral bracket CAD file for downstream use.",
      producerBlockId: "block.export-step",
      requiredForBlockIds: ["block.release-package"],
      previewPolicy: "inline",
      allowedActions: ["inspect", "preview", "open", "download"],
    },
    {
      id: "artifact.release-package",
      name: "Design handoff package",
      typeId: "type.package.review",
      mediaType: "application/zip",
      description:
        "Local ZIP containing the approved STEP file and manufacturing report.",
      producerBlockId: "block.release-package",
      requiredForBlockIds: [],
      previewPolicy: "metadata",
      allowedActions: ["inspect", "download"],
    },
  ],
  bindings: [
    {
      id: "binding.company-context",
      kind: "internal",
      providerId: "provider.wright-local",
      serverId: null,
      toolId: "knowledge.retrieve-company-context",
      schemaDigest: sha("6"),
      argumentMap: [],
      resultMap: [
        {
          semanticSource: "port.company-context-out",
          implementationTarget: "result.company_context",
        },
      ],
      approvalPolicy: "none",
      capabilityName: "Retrieve approved company standards and context",
    },
    {
      id: "binding.create-design-specification",
      kind: "internal",
      providerId: "provider.wright-local",
      serverId: null,
      toolId: "ai.create-design-specification",
      schemaDigest: sha("7"),
      argumentMap: [
        {
          semanticSource: "port.design-intent-in",
          implementationTarget: "inputs.design_intent",
        },
        {
          semanticSource: "port.reference-images-in",
          implementationTarget: "inputs.reference_images",
        },
        {
          semanticSource: "port.company-context-in",
          implementationTarget: "inputs.company_context",
        },
      ],
      resultMap: [
        {
          semanticSource: "port.design-specification-out",
          implementationTarget: "result.design_specification",
        },
      ],
      approvalPolicy: "review_before_run",
      capabilityName: "Create a reviewable engineering design specification",
    },
    {
      id: "binding.generate-geometry",
      kind: "mcp_tool",
      providerId: "provider.wright-local",
      serverId: "server.solid-edge",
      toolId: "tool.create-mounting-bracket",
      schemaDigest: sha("1"),
      argumentMap: [
        {
          semanticSource: "port.design-specification-in",
          implementationTarget: "arguments.design_specification",
        },
      ],
      resultMap: [
        {
          semanticSource: "port.geometry-out",
          implementationTarget: "result.geometry",
        },
      ],
      approvalPolicy: "review_before_run",
      capabilityName: "Create mounting bracket CAD model",
    },
    {
      id: "binding.check-manufacturability",
      kind: "internal",
      providerId: "provider.wright-local",
      serverId: null,
      toolId: "check.bracket-manufacturability",
      schemaDigest: sha("2"),
      argumentMap: [
        {
          semanticSource: "port.geometry-check-in",
          implementationTarget: "geometry",
        },
        {
          semanticSource: "port.design-specification-check-in",
          implementationTarget: "design_specification",
        },
      ],
      resultMap: [
        { semanticSource: "port.report-out", implementationTarget: "report" },
      ],
      approvalPolicy: "none",
      capabilityName: "Run bracket manufacturing checks",
    },
    {
      id: "binding.export-step",
      kind: "mcp_tool",
      providerId: "provider.wright-local",
      serverId: "server.solid-edge",
      toolId: "tool.export-step-ap242",
      schemaDigest: sha("3"),
      argumentMap: [
        {
          semanticSource: "port.approved-geometry-in",
          implementationTarget: "arguments.model",
        },
      ],
      resultMap: [
        {
          semanticSource: "port.step-out",
          implementationTarget: "result.step_file",
        },
      ],
      approvalPolicy: "review_before_run",
      capabilityName: "Export approved model as STEP AP242",
    },
    {
      id: "binding.release-package",
      kind: "internal",
      providerId: "provider.wright-local",
      serverId: null,
      toolId: "package.local-review-bundle",
      schemaDigest: sha("4"),
      argumentMap: [
        { semanticSource: "port.step-in", implementationTarget: "files.step" },
        {
          semanticSource: "port.report-package-in",
          implementationTarget: "files.report",
        },
      ],
      resultMap: [
        { semanticSource: "port.package-out", implementationTarget: "package" },
      ],
      approvalPolicy: "none",
      capabilityName: "Create local design handoff package",
    },
  ],
  components: [
    {
      id: "component.review-cell",
      version: "1.0.0",
      title: "Design review step group",
      inputPortIds: [
        "port.design-specification-review-in",
        "port.geometry-review-in",
        "port.report-in",
      ],
      outputPortIds: ["port.approved-geometry-out"],
      internalDefinitionDigest: sha("5"),
      internalAddresses: [
        {
          semanticId: "component.review-cell.block.evaluate",
          conceptKind: "block",
          relativePath: "blocks/block.evaluate",
        },
        {
          semanticId: "component.review-cell.relationship.accept",
          conceptKind: "relationship",
          relativePath: "relationships/rel.accept",
        },
        {
          semanticId: "component.review-cell.artifact.approved",
          conceptKind: "artifact_contract",
          relativePath: "artifact-contracts/artifact.approved",
        },
        {
          semanticId: "component.review-cell.port.approved",
          conceptKind: "port",
          relativePath: "ports/port.approved",
        },
      ],
    },
  ],
};

export const initialLayout: RecoveryLayout = {
  documentKind: "workflow-layout",
  schemaVersion: "1.0.0-recovery.1",
  workflowId: "workflow.mounting-bracket",
  semanticRevision: 2,
  layoutRevision: 1,
  positions: {
    "block.reference-images": { x: 10, y: 20 },
    "block.design-intent": { x: 10, y: 180 },
    "block.company-context": { x: 10, y: 340 },
    "block.create-design-specification": { x: 260, y: 180 },
    "block.generate-geometry": { x: 510, y: 180 },
    "block.check-manufacturability": { x: 760, y: 330 },
    "block.review-design": { x: 760, y: 40 },
    "block.export-step": { x: 1010, y: 40 },
    "block.release-package": { x: 1010, y: 330 },
  },
  viewport: { x: 0, y: 0, zoom: 0.72 },
};

export function cloneWorkflow(workflow: RecoveryWorkflow): RecoveryWorkflow {
  return structuredClone(workflow);
}

export function cloneLayout(layout: RecoveryLayout): RecoveryLayout {
  return structuredClone(layout);
}

export function validateRecoveryLayoutDocument(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
): RecoveryDiagnostic[] {
  if (
    layout.documentKind !== "workflow-layout" ||
    layout.schemaVersion !== "1.0.0-recovery.1"
  ) {
    return [
      {
        code: "WFR-LAYOUT-VERSION-UNSUPPORTED",
        semanticId: null,
        line: null,
        explanation: `Unsupported layout document ${String(layout.documentKind)} version ${String(layout.schemaVersion)}.`,
        correction:
          "Preserve the original bytes and use an explicitly compatible reader; never silently rewrite an unknown version.",
      },
    ];
  }
  if (
    layout.workflowId !== workflow.workflowId ||
    layout.semanticRevision !== workflow.revision
  ) {
    return [
      {
        code: "WFR-LAYOUT-SUBJECT-MISMATCH",
        semanticId: null,
        line: null,
        explanation:
          "The layout does not target the current workflow identity and semantic revision.",
        correction:
          "Load or explicitly migrate a layout bound to the accepted workflow revision.",
      },
    ];
  }
  const blockIds = new Set(workflow.blocks.map((item) => item.id));
  const unknown = Object.keys(layout.positions).find((id) => !blockIds.has(id));
  if (unknown)
    return [
      {
        code: "WFR-LAYOUT-IDENTITY-UNKNOWN",
        semanticId: unknown,
        line: null,
        explanation: `Layout position ${unknown} has no canonical block.`,
        correction:
          "Remove the unknown presentation identity or restore its canonical block.",
      },
    ];
  const numbers = [
    layout.viewport.x,
    layout.viewport.y,
    layout.viewport.zoom,
    ...Object.values(layout.positions).flatMap((position) => [
      position.x,
      position.y,
    ]),
  ];
  if (!numbers.every(Number.isFinite))
    return [
      {
        code: "WFR-LAYOUT-NUMBER-NONFINITE",
        semanticId: null,
        line: null,
        explanation: "Layout coordinates and viewport values must be finite.",
        correction:
          "Replace NaN or infinity with bounded numeric presentation metadata.",
      },
    ];
  if (!Number.isInteger(layout.layoutRevision) || layout.layoutRevision < 1)
    return [
      {
        code: "WFR-LAYOUT-REVISION-INVALID",
        semanticId: null,
        line: null,
        explanation: "Layout revision must be a positive integer.",
        correction:
          "Use the next positive layout revision assigned by the host.",
      },
    ];
  if (layout.viewport.zoom <= 0)
    return [
      {
        code: "WFR-LAYOUT-ZOOM-INVALID",
        semanticId: null,
        line: null,
        explanation: "Layout zoom must be greater than zero.",
        correction: "Use a positive finite zoom value.",
      },
    ];
  return [];
}

export function findBlock(
  workflow: RecoveryWorkflow,
  id: string | null,
): RecoveryBlock | null {
  return id === null
    ? null
    : (workflow.blocks.find((block) => block.id === id) ?? null);
}

export function findPort(
  workflow: RecoveryWorkflow,
  id: string,
): RecoveryPort | null {
  return workflow.ports.find((port) => port.id === id) ?? null;
}

export function phaseName(
  workflow: RecoveryWorkflow,
  id: string | null,
): string {
  return (
    workflow.phases.find((phase) => phase.id === id)?.name ??
    id ??
    "Reusable component"
  );
}

const LEGACY_INPUT_BLOCK_IDS = new Set([
  "block.reference-images",
  "block.design-intent",
  "block.company-context",
]);

export function recoveryAuthoringSectionKind(
  block: RecoveryBlock,
): "input" | "task" {
  if (
    block.configuration[RECOVERY_AUTHORING_SECTION_CONFIGURATION_KEY] ===
    "input"
  )
    return "input";
  return LEGACY_INPUT_BLOCK_IDS.has(block.id) ? "input" : "task";
}

function roleFor(
  block: RecoveryBlock,
): "input" | "work" | "review" | "release" {
  if (recoveryAuthoringSectionKind(block) === "input") return "input";
  if (
    block.kind === "approval" ||
    block.componentRef?.componentId === "component.review-cell"
  )
    return "review";
  if (block.id.includes("release") || block.id.includes("export"))
    return "release";
  return "work";
}

export function resolveRecoveryComponentScope(
  workflow: RecoveryWorkflow,
  componentInstanceId: string,
  internalSemanticId: string,
): RecoveryComponentScope {
  const instance = workflow.blocks.find(
    (block) => block.id === componentInstanceId,
  );
  if (!instance?.componentRef)
    throw new Error(`WFR-COMPONENT-INSTANCE-MISSING:${componentInstanceId}`);
  const component = workflow.components.find(
    (item) => item.id === instance.componentRef?.componentId,
  );
  if (!component)
    throw new Error(
      `WFR-COMPONENT-REFERENCE-MISSING:${instance.componentRef.componentId}`,
    );
  if (
    !component.internalAddresses.some(
      (address) => address.semanticId === internalSemanticId,
    )
  ) {
    throw new Error(`WFR-COMPONENT-ADDRESS-MISSING:${internalSemanticId}`);
  }
  return {
    componentInstanceId,
    componentId: component.id,
    componentVersion: component.version,
    internalSemanticId,
  };
}

export function toDraftProjection(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
): DraftProjection {
  const layoutIssue = validateRecoveryLayoutDocument(workflow, layout)[0];
  if (layoutIssue) throw new Error(layoutIssue.code);
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
      cardinality:
        source.cardinality === "many" ? ("many" as const) : ("one" as const),
      semanticId: source.id,
    };
  };
  const blocks = new Map(workflow.blocks.map((block) => [block.id, block]));
  const gatesByOwner = new Map<
    string,
    {
      id: string;
      owner_block_id: string;
      condition: string;
      proceed_target_block_id: string;
      revise_target_block_id: string;
      feedback_path_id: string;
      semanticId: string;
    }
  >();
  for (const block of workflow.blocks) {
    const isReviewGate =
      block.kind === "approval" ||
      block.componentRef?.componentId === "component.review-cell";
    if (!isReviewGate) continue;
    const decision = workflow.relationships
      .filter(
        (relationship) =>
          relationship.kind === "decision" &&
          relationship.sourceId === block.id,
      )
      .sort((left, right) => left.id.localeCompare(right.id))[0];
    const feedback = workflow.relationships
      .filter(
        (relationship) =>
          relationship.kind === "feedback" &&
          relationship.sourceId === block.id,
      )
      .sort((left, right) => left.id.localeCompare(right.id))[0];
    if (!decision || !feedback) continue;
    const gateId =
      block.id === "block.review-design"
        ? "gate.review-decision"
        : `gate.${block.id.replace(/^block\./, "")}-decision`;
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
      artifactsByProducer.set(artifact.producerBlockId, [
        ...(artifactsByProducer.get(artifact.producerBlockId) ?? []),
        artifact,
      ]);
    }
  }
  const projectedBlocks = new Map(
    workflow.blocks.map((block) => {
      const gate = gatesByOwner.get(block.id);
      const gates = gate ? [gate] : [];
      return [
        block.id,
        {
          id: block.id,
          title: block.title,
          purpose: block.purpose,
          role: roleFor(block),
          phase_id: block.phaseId ?? "phase.unassigned-component",
          input_port_ids: [...block.inputPortIds],
          output_port_ids: [...block.outputPortIds],
          gate_ids: gates.map((gate) => gate.id),
          intended_artifact_ids: (artifactsByProducer.get(block.id) ?? []).map(
            (item) => item.id,
          ),
          semanticId: block.id,
          position: {
            semantic_id: block.id,
            ...(layout.positions[block.id] ?? { x: 40, y: 40 }),
          },
          inputs: block.inputPortIds.map(port),
          outputs: block.outputPortIds.map(port),
          gates,
          artifacts: (artifactsByProducer.get(block.id) ?? []).map(
            (artifact) => ({
              id: artifact.id,
              title: artifact.name,
              artifact_type_id: artifact.typeId,
              description: artifact.description,
              produced_by_block_id: block.id,
              semanticId: artifact.id,
            }),
          ),
          componentRef:
            block.componentRef === null
              ? null
              : {
                  componentId: block.componentRef.componentId,
                  versionRange: block.componentRef.versionRange,
                },
        },
      ];
    }),
  );
  const portOwners = new Map(
    workflow.ports.map((item) => [item.id, item.ownerBlockId]),
  );
  const unphasedBlockIds = workflow.blocks
    .filter((block) => block.phaseId === null)
    .map((block) => block.id);
  const projectedPhases = workflow.phases.map((phase) => ({
    id: phase.id,
    name: phase.name,
    purpose: phase.purpose,
    order: phase.order,
    block_ids: [...phase.blockIds],
    semanticId: phase.id,
    blocks: phase.blockIds.map((id) => {
      const projected = projectedBlocks.get(id);
      if (!projected || !blocks.has(id))
        throw new Error(`RECOVERY_BLOCK_MISSING:${id}`);
      return projected;
    }),
  }));
  if (unphasedBlockIds.length > 0) {
    projectedPhases.push({
      id: "phase.unassigned-component",
      name: "Reusable components",
      purpose:
        "Projection-only grouping for canonical component blocks that are not assigned to an execution phase.",
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
    connections: workflow.relationships
      .filter((relationship) => relationship.kind === "data")
      .map((relationship) => ({
        id: relationship.id,
        source_port_id: relationship.sourceId,
        target_port_id: relationship.targetId,
        semanticId: relationship.id,
        sourceBlockId:
          portOwners.get(relationship.sourceId) ?? relationship.sourceId,
        targetBlockId:
          portOwners.get(relationship.targetId) ?? relationship.targetId,
      })),
    feedbackPaths: workflow.relationships.flatMap((relationship) => {
      if (relationship.kind !== "feedback") return [];
      const gate = gatesByOwner.get(relationship.sourceId);
      return [
        {
          id: relationship.id,
          from_gate_id: gate?.id ?? relationship.sourceId,
          to_block_id: relationship.targetId,
          reason: relationship.condition ?? relationship.label,
          semanticId: relationship.id,
          label: relationship.label,
        },
      ];
    }),
    components: workflow.components.map((component) => ({
      semanticId: component.id,
      version: component.version,
      title: component.title,
      inputPortIds: [...component.inputPortIds],
      outputPortIds: [...component.outputPortIds],
      internalDefinitionDigest: component.internalDefinitionDigest,
      internalAddresses: component.internalAddresses.map((address) => ({
        ...address,
      })),
    })),
  };
}

export function initialRunProjection(
  subject: RecoveryWorkflow = initialWorkflow,
  semanticSha256 = "",
  createdAt = "",
): RecoveryRunProjection {
  return {
    documentKind: "workflow-run",
    schemaVersion: "1.0.0-recovery.1",
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
    steps: Object.fromEntries(
      subject.blocks.map((block) => [
        block.id,
        {
          state: "idle",
          label: "Not started",
          detail: "Waiting for the simulated run.",
        },
      ]),
    ),
    activity: [],
    artifactRecords: [],
    materialSupplied: false,
    outputsReady: false,
  };
}

export function validateRecoveryRunProjection(
  run: RecoveryRunProjection,
  subject: RecoveryRunSubject | null = null,
): RecoveryDiagnostic[] {
  if (
    run.documentKind !== "workflow-run" ||
    run.schemaVersion !== "1.0.0-recovery.1"
  ) {
    return [
      {
        code: "WFR-RUN-VERSION-UNSUPPORTED",
        semanticId: run.runId ?? null,
        line: null,
        explanation: `Unsupported run document ${String(run.documentKind)} version ${String(run.schemaVersion)}.`,
        correction:
          "Preserve the original record bytes and open them with an explicitly compatible reader; never rewrite an unknown version.",
      },
    ];
  }
  if (
    subject !== null &&
    (run.workflowId !== subject.workflowId ||
      run.workflowRevision !== subject.workflowRevision ||
      run.semanticSha256 !== subject.semanticSha256)
  ) {
    return [
      {
        code: "WFR-RUN-SUBJECT-MISMATCH",
        semanticId: run.runId,
        line: null,
        explanation:
          "The run projection does not match the captured workflow identity, revision, and semantic digest.",
        correction:
          "Project only the immutable run record captured for this exact accepted definition subject.",
      },
    ];
  }
  return [];
}
