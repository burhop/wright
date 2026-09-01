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
    return "This bounded simulation supports the six-block mounting-bracket fixture only. Restore that topology before running.";
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
  succeed("block.capture-brief");
  if (stage === 2) {
    projection.state = "running";
    projection.activeBlockId = "block.generate-geometry";
    projection.activeRelationshipId = "rel.brief-to-geometry";
    projection.steps["block.generate-geometry"] = { state: "running", label: "Running", detail: "Generating a local bracket preview." };
  } else {
    succeed("block.generate-geometry");
  }
  if (stage === 3) {
    projection.state = "needs-input";
    projection.activeBlockId = "block.check-manufacturability";
    projection.activeRelationshipId = "rel.geometry-to-check";
    projection.steps["block.check-manufacturability"] = { state: "needs-input", label: "Needs input", detail: "Material specification is required before bend and edge checks can run." };
    for (const id of ["block.review-design", "block.export-step", "block.release-package"]) {
      projection.steps[id] = scopedStep(id, "blocked", "Blocked", "Waiting for the missing 6061-T6 material specification.");
    }
  }
  if (stage === 4) {
    projection.state = "running";
    projection.activeBlockId = "block.check-manufacturability";
    projection.activeRelationshipId = "rel.geometry-to-check";
    projection.steps["block.check-manufacturability"] = { state: "running", label: "Running", detail: "Material supplied; simulated manufacturability checks resumed." };
  }
  if (stage >= 5) succeed("block.check-manufacturability");
  if (stage === 5) {
    projection.state = "running";
    projection.activeBlockId = "block.review-design";
    projection.activeRelationshipId = "rel.report-to-review";
    projection.steps["block.review-design"] = scopedStep("block.review-design", "running", "Awaiting review", "Reviewing exact geometry and report identities.");
  }
  if (stage >= 6) succeed("block.review-design");
  if (stage === 6) {
    projection.state = "running";
    projection.activeBlockId = "block.export-step";
    projection.activeRelationshipId = "rel.review-to-export";
    projection.steps["block.export-step"] = { state: "running", label: "Running", detail: "Exporting a simulated AP242 output." };
  }
  if (stage >= 7) succeed("block.export-step");
  if (stage === 7) {
    projection.state = "running";
    projection.activeBlockId = "block.release-package";
    projection.activeRelationshipId = "rel.step-to-package";
    projection.steps["block.release-package"] = { state: "running", label: "Running", detail: "Assembling the local-only review package." };
  }
  if (stage >= 8) {
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
      upstreamContractIds: ["artifact.approved-geometry", "artifact.geometry", "artifact.manufacturability-report", "artifact.brief", "artifact.material"],
    }];
  }
  projection.activity = [
    { at: "00:00", label: "Run queued", detail: "Definition revision captured." },
    { at: "00:02", label: "Brief resolved", detail: "artifact.brief attached." },
    ...(materialSupplied ? [{ at: "00:11", label: "Input supplied", detail: "6061-T6 material specification attached by the engineer." }] : []),
  ];
  return projection;
}

function TreatmentCard({ treatment, selected, onSelect }: { readonly treatment: PortTreatment; readonly selected: boolean; readonly onSelect: () => void }) {
  const [labFeedback, setLabFeedback] = useState("Try both controls to compare connection and artifact inspection affordances.");
  const labels: Record<PortTreatment, [string, string]> = {
    dot: ["A · Round socket", "Compact, familiar graph handle; artifact action remains easy to overlook."],
    terminal: ["B · Terminal block", "Strong electrical metaphor; visually heavy at engineering-workflow scale."],
    hybrid: ["C · Hybrid terminal", "Distinct socket plus labeled artifact action and type contract."],
  };
  return (
    <article className={`port-treatment ${selected ? "is-selected" : ""}`} data-testid={`workflow-port-lab-${treatment}`}>
      <header><h3>{labels[treatment][0]}</h3>{selected && <span>SELECTED TREATMENT</span>}</header>
      <p>{labels[treatment][1]}</p>
      <div className={`port-treatment__demo port-treatment__demo--${treatment}`}>
        <button type="button" className="port-treatment__socket" data-testid={`workflow-port-lab-${treatment}-connect`} aria-label={`${treatment} connect socket`} onClick={() => setLabFeedback("Connection started from Approved geometry; choose a compatible typed input to complete it.")}>{treatment === "terminal" ? "▣" : "●"}</button>
        <div><strong>Approved geometry</strong><small>geometry.approved · required · one</small></div>
        <button type="button" className="port-treatment__artifact" data-testid={`workflow-port-lab-${treatment}-artifact`} aria-label={`${treatment} inspect artifact`} onClick={() => setLabFeedback("Artifact inspected separately: approved geometry, exact source revision, preview available.")}>▧ Inspect</button>
      </div>
      <div className="port-treatment__feedback" role="status">{labFeedback}</div>
      <div className="port-treatment__states" aria-label="Port states"><span>○ missing</span><span>⊘ incompatible</span><span>◷ pending</span><span>✓ produced</span><span>× failed</span><span>↺ stale</span></div>
      <button type="button" className="recovery-button recovery-button--secondary" data-testid={`workflow-port-lab-${treatment}-select`} onClick={onSelect}>{selected ? "Selected for concept" : "Select treatment"}</button>
    </article>
  );
}

