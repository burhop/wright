import { useEffect, useMemo, useRef, useState } from "react";

import type { DraftCanvasIntent } from "../../components/workflow-composer/draft-intents";
import {
  acceptRecoveryResult,
  aiDrawingProposal,
  applyRecoveryBatch,
  paletteBlock,
  recoveryCommandBatch,
  textEditCommands,
  type RecoveryCommand,
  type RecoveryCommandBatch,
} from "./command-system";
import {
  cloneLayout,
  cloneWorkflow,
  findBlock,
  findPort,
  initialLayout,
  initialRunProjection,
  initialWorkflow,
  phaseName,
  resolveRecoveryComponentScope,
  toDraftProjection,
  type RecoveryDiagnostic,
  type RecoveryLayout,
  type RecoveryRunProjection,
  type RecoveryRunState,
  type RecoveryWorkflow,
} from "./model";
import {
  formatRecoveryDsl,
  parseRecoveryDsl,
  sourceSelection,
} from "./recovery-dsl";
import {
  ReactFlowRecoveryCanvas,
  RecoveryCanvasRuntimeProvider,
} from "./ReactFlowRecoveryCanvas";
import { canonicalDefinitionBytes } from "./canonical-wire";
import "./workflow-recovery.css";

type ViewMode = "diagram" | "code" | "split";
type InspectorTab = "definition" | "inputs" | "outputs" | "activity" | "diagnosis";
type PortTreatment = "dot" | "terminal" | "hybrid";

const inspectorTabLabel: Record<InspectorTab, string> = {
  definition: "Setup",
  inputs: "Uses",
  outputs: "Creates",
  activity: "Run log",
  diagnosis: "Issues",
};

const runStateLabel: Record<RecoveryRunState, string> = {
  idle: "not started",
  queued: "waiting",
  running: "running",
  "needs-input": "needs input",
  succeeded: "complete",
  failed: "failed",
  blocked: "blocked",
  stale: "out of date",
};

interface Snapshot {
  workflow: RecoveryWorkflow;
  layout: RecoveryLayout;
}

export interface WorkflowRecoveryConceptProps {
  readonly surfaceState?: "ready" | "loading" | "error";
  readonly onRetry?: () => void;
}

export function WorkflowRecoveryConcept({ surfaceState = "ready", onRetry = () => undefined }: WorkflowRecoveryConceptProps = {}) {
  if (surfaceState === "loading") {
    return <section className="workflow-recovery recovery-boundary-state" data-testid="workflow-recovery-concept" data-surface-state="loading" aria-busy="true"><b>Loading canonical workflow recovery concept…</b><span>Accepted definition and renderer projection are not available yet.</span></section>;
  }
  if (surfaceState === "error") {
    return <section className="workflow-recovery recovery-boundary-state" data-testid="workflow-recovery-concept" data-surface-state="error" role="alert"><b>Recovery concept could not be prepared.</b><span>The accepted workflow was not changed.</span><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-boundary-retry" onClick={onRetry}>Retry concept load</button></section>;
  }
  return <WorkflowRecoveryReadyConcept />;
}

function contentIdentity(workflow: RecoveryWorkflow): string {
  return canonicalDefinitionBytes(workflow, true);
}