function WorkflowRecoveryReadyConcept() {
  const [workflow, setWorkflow] = useState(() => cloneWorkflow(initialWorkflow));
  const [layout, setLayout] = useState(() => cloneLayout(initialLayout));
  const [selectedId, setSelectedId] = useState<string | null>("block.generate-geometry");
  const [view, setView] = useState<ViewMode>("diagram");
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("definition");
  const [diagnostics, setDiagnostics] = useState<RecoveryDiagnostic[]>([]);
  const initialSource = useMemo(() => formatRecoveryDsl(initialWorkflow).text, []);
  const [sourceDraft, setSourceDraft] = useState(initialSource);
  const [sourceDirty, setSourceDirty] = useState(false);
  const [undoStack, setUndoStack] = useState<Snapshot[]>([]);
  const [redoStack, setRedoStack] = useState<Snapshot[]>([]);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [briefName, setBriefName] = useState<string | null>(null);
  const [modal, setModal] = useState<"none" | "port-lab" | "brief" | "output">("none");
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
  const canRun = briefName !== null && sourceValid && !sourceDirty && proposal === null && simulationIssue === null && /^sha256:[a-f0-9]{64}$/.test(semanticDigest);
  const nextRun = () => {
    setRunOverride(null);
    setRunStage((stage) => stage === 0 ? 1 : stage === 1 ? 2 : stage === 2 ? 3 : stage === 4 ? 5 : stage === 5 ? 6 : stage === 6 ? 7 : stage === 7 ? 8 : stage);
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
      <header className="recovery-hero">
        <div>
          <div className="recovery-kicker">Canonical workflow recovery · disposable concept</div>
          <h1>Mounting bracket workflow</h1>
          <p>Block-and-flow first, with one accepted definition projected into diagram, code, inspector, AI review, and a simulated run.</p>
        </div>
        <div className="recovery-authority" data-testid="workflow-recovery-authority" data-revision={workflow.revision} data-semantic-digest={semanticDigest} data-layout-digest={layoutDigest}>
          <b>PROVISIONAL · NOT PRODUCTION</b>
          <span>Accepted definition r{workflow.revision}</span>
          <span>{sourceValid && !sourceDirty ? "✓ valid" : "! invalid source draft · last-valid graph retained"}</span>
          <span>Run authority: <strong>SIMULATED</strong></span>
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
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-validate" onClick={() => { const parsed = parseRecoveryDsl(sourceDraft); setDiagnostics(parsed.diagnostics); }}>✓ Validate</button>
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-port-lab-open" onClick={() => setModal("port-lab")}>Port lab</button>
          <button type="button" className="recovery-button recovery-button--ai" data-testid="workflow-recovery-ai-request" onClick={requestProposal}>✦ Propose with AI</button>
          <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-run-start" disabled={!canRun} title={briefName === null ? "Attach the required bracket brief before simulation." : simulationIssue ?? undefined} onClick={runStage === 0 ? startRun : undefined}>{runStage === 0 ? "▶ Simulate run" : `SIMULATED · ${run.state}`}</button>
        </div>
      </div>

      <div className="recovery-workbench">
        <aside className="recovery-palette" data-testid="workflow-recovery-palette">
          <div className="recovery-panel-heading"><span>BUILD</span><h2>Engineering blocks</h2></div>
          <label className="recovery-search">Search palette<input data-testid="workflow-recovery-palette-search" value={paletteQuery} onChange={(event) => setPaletteQuery(event.target.value)} placeholder="tolerance, drawing…" /></label>
          <div className="recovery-palette__items">
            {[{ id: "tolerance", label: "Inspect tolerances", detail: "Deterministic check" }, { id: "drawing", label: "Create drawing", detail: "Reviewable A3 output" }].filter((item) => item.label.toLowerCase().includes(paletteQuery.toLowerCase())).map((item) => (
              <button key={item.id} type="button" data-testid={`workflow-recovery-palette-item-${item.id}`} onClick={() => {
                const command = paletteBlock(item.id as "tolerance" | "drawing", 580, 650, new Set(workflow.blocks.map((block) => block.id)));
                if (applyCommands("graph", [command])) setSelectedId(command.kind === "add_block" ? command.block.id : null);
              }}><b>＋ {item.label}</b><span>{item.detail}</span></button>
            ))}
          </div>
          <section className="recovery-attachment" data-testid="workflow-recovery-attachment-artifact.brief">
            <div className="recovery-attachment__icon">PDF</div>
            {briefName === null ? <><div><b>Bracket brief</b><span>No source attached</span><small>Required human source · artifact.brief</small></div><div className="recovery-attachment__actions"><button type="button" data-testid="workflow-recovery-attachment-attach-artifact.brief" onClick={() => setBriefName("bracket-requirements-r3.pdf")}>Attach brief</button></div></> : <><div><b>Bracket brief</b><span>{briefName}</span><small>Attached · human source · artifact.brief</small></div><div className="recovery-attachment__actions">
              <button type="button" data-testid="workflow-recovery-attachment-preview-artifact.brief" onClick={() => setModal("brief")}>Preview</button>
              <button type="button" data-testid="workflow-recovery-attachment-replace-artifact.brief" onClick={() => setBriefName((name) => name?.includes("r4") ? "bracket-requirements-r3.pdf" : "bracket-requirements-r4.pdf")}>Replace</button>
            </div></>}
          </section>
          <section className="recovery-legend"><h3>Run state language</h3>{(["queued", "running", "needs-input", "succeeded", "failed", "blocked", "stale"] as RecoveryRunState[]).map((state) => <span key={state} className={`recovery-state recovery-state--${state}`}>{state === "running" ? "▶" : state === "succeeded" ? "✓" : state === "failed" ? "×" : state === "blocked" ? "⊘" : state === "stale" ? "↺" : state === "needs-input" ? "!" : "◷"} {state.replace("-", " ")}</span>)}</section>
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
            <footer><span>{sourceDirty ? "Unapplied source draft" : "Synchronized with accepted definition"}</span><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-source-apply" onClick={applySource}>Apply valid edit</button></footer>
          </section>}
          {diagnostics.length > 0 && <div className="recovery-diagnostics" role="alert">{diagnostics.map((item, index) => <article key={`${item.code}-${index}`} role={item.semanticId ? "button" : undefined} tabIndex={item.semanticId ? 0 : undefined} onClick={() => { if (item.semanticId) { setSelectedId(item.semanticId); const range = parsedSource.sourceMap[item.semanticId]; if (range && sourceRef.current) { sourceRef.current.focus(); sourceRef.current.setSelectionRange(range.startOffset, range.endOffset); } } }} onKeyDown={(event) => { if (item.semanticId && (event.key === "Enter" || event.key === " ")) event.currentTarget.click(); }} data-testid={`workflow-recovery-diagnostic-${item.code}`} data-semantic-id={item.semanticId ?? ""} data-source-line={item.line ?? ""}><b>{item.code}</b><span>{item.explanation}</span><small>Correction: {item.correction}</small></article>)}</div>}
          {runStage > 0 && <section className="recovery-runbar" data-testid="workflow-recovery-run-mode">
            <div><b>SIMULATED RUN</b><span>{run.runId} · {run.workflowId} r{run.workflowRevision} · sha256:{run.semanticSha256.slice(0, 12)}… · {run.state}</span></div>
            {run.state === "needs-input" && <button type="button" data-testid="workflow-recovery-run-recover" onClick={() => { setMaterialSupplied(true); setRunStage(4); }}>Supply 6061-T6 material</button>}
            {runStage > 0 && runStage < 8 && run.state !== "needs-input" && <button type="button" data-testid="workflow-recovery-run-advance" onClick={nextRun}>Advance simulation</button>}
            {runStage >= 6 && <button type="button" className="recovery-button--quiet" data-testid="workflow-recovery-run-project-failed" onClick={() => setRunOverride("failed")}>Project failure</button>}
            {runStage >= 6 && <button type="button" className="recovery-button--quiet" data-testid="workflow-recovery-run-project-stale" onClick={() => setRunOverride("stale")}>Project stale output</button>}
          </section>}
        </div>

        <aside className="recovery-inspector" data-testid="workflow-recovery-inspector">
          <div className="recovery-panel-heading"><span>{candidateSelection ? "INSPECT · AI CANDIDATE (READ-ONLY)" : proposal !== null ? "INSPECT · REVIEW MODE (READ-ONLY)" : "INSPECT"}</span><h2>{selectedBlock?.title ?? selectedPort?.name ?? selectedRelationship?.label ?? "Select a block"}</h2><small>{selectedId ?? "No semantic identity selected"}</small></div>
          <div className="recovery-inspector__tabs" role="tablist" aria-label="Inspector sections">
            {(["definition", "inputs", "outputs", "activity", "diagnosis"] as const).map((tab) => <button key={tab} type="button" role="tab" aria-selected={inspectorTab === tab} data-testid={`workflow-recovery-inspector-tab-${tab}`} onClick={() => setInspectorTab(tab)}>{tab[0]!.toUpperCase() + tab.slice(1)}</button>)}
          </div>
          <div className="recovery-inspector__body">
            {inspectorTab === "definition" && selectedBlock && <DefinitionInspector blockId={selectedBlock.id} workflow={inspectionWorkflow} readOnly={proposal !== null} onApply={(commands) => applyCommands("form", commands)} onDelete={() => { if (applyCommands("graph", [{ kind: "delete_block", blockId: selectedBlock.id }])) setSelectedId(null); }} />}
            {inspectorTab === "definition" && selectedRelationship && <RelationshipInspector relationshipId={selectedRelationship.id} workflow={inspectionWorkflow} readOnly={proposal !== null} onApply={(commands) => applyCommands("form", commands)} onDisconnect={() => handleIntent({ type: "delete-connection", semanticId: selectedRelationship.id })} />}
            {inspectorTab === "definition" && selectedPort && <section><div className="recovery-fact"><span>Port contract</span><b>{selectedPort.typeId}</b></div><div className="recovery-fact"><span>Direction</span><b>{selectedPort.direction}</b></div><div className="recovery-fact"><span>Requirement</span><b>{selectedPort.required ? "required" : "optional"} · {selectedPort.cardinality}</b></div><p>{selectedPort.description}</p></section>}
            {inspectorTab === "inputs" && <PortInspector direction="input" workflow={inspectionWorkflow} blockId={selectedBlock?.id ?? selectedPort?.ownerBlockId ?? null} run={run} />}
            {inspectorTab === "outputs" && <PortInspector direction="output" workflow={inspectionWorkflow} blockId={selectedBlock?.id ?? selectedPort?.ownerBlockId ?? null} run={run} onOutput={() => setModal("output")} />}
            {inspectorTab === "activity" && <section>{run.activity.length === 0 ? <p>No simulated activity yet.</p> : run.activity.map((item) => <div className="recovery-activity" key={`${item.at}-${item.label}`}><time>{item.at}</time><div><b>{item.label}</b><span>{item.detail}</span></div></div>)}{selectedStep && <div className={`recovery-run-detail recovery-run-detail--${selectedStep.state}`} data-testid={`workflow-recovery-run-step-${selectedBlock?.id}`}><b>{selectedStep.label}</b><span>{selectedStep.detail}</span></div>}</section>}
            {inspectorTab === "diagnosis" && <section><div className="recovery-diagnosis"><b>{run.state === "needs-input" ? "Material input is missing" : run.state === "failed" ? "Simulated export failed" : run.state === "stale" ? "Output revision is stale" : "No unresolved diagnosis"}</b><p>{run.state === "needs-input" ? "Manufacturability evidence cannot be trusted without material and temper. Review, export, and packaging remain blocked." : "This projection is isolated from the accepted definition."}</p></div><button type="button" data-testid="workflow-recovery-diagnosis-show-failed" onClick={() => setRunOverride("failed")}>Show failed projection</button><button type="button" data-testid="workflow-recovery-diagnosis-show-stale" onClick={() => setRunOverride("stale")}>Show stale projection</button></section>}
          </div>
          {selectedBlock?.bindingId && <details className="recovery-binding"><summary data-testid="workflow-recovery-binding-disclosure">Implementation binding · progressive disclosure</summary>{(() => { const binding = inspectionWorkflow.bindings.find((item) => item.id === selectedBlock.bindingId); return binding ? <div><code>{binding.id}</code><span>{binding.kind} · {binding.capabilityName}</span><span>{binding.serverId ?? "internal"} / {binding.toolId}</span><span>Schema {binding.schemaDigest}</span><span>Approval: {binding.approvalPolicy}</span><b>Exact argument map</b>{binding.argumentMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}<b>Exact result map</b>{binding.resultMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}</div> : null; })()}</details>}
        </aside>
      </div>

      {proposal && proposalResult && <section className="recovery-proposal" data-testid="workflow-recovery-proposal" data-base-revision={proposal.baseRevision} data-validation={proposalResult.ok ? "valid" : "invalid"}>
        <header><div><span>AI CANDIDATE · REVIEW REQUIRED</span><h2>Add drawing creation and review</h2></div><b>{proposalResult.ok ? "✓ structurally valid" : "! invalid"}</b></header>
        <div className="recovery-proposal__grid"><div><h3>Assumptions</h3><ul><li>Approved geometry is the authoritative drawing source.</li><li>ASME Y14.5 and A3 are reviewable defaults, not hidden commitments.</li></ul><h3>Warnings</h3><ul><li>No drawing-template binding is selected.</li><li>Acceptance does not execute or approve anything.</li></ul></div><div><h3>Semantic diff</h3>{proposalResult.diff.map((line) => <p key={line}>＋ {line}</p>)}</div><div className="recovery-proposal__preview" data-testid="workflow-recovery-proposal-preview"><h3>Graphical candidate</h3><span>The main canvas now projects the full candidate; added blocks are dashed and marked AI CANDIDATE.</span><b>Approved geometry ┄▷ Create inspection drawing</b><b>Inspection drawing ┄▷ Review inspection drawing</b><small>Candidate projection · not part of accepted definition</small><details><summary data-testid="workflow-recovery-proposal-code-disclosure">Candidate Code projection</summary><pre>{proposalResult.workflow ? formatRecoveryDsl(proposalResult.workflow).text : "Invalid candidate"}</pre></details></div></div>
        <footer><button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-proposal-reject" onClick={() => { setProposal(null); setProposalResult(null); }}>Reject · no definition change</button><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-proposal-accept" disabled={!proposalResult.ok} onClick={() => { if (applyBatch(proposal)) { setProposal(null); setProposalResult(null); } }}>Accept reviewed diff</button></footer>
      </section>}

      {modal !== "none" && <div className="recovery-modal-backdrop" data-testid="workflow-recovery-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal("none"); }} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); setModal("none"); return; } if (event.key === "Tab" && modalRef.current) { const focusable = [...modalRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]; if (focusable.length === 0) return; const first = focusable[0]!; const last = focusable.at(-1)!; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } } }}><section ref={modalRef} className={`recovery-modal recovery-modal--${modal}`} role="dialog" aria-modal="true" aria-labelledby="recovery-modal-title">
        <header><div><span>DISPOSABLE RESEARCH SURFACE</span><h2 id="recovery-modal-title">{modal === "port-lab" ? "Port interaction lab" : modal === "brief" ? "Bracket brief preview" : "Mounting bracket STEP output"}</h2></div><button type="button" data-testid="workflow-recovery-modal-close" aria-label="Close dialog" onClick={() => setModal("none")}>×</button></header>
        {modal === "port-lab" && <div data-testid="workflow-port-lab"><p className="recovery-modal__lead">Compare how an engineer connects typed data and separately inspects the artifact. The chosen treatment must make both actions unmistakable.</p><div className="port-lab-grid"><TreatmentCard treatment="dot" selected={portTreatment === "dot"} onSelect={() => setPortTreatment("dot")} /><TreatmentCard treatment="terminal" selected={portTreatment === "terminal"} onSelect={() => setPortTreatment("terminal")} /><TreatmentCard treatment="hybrid" selected={portTreatment === "hybrid"} onSelect={() => setPortTreatment("hybrid")} /></div><div className="port-lab-result"><b>Current concept treatment: {portTreatment}</b><span>Human product approval remains required; selection here changes only the disposable visual treatment.</span></div></div>}
        {modal === "brief" && briefName !== null && <div className="brief-preview"><div className="brief-preview__sheet"><span>WRIGHT / REQUIREMENT BASIS</span><h3>L-bracket mounting interface</h3><div className="bracket-sketch">┌──────────── 120 mm ────────────┐<br />│ ○　　　　　　　　　　　　○ │<br />│　　　　　60 × 40　　　　　 │<br />└────────────┐<br />　　　　　　│　○　 slot 24 × 8<br />　　　　　　└──────── 80 mm</div><dl><dt>Material</dt><dd>6061-T6 aluminium</dd><dt>Thickness</dt><dd>6 mm</dd><dt>Design load</dt><dd>1.8 kN static</dd></dl></div><aside><b>{briefName}</b><span>application/pdf</span><span>Human-attached source</span><span>Used by Generate bracket geometry</span></aside></div>}
        {modal === "output" && <div className="output-preview"><img src={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.svg`} alt="Isometric L-shaped mounting bracket with four holes" /><aside><b>mounting-bracket-simulated-fixture.step</b><span>artifact.step · STEP AP242</span><span>Static illustrative fixture referenced by block.export-step; these bytes were not generated by the simulated run.</span><span>Run {run.runId} · immutable {run.workflowId} r{run.workflowRevision}</span><span>Definition sha256:{run.semanticSha256}</span>{stepArtifact && <><span>Fixture record {stepArtifact.recordId}</span><span>Fixture sha256:{stepArtifact.digestSha256}</span></>}<div className="recovery-lineage" data-testid="workflow-recovery-output-lineage"><b>Declared upstream lineage</b><span>artifact.step</span><span>← artifact.approved-geometry + review decision</span><span>← artifact.geometry + artifact.manufacturability-report</span><span>← artifact.brief + artifact.material (6061-T6)</span></div><div><a className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-output-open-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/manufacturability-report.html`} target="_blank" rel="noreferrer">Open report fixture</a><a className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-download-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.step`} download="mounting-bracket-simulated-fixture.step">Download STEP fixture</a></div></aside></div>}
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
  return <section><div className="recovery-fact"><span>Relationship</span><b>{relationship.kind}</b></div><div className="recovery-fact"><span>From</span><b>{relationship.sourceId}</b></div><label>Relationship label<input data-testid={`workflow-recovery-relationship-label-${relationship.id}`} value={label} readOnly={readOnly} onChange={(event) => setLabel(event.target.value)} /></label>{blockRelationship ? <label>Outcome target<select data-testid={`workflow-recovery-relationship-target-${relationship.id}`} value={targetId} disabled={readOnly} onChange={(event) => setTargetId(event.target.value)}>{workflow.blocks.map((block) => <option key={block.id} value={block.id}>{block.title} · {block.id}</option>)}</select></label> : <div className="recovery-fact"><span>To</span><b>{relationship.targetId}</b></div>}<label>Condition or reason<textarea data-testid={`workflow-recovery-relationship-condition-${relationship.id}`} value={condition} readOnly={readOnly} onChange={(event) => setCondition(event.target.value)} /></label>{readOnly ? <p className="recovery-inspector__hint">Candidate relationships are inspection-only until the reviewed diff is accepted.</p> : <><button type="button" className="recovery-button recovery-button--primary" data-testid={`workflow-recovery-relationship-apply-${relationship.id}`} onClick={() => { const patch: Partial<Pick<typeof relationship, "targetId" | "label" | "condition">> = {}; if (label.trim() !== relationship.label) patch.label = label.trim(); if ((condition.trim() || null) !== relationship.condition) patch.condition = condition.trim() || null; if (blockRelationship && targetId !== relationship.targetId) patch.targetId = targetId; if (Object.keys(patch).length > 0) onApply([{ kind: "update_relationship", relationshipId: relationship.id, patch }]); }}>Apply relationship change</button><button type="button" className="recovery-button recovery-button--danger" data-testid={`workflow-recovery-disconnect-${relationship.id}`} onClick={onDisconnect}>Disconnect relationship</button></>}</section>;
}

function DefinitionInspector({ blockId, workflow, readOnly, onApply, onDelete }: { readonly blockId: string; readonly workflow: RecoveryWorkflow; readonly readOnly: boolean; readonly onApply: (commands: RecoveryCommand[]) => void; readonly onDelete: () => void }) {
  const block = findBlock(workflow, blockId)!;
  const [title, setTitle] = useState(block.title);
  const [thickness, setThickness] = useState(String(block.configuration.thickness_mm ?? ""));
  useEffect(() => { setTitle(block.title); setThickness(String(block.configuration.thickness_mm ?? "")); }, [block.id, block.title, block.configuration.thickness_mm]);
  return <section><label>Friendly block name<input data-testid={`workflow-recovery-block-title-${block.id}`} value={title} readOnly={readOnly} onChange={(event) => setTitle(event.target.value)} /></label><div className="recovery-fact"><span>Phase</span><b>{phaseName(workflow, block.phaseId)}</b></div><div className="recovery-fact"><span>Execution</span><b>{block.executionKind.replace("_", " ")}</b></div><label>Instructions<textarea data-testid={`workflow-recovery-block-instructions-${block.id}`} value={block.instructions} readOnly /></label>{"thickness_mm" in block.configuration && <label>Thickness (mm)<input data-testid={`workflow-recovery-block-thickness-${block.id}`} type="number" min="1" value={thickness} readOnly={readOnly} onChange={(event) => setThickness(event.target.value)} /></label>}{readOnly ? <p className="recovery-inspector__hint" data-testid="workflow-recovery-candidate-readonly">Review mode is read-only. Reject the candidate or accept its reviewed diff before editing the accepted definition.</p> : <><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-config-apply" onClick={() => { const commands: RecoveryCommand[] = []; if (title.trim() !== block.title) commands.push({ kind: "set_block_title", blockId: block.id, title }); if (thickness && Number(thickness) !== block.configuration.thickness_mm) commands.push({ kind: "set_block_configuration", blockId: block.id, key: "thickness_mm", value: Number(thickness) }); if (commands.length > 0) onApply(commands); }}>Apply definition change</button><button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-delete" onClick={onDelete}>Delete selected block</button><p className="recovery-inspector__hint">One reviewed command batch → one accepted semantic revision. Connected blocks fail closed until dependencies are disconnected.</p></> }</section>;
}

function PortInspector({ direction, workflow, blockId, run, onOutput }: { readonly direction: "input" | "output"; readonly workflow: RecoveryWorkflow; readonly blockId: string | null; readonly run: RecoveryRunProjection; readonly onOutput?: () => void }) {
  const block = findBlock(workflow, blockId);
  if (!block) return <p>Select a block to inspect its {direction}s.</p>;
  const ids = direction === "input" ? block.inputPortIds : block.outputPortIds;
  return <section>{ids.length === 0 ? <p>No {direction} ports.</p> : ids.map((id) => { const port = findPort(workflow, id)!; const artifact = workflow.artifactContracts.find((item) => item.id === port.artifactContractId); const outputReady = direction === "output" && run.outputsReady && port.id === "port.step-out"; return <article className="recovery-port-card" key={id}><header><b>{port.name}</b><span>{port.required ? "required" : "optional"} · {port.cardinality}</span></header><code>{port.typeId}</code><p>{port.description}</p>{artifact && <small>{artifact.name} · {artifact.mediaType}</small>}{outputReady && <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-artifact.step" onClick={onOutput}>Open STEP output</button>}{port.id === "port.material-in" && run.state === "needs-input" && <div className="recovery-port-card__missing">! Missing · blocks trustworthy manufacturability evidence</div>}</article>; })}</section>;
}

export default WorkflowRecoveryConcept;