function useSha256(value: string): string {
  const [result, setResult] = useState<{ source: string; digest: string }>({ source: "", digest: "sha256:calculating" });
  useEffect(() => {
    let current = true;
    setResult({ source: value, digest: "sha256:calculating" });
    const bytes = new TextEncoder().encode(value);
    void crypto.subtle.digest("SHA-256", bytes).then((buffer) => {
      if (!current) return;
      const hex = [...new Uint8Array(buffer)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
      setResult({ source: value, digest: `sha256:${hex}` });
    }).catch(() => {
      if (current) setResult({ source: value, digest: "sha256:unavailable-in-this-browser" });
    });
    return () => { current = false; };
  }, [value]);
  return result.source === value ? result.digest : "sha256:calculating";
}

const STEP_FIXTURE_SHA256 = "bf316fa511f5e6a3312f03cb5b36184d91109185730defc41542b8805884be83";
const SIMULATED_BLOCK_IDS = new Set(initialWorkflow.blocks.map((block) => block.id));
const SIMULATED_RELATIONSHIP_IDS = new Set(initialWorkflow.relationships.map((relationship) => relationship.id));

function simulationContractIssue(workflow: RecoveryWorkflow): string | null {
  const blockIds = new Set(workflow.blocks.map((block) => block.id));
  if (blockIds.size !== SIMULATED_BLOCK_IDS.size || [...SIMULATED_BLOCK_IDS].some((id) => !blockIds.has(id))) {
    return "This bounded simulation supports the nine-step mounting-bracket example only. Restore that topology before running.";
  }
  const relationshipIds = new Set(workflow.relationships.map((relationship) => relationship.id));
  if (relationshipIds.size !== SIMULATED_RELATIONSHIP_IDS.size || [...SIMULATED_RELATIONSHIP_IDS].some((id) => !relationshipIds.has(id))) {
    return "The fixture simulation requires its complete canonical data, decision, and feedback relationships.";
  }
  if (contentIdentity(workflow) !== contentIdentity(initialWorkflow)) {
    return "The fixed engineering report supports only the exact mounting-bracket fixture facts. Undo semantic edits before running this bounded simulation.";
  }
  return null;
}

function runProjection(stage: number, materialSupplied: boolean, subject: RecoveryWorkflow, semanticSha256: string, createdAt: string): RecoveryRunProjection {
  const projection = initialRunProjection(subject, semanticSha256, createdAt);
  const order = subject.blocks.map((block) => block.id);
  const reviewScope = resolveRecoveryComponentScope(subject, "block.review-design", "component.review-cell.block.evaluate");
  projection.steps = Object.fromEntries(order.map((id) => [id, {
    state: "idle" as const,
    label: "Not started",
    detail: "Waiting for the simulated run.",
    ...(id === "block.review-design" ? { componentScope: reviewScope } : {}),
  }]));
  const scopedStep = (id: string, state: RecoveryRunState, label: string, detail: string) => ({
    state,
    label,
    detail,
    ...(id === "block.review-design" ? { componentScope: reviewScope } : {}),
  });
  const setAll = (state: RecoveryRunState, label: string, detail: string) => {
    projection.steps = Object.fromEntries(order.map((id) => [id, scopedStep(id, state, label, detail)]));
  };
  projection.materialSupplied = materialSupplied;
  if (stage === 0) return projection;
  if (stage === 1) {
    projection.state = "queued";
    setAll("queued", "Queued", "Waiting in the local simulated run.");
    projection.activity = [{ at: "00:00", label: "Run queued", detail: "Definition revision captured; no external tools called." }];
    return projection;
  }
  setAll("queued", "Queued", "Waiting for upstream simulated work.");
  const succeed = (id: string) => { projection.steps[id] = scopedStep(id, "succeeded", "Succeeded", "Simulated output captured with lineage."); };
  for (const id of ["block.reference-images", "block.design-intent", "block.company-context"]) succeed(id);
  if (stage === 2) {
    projection.state = "running";
    projection.activeBlockId = "block.create-design-specification";
    projection.activeRelationshipId = "rel.design-intent-to-specification";
    projection.steps["block.create-design-specification"] = { state: "running", label: "Drafting specification", detail: "Combining design intent, reference images, and company context into a reviewable design specification." };
  }
  if (stage === 3) {
    projection.state = "needs-input";
    projection.activeBlockId = "block.create-design-specification";
    projection.activeRelationshipId = "rel.specification-revise";
    projection.steps["block.create-design-specification"] = { state: "needs-input", label: "Engineer input needed", detail: "Material and temper are missing from the design intent. Add them before accepting the design specification." };
    for (const id of ["block.generate-geometry", "block.check-manufacturability", "block.review-design", "block.export-step", "block.release-package"]) {
      projection.steps[id] = scopedStep(id, "blocked", "Blocked", "Waiting for the reviewed design specification and material decision.");
    }
  }
  if (stage === 4) {
    projection.state = "running";
    projection.activeBlockId = "block.create-design-specification";
    projection.activeRelationshipId = "rel.context-to-specification";
    projection.steps["block.create-design-specification"] = { state: "running", label: "Updating specification", detail: "Material supplied; the design specification is being updated for engineer review." };
  }
  if (stage >= 5) succeed("block.create-design-specification");
  if (stage === 5) {
    projection.state = "running";
    projection.activeBlockId = "block.generate-geometry";
    projection.activeRelationshipId = "rel.specification-to-geometry";
    projection.steps["block.generate-geometry"] = { state: "running", label: "Creating CAD model", detail: "Creating a local bracket preview from the reviewed design specification." };
  }
  if (stage >= 6) succeed("block.generate-geometry");
  if (stage === 6) {
    projection.state = "running";
    projection.activeBlockId = "block.check-manufacturability";
    projection.activeRelationshipId = "rel.geometry-to-check";
    projection.steps["block.check-manufacturability"] = { state: "running", label: "Running manufacturing checks", detail: "Checking bend radius, edge distance, thickness, and tool access after the CAD model exists." };
  }
  if (stage >= 7) succeed("block.check-manufacturability");
  if (stage === 7) {
    projection.state = "running";
    projection.activeBlockId = "block.review-design";
    projection.activeRelationshipId = "rel.report-to-review";
    projection.steps["block.review-design"] = scopedStep("block.review-design", "running", "Awaiting design review", "Reviewing the exact CAD model and manufacturing report.");
  }
  if (stage >= 8) succeed("block.review-design");
  if (stage === 8) {
    projection.state = "running";
    projection.activeBlockId = "block.export-step";
    projection.activeRelationshipId = "rel.review-to-export";
    projection.steps["block.export-step"] = { state: "running", label: "Exporting STEP file", detail: "Exporting a simulated AP242 file from the approved CAD model." };
  }
  if (stage >= 9) succeed("block.export-step");
  if (stage === 9) {
    projection.state = "running";
    projection.activeBlockId = "block.release-package";
    projection.activeRelationshipId = "rel.step-to-package";
    projection.steps["block.release-package"] = { state: "running", label: "Creating handoff package", detail: "Assembling the local-only design handoff package." };
  }
  if (stage >= 10) {
    for (const id of order) succeed(id);
    projection.state = "succeeded";
    projection.outputsReady = true;
    projection.completedAt = createdAt;
    projection.artifactRecords = [{
      recordId: "artifact-record.step-static-fixture",
      contractId: "artifact.step",
      producedByBlockId: "block.export-step",
      digestSha256: STEP_FIXTURE_SHA256,
      origin: "static_fixture",
      upstreamContractIds: ["artifact.approved-geometry", "artifact.geometry", "artifact.manufacturability-report", "artifact.design-specification", "artifact.reference-images", "artifact.design-intent", "artifact.company-context"],
    }];
  }
  projection.activity = [
    { at: "00:00", label: "Workflow test queued", detail: "The current workflow version was recorded; no external tools were called." },
    { at: "00:02", label: "Three input sources ready", detail: "Design intent, reference images, and approved company context are available to the design-specification step." },
    ...(materialSupplied ? [{ at: "00:11", label: "Design decision supplied", detail: "The engineer added 6061-T6 material and temper to the design specification." }] : []),
  ];
  return projection;
}

function TreatmentCard({ treatment, selected, onSelect }: { readonly treatment: PortTreatment; readonly selected: boolean; readonly onSelect: () => void }) {
  const [labFeedback, setLabFeedback] = useState("Try both controls: one connects workflow steps; the other opens the related engineering item.");
  const labels: Record<PortTreatment, [string, string]> = {
    dot: ["A · Round socket", "Compact graph connector; the separate Open action can be easy to overlook."],
    terminal: ["B · Terminal block", "Strong electrical metaphor; visually heavy at engineering-workflow scale."],
    hybrid: ["C · Hybrid terminal", "Distinct connection socket plus a labeled action for the CAD model, file, or report."],
  };
  return (
    <article className={`port-treatment ${selected ? "is-selected" : ""}`} data-testid={`workflow-port-lab-${treatment}`}>
      <header><h3>{labels[treatment][0]}</h3>{selected && <span>SELECTED TREATMENT</span>}</header>
      <p>{labels[treatment][1]}</p>
      <div className={`port-treatment__demo port-treatment__demo--${treatment}`}>
        <button type="button" className="port-treatment__socket" data-testid={`workflow-port-lab-${treatment}-connect`} aria-label={`${treatment} connect socket`} onClick={() => setLabFeedback("Connection started from Approved CAD model; choose a compatible required item on another step.")}>{treatment === "terminal" ? "▣" : "●"}</button>
        <div><strong>Approved CAD model</strong><small>3D design model · Required</small></div>
        <button type="button" className="port-treatment__artifact" data-testid={`workflow-port-lab-${treatment}-artifact`} aria-label={`${treatment} open CAD model`} onClick={() => setLabFeedback("Approved CAD model opened separately with its exact source revision and preview.")}>▧ Open</button>
      </div>
      <div className="port-treatment__feedback" role="status">{labFeedback}</div>
      <div className="port-treatment__states" aria-label="Connection states"><span>○ not available</span><span>⊘ wrong item</span><span>◷ waiting</span><span>✓ ready</span><span>× failed</span><span>↺ out of date</span></div>
      <button type="button" className="recovery-button recovery-button--secondary" data-testid={`workflow-port-lab-${treatment}-select`} onClick={onSelect}>{selected ? "Current style" : "Use this style"}</button>
    </article>
  );
}

function WorkflowRecoveryReadyConcept() {
  const [workflow, setWorkflow] = useState(() => cloneWorkflow(initialWorkflow));
  const [layout, setLayout] = useState(() => cloneLayout(initialLayout));
  const [selectedId, setSelectedId] = useState<string | null>("block.design-intent");
  const [view, setView] = useState<ViewMode>("diagram");
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("definition");
  const [diagnostics, setDiagnostics] = useState<RecoveryDiagnostic[]>([]);
  const initialSource = useMemo(() => formatRecoveryDsl(initialWorkflow).text, []);
  const [sourceDraft, setSourceDraft] = useState(initialSource);
  const [sourceDirty, setSourceDirty] = useState(false);
  const [undoStack, setUndoStack] = useState<Snapshot[]>([]);
  const [redoStack, setRedoStack] = useState<Snapshot[]>([]);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [designIntentName, setDesignIntentName] = useState<string | null>(null);
  const [modal, setModal] = useState<"none" | "port-lab" | "design-intent" | "output">("none");
  const [portTreatment, setPortTreatment] = useState<PortTreatment>("hybrid");
  const [proposal, setProposal] = useState<RecoveryCommandBatch | null>(null);
  const [proposalResult, setProposalResult] = useState<ReturnType<typeof applyRecoveryBatch> | null>(null);
  const [runStage, setRunStage] = useState(0);
  const [runSubject, setRunSubject] = useState<RecoveryWorkflow | null>(null);
  const [runSubjectDigest, setRunSubjectDigest] = useState("");
  const [runCreatedAt, setRunCreatedAt] = useState("");
  const [materialSupplied, setMaterialSupplied] = useState(false);
  const [runOverride, setRunOverride] = useState<RecoveryRunState | null>(null);
  const sourceRef = useRef<HTMLTextAreaElement>(null);
  const modalRef = useRef<HTMLElement>(null);
  const modalReturnFocusRef = useRef<HTMLElement | null>(null);

  const candidateWorkflow = proposalResult?.ok && proposalResult.workflow ? proposalResult.workflow : workflow;
  const candidateLayout = proposalResult?.ok && proposalResult.layout ? proposalResult.layout : layout;
  const projection = useMemo(() => toDraftProjection(candidateWorkflow, candidateLayout), [candidateWorkflow, candidateLayout]);
  const portArtifacts = useMemo(() => Object.fromEntries(candidateWorkflow.ports.filter((port) => port.artifactContractId).map((port) => [port.id, port.artifactContractId as string])), [candidateWorkflow]);
  const formatted = useMemo(() => formatRecoveryDsl(workflow), [workflow]);
  const parsedSource = useMemo(() => parseRecoveryDsl(sourceDraft), [sourceDraft]);
  const sourceValid = parsedSource.ok;
  const run = useMemo(() => {
    const value = runProjection(runStage, materialSupplied, runSubject ?? workflow, runSubjectDigest, runCreatedAt);
    if (runOverride === "failed") {
      value.state = "failed";
      value.activeBlockId = "block.export-step";
      value.activeRelationshipId = "rel.review-to-export";
      value.steps["block.export-step"] = { state: "failed", label: "Failed", detail: "Simulated export rejected an unsupported local unit option." };
      if (value.steps["block.release-package"]) value.steps["block.release-package"] = { state: "blocked", label: "Blocked", detail: "No trustworthy STEP output is available for packaging." };
      value.outputsReady = false;
      value.artifactRecords = [];
      value.completedAt = runCreatedAt;
    }
    if (runOverride === "stale") {
      value.state = "stale";
      value.activeBlockId = null;
      value.activeRelationshipId = null;
      value.steps["block.export-step"] = { state: "stale", label: "Stale", detail: "Output belongs to an earlier accepted definition revision." };
      if (value.steps["block.release-package"]) value.steps["block.release-package"] = { state: "blocked", label: "Blocked", detail: "Stale STEP bytes cannot enter a new review package." };
      value.outputsReady = false;
      value.artifactRecords = [];
      value.completedAt = runCreatedAt;
    }
    return value;
  }, [runStage, materialSupplied, runOverride, runSubject, runSubjectDigest, runCreatedAt, workflow]);
  const semanticDigest = useSha256(canonicalDefinitionBytes(workflow));
  const layoutDigest = useSha256(JSON.stringify(layout));
  const inspectionWorkflow = proposal !== null ? candidateWorkflow : workflow;
  const selectedBlock = findBlock(inspectionWorkflow, selectedId);
  const selectedRelationship = inspectionWorkflow.relationships.find((item) => item.id === selectedId) ?? null;
  const selectedPort = inspectionWorkflow.ports.find((item) => item.id === selectedId) ?? null;
  const candidateSelection = proposal !== null && selectedId !== null && !workflow.blocks.some((item) => item.id === selectedId) && !workflow.ports.some((item) => item.id === selectedId) && !workflow.relationships.some((item) => item.id === selectedId);
  const stepArtifact = run.artifactRecords.find((record) => record.contractId === "artifact.step") ?? null;
  const simulationIssue = simulationContractIssue(workflow);

  useEffect(() => {
    const range = sourceSelection(formatted.sourceMap, selectedId);
    if (!range || !sourceRef.current || sourceDirty) return;
    sourceRef.current.setSelectionRange(range.startOffset, range.endOffset);
  }, [formatted.sourceMap, selectedId, sourceDirty, view]);

  useEffect(() => {
    if (modal !== "none") {
      if (modalReturnFocusRef.current === null && document.activeElement instanceof HTMLElement) modalReturnFocusRef.current = document.activeElement;
      modalRef.current?.querySelector<HTMLElement>('button[aria-label="Close dialog"]')?.focus();
    } else if (modalReturnFocusRef.current !== null) {
      modalReturnFocusRef.current.focus();
      modalReturnFocusRef.current = null;
    }
  }, [modal]);

  const pushSnapshot = (nextWorkflow: RecoveryWorkflow, nextLayout: RecoveryLayout, before: Snapshot) => {
    setUndoStack((stack) => [...stack, before]);
    setRedoStack([]);
    setWorkflow(nextWorkflow);
    setLayout(nextLayout);
    setSourceDraft(formatRecoveryDsl(nextWorkflow).text);
    setSourceDirty(false);
    setDiagnostics([]);
  };

  const applyBatch = (batch: RecoveryCommandBatch) => {
    const result = applyRecoveryBatch(workflow, layout, batch);
    if (!result.ok) {
      setDiagnostics(result.diagnostics);
      return false;
    }
    const accepted = acceptRecoveryResult(workflow, layout, result);
    if (!accepted) return false;
    const before = { workflow: cloneWorkflow(workflow), layout: cloneLayout(layout) };
    pushSnapshot(accepted.workflow, accepted.layout, before);
    return true;
  };

  const applyCommands = (origin: RecoveryCommandBatch["origin"], commands: RecoveryCommand[]) => applyBatch(recoveryCommandBatch(workflow.revision, origin, commands));

  const restore = (snapshot: Snapshot, direction: "undo" | "redo") => {
    const current = { workflow: cloneWorkflow(workflow), layout: cloneLayout(layout) };
    const result = applyRecoveryBatch(workflow, layout, recoveryCommandBatch(workflow.revision, "history", [{
      kind: "restore_snapshot",
      direction,
      workflow: cloneWorkflow(snapshot.workflow),
      layout: cloneLayout(snapshot.layout),
    }]));
    if (!result.ok) {
      setDiagnostics(result.diagnostics);
      return;
    }
    const restored = acceptRecoveryResult(workflow, layout, result);
    if (restored === null) return;
    if (direction === "undo") {
      setUndoStack((stack) => stack.slice(0, -1));
      setRedoStack((stack) => [...stack, current]);
    } else {
      setRedoStack((stack) => stack.slice(0, -1));
      setUndoStack((stack) => [...stack, current]);
    }
    setWorkflow(restored.workflow);
    setLayout(restored.layout);
    setSourceDraft(formatRecoveryDsl(restored.workflow).text);
    setSourceDirty(false);
    setDiagnostics([]);
  };

  const handleIntent = (intent: DraftCanvasIntent) => {
    if (intent.type === "select") {
      setSelectedId(intent.semanticId);
      return;
    }
    if (intent.type === "move-block") {
      applyCommands("graph", [{ kind: "move_block", blockId: intent.semanticId, x: intent.x, y: intent.y }]);
      return;
    }
    if (intent.type === "create-connection") {
      const source = findPort(workflow, intent.sourcePortId);
      const target = findPort(workflow, intent.targetPortId);
      if (!source || !target) return;
      const known = source.id === "port.approved-geometry-out" && target.id === "port.approved-geometry-in";
      const id = known ? "rel.review-to-export" : `rel.user-${source.id.replace("port.", "")}-to-${target.id.replace("port.", "")}`;
      applyCommands("graph", [{ kind: "connect", relationship: { id, kind: "data", sourceId: source.id, targetId: target.id, label: source.name.toLowerCase(), condition: known ? "decision.accepted" : null } }]);
      setSelectedId(id);
      return;
    }
    if (intent.type === "delete-connection") {
      applyCommands("graph", [{ kind: "disconnect", relationshipId: intent.semanticId }]);
      setSelectedId(null);
      return;
    }
    if (intent.type === "delete-concept") {
      if (applyCommands("graph", [{ kind: "delete_block", blockId: intent.semanticId }])) setSelectedId(null);
    }
  };

  const applySource = () => {
    const parsed = parseRecoveryDsl(sourceDraft);
    if (!parsed.ok || !parsed.workflow) {
      setDiagnostics(parsed.diagnostics);
      return;
    }
    const commands = textEditCommands(workflow, parsed.workflow);
    if (commands.length > 0 && "code" in commands[0]!) {
      setDiagnostics(commands as RecoveryDiagnostic[]);
      return;
    }
    if (commands.length === 0) {
      setSourceDraft(formatted.text);
      setSourceDirty(false);
      setDiagnostics([]);
      return;
    }
    applyCommands("text", commands as RecoveryCommand[]);
  };

  const requestProposal = () => {
    const batch = aiDrawingProposal(workflow);
    setProposal(batch);
    setProposalResult(applyRecoveryBatch(workflow, layout, batch));
  };

  const selectedStep = selectedBlock ? run.steps[selectedBlock.id] : null;
  const downstreamLibraryAvailable = selectedBlock !== null && !["block.reference-images", "block.design-intent", "block.company-context", "block.create-design-specification"].includes(selectedBlock.id);
  const canRun = designIntentName !== null && sourceValid && !sourceDirty && proposal === null && simulationIssue === null && /^sha256:[a-f0-9]{64}$/.test(semanticDigest);
  const nextRun = () => {
    setRunOverride(null);
    setRunStage((stage) => stage === 0 ? 1 : stage === 1 ? 2 : stage === 2 ? 3 : stage >= 4 && stage < 10 ? stage + 1 : stage);
  };
  const startRun = () => {
    setRunSubject(cloneWorkflow(workflow));
    setRunSubjectDigest(semanticDigest.replace(/^sha256:/, ""));
    setRunCreatedAt(new Date().toISOString());
    setRunOverride(null);
    setRunStage(1);
  };

  return (
    <section
      className="workflow-recovery"
      data-testid="workflow-recovery-concept"
      data-revision={workflow.revision}
      data-semantic-digest={semanticDigest}
      data-layout-digest={layoutDigest}
    >
      <header className="recovery-filebar" data-testid="workflow-recovery-filebar">
        <div className="recovery-filebar__identity">
          <span className="recovery-filebar__icon" aria-hidden="true">WF</span>
          <div>
            <h1>Mounting bracket workflow</h1>
            <small title="Diagram, Code, and the inspector read this workflow file. Layout and workflow-test records are stored separately.">mounting-bracket.workflow.wflow · one workflow file · all views synchronized</small>
          </div>
        </div>
        <div className="recovery-authority" data-testid="workflow-recovery-authority" data-revision={workflow.revision} data-semantic-digest={semanticDigest} data-layout-digest={layoutDigest}>
          <b>PROVISIONAL · NOT PRODUCTION</b>
          <span>Current workflow version {workflow.revision}</span>
          <span>{sourceValid && !sourceDirty ? "✓ workflow checks pass" : "! source edit has issues · current diagram retained"}</span>
          <span>Test mode: <strong>SIMULATION</strong></span>
          {simulationIssue && <span data-testid="workflow-recovery-simulation-issue">! {simulationIssue}</span>}
        </div>
      </header>

      <div className="recovery-toolbar">
        <div className="recovery-tabs" role="tablist" aria-label="Workflow view">
          {(["diagram", "code", "split"] as const).map((mode) => <button key={mode} type="button" role="tab" aria-selected={view === mode} data-testid={`workflow-recovery-view-${mode}`} onClick={() => setView(mode)}>{mode[0]!.toUpperCase() + mode.slice(1)}</button>)}
        </div>
        <div className="recovery-toolbar__actions">
          <button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-undo" disabled={undoStack.length === 0} onClick={() => restore(undoStack.at(-1)!, "undo")}>↶ Undo</button>
          <button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-redo" disabled={redoStack.length === 0} onClick={() => restore(redoStack.at(-1)!, "redo")}>↷ Redo</button>
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-validate" onClick={() => { const parsed = parseRecoveryDsl(sourceDraft); setDiagnostics(parsed.diagnostics); }}>✓ Check workflow</button>
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-port-lab-open" onClick={() => setModal("port-lab")}>Connection style preview</button>
          <button type="button" className="recovery-button recovery-button--ai" data-testid="workflow-recovery-ai-request" onClick={requestProposal}>✦ Ask AI to add drawing steps</button>
          <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-run-start" disabled={!canRun} title={designIntentName === null ? "Add design intent as text or a document before testing the workflow." : simulationIssue ?? undefined} onClick={runStage === 0 ? startRun : undefined}>{runStage === 0 ? "▶ Test workflow" : `SIMULATION · ${runStateLabel[run.state]}`}</button>
        </div>
      </div>

      <div className="recovery-workbench">
        <aside className="recovery-palette" data-testid="workflow-recovery-palette">
          <div className="recovery-panel-heading"><span>WORKFLOW INPUTS</span><h2>Three source inputs</h2><p>Each source is explicit about what it contains and where it comes from. Together they create the reviewed design specification.</p></div>
          <div className="recovery-source-list">
            <section className={`recovery-source-card ${selectedId === "block.reference-images" ? "is-selected" : ""}`} data-testid="workflow-recovery-input-source-reference-images">
              <header><div className="recovery-source-card__icon">IMG</div><div><b>Reference images</b><span>2 example images ready</span></div></header>
              <dl><div><dt>Comes from</dt><dd>Engineer upload</dd></div><div><dt>Contains</dt><dd>JPG or PNG images</dd></div></dl>
              <button type="button" data-testid="workflow-recovery-input-source-show-reference-images" onClick={() => { setSelectedId("block.reference-images"); setInspectorTab("definition"); }}>Show on diagram</button>
            </section>
            <section className={`recovery-source-card ${selectedId === "block.design-intent" ? "is-selected" : ""}`} data-testid="workflow-recovery-attachment-artifact.design-intent">
              <header><div className="recovery-source-card__icon recovery-source-card__icon--text">TEXT</div><div><b>Design intent</b><span>{designIntentName ?? "Not added yet"}</span></div></header>
              <dl><div><dt>Comes from</dt><dd>Engineer input</dd></div><div><dt>Contains</dt><dd>Typed text or common document</dd></div></dl>
              <div className="recovery-attachment__actions">
                {designIntentName === null ? <button type="button" data-testid="workflow-recovery-attachment-attach-artifact.design-intent" onClick={() => setDesignIntentName("mounting-bracket-design-intent.docx")}>Add text or document</button> : <><button type="button" data-testid="workflow-recovery-attachment-preview-artifact.design-intent" onClick={() => setModal("design-intent")}>View input</button><button type="button" data-testid="workflow-recovery-attachment-replace-artifact.design-intent" onClick={() => setDesignIntentName((name) => name?.endsWith(".txt") ? "mounting-bracket-design-intent.docx" : "mounting-bracket-design-intent.txt")}>Replace input</button></>}
                <button type="button" data-testid="workflow-recovery-input-source-show-design-intent" onClick={() => { setSelectedId("block.design-intent"); setInspectorTab("definition"); }}>Show on diagram</button>
              </div>
            </section>
            <section className={`recovery-source-card ${selectedId === "block.company-context" ? "is-selected" : ""}`} data-testid="workflow-recovery-input-source-company-context">
              <header><div className="recovery-source-card__icon recovery-source-card__icon--context">LIB</div><div><b>Company standards and context</b><span>Approved source ready</span></div></header>
              <dl><div><dt>Comes from</dt><dd>Company knowledge library</dd></div><div><dt>Contains</dt><dd>Standards and past designs</dd></div></dl>
              <button type="button" data-testid="workflow-recovery-input-source-show-company-context" onClick={() => { setSelectedId("block.company-context"); setInspectorTab("definition"); }}>Show on diagram</button>
            </section>
          </div>
          <div className="recovery-palette__section-label">Add downstream work</div>
          {downstreamLibraryAvailable ? <>
            <label className="recovery-search">Find a step<input data-testid="workflow-recovery-palette-search" value={paletteQuery} onChange={(event) => setPaletteQuery(event.target.value)} placeholder="drawing, tolerance check…" /></label>
            <div className="recovery-palette__items">
              {[{ id: "tolerance", label: "Check dimensions and tolerances", detail: "Uses the CAD model and reviewed design specification" }, { id: "drawing", label: "Create manufacturing drawing", detail: "Creates a drawing from the approved CAD model" }].filter((item) => item.label.toLowerCase().includes(paletteQuery.toLowerCase())).map((item) => (
                <button key={item.id} type="button" data-testid={`workflow-recovery-palette-item-${item.id}`} onClick={() => {
                  const command = paletteBlock(item.id as "tolerance" | "drawing", 580, 650, new Set(workflow.blocks.map((block) => block.id)));
                  if (applyCommands("graph", [command])) setSelectedId(command.kind === "add_block" ? command.block.id : null);
                }}><b>＋ {item.label}</b><span>{item.detail}</span></button>
              ))}
            </div>
          </> : <p className="recovery-palette__context-hint" data-testid="workflow-recovery-palette-context-hint">Select the CAD model or a later workflow step before adding checks or deliverables. Tolerances come from the reviewed design specification, not this first input stage.</p>}
          <section className="recovery-legend"><h3>Status key</h3>{(["queued", "running", "needs-input", "succeeded", "failed", "blocked", "stale"] as RecoveryRunState[]).map((state) => <span key={state} className={`recovery-state recovery-state--${state}`}>{state === "running" ? "▶" : state === "succeeded" ? "✓" : state === "failed" ? "×" : state === "blocked" ? "⊘" : state === "stale" ? "↺" : state === "needs-input" ? "!" : "◷"} {runStateLabel[state]}</span>)}</section>
        </aside>

        <div className={`recovery-stage recovery-stage--${view}`}>
          {(view === "diagram" || view === "split") && (
            <RecoveryCanvasRuntimeProvider value={{ run, runSubject: runStage > 0 && runSubject !== null ? { workflowId: runSubject.workflowId, workflowRevision: runSubject.revision, semanticSha256: runSubjectDigest } : null, proposedBlockIds: new Set(proposalResult?.workflow?.blocks.filter((block) => !workflow.blocks.some((accepted) => accepted.id === block.id)).map((block) => block.id) ?? []), portArtifactIds: portArtifacts, relationshipLabels: Object.fromEntries(candidateWorkflow.relationships.map((relationship) => [relationship.id, relationship.label])), overlayRelationships: candidateWorkflow.relationships.filter((relationship) => relationship.kind === "control" || relationship.kind === "decision"), portTreatment, onArtifactInspect: (portId) => { setSelectedId(portId); setInspectorTab(findPort(candidateWorkflow, portId)?.direction === "input" ? "inputs" : "outputs"); } }}>
              <ReactFlowRecoveryCanvas key={`${candidateWorkflow.revision}-${candidateWorkflow.blocks.length}-${proposal === null ? "accepted" : "candidate"}`} projection={projection} selectedSemanticId={selectedId} onIntent={proposal === null ? handleIntent : (intent) => { if (intent.type === "select") handleIntent(intent); }} />
            </RecoveryCanvasRuntimeProvider>
          )}
          {(view === "code" || view === "split") && <section className="recovery-code">
            <header><div><span>CODE PROJECTION</span><b>Wright workflow language · treatment 0.1</b></div><div>{parsedSource.ok ? "✓ parse valid" : "! parse failed"}</div></header>
            <textarea ref={sourceRef} spellCheck={false} aria-label="Workflow source" data-testid="workflow-recovery-source-editor" value={sourceDraft} onChange={(event) => { setSourceDraft(event.target.value); setSourceDirty(event.target.value !== formatted.text); }} onSelect={(event) => { const offset = event.currentTarget.selectionStart; const sourceMap = sourceDirty ? parsedSource.sourceMap : formatted.sourceMap; const match = Object.entries(sourceMap).find(([, span]) => span.startOffset <= offset && offset <= span.endOffset); if (match) setSelectedId(match[0]); }} />
            <footer><span>{sourceDirty ? "Unsaved source edit" : "Matches the current workflow"}</span><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-source-apply" onClick={applySource}>Apply checked edit</button></footer>
          </section>}
          {diagnostics.length > 0 && <div className="recovery-diagnostics" role="alert">{diagnostics.map((item, index) => <article key={`${item.code}-${index}`} role={item.semanticId ? "button" : undefined} tabIndex={item.semanticId ? 0 : undefined} onClick={() => { if (item.semanticId) { setSelectedId(item.semanticId); const range = parsedSource.sourceMap[item.semanticId]; if (range && sourceRef.current) { sourceRef.current.focus(); sourceRef.current.setSelectionRange(range.startOffset, range.endOffset); } } }} onKeyDown={(event) => { if (item.semanticId && (event.key === "Enter" || event.key === " ")) event.currentTarget.click(); }} data-testid={`workflow-recovery-diagnostic-${item.code}`} data-semantic-id={item.semanticId ?? ""} data-source-line={item.line ?? ""}><b>{item.code}</b><span>{item.explanation}</span><small>Correction: {item.correction}</small></article>)}</div>}
          {runStage > 0 && <section className="recovery-runbar" data-testid="workflow-recovery-run-mode">
            <div><b>WORKFLOW TEST · NO EXTERNAL TOOLS</b><span>Workflow version {run.workflowRevision} · {runStateLabel[run.state]}</span></div>
            {run.state === "needs-input" && <button type="button" data-testid="workflow-recovery-run-recover" onClick={() => { setMaterialSupplied(true); setRunStage(4); }}>Add 6061-T6 to design specification</button>}
            {runStage > 0 && runStage < 10 && run.state !== "needs-input" && <button type="button" data-testid="workflow-recovery-run-advance" onClick={nextRun}>Advance simulation</button>}
            {runStage >= 7 && <button type="button" className="recovery-button--quiet" data-testid="workflow-recovery-run-project-failed" onClick={() => setRunOverride("failed")}>Preview failed run</button>}
            {runStage >= 7 && <button type="button" className="recovery-button--quiet" data-testid="workflow-recovery-run-project-stale" onClick={() => setRunOverride("stale")}>Preview out-of-date result</button>}
          </section>}
        </div>

        <aside className="recovery-inspector" data-testid="workflow-recovery-inspector">
          <div className="recovery-panel-heading"><span>{candidateSelection ? "STEP DETAILS · AI SUGGESTION (READ-ONLY)" : proposal !== null ? "STEP DETAILS · REVIEW MODE (READ-ONLY)" : "STEP DETAILS"}</span><h2>{selectedBlock?.title ?? selectedPort?.name ?? selectedRelationship?.label ?? "Select a step"}</h2><small>{selectedBlock ? "Workflow step" : selectedPort ? "Required or created item" : selectedRelationship ? "Connection between steps" : "Nothing selected"}</small></div>
          <div className="recovery-inspector__tabs" role="tablist" aria-label="Step detail sections">
            {(["definition", "inputs", "outputs", "activity", "diagnosis"] as const).map((tab) => <button key={tab} type="button" role="tab" aria-selected={inspectorTab === tab} data-testid={`workflow-recovery-inspector-tab-${tab}`} onClick={() => setInspectorTab(tab)}>{inspectorTabLabel[tab]}</button>)}
          </div>
          <div className="recovery-inspector__body">
            {inspectorTab === "definition" && selectedBlock && <DefinitionInspector blockId={selectedBlock.id} workflow={inspectionWorkflow} readOnly={proposal !== null} onApply={(commands) => applyCommands("form", commands)} onDelete={() => { if (applyCommands("graph", [{ kind: "delete_block", blockId: selectedBlock.id }])) setSelectedId(null); }} />}
            {inspectorTab === "definition" && selectedRelationship && <RelationshipInspector relationshipId={selectedRelationship.id} workflow={inspectionWorkflow} readOnly={proposal !== null} onApply={(commands) => applyCommands("form", commands)} onDisconnect={() => handleIntent({ type: "delete-connection", semanticId: selectedRelationship.id })} />}
            {inspectorTab === "definition" && selectedPort && <section><div className="recovery-fact"><span>Item</span><b>{selectedPort.name}</b></div><div className="recovery-fact"><span>How it is used</span><b>{selectedPort.direction === "input" ? "Used by this step" : "Created by this step"}</b></div><div className="recovery-fact"><span>Requirement</span><b>{selectedPort.required ? "Required" : "Optional"}</b></div><p>{selectedPort.description}</p><details className="recovery-technical-details"><summary data-testid={`workflow-recovery-port-technical-${selectedPort.id}`}>Technical details</summary><code>{selectedPort.typeId}</code><code>{selectedPort.id}</code></details></section>}
            {inspectorTab === "inputs" && <PortInspector direction="input" workflow={inspectionWorkflow} blockId={selectedBlock?.id ?? selectedPort?.ownerBlockId ?? null} run={run} />}
            {inspectorTab === "outputs" && <PortInspector direction="output" workflow={inspectionWorkflow} blockId={selectedBlock?.id ?? selectedPort?.ownerBlockId ?? null} run={run} onOutput={() => setModal("output")} />}
            {inspectorTab === "activity" && <section>{run.activity.length === 0 ? <p>No simulated activity yet.</p> : run.activity.map((item) => <div className="recovery-activity" key={`${item.at}-${item.label}`}><time>{item.at}</time><div><b>{item.label}</b><span>{item.detail}</span></div></div>)}{selectedStep && <div className={`recovery-run-detail recovery-run-detail--${selectedStep.state}`} data-testid={`workflow-recovery-run-step-${selectedBlock?.id}`}><b>{selectedStep.label}</b><span>{selectedStep.detail}</span></div>}</section>}
            {inspectorTab === "diagnosis" && <section><div className="recovery-diagnosis"><b>{run.state === "needs-input" ? "Design decision is missing" : run.state === "failed" ? "Simulated export failed" : run.state === "stale" ? "Output revision is stale" : "No unresolved diagnosis"}</b><p>{run.state === "needs-input" ? "Material and temper are not stated in the design intent. The design specification cannot be accepted, so CAD and downstream work remain blocked." : "This projection is isolated from the accepted definition."}</p></div><button type="button" data-testid="workflow-recovery-diagnosis-show-failed" onClick={() => setRunOverride("failed")}>Show failed projection</button><button type="button" data-testid="workflow-recovery-diagnosis-show-stale" onClick={() => setRunOverride("stale")}>Show stale projection</button></section>}
          </div>
          {selectedBlock?.bindingId && <details className="recovery-binding"><summary data-testid="workflow-recovery-binding-disclosure">Automation details</summary>{(() => { const binding = inspectionWorkflow.bindings.find((item) => item.id === selectedBlock.bindingId); return binding ? <div><code>{binding.id}</code><span>{binding.kind} · {binding.capabilityName}</span><span>{binding.serverId ?? "internal"} / {binding.toolId}</span><span>Schema {binding.schemaDigest}</span><span>Approval: {binding.approvalPolicy}</span><b>Exact argument map</b>{binding.argumentMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}<b>Exact result map</b>{binding.resultMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}</div> : null; })()}</details>}
        </aside>
      </div>

      {proposal && proposalResult && <section className="recovery-proposal" data-testid="workflow-recovery-proposal" data-base-revision={proposal.baseRevision} data-validation={proposalResult.ok ? "valid" : "invalid"}>
        <header><div><span>AI SUGGESTION · REVIEW BEFORE ADDING</span><h2>Add drawing creation and review</h2></div><b>{proposalResult.ok ? "✓ workflow checks pass" : "! suggestion has issues"}</b></header>
        <div className="recovery-proposal__grid"><div><h3>Assumptions</h3><ul><li>The approved CAD model is the drawing source.</li><li>ASME Y14.5 and A3 are suggested review defaults, not hidden commitments.</li></ul><h3>Warnings</h3><ul><li>No drawing template or automation is selected.</li><li>Adding these steps does not run or approve them.</li></ul></div><div><h3>Changes</h3>{proposalResult.diff.map((line) => <p key={line}>＋ {line}</p>)}</div><div className="recovery-proposal__preview" data-testid="workflow-recovery-proposal-preview"><h3>Suggested workflow steps</h3><span>The diagram previews the full suggestion. New steps are dashed and clearly marked until you add them.</span><b>Approved CAD model ┄▷ Create manufacturing drawing</b><b>Manufacturing drawing ┄▷ Review manufacturing drawing</b><small>Preview only · not part of the current workflow</small><details><summary data-testid="workflow-recovery-proposal-code-disclosure">View suggested source</summary><pre>{proposalResult.workflow ? formatRecoveryDsl(proposalResult.workflow).text : "Suggestion has issues"}</pre></details></div></div>
        <footer><button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-proposal-reject" onClick={() => { setProposal(null); setProposalResult(null); }}>Discard suggestion</button><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-proposal-accept" disabled={!proposalResult.ok} onClick={() => { if (applyBatch(proposal)) { setProposal(null); setProposalResult(null); } }}>Add suggested steps</button></footer>
      </section>}

      {modal !== "none" && <div className="recovery-modal-backdrop" data-testid="workflow-recovery-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal("none"); }} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); setModal("none"); return; } if (event.key === "Tab" && modalRef.current) { const focusable = [...modalRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]; if (focusable.length === 0) return; const first = focusable[0]!; const last = focusable.at(-1)!; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } } }}><section ref={modalRef} className={`recovery-modal recovery-modal--${modal}`} role="dialog" aria-modal="true" aria-labelledby="recovery-modal-title">
        <header><div><span>LOCAL CONCEPT PREVIEW</span><h2 id="recovery-modal-title">{modal === "port-lab" ? "Connection style preview" : modal === "design-intent" ? "Design intent" : "Mounting bracket STEP file"}</h2></div><button type="button" data-testid="workflow-recovery-modal-close" aria-label="Close dialog" onClick={() => setModal("none")}>×</button></header>
        {modal === "port-lab" && <div data-testid="workflow-port-lab"><p className="recovery-modal__lead">Compare how an engineer connects required items between steps and separately opens the related file, CAD model, or report.</p><div className="port-lab-grid"><TreatmentCard treatment="dot" selected={portTreatment === "dot"} onSelect={() => setPortTreatment("dot")} /><TreatmentCard treatment="terminal" selected={portTreatment === "terminal"} onSelect={() => setPortTreatment("terminal")} /><TreatmentCard treatment="hybrid" selected={portTreatment === "hybrid"} onSelect={() => setPortTreatment("hybrid")} /></div><div className="port-lab-result"><b>Current connection style: {portTreatment}</b><span>This changes only the local concept preview.</span></div></div>}
        {modal === "design-intent" && designIntentName !== null && <div className="design-intent-preview"><div className="design-intent-preview__sheet"><span>ENGINEER INPUT / DESIGN INTENT</span><h3>Wall-mounted equipment bracket</h3><p>Support a small control enclosure on a vertical frame. Use two mounting holes on the frame side and a slotted interface on the enclosure side so assembly can be adjusted.</p><dl><dt>Design load</dt><dd>1.8 kN static</dd><dt>Envelope</dt><dd>120 × 80 × 60 mm maximum</dd><dt>Interfaces</dt><dd>Two frame holes; one adjustable slot</dd><dt>Material</dt><dd>Not yet decided</dd></dl></div><aside><b>{designIntentName}</b><span>Text or common document</span><span>Added by an engineer</span><span>Used by Create and review design specification</span></aside></div>}
        {modal === "output" && <div className="output-preview"><img src={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.svg`} alt="Isometric L-shaped mounting bracket with four holes" /><aside><b>mounting-bracket-simulated-fixture.step</b><span>STEP AP242 file</span><span>Demo STEP file. This simulated workflow did not create this file.</span><span>Workflow test version {run.workflowRevision}</span>{stepArtifact && <><span>Recorded demo output</span><span>File sha256:{stepArtifact.digestSha256}</span></>}<div className="recovery-lineage" data-testid="workflow-recovery-output-lineage"><b>Created from</b><span>Approved CAD model and design-review decision</span><span>Bracket CAD model and manufacturing check report</span><span>Reviewed design specification</span><span>Design intent + reference images + company standards and context</span></div><div><a className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-output-open-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/manufacturability-report.html`} target="_blank" rel="noreferrer">Open demo manufacturing report</a><a className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-download-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.step`} download="mounting-bracket-simulated-fixture.step">Download demo STEP file</a></div></aside></div>}
      </section></div>}
    </section>
  );
}

function RelationshipInspector({ relationshipId, workflow, readOnly, onApply, onDisconnect }: { readonly relationshipId: string; readonly workflow: RecoveryWorkflow; readonly readOnly: boolean; readonly onApply: (commands: RecoveryCommand[]) => void; readonly onDisconnect: () => void }) {
  const relationship = workflow.relationships.find((item) => item.id === relationshipId)!;
  const [label, setLabel] = useState(relationship.label);
  const [condition, setCondition] = useState(relationship.condition ?? "");
  const [targetId, setTargetId] = useState(relationship.targetId);
  useEffect(() => {
    setLabel(relationship.label);
    setCondition(relationship.condition ?? "");
    setTargetId(relationship.targetId);
  }, [relationship.id, relationship.label, relationship.condition, relationship.targetId]);
  const blockRelationship = relationship.kind !== "data";
  const endpointName = (semanticId: string) => {
    const endpointBlock = findBlock(workflow, semanticId);
    if (endpointBlock) return endpointBlock.title;
    const endpointPort = findPort(workflow, semanticId);
    const owner = endpointPort ? findBlock(workflow, endpointPort.ownerBlockId) : null;
    return endpointPort ? `${owner?.title ?? "Workflow step"}: ${endpointPort.name}` : semanticId;
  };
  const relationshipKind = relationship.kind === "data" ? "Engineering item" : relationship.kind === "decision" ? "Approved outcome" : relationship.kind === "feedback" ? "Revision path" : "Step order";
  return <section><div className="recovery-fact"><span>Connection type</span><b>{relationshipKind}</b></div><div className="recovery-fact"><span>From</span><b>{endpointName(relationship.sourceId)}</b></div><label>Connection label<input data-testid={`workflow-recovery-relationship-label-${relationship.id}`} value={label} readOnly={readOnly} onChange={(event) => setLabel(event.target.value)} /></label>{blockRelationship ? <label>Outcome goes to<select data-testid={`workflow-recovery-relationship-target-${relationship.id}`} value={targetId} disabled={readOnly} onChange={(event) => setTargetId(event.target.value)}>{workflow.blocks.map((block) => <option key={block.id} value={block.id}>{block.title}</option>)}</select></label> : <div className="recovery-fact"><span>To</span><b>{endpointName(relationship.targetId)}</b></div>}<label>Condition or reason<textarea data-testid={`workflow-recovery-relationship-condition-${relationship.id}`} value={condition} readOnly={readOnly} onChange={(event) => setCondition(event.target.value)} /></label><details className="recovery-technical-details"><summary data-testid={`workflow-recovery-relationship-technical-${relationship.id}`}>Technical details</summary><code>{relationship.id}</code><code>{relationship.sourceId} → {relationship.targetId}</code></details>{readOnly ? <p className="recovery-inspector__hint">Suggested connections stay read-only until you add the reviewed changes.</p> : <><button type="button" className="recovery-button recovery-button--primary" data-testid={`workflow-recovery-relationship-apply-${relationship.id}`} onClick={() => { const patch: Partial<Pick<typeof relationship, "targetId" | "label" | "condition">> = {}; if (label.trim() !== relationship.label) patch.label = label.trim(); if ((condition.trim() || null) !== relationship.condition) patch.condition = condition.trim() || null; if (blockRelationship && targetId !== relationship.targetId) patch.targetId = targetId; if (Object.keys(patch).length > 0) onApply([{ kind: "update_relationship", relationshipId: relationship.id, patch }]); }}>Save connection changes</button><button type="button" className="recovery-button recovery-button--danger" data-testid={`workflow-recovery-disconnect-${relationship.id}`} onClick={onDisconnect}>Disconnect steps</button></>}</section>;
}

function instructionField(executionKind: RecoveryWorkflow["blocks"][number]["executionKind"]): { label: string; performedBy: string; source: string } {
  if (executionKind === "human") {
    return {
      label: "Engineer checklist",
      performedBy: "Engineer",
      source: "Source: current workflow version. This checklist tells the engineer what to confirm; it is not copied from an input document.",
    };
  }
  if (executionKind === "ai_capable") {
    return {
      label: "AI prompt",
      performedBy: "AI-assisted check",
      source: "Source: current workflow version. This prompt is supplied to the configured AI-assisted check when the step runs.",
    };
  }
  return {
    label: "Automation instructions",
    performedBy: "Configured tool",
    source: "Source: current workflow version. These instructions are used by the configured tool when the step runs.",
  };
}

function mediaLabel(mediaType: string): string {
  if (mediaType === "text/plain") return "Text or common document";
  if (mediaType === "text/markdown") return "Editable design specification";
  if (mediaType.startsWith("image/")) return "JPG or PNG images";
  if (mediaType === "application/vnd.wright.context+json") return "Approved company knowledge";
  if (mediaType === "model/step") return "STEP AP242 file";
  if (mediaType === "text/html") return "Engineering report";
  if (mediaType === "application/zip") return "ZIP package";
  if (mediaType.startsWith("model/")) return "3D CAD model";
  return "Engineering file or record";
}

function DefinitionInspector({ blockId, workflow, readOnly, onApply, onDelete }: { readonly blockId: string; readonly workflow: RecoveryWorkflow; readonly readOnly: boolean; readonly onApply: (commands: RecoveryCommand[]) => void; readonly onDelete: () => void }) {
  const block = findBlock(workflow, blockId)!;
  const [title, setTitle] = useState(block.title);
  const [thickness, setThickness] = useState(String(block.configuration.thickness_mm ?? ""));
  useEffect(() => { setTitle(block.title); setThickness(String(block.configuration.thickness_mm ?? "")); }, [block.id, block.title, block.configuration.thickness_mm]);
  const instruction = instructionField(block.executionKind);
  const reviewedAiDraft = block.kind === "approval" && block.executionKind === "ai_capable";
  const reviewCriteria = reviewedAiDraft
    ? workflow.relationships
      .filter((relationship) => relationship.sourceId === block.id && (relationship.kind === "decision" || relationship.kind === "feedback"))
      .map((relationship) => `${relationship.kind === "decision" ? "Accept" : "Revise"} when: ${relationship.condition ?? relationship.label}`)
      .join("\n")
    : "";
  const performedBy = reviewedAiDraft ? "AI drafts; engineer reviews" : instruction.performedBy;
  return <section><label>Step name<input data-testid={`workflow-recovery-block-title-${block.id}`} value={title} readOnly={readOnly} onChange={(event) => setTitle(event.target.value)} /></label><div className="recovery-fact"><span>Workflow stage</span><b>{phaseName(workflow, block.phaseId)}</b></div><div className="recovery-fact"><span>Performed by</span><b>{performedBy}</b></div><label>{instruction.label}<textarea data-testid={`workflow-recovery-block-instructions-${block.id}`} value={block.instructions} readOnly /><small className="recovery-field-help">{instruction.source}</small></label>{reviewedAiDraft && <label>Engineer checklist<textarea data-testid={`workflow-recovery-block-review-${block.id}`} value={reviewCriteria} readOnly /><small className="recovery-field-help">Source: current workflow version. These criteria come from this step&apos;s accept and revise paths; they are not copied from an input document.</small></label>}{"thickness_mm" in block.configuration && <label>Thickness (mm)<input data-testid={`workflow-recovery-block-thickness-${block.id}`} type="number" min="1" value={thickness} readOnly={readOnly} onChange={(event) => setThickness(event.target.value)} /></label>}{readOnly ? <p className="recovery-inspector__hint" data-testid="workflow-recovery-candidate-readonly">The AI suggestion is read-only. Discard it or add the reviewed steps before editing the current workflow.</p> : <><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-config-apply" onClick={() => { const commands: RecoveryCommand[] = []; if (title.trim() !== block.title) commands.push({ kind: "set_block_title", blockId: block.id, title }); if (thickness && Number(thickness) !== block.configuration.thickness_mm) commands.push({ kind: "set_block_configuration", blockId: block.id, key: "thickness_mm", value: Number(thickness) }); if (commands.length > 0) onApply(commands); }}>Save step changes</button><button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-delete" onClick={onDelete}>Delete step</button><p className="recovery-inspector__hint">Saving creates a new workflow version. Disconnect dependent steps before deleting this step.</p></> }</section>;
}

function PortInspector({ direction, workflow, blockId, run, onOutput }: { readonly direction: "input" | "output"; readonly workflow: RecoveryWorkflow; readonly blockId: string | null; readonly run: RecoveryRunProjection; readonly onOutput?: () => void }) {
  const block = findBlock(workflow, blockId);
  if (!block) return <p>Select a step to see what it {direction === "input" ? "uses" : "creates"}.</p>;
  const ids = direction === "input" ? block.inputPortIds : block.outputPortIds;
  return <section>{ids.length === 0 ? <p>This step {direction === "input" ? "does not require an input" : "does not create an output"}.</p> : ids.map((id) => { const port = findPort(workflow, id)!; const artifact = workflow.artifactContracts.find((item) => item.id === port.artifactContractId); const outputReady = direction === "output" && run.outputsReady && port.id === "port.step-out"; return <article className="recovery-port-card" key={id}><header><b>{port.name}</b><span>{port.required ? "Required" : "Optional"}</span></header><p>{port.description}</p>{artifact && <small>{mediaLabel(artifact.mediaType)} · {direction === "input" ? "Used by this step" : "Created by this step"}</small>}<details className="recovery-technical-details"><summary data-testid={`workflow-recovery-port-details-${port.id}`}>Technical details</summary><code>{port.typeId}</code><code>{port.artifactContractId ?? "No stored item contract"}</code>{artifact && <code>{artifact.mediaType}</code>}</details>{outputReady && <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-artifact.step" onClick={onOutput}>Open STEP file</button>}{port.id === "port.design-intent-in" && run.state === "needs-input" && <div className="recovery-port-card__missing">! Material and temper are not stated in the design intent. Add the decision before the design specification can be accepted.</div>}</article>; })}</section>;
}

export default WorkflowRecoveryConcept;
