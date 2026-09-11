import { createMcpServerBlock } from "./mcp-server-blocks";
import { disconnectedProcessDiagnostic } from "./run-readiness";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";

import type { DraftCanvasIntent } from "../../components/workflow-composer/draft-intents";
import {
  acceptRecoveryResult,
  aiDrawingProposal,
  applyRecoveryBatch,
  recoveryCommandBatch,
  textEditCommands,
  type RecoveryCommand,
  type RecoveryCommandBatch,
} from "./command-system";
import {
  cloneLayout,
  recoveryAuthoringSectionKind,
  cloneWorkflow,
  findBlock,
  findPort,
  initialRunProjection,
  initialWorkflow,
  resolveRecoveryComponentScope,
  toDraftProjection,
  type RecoveryDiagnostic,
  type RecoveryLayout,
  type RecoveryRunProjection,
  type RecoveryRunState,
  type RecoveryWorkflow,
} from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  recoveryAuthoringSemanticIdAtOffset,
  recoveryAuthoringSourceSelection,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";
import {
  ReactFlowRecoveryCanvas,
  RecoveryCanvasRuntimeProvider,
} from "./ReactFlowRecoveryCanvas";
import { canonicalDefinitionBytes, canonicalLayoutBytes, canonicalLayoutPositionBytes } from "./canonical-wire";
import { AuthoringCreateRail, AuthoringInputsNavigator, AuthoringSettings, AuthoringPortConnections, type AuthoringWorkspaceFile } from "./AuthoringControls";
import { authoringDeletionImpact, authoringReadiness, buildDeletionCommands, canConnectAuthoringPorts, createAuthoringObject, hydrateAuthoringLayout, singleImageInputCorrections } from "./authoring-objects";
import { recoveryBlockIconKinds } from "./WorkflowObjectIcon";
import { McpBlockEditor } from "./McpBlockEditor";
import { connectMcpInput, isMcpBlock, mcpCandidates, hiddenMcpInputs } from "./mcp-settings";
import { InputBlockEditor } from "./InputBlockEditor";
import { PromptBlockEditor } from "./PromptBlockEditor";
import { connectPromptCommands, isPromptBlock, promptSourceCandidates, sourceKey } from "./prompt-settings";
import type { WorkspaceWorkflowOutput, WorkspaceWorkflowRunEvent, WorkspaceWorkflowStep, WorkspaceEngineeringResult, WorkspaceWorkflowReview, WorkspaceWorkflowRunSummary } from "../../services/workspace-service";
import { WorkflowReviewPanel, useWorkflowReviews } from "./WorkflowReviewPanel";
import { WorkflowRunHistory } from "./WorkflowRunHistory";
import { preferObservedRun, useWorkflowRunObserver } from "./useWorkflowRunObserver";
import { engineeringConnectionIssue,useEngineeringConnectionCapabilities } from "./engineering-connections";
import { applicationConnectionCommands,applicationPortId } from "./ApplicationTaskOptions";
import { cadCommands,cadPortId,type CadOptions } from "./CadTaskOptions";
import { EngineeringResults } from "./EngineeringResults";
import { BlockNameHeading } from "./BlockNameHeading";
import { cadOutputPresentation } from "./cad-output-presentation";
import { workspaceContentUrl } from "../../services/viewer-panel/providers/workspace-content-url";
import "./workflow-recovery.css";

type ViewMode = "diagram" | "code" | "split";
type InspectorTab = "overview" | "definition" | "inputs" | "outputs" | "activity" | "diagnosis";
type PortTreatment = "dot" | "terminal" | "hybrid";

const inspectorTabLabel: Record<InspectorTab, string> = {
  overview: "Overview",
  definition: "Settings",
  inputs: "Inputs",
  outputs: "Outputs",
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

interface PersistedRunSubject {
  workflow: RecoveryWorkflow;
  storageDigest: string;
}

interface CapturedRunSubject extends PersistedRunSubject {
  semanticSha256: string;
}

export interface WorkflowRecoveryPersistedSource {
  readonly source: string;
  readonly definition_revision: number;
  readonly storage_digest: string;
  readonly layout?: RecoveryLayout | null;
}

export interface WorkflowRecoveryConceptProps {
  /** Internal component demonstrations only; workspace pages must not enable this. */
  readonly simulationPreview?: boolean;
  readonly surfaceState?: "ready" | "loading" | "error";
  readonly onRetry?: () => void;
  readonly workflowSource?: string;
  readonly definitionRevision?: number;
  readonly storageDigest?: string;
  readonly workflowFilePath?: string;
  readonly reopenRequest?: number;
  readonly workflowLayout?: RecoveryLayout;
  readonly workspaceSessionId?: string;
  readonly workspaceId?: string;
  readonly onSave?: (source: string, layout: RecoveryLayout) => Promise<WorkflowRecoveryPersistedSource>;
  readonly onListWorkspaceFiles?: () => Promise<AuthoringWorkspaceFile[]>;
  readonly onReadStoredSource?: () => Promise<WorkflowRecoveryStoredSource>;
  readonly onReloadStoredSource?: (canReplace?: (stored: WorkflowRecoveryStoredSource) => boolean) => Promise<void>;
  readonly onOpenFile?: (path: string) => void;
  readonly fileActions?: ReactNode;
  readonly onRun?: (options?: WorkflowRunOptions) => Promise<WorkflowRecoveryRunResult>;
}

export interface WorkflowRunOptions { signal?: AbortSignal; expectedStorageDigest?: string; onEvent?: (event: WorkspaceWorkflowRunEvent) => void }

export interface WorkflowRecoveryRunResult {
  readonly status?: "completed" | "pending_review";
  readonly review?: WorkspaceWorkflowReview;
  readonly runLogPath?: string;
  readonly outputPath: string;
  readonly outputBytes: number;
  readonly taskTitle: string;
  readonly taskId?: string;
  readonly workflowTitle?: string;
  readonly outputs?: WorkspaceWorkflowOutput[];
  readonly results?: WorkspaceEngineeringResult[];
  readonly steps?: WorkspaceWorkflowStep[];
}

interface NativeRunEvent {
  readonly at: string;
  readonly label: string;
  readonly detail: string;
}

interface NativeRunInput {
  readonly executionKind?: "ai" | "mcp" | "mcp_task";
  readonly prompt: string;
  readonly taskTitle: string;
  readonly workflowPath: string;
  readonly storageDigest?: string;
  readonly formatInstructions?: string;
}

function reviewRunPresentation(reviews: readonly WorkspaceWorkflowReview[], result: WorkflowRecoveryRunResult | null, error: string) {
  // A fresh execution result/error takes precedence over unrelated historical reviews.
  if (error || (result && !result.review)) return null;
  const review = result?.review
    ? reviews.find(item => item.review_id === result.review!.review_id) ?? result.review
    : reviews[0]; // The scoped review API returns newest first.
  if (!review) return null;
  const label = {pending: "Awaiting your review", approved: "Review approved", changes_requested: "Changes requested"}[review.state];
  const detail = review.evidence_status === "stale"
    ? "The recorded review applies to its original package. Evidence has changed; create a new run for a current review."
    : review.state === "pending"
      ? "Open the saved document and record your decision below."
      : review.state === "approved"
        ? "Your approval is recorded for the saved review package."
        : "Your change request is recorded for the saved review package. See the review notes below.";
  return {label, detail};
}

function NativeRunPanel({
  reviews,
  pending,
  result,
  error,
  prompt,
  taskTitle,
  executionKind,
  workflowPath,
  workspaceSessionId,
  storageDigest,
  startedAt,
  completedAt,
  events,
  partialResults,
  runLogPath,
  onOpenFile,
  observed,
  statusPresentation,
  sourceMismatch,
  refreshError,
  onRefresh,
}: {
  readonly reviews: ReturnType<typeof useWorkflowReviews>;
  readonly pending: boolean;
  readonly result: WorkflowRecoveryRunResult | null;
  readonly error: string;
  readonly prompt: string;
  readonly taskTitle: string;
  readonly executionKind?: "ai" | "mcp" | "mcp_task";
  readonly workflowPath: string;
  readonly workspaceSessionId?: string;
  readonly storageDigest?: string;
  readonly startedAt: string;
  readonly completedAt: string;
  readonly events: readonly NativeRunEvent[];
  readonly partialResults: WorkspaceEngineeringResult[];
  readonly runLogPath: string;
  readonly onOpenFile?: (path: string) => void;
  readonly observed?: WorkspaceWorkflowRunSummary | null;
  readonly statusPresentation?: {label:string;detail:string} | null;
  readonly sourceMismatch?: boolean;
  readonly refreshError?: string;
  readonly onRefresh?: () => void;
}) {
  const reviewPresentation = reviewRunPresentation(reviews.reviews, result, error);
  const [now,setNow]=useState(Date.now);
  useEffect(() => { if (!pending) return; const timer=setInterval(() => setNow(Date.now()),1000); return () => clearInterval(timer); },[pending]);
  const durationMs = startedAt && (completedAt || pending)
    ? Math.max(0, (completedAt ? Date.parse(completedAt) : now) - Date.parse(startedAt))
    : null;
  return <section className="recovery-runbar recovery-native-run" data-testid="workflow-recovery-native-run-mode">
    <div className="recovery-native-run__summary" data-testid="workflow-native-run-summary" aria-live="polite">
      <b>{statusPresentation ? statusPresentation.label : pending ? "Workflow running" : reviewPresentation ? reviewPresentation.label : result ? "Workflow completed" : error ? error.startsWith("Workflow cancelled.") ? "Workflow cancelled" : "Workflow failed" : "Ready to run"}</b>
      <span>{statusPresentation ? statusPresentation.detail : pending ? `${taskTitle}: ${events.at(-1)?.label ?? "Starting"}.` : reviewPresentation ? reviewPresentation.detail : result ? result.results?.length ? `${result.results.length} engineering result(s) ready.` : `${result.outputs?.length ?? 1} output file(s) ready in this workspace.` : error || "Run the saved workflow to create its responses and output files."}</span>
    </div>
    {refreshError && <div role="alert" data-testid="workflow-run-refresh-error"><p>Execution status could not be refreshed. The last known status is retained. {refreshError}</p><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-run-refresh" onClick={onRefresh}>Refresh status</button></div>}
    {sourceMismatch && <p role="status" data-testid="workflow-run-source-mismatch">This run uses a different saved definition or your current draft has edits. Run details and output links belong to that recorded run; graph activity is hidden.</p>}
    {observed?.execution && <p data-testid="workflow-run-observed-metrics">Observed execution · {observed.execution.model_call_count} model calls · {observed.execution.tool_call_count} tool calls started · {observed.execution.tool_completed_count} tool calls finished · {observed.execution.event_count} events{observed.execution.revision_count ? ` · ${observed.execution.revision_count} design revisions` : ""}{durationMs !== null ? ` · ${(durationMs/1000).toFixed(1)} s` : ""}{observed.execution.truncated ? " · Open the saved log for full evidence." : ""}</p>}
    {reviews.error && <div role="alert"><p>{reviews.error}</p><button type="button" className="recovery-button recovery-button--secondary" onClick={reviews.refresh}>Refresh reviews</button></div>}
    {workspaceSessionId && reviews.reviews.map(review => <WorkflowReviewPanel key={`${review.review_id}-${review.state}`} review={review} sessionId={workspaceSessionId} onOpenFile={onOpenFile} onUpdate={reviews.update} onRefresh={reviews.refresh}/>)}
    {result?.results?.length ? <EngineeringResults results={result.results} onOpenFile={onOpenFile}/> : (result?.outputs ?? (result ? [{ task_id: result.taskId ?? "", task_title: result.taskTitle, output_path: result.outputPath, output_bytes: result.outputBytes, output_format: "" }] : [])).map((output) => <p className="recovery-native-run__output" key={`${output.task_id}-${output.output_path}`}><span><b>{output.output_path}</b> · {output.output_bytes.toLocaleString("en-US")} bytes<br /><small>{output.task_title}{output.cad_role === "native" ? " · Native model" : output.cad_role === "export" ? " · CAD export" : ""}</small></span>{onOpenFile ? <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-native-run-output-link" onClick={() => onOpenFile(output.output_path)}>Open {output.output_path}</button> : workspaceSessionId ? <a className="recovery-button recovery-button--primary" data-testid="workflow-recovery-native-run-output-link" href={workspaceContentUrl(output.output_path, workspaceSessionId)} target="_blank" rel="noreferrer">Open {output.output_path}</a> : "Open the file in the workspace file browser."}</p>)}
    {!result && partialResults.length > 0 && <section data-testid="workflow-recovery-partial-results"><h3>Results produced so far</h3><EngineeringResults results={partialResults} onOpenFile={onOpenFile}/></section>}
    {!result?.results?.length && result?.steps?.filter(step => step.cad_document).map(step => <p key={step.task_id} data-testid="workflow-recovery-cad-result"><b>{step.cad_document!.displayName}</b> · {step.cad_document!.isDirty ? "Open model · unsaved changes" : "Open model · saved"}<br /><small>{step.task_title} · CAD model available to connected steps</small></p>)}
    {startedAt && !observed && <section className="recovery-native-run__input" data-testid="workflow-recovery-native-run-input">
      {result?.steps?.length ? result.steps.map((step) => <details key={step.task_id}><summary data-testid={`workflow-recovery-run-prompt-${step.task_id}`}>{step.task_title} · {step.execution_kind === "mcp" ? "Tool inputs and result" : "Prompt and response"}</summary>{step.execution_kind === "mcp" ? <><h3>{step.tool}</h3><pre>{JSON.stringify(step.arguments, null, 2)}</pre></> : <><h3>Prompt sent</h3><pre>{step.prompt}</pre><h3>Format instructions</h3><pre>{step.format_instructions}</pre></>}<h3>Response</h3><pre>{step.response}</pre>{step.tool_calls && <details><summary>Tool calls · {step.tool_calls.length}</summary><pre>{JSON.stringify(step.tool_calls, null, 2)}</pre></details>}</details>) : <><h2>{executionKind === "mcp" ? "Tool inputs for" : "Prompt sent to"} {taskTitle}</h2><p>{prompt || "Preparing the saved inputs…"}</p></>}
    </section>}
    <details className="recovery-technical-details recovery-native-run__log" open={pending} data-testid="workflow-recovery-native-run-log">
      <summary>Technical log and telemetry</summary>
      {(result?.runLogPath || runLogPath) && onOpenFile && <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-open-run-record" onClick={() => onOpenFile(result?.runLogPath || runLogPath)}>Open saved run log</button>}
      <ol>
        {events.map((event, index) => <li key={`${event.at}-${event.label}-${index}`}><time dateTime={event.at}>{new Date(event.at).toLocaleTimeString()}</time><div><b>{event.label}</b><span>{event.detail}</span></div></li>)}
      </ol>
      <div className="recovery-native-run__metadata">
        <span>Workflow source: <code>{workflowPath}</code></span>
        {storageDigest && <span>Saved source digest: <code>{storageDigest}</code></span>}
        {result?.taskId && <span>Task: <code>{result.taskId}</code></span>}
        {durationMs !== null && <span>Elapsed: {durationMs.toLocaleString("en-US")} ms</span>}
      </div>
      <small>Recorded workflow events and request details.</small>
    </details>
    <WorkflowRunHistory sessionId={workspaceSessionId} path={workflowPath} refreshKey={completedAt} onOpenFile={onOpenFile}/>
  </section>;
}

export interface WorkflowRecoveryStoredSource {
  readonly source: string;
  readonly definition_revision: number;
  readonly storage_revision?: number;
  readonly storage_digest?: string;
  readonly layout?: RecoveryLayout | null;
}

export function WorkflowRecoveryConcept({
  simulationPreview = false,
  surfaceState = "ready",
  onRetry = () => undefined,
  workflowSource = formatRecoveryAuthoringSource(initialWorkflow).text,
  definitionRevision = initialWorkflow.revision,
  storageDigest,
  workflowFilePath = "workflows/mounting-bracket.workflow.wflow",
  reopenRequest = 0,
  workflowLayout,
  workspaceSessionId,
  workspaceId,
  onSave,
  onListWorkspaceFiles,
  onReadStoredSource,
  onReloadStoredSource,
  onRun,
  onOpenFile,
  fileActions,
}: WorkflowRecoveryConceptProps = {}) {
  if (surfaceState === "loading") {
    return <section className="workflow-recovery recovery-boundary-state" data-testid="workflow-recovery-concept" data-surface-state="loading" aria-busy="true"><b>Loading workflow editor…</b><span>The accepted workflow file is not available yet.</span></section>;
  }
  if (surfaceState === "error") {
    return <section className="workflow-recovery recovery-boundary-state" data-testid="workflow-recovery-concept" data-surface-state="error" role="alert"><b>Workflow could not be loaded.</b><span>The accepted workflow was not changed.</span><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-boundary-retry" onClick={onRetry}>Retry workflow load</button></section>;
  }
  const loaded = workflowFromSource(workflowSource, definitionRevision);
  if (!loaded.ok || loaded.workflow === null) {
    const issue = loaded.diagnostics[0];
    return <section className="workflow-recovery recovery-boundary-state" data-testid="workflow-recovery-concept" data-surface-state="invalid-source" role="alert"><b>Workflow file needs correction.</b><span>{issue?.explanation ?? "The saved engineering source is invalid."}</span><small>{issue?.code ?? "WFR-SOURCE-INVALID"} · The accepted diagram was not replaced with fallback content.</small></section>;
  }
  return <WorkflowRecoveryReadyConcept simulationPreview={simulationPreview} loadedWorkflow={loaded.workflow} workflowSource={workflowSource} definitionRevision={definitionRevision} storageDigest={storageDigest} workflowFilePath={workflowFilePath} reopenRequest={reopenRequest} workflowLayout={workflowLayout} workspaceSessionId={workspaceSessionId} workspaceId={workspaceId} onSave={onSave} onListWorkspaceFiles={onListWorkspaceFiles} onReadStoredSource={onReadStoredSource} onReloadStoredSource={onReloadStoredSource} onRun={onRun} onOpenFile={onOpenFile} fileActions={fileActions} />;
}

function contentIdentity(workflow: RecoveryWorkflow): string {
  return canonicalDefinitionBytes(workflow, true);
}

function proposalChangeSummaries(batch: RecoveryCommandBatch, candidate: RecoveryWorkflow): string[] {
  const endpointName = (semanticId: string) => {
    const block = findBlock(candidate, semanticId);
    if (block) return block.title;
    const port = findPort(candidate, semanticId);
    const owner = port ? findBlock(candidate, port.ownerBlockId) : null;
    return port ? `${owner?.title ?? "Workflow step"}: ${port.name}` : "Workflow endpoint";
  };
  const settings = (block: RecoveryWorkflow["blocks"][number]) => Object.entries(block.configuration)
    .map(([key, value]) => `${key.replace(/_/g, " ")} ${String(value)}`)
    .join(", ");
  return batch.commands.map((command) => {
    if (command.kind === "add_block") return `Add step: ${command.block.title}${settings(command.block) ? ` · ${settings(command.block)}` : ""}`;
    if (command.kind === "connect") return `Connect ${endpointName(command.relationship.sourceId)} to ${endpointName(command.relationship.targetId)} · ${command.relationship.label}`;
    if (command.kind === "disconnect") return "Disconnect a reviewed workflow connection";
    if (command.kind === "set_block_title") return `Rename step to ${command.title}`;
    if (command.kind === "set_block_configuration") return `Change ${command.key.replace(/_/g, " ")} to ${String(command.value)}`;
    if (command.kind === "set_artifact_definition") return `Update engineering item: ${command.patch.name ?? "description"}`;
    if (command.kind === "update_relationship") return `Update workflow connection${command.patch.label ? `: ${command.patch.label}` : ""}`;
    return "Update reviewed workflow settings";
  });
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
  const reviewScope = subject.blocks.some((block) => block.id === "block.review-design")
    ? resolveRecoveryComponentScope(subject, "block.review-design", "component.review-cell.block.evaluate")
    : undefined;
  projection.steps = Object.fromEntries(order.map((id) => [id, {
    state: "idle" as const,
    label: "Not started",
    detail: "Waiting for the simulated run.",
    ...(id === "block.review-design" && reviewScope ? { componentScope: reviewScope } : {}),
  }]));
  const scopedStep = (id: string, state: RecoveryRunState, label: string, detail: string) => ({
    state,
    label,
    detail,
    ...(id === "block.review-design" && reviewScope ? { componentScope: reviewScope } : {}),
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

function workflowFromSource(source: string, definitionRevision: number): ReturnType<typeof parseRecoveryAuthoringSource> {
  const base = cloneWorkflow(initialWorkflow);
  // At the file-open boundary the public workflow declaration establishes this
  // document's identity. Subsequent Source edits still parse against its accepted
  // base and cannot silently rename that identity. File name is not identity.
  const declarations = [...source.matchAll(/^workflow ([a-z][a-z0-9_]*)\s*$/gm)];
  if (declarations.length === 1) base.workflowId = `workflow.${declarations[0]![1]!.replaceAll("_", "-")}`;
  base.revision = definitionRevision;
  base.parentRevision = definitionRevision > 1 ? definitionRevision - 1 : null;
  return parseRecoveryAuthoringSource(source, base);
}

function persistedRunSubject(workflow: RecoveryWorkflow, storageDigest: string | undefined): PersistedRunSubject | null {
  if (!storageDigest || !/^[a-f0-9]{64}$/.test(storageDigest)) return null;
  return { workflow: cloneWorkflow(workflow), storageDigest };
}

function runDefinitionLockDiagnostic(): RecoveryDiagnostic {
  return {
    code: "WFR-RUN-DEFINITION-LOCKED",
    semanticId: null,
    line: null,
    explanation: "This workflow test is bound to the saved definition that started it, so the definition cannot change while the test remains open.",
    correction: "End the current test before changing steps, connections, source, history, or AI suggestions. Canvas layout moves remain available.",
  };
}

interface WorkflowRecoveryReadyConceptProps {
  readonly simulationPreview: boolean;
  readonly loadedWorkflow: RecoveryWorkflow;
  readonly workflowSource: string;
  readonly definitionRevision: number;
  readonly storageDigest?: string;
  readonly workflowFilePath: string;
  readonly reopenRequest: number;
  readonly workflowLayout?: RecoveryLayout;
  readonly workspaceSessionId?: string;
  readonly workspaceId?: string;
  readonly onSave?: (source: string, layout: RecoveryLayout) => Promise<WorkflowRecoveryPersistedSource>;
  readonly onListWorkspaceFiles?: () => Promise<AuthoringWorkspaceFile[]>;
  readonly onReadStoredSource?: () => Promise<WorkflowRecoveryStoredSource>;
  readonly onReloadStoredSource?: (canReplace?: (stored: WorkflowRecoveryStoredSource) => boolean) => Promise<void>;
  readonly onOpenFile?: (path: string) => void;
  readonly fileActions?: ReactNode;
  readonly onRun?: (options?: WorkflowRunOptions) => Promise<WorkflowRecoveryRunResult>;
}

function WorkflowRecoveryReadyConcept({ simulationPreview, loadedWorkflow, workflowSource, definitionRevision, storageDigest, workflowFilePath, reopenRequest, workflowLayout, workspaceSessionId, workspaceId, onSave, onListWorkspaceFiles, onReadStoredSource, onReloadStoredSource, onRun, onOpenFile, fileActions }: WorkflowRecoveryReadyConceptProps) {
  const loadedDocumentKeyRef = useRef(`${definitionRevision}\u0000${storageDigest ?? ""}\u0000${workflowSource}`);
  const [workflow, setWorkflow] = useState(() => loadedWorkflow);
  const connectionCapabilities=useEngineeringConnectionCapabilities(workflow,workspaceSessionId);
  const [layout, setLayout] = useState(() => hydrateAuthoringLayout(loadedWorkflow, workflowLayout));
  const [savedLayoutIdentity, setSavedLayoutIdentity] = useState(() => canonicalLayoutPositionBytes(hydrateAuthoringLayout(loadedWorkflow, workflowLayout)));
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [view, setView] = useState<ViewMode>("diagram");
  const [inspectorTab, setInspectorTab] = useState<InspectorTab>("overview");
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [runDetailsOpen, setRunDetailsOpen] = useState(false);
  const [focusPath, setFocusPath] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [diagnostics, setDiagnostics] = useState<RecoveryDiagnostic[]>([]);
  const checkButtonRef = useRef<HTMLButtonElement>(null);
  const [sourceDraft, setSourceDraft] = useState(workflowSource);
  const [sourceDirty, setSourceDirty] = useState(false);
  const [savedSemanticIdentity, setSavedSemanticIdentity] = useState(() => contentIdentity(loadedWorkflow));
  const [hostDefinitionRevision, setHostDefinitionRevision] = useState(definitionRevision);
  const [persistedSubject, setPersistedSubject] = useState(() => persistedRunSubject(loadedWorkflow, storageDigest));
  const [saveState, setSaveState] = useState<"saved" | "saving" | "error" | "conflict">("saved");
  const [saveMessage, setSaveMessage] = useState("");
  const [saveConflict, setSaveConflict] = useState(false);
  const [storedComparison, setStoredComparison] = useState<WorkflowRecoveryStoredSource | null>(null);
  const [conflictAction, setConflictAction] = useState<"idle" | "copying" | "comparing" | "reloading">("idle");
  const [conflictActionMessage, setConflictActionMessage] = useState("");
  const [undoStack, setUndoStack] = useState<Snapshot[]>([]);
  const [redoStack, setRedoStack] = useState<Snapshot[]>([]);
  const [modal, setModal] = useState<"none" | "port-lab" | "delete" | "output" | "source-compare" | "reload-stored" | "run-preflight">("none");
  const [portTreatment, setPortTreatment] = useState<PortTreatment>("dot");
  const [proposal, setProposal] = useState<RecoveryCommandBatch | null>(null);
  const [proposalResult, setProposalResult] = useState<ReturnType<typeof applyRecoveryBatch> | null>(null);
  const [runStage, setRunStage] = useState(0);
  const [runSubject, setRunSubject] = useState<CapturedRunSubject | null>(null);
  const [runCreatedAt, setRunCreatedAt] = useState("");
  const [materialSupplied, setMaterialSupplied] = useState(false);
  const [runOverride, setRunOverride] = useState<RecoveryRunState | null>(null);
  const [workflowRun, setWorkflowRun] = useState<WorkflowRecoveryRunResult | null>(null);
  const [workflowRunError, setWorkflowRunError] = useState("");
  const runAbort = useRef<AbortController | null>(null);
  useEffect(() => () => runAbort.current?.abort(), []);
  const [workflowRunPending, setWorkflowRunPending] = useState(false);
  const [nativeRunStartedAt, setNativeRunStartedAt] = useState("");
  const [nativeRunCompletedAt, setNativeRunCompletedAt] = useState("");
  const [nativeRunEvents, setNativeRunEvents] = useState<NativeRunEvent[]>([]);
  const [nativePartialResults, setNativePartialResults] = useState<WorkspaceEngineeringResult[]>([]);
  const [nativeRunLogPath, setNativeRunLogPath] = useState("");
  const [nativeRunInput, setNativeRunInput] = useState<NativeRunInput | null>(null);
  // Undefined preserves the initial submitting indicator; null means that no
  // task is active between server events. An unknown ID must never select another task.
  const [nativeActiveTaskId, setNativeActiveTaskId] = useState<string | null | undefined>(undefined);
  const [nativeCompletedTaskIds, setNativeCompletedTaskIds] = useState<ReadonlySet<string>>(() => new Set());
  const observer = useWorkflowRunObserver(onRun && !simulationPreview ? workspaceSessionId : undefined,workspaceId,workflowFilePath,`${reopenRequest}-${nativeRunCompletedAt}`);
  const observed = preferObservedRun(observer.record,{pending:workflowRunPending,startedAt:nativeRunStartedAt,logPath:nativeRunLogPath || workflowRun?.runLogPath || "",hasResult:Boolean(workflowRun)}) ? observer.record : null;
  const presentedRun = useMemo<WorkflowRecoveryRunResult | null>(() => {
    if (!observed) return workflowRun && observer.record && observer.record.path === workflowRun.runLogPath && observer.record.review ? {...workflowRun,review:observer.record.review} : workflowRun;
    if (!["completed","pending_review","changes_requested"].includes(observed.status)) return null;
    const output=observed.execution?.outputs.at(-1);
    return {status:observed.review ? "pending_review" : "completed",review:observed.review,runLogPath:observed.path,
      outputPath:output?.output_path ?? "",outputBytes:output?.output_bytes ?? 0,taskTitle:output?.task_title ?? "Workflow",
      taskId:output?.task_id,outputs:observed.execution?.outputs ?? [],results:observed.results};
  },[observed,workflowRun,observer.record]);
  const presentedPending=workflowRunPending || observed?.status === "running";
  const presentedError=observed ? observed.status === "cancelled" ? "Workflow cancelled. An application operation already submitted may still be running. Check the saved run before retrying." : observed.status === "failed" ? observed.error || "The saved workflow failed." : "" : workflowRunError;
  const presentedStartedAt=observed?.started_at ?? nativeRunStartedAt;
  const presentedCompletedAt=observed ? observed.execution_ended_at ?? observed.completed_at ?? "" : nativeRunCompletedAt;
  const presentedRunLogPath=observed?.path ?? nativeRunLogPath;
  const presentedActiveTaskId=observed ? observed.execution?.active_task_id ?? null : nativeActiveTaskId;
  const presentedCompletedTaskIds=useMemo(() => observed ? new Set(observed.execution?.completed_task_ids ?? []) : nativeCompletedTaskIds,[observed,nativeCompletedTaskIds]);
  const presentedEvents=useMemo(() => observed ? observed.execution?.last_progress ? [{at:observed.execution.last_progress.at ?? observed.started_at,label:observed.execution.last_progress.message ?? observed.execution.last_progress.kind.replaceAll("_"," "),detail:observed.execution.last_progress.task_title ?? ""}] : [] : nativeRunEvents,[observed,nativeRunEvents]);
  const documentReviews = useWorkflowReviews(onRun ? workspaceSessionId : undefined, workflowFilePath, `${presentedCompletedAt}-${reopenRequest}`, presentedRun?.review);
  const reviewPresentation = reviewRunPresentation(documentReviews.reviews, presentedRun, presentedError);
  const observedStatus = observed?.status === "interrupted" ? {label:"Execution interrupted",detail:"The workflow no longer owns its execution lease. An already submitted application operation may still be running; inspect the saved run before retrying."}
    : observed?.status === "unknown" ? {label:"Execution status unknown",detail:"Wright cannot confirm who owns this execution. Its last recorded activity and results are preserved."}
    : observer.enabled && !observer.checked && !nativeRunStartedAt ? {label:"Checking run status…",detail:"Checking the saved workflow for existing execution."}
    : observer.error && !observer.record && !nativeRunStartedAt ? {label:"Execution status unavailable",detail:"Refresh status before starting another run."} : null;
  useEffect(() => {
    if (!simulationPreview) {
      setRunStage(0);
      setRunSubject(null);
      setRunOverride(null);
    }
  }, [simulationPreview]);
  const sourceRef = useRef<HTMLTextAreaElement>(null);
  const modalRef = useRef<HTMLElement>(null);
  const modalReturnFocusRef = useRef<HTMLElement | null>(null);

  const candidateWorkflow = runStage === 0 && proposalResult?.ok && proposalResult.workflow ? proposalResult.workflow : workflow;
  const blockIcons = useMemo(() => recoveryBlockIconKinds(candidateWorkflow), [candidateWorkflow]);
  const candidateLayout = runStage === 0 && proposalResult?.ok && proposalResult.layout ? proposalResult.layout : layout;
  const cadOutputs = useMemo(() => cadOutputPresentation(candidateWorkflow), [candidateWorkflow]);
  const hiddenPorts = useMemo(() => new Set([...hiddenMcpInputs(candidateWorkflow), ...cadOutputs.hidden]), [candidateWorkflow,cadOutputs]);
  const projection = useMemo(() => toDraftProjection(candidateWorkflow, candidateLayout), [candidateWorkflow, candidateLayout]);
  const portArtifacts = useMemo(() => Object.fromEntries(candidateWorkflow.ports.filter((port) => port.artifactContractId).map((port) => [port.id, port.artifactContractId as string])), [candidateWorkflow]);
  const formatted = useMemo(() => formatRecoveryAuthoringSource(workflow), [workflow]);
  const parsedSource = useMemo(() => parseRecoveryAuthoringSource(sourceDraft, workflow), [sourceDraft, workflow]);
  const nativeRunBlock = useMemo(
    () => presentedActiveTaskId === undefined
      ? workflow.blocks.find((block) => block.executionKind === "ai_capable" && block.kind === "work") ?? null
      : workflow.blocks.find((block) => block.id === `block.${presentedActiveTaskId?.replaceAll("_", "-")}`) ?? null,
    [workflow.blocks, presentedActiveTaskId],
  );
  const sourceValid = parsedSource.ok;
  const semanticDirty = contentIdentity(workflow) !== savedSemanticIdentity;
  const observedSourceMismatch=Boolean(observed && (observed.source_matches_current !== true || observed.source_digest !== persistedSubject?.storageDigest || semanticDirty || sourceDirty || proposal !== null));
  const layoutDirty = canonicalLayoutPositionBytes(layout) !== savedLayoutIdentity;
  const reopenState = useRef({ dirty: false, busy: false, storageDigest, workflowSource, workflowLayout });
  reopenState.current = {
    dirty: semanticDirty || sourceDirty || layoutDirty || proposal !== null,
    busy: workflowRunPending || saveState === "saving",
    storageDigest, workflowSource, workflowLayout,
  };
  const lastReopenRequest = useRef(reopenRequest);
  useEffect(() => {
    if (lastReopenRequest.current === reopenRequest) return;
    lastReopenRequest.current = reopenRequest;
    if (!onReloadStoredSource) return;
    let current = true;
    void onReloadStoredSource((stored) => {
      if (!current) return false;
      const local = reopenState.current;
      const changed = stored.storage_digest !== local.storageDigest || stored.source !== local.workflowSource
        || JSON.stringify(stored.layout ?? null) !== JSON.stringify(local.workflowLayout ?? null);
      if (local.dirty || local.busy) {
        if (local.dirty && changed) {
          setSaveConflict(true);
          setStoredComparison(stored);
        }
        setSaveMessage(local.busy
          ? "The running or saving workflow was kept. Open the file again when it finishes."
          : changed ? "Your local edits were kept. Compare the stored file before discarding changes."
            : "Your local edits were kept. Save them when ready.");
        return false;
      }
      // Reopening an unchanged clean file should preserve its run details/view.
      return changed;
    }).catch((error: unknown) => {
      if (!current) return;
      setSaveState("error");
      setSaveMessage(error instanceof Error ? error.message : "The saved workflow could not be refreshed. The open editor was kept.");
    });
    return () => { current = false; };
  }, [reopenRequest, onReloadStoredSource]);
  const visibleFileName = workflowFilePath.replace(/\\/g, "/").split("/").at(-1) ?? workflowFilePath;
  const visibleFileStatus = onSave
    ? (semanticDirty || sourceDirty || layoutDirty ? "Unsaved changes" : "Saved in workspace")
    : "Local preview · not saved";
  const visibleSaveState = saveConflict ? "conflict" : saveState;
  const visibleSaveMessage = saveConflict
    ? "The workspace file changed elsewhere. Your local edits are still here and protected until you explicitly compare or reload."
    : saveMessage || (semanticDirty || sourceDirty || layoutDirty ? "Unsaved workflow changes" : "Saved in workspace");
  const run = useMemo(() => {
    const value = runProjection(
      runStage,
      materialSupplied,
      runSubject?.workflow ?? workflow,
      runSubject?.semanticSha256 ?? "",
      runCreatedAt,
    );
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
  }, [runStage, materialSupplied, runOverride, runSubject, runCreatedAt, workflow]);
  const canvasRun = useMemo(() => {
    // Execution badges belong to the active run; completed results stay in the drawer.
    if (!onRun || !presentedPending || observedSourceMismatch) return run;
    const projection = initialRunProjection(workflow, "", presentedStartedAt);
    projection.mode = "native";
    projection.state = "running";
    projection.runId = observed?.path ?? `native-${presentedStartedAt || "pending"}`;
    projection.activity = presentedEvents;
    // Input sources supply saved values/files; they are not queued execution tasks.
    projection.steps = Object.fromEntries(workflow.blocks.map((block) => [block.id, recoveryAuthoringSectionKind(block) === "input" ? {
      state: "idle" as const,
      label: "Input source",
      detail: "Supplies input to connected steps.",
    } : {
      state: "queued" as const,
      label: "Waiting",
      detail: "Waiting for the active workflow step.",
    }]));
    for (const taskId of presentedCompletedTaskIds) {
      const blockId = `block.${taskId.replaceAll("_", "-")}`;
      // An input source is never an execution task, even if a stray event names it.
      if (projection.steps[blockId]?.state === "queued") {
        projection.steps[blockId] = {
          state: "succeeded",
          label: "Completed",
          detail: "This step completed in the current run.",
        };
      }
    }
    if (nativeRunBlock && recoveryAuthoringSectionKind(nativeRunBlock) !== "input") {
      projection.activeBlockId = nativeRunBlock.id;
      projection.steps[nativeRunBlock.id] = {
        state: "running",
        label: "Generating response",
        detail: "Waiting for the model response.",
      };
    }
    return projection;
  }, [nativeRunBlock, presentedCompletedTaskIds, presentedEvents, presentedStartedAt, onRun, run, workflow, presentedPending, observedSourceMismatch, observed?.path]);
  const semanticDigest = useSha256(canonicalDefinitionBytes(workflow));
  const persistedSemanticDigest = useSha256(
    persistedSubject === null ? "" : canonicalDefinitionBytes(persistedSubject.workflow),
  );
  const persistedSemanticSha256 = /^sha256:([a-f0-9]{64})$/.exec(persistedSemanticDigest)?.[1] ?? null;
  const layoutDigest = useSha256(canonicalLayoutBytes(layout));
  const inspectionWorkflow = proposal !== null ? candidateWorkflow : workflow;
  const selectedBlock = findBlock(inspectionWorkflow, selectedId);
  const selectedRelationship = inspectionWorkflow.relationships.find((item) => item.id === selectedId) ?? null;
  const selectedPort = inspectionWorkflow.ports.find((item) => item.id === selectedId) ?? null;
  const candidateSelection = proposal !== null && selectedId !== null && !workflow.blocks.some((item) => item.id === selectedId) && !workflow.ports.some((item) => item.id === selectedId) && !workflow.relationships.some((item) => item.id === selectedId);
  const stepArtifact = run.artifactRecords.find((record) => record.contractId === "artifact.step") ?? null;
  const simulationIssue = simulationContractIssue(workflow);
  const missingInputs = authoringReadiness(workflow).inputs.filter((input) => input.status !== "configured");
  const blockEditorReadOnly = candidateSelection || proposal !== null || workflowRunPending || runStage > 0 || sourceDirty || saveState === "saving";
  const selectedOwner = selectedBlock ?? findBlock(inspectionWorkflow, selectedPort?.ownerBlockId ?? null);
  const hasInspection = inspectorOpen && (selectedBlock !== null || selectedPort !== null || selectedRelationship !== null);
  const selectObject = (id: string | null, tab: InspectorTab = "overview") => {
    const block = findBlock(inspectionWorkflow, id);
    const preferredTab = tab === "overview" && block?.executionKind === "ai_capable" && block.kind === "work" ? "definition" : tab;
    setSelectedId(id);
    setInspectorOpen(id !== null);
    setInspectorTab(preferredTab);
  };
  const requestDelete = (id: string) => { setDeleteTargetId(id); setModal("delete"); };
  const deleteImpact = deleteTargetId ? authoringDeletionImpact(workflow, deleteTargetId) : null;

  useEffect(() => {
    const range = recoveryAuthoringSourceSelection(formatted.sourceMap, selectedId);
    if (!range || !sourceRef.current || sourceDirty) return;
    sourceRef.current.setSelectionRange(range.startOffset, range.endOffset);
  }, [formatted.sourceMap, selectedId, sourceDirty, view]);

  useEffect(() => {
    const incomingKey = `${definitionRevision}\u0000${storageDigest ?? ""}\u0000${workflowSource}`;
    if (incomingKey === loadedDocumentKeyRef.current) return;
    if (semanticDirty || sourceDirty || layoutDirty) return;
    const incomingResult = workflowFromSource(workflowSource, definitionRevision);
    if (!incomingResult.ok || incomingResult.workflow === null) {
      setDiagnostics(incomingResult.diagnostics);
      setSaveState("error");
      setSaveMessage("The saved workflow source is invalid. The current accepted diagram was retained.");
      return;
    }
    const incoming = incomingResult.workflow;
    loadedDocumentKeyRef.current = incomingKey;
    setWorkflow(incoming);
    const incomingLayout = hydrateAuthoringLayout(incoming, workflowLayout);
    setLayout(incomingLayout);
    setSavedLayoutIdentity(canonicalLayoutPositionBytes(incomingLayout));
    setSourceDraft(workflowSource);
    setSourceDirty(false);
    setSavedSemanticIdentity(contentIdentity(incoming));
    setHostDefinitionRevision(definitionRevision);
    setPersistedSubject(persistedRunSubject(incoming, storageDigest));
    setUndoStack([]);
    setRedoStack([]);
    setDiagnostics([]);
    setSaveState("saved");
    setSaveMessage("");
    setSaveConflict(false);
    setStoredComparison(null);
    setConflictAction("idle");
    setConflictActionMessage("");
  }, [definitionRevision, semanticDirty, sourceDirty, layoutDirty, storageDigest, workflowSource, workflowLayout]);

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
    setSourceDraft(formatRecoveryAuthoringSource(nextWorkflow).text);
    setSourceDirty(false);
    setDiagnostics([]);
    setSaveState("saved");
    setSaveMessage("");
  };

  const rejectSemanticChangeDuringRun = (semanticChanged: boolean) => {
    if ((!workflowRunPending && runStage === 0) || !semanticChanged) return false;
    setDiagnostics([runDefinitionLockDiagnostic()]);
    return true;
  };

  const applyBatch = (batch: RecoveryCommandBatch) => {
    const result = applyRecoveryBatch(workflow, layout, batch);
    if (!result.ok) {
      setDiagnostics(result.diagnostics);
      return false;
    }
    if (rejectSemanticChangeDuringRun(result.semanticChanged)) return false;
    const accepted = acceptRecoveryResult(workflow, layout, result);
    if (!accepted) return false;
    const before = { workflow: cloneWorkflow(workflow), layout: cloneLayout(layout) };
    pushSnapshot(accepted.workflow, accepted.layout, before);
    return true;
  };

  const applyCommands = (origin: RecoveryCommandBatch["origin"], commands: RecoveryCommand[]) => {
    const semanticEdit = commands.some((command) => command.kind !== "move_block");
    if (sourceDirty && origin !== "text" && semanticEdit) {
      setDiagnostics([{
        code: "WFR-SOURCE-DRAFT-CONFLICT",
        semanticId: null,
        line: null,
        explanation: "The Source view has an unapplied edit. A second semantic edit would replace that draft.",
        correction: "Apply the checked source edit or restore the current source before changing the diagram or inspector.",
      }]);
      return false;
    }
    return applyBatch(recoveryCommandBatch(workflow.revision, origin, commands));
  };

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
    if (rejectSemanticChangeDuringRun(result.semanticChanged)) return;
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
    setSourceDraft(formatRecoveryAuthoringSource(restored.workflow).text);
    setSourceDirty(false);
    setDiagnostics([]);
    setSaveState("saved");
    setSaveMessage("");
  };

  const isConnectionAllowed = (sourceId: string, targetId: string) => {
    const source = findPort(workflow, sourceId);
    const target = findPort(workflow, targetId);
    if (!source || !target || source.direction !== "output" || target.direction !== "input" || source.ownerBlockId === target.ownerBlockId) return false;
    const engineeringIssue=engineeringConnectionIssue(workflow,sourceId,targetId,connectionCapabilities);
    if(engineeringIssue!==undefined)return engineeringIssue===null;
    const owner = findBlock(workflow, target.ownerBlockId);
    if (owner && isPromptBlock(owner) && target.name === "Prompt") {
      return promptSourceCandidates(owner, workflow).some((port) => port.id === sourceId);
    }
    if (owner && isMcpBlock(owner)) return mcpCandidates(owner, workflow, target).some((p) => p.id === sourceId);
    return canConnectAuthoringPorts(source, target);
  };

  const handleIntent = (intent: DraftCanvasIntent) => {
    if (intent.type === "select") {
      selectObject(intent.semanticId, inspectorTab === "activity" || inspectorTab === "diagnosis" ? inspectorTab : "overview");
      return;
    }
    if (intent.type === "move-block") {
      applyCommands("graph", [{ kind: "move_block", blockId: intent.semanticId, x: intent.x, y: intent.y }]);
      return;
    }
    if (intent.type === "edit-block") {
      applyCommands("graph", [{ kind: "set_block_title", blockId: intent.semanticId, title: intent.title }]);
      return;
    }
    if (intent.type === "create-connection") {
      const source = findPort(workflow, intent.sourcePortId);
      const target = findPort(workflow, intent.targetPortId);
      if (!source || !target || !isConnectionAllowed(source.id, target.id)) return;
      const mcpOwner = findBlock(workflow, target.ownerBlockId);
      if(mcpOwner?.configuration.application_resource&&target.id===applicationPortId(mcpOwner,"input")) {
        applyCommands("graph",applicationConnectionCommands(mcpOwner,workflow,source.id,source.typeId)); return;
      }
      if(mcpOwner?.configuration.cad&&target.id===cadPortId(mcpOwner,"input")) {
        const cad=JSON.parse(String(mcpOwner.configuration.cad)) as CadOptions;
        applyCommands("graph",[
          ...workflow.relationships.filter(e=>e.targetId===target.id).map(e=>({kind:"disconnect" as const,relationshipId:e.id})),
          {kind:"connect",relationship:{id:`rel.${mcpOwner.id.slice(6)}-cad-model`,kind:"data",sourceId:source.id,targetId:target.id,label:"CAD model",condition:null}},
          ...cadCommands(mcpOwner,workflow,{...cad,source:"upstream",from_port:sourceKey(target.id)}),
        ]); return;
      }
      if (mcpOwner && isMcpBlock(mcpOwner)) { applyCommands("graph", connectMcpInput(mcpOwner, workflow, target.id, source.id)); return; }
      const owner = findBlock(workflow, target.ownerBlockId);
      if (owner && isPromptBlock(owner) && target.name === "Prompt") {
        applyCommands("graph", connectPromptCommands(owner, workflow, source.id));
        return;
      }
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
      requestDelete(intent.semanticId);
    }
  };

  const applySource = () => {
    const parsed = parseRecoveryAuthoringSource(sourceDraft, workflow);
    if (!parsed.ok || !parsed.workflow) {
      setDiagnostics(parsed.diagnostics);
      return;
    }
    const commands = textEditCommands(workflow, parsed.workflow, layout);
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
    if (sourceDirty) {
      setDiagnostics([{ code: "WFR-SOURCE-DRAFT-CONFLICT", semanticId: null, line: null, explanation: "The Source view has an unapplied edit. An example suggestion would be based on a different workflow.", correction: "Apply the checked source edit or restore the current source before requesting a suggestion." }]);
      return;
    }
    const batch = aiDrawingProposal(workflow);
    const result = applyRecoveryBatch(workflow, layout, batch);
    if (!result.ok) {
      setDiagnostics(result.diagnostics);
      return;
    }
    if (rejectSemanticChangeDuringRun(result.semanticChanged)) return;
    setProposal(batch);
    setProposalResult(result);
  };

  const selectedStep = selectedBlock ? run.steps[selectedBlock.id] : null;
  const currentMatchesPersistedSubject = persistedSubject !== null
    && contentIdentity(persistedSubject.workflow) === contentIdentity(workflow);
  const canRun = sourceValid
    && !sourceDirty
    && !semanticDirty
    && !saveConflict
    && saveState === "saved"
    && currentMatchesPersistedSubject
    && proposal === null
    && simulationIssue === null
    && persistedSemanticSha256 !== null;
  const runDisabledReason = sourceDirty || !sourceValid
      ? "Apply a valid source edit before testing the workflow."
      : semanticDirty
        ? "Save workflow changes successfully before testing the workflow."
        : saveConflict
          ? "Resolve the workspace file conflict before testing the workflow."
          : saveState === "saving"
            ? "Wait for the workflow save to finish before testing the workflow."
            : saveState === "error"
              ? "Save the workflow successfully before testing it."
              : !currentMatchesPersistedSubject
                ? "Testing requires a workflow revision and digest confirmed by the workspace host."
                : persistedSemanticSha256 === null
                  ? "Wait for Wright to calculate the saved definition's semantic SHA-256 before testing."
                : proposal !== null
                  ? "Add or discard the AI suggestion before testing the workflow."
                  : simulationIssue ?? undefined;
  const nextRun = () => {
    setRunOverride(null);
    setRunStage((stage) => stage === 0 ? 1 : stage === 1 ? 2 : stage === 2 ? 3 : stage >= 4 && stage < 10 ? stage + 1 : stage);
  };
  const startRun = async () => {
    const connectivityIssue = disconnectedProcessDiagnostic(workflow);
    if (connectivityIssue) {
      setDiagnostics([connectivityIssue]);
      return;
    }
    if (presentedPending || (observer.enabled && (!observer.checked || Boolean(observer.error && !observer.record)))) return;
    if (onRun) {
      setNativePartialResults([]);
      setNativeRunLogPath("");
      let subject = persistedSubject;
      if (!sourceDirty && sourceValid && !saveConflict && (semanticDirty || layoutDirty) && onSave) subject = await saveWorkflow();
      if (sourceDirty || !sourceValid || saveConflict || subject === null || ((semanticDirty || layoutDirty) && subject === persistedSubject)) {
        setWorkflowRun(null);
        setNativeRunInput(null);
        setNativeRunStartedAt("");
        setNativeRunCompletedAt("");
        setNativeRunEvents([]);
        setWorkflowRunError("Save the valid workflow file before running it.");
        setRunDetailsOpen(true);
        return;
      }
      setWorkflowRun(null);
      setWorkflowRunError("");
      // Source `prompt` maps to canonical block.instructions. Capture the saved
      // subject now so later edits cannot rewrite the input shown for this run.
      const savedBlock = subject.workflow.blocks.find((block) => block.executionKind === "ai_capable" && block.kind === "work");
      const input: NativeRunInput = {
        prompt: savedBlock?.instructions ?? "",
        taskTitle: savedBlock?.title ?? "the active step",
        workflowPath: workflowFilePath,
        storageDigest: subject.storageDigest,
      };
      setNativeRunInput(input);
      setNativeActiveTaskId(undefined);
      setNativeCompletedTaskIds(new Set());
      const startedAt = new Date().toISOString();
      setNativeRunStartedAt(startedAt);
      setNativeRunCompletedAt("");
      setNativeRunEvents([
        { at: startedAt, label: "Run requested", detail: `Requested execution of ${workflowFilePath}.` },
        { at: startedAt, label: "Saved input", detail: `Captured the saved prompt for ${input.taskTitle}.` },
      ]);
      runAbort.current = new AbortController();
      setWorkflowRunPending(true);
      setRunDetailsOpen(true);
      try {
        const result = await onRun({ signal: runAbort.current?.signal, expectedStorageDigest: subject.storageDigest, onEvent: (event) => {
          if (event.kind === "run_started") setNativeRunLogPath(event.run_log_path ?? "");
          if (event.kind === "result_ready" && event.engineering_result) {
            const ready = event.engineering_result;
            setNativePartialResults(results => [...results.filter(result => result.id !== ready.id), ready]);
          }
          if (event.kind === "design_revision") {
            const invalidated = new Set(event.invalidated_task_ids ?? []);
            setNativeCompletedTaskIds(ids => new Set([...ids].filter(id => !invalidated.has(id))));
            setNativeActiveTaskId(id => id === undefined || (id !== null && invalidated.has(id)) ? null : id);
            setNativePartialResults(results => results.filter(result => !event.invalidated_task_ids?.includes(result.provenance.task_id)));
          }
          if (event.kind === "step_completed") {
            setNativeCompletedTaskIds(ids => new Set([...ids, event.task_id]));
            setNativeActiveTaskId(id => id === undefined || id === event.task_id ? null : id);
          }
          if (event.kind === "step_started") {
            setNativeCompletedTaskIds(ids => new Set([...ids].filter(id => id !== event.task_id)));
            setNativeActiveTaskId(event.task_id);
            setNativeRunInput({ ...input, taskTitle: event.task_title, executionKind: event.execution_kind, prompt: event.execution_kind === "mcp" ? JSON.stringify(event.arguments, null, 2) : event.prompt ?? "", formatInstructions: event.format_instructions });
          }
          setNativeRunEvents((events) => [...events, { at: event.at, label: (event.kind === "task_progress" || event.kind === "operation_progress") ? event.message ?? "Working" : event.kind === "tool_started" ? `Using ${event.tool}` : ({review_requested: "Awaiting your review", design_check: `Design check: ${event.report?.verdict ?? "reviewed"}`, design_revision: `Correcting design · revision ${event.revision}`, run_started: "Run log opened", result_ready: "Result ready", step_started: "Step started", step_completed: "Response validated", output_saved: "File saved", task_progress: "Task progress", tool_started: "Tool started", tool_completed: "Tool result"})[event.kind], detail: `${event.task_title} · ${event.report ? event.report.corrections.join(" ") : event.message ?? event.tool ?? event.output_path ?? ""}${event.arguments ? ` · ${JSON.stringify(event.arguments)}` : ""}${event.kind === "tool_completed" ? ` · ${event.status}: ${event.text ?? ""}` : ""}` }]);
        } });
        const completedAt = new Date().toISOString();
        setNativeRunCompletedAt(completedAt);
        setWorkflowRun(result);
        setNativeRunEvents((events) => [...events, {
          at: completedAt,
          label: result.status === "pending_review" ? "Awaiting your review" : "Run completed",
          detail: result.outputPath ? `${result.outputPath} was saved in this workspace (${result.outputBytes.toLocaleString("en-US")} bytes).` : `${result.results?.length ?? 0} engineering result(s) produced; open the results to review them.`,
        }]);
      } catch (error) {
        const message = runAbort.current?.signal.aborted ? "Workflow cancelled. An application job already submitted may still be running. Check its status before running again. Results produced so far are preserved." : error instanceof Error ? error.message : "The workflow could not run.";
        const completedAt = new Date().toISOString();
        setNativeRunCompletedAt(completedAt);
        setWorkflowRunError(message);
        setNativeRunEvents((events) => [...events, { at: completedAt, label: runAbort.current?.signal.aborted ? "Run cancelled" : "Run failed", detail: message }]);
      } finally {
        setWorkflowRunPending(false);
      }
      return;
    }
    if (!simulationPreview) { setModal("run-preflight"); return; }
    if (!canRun || persistedSubject === null || persistedSemanticSha256 === null) return;
    setRunSubject({
      workflow: cloneWorkflow(persistedSubject.workflow),
      storageDigest: persistedSubject.storageDigest,
      semanticSha256: persistedSemanticSha256,
    });
    setRunCreatedAt(new Date().toISOString());
    setRunOverride(null);
    setRunStage(1);
    setRunDetailsOpen(true);
  };
  const endRun = () => {
    setRunStage(0);
    setRunSubject(null);
    setRunCreatedAt("");
    setMaterialSupplied(false);
    setRunOverride(null);
    setDiagnostics([]);
  };

  const saveWorkflow = async () => {
    if (!onSave || sourceDirty || !sourceValid || (!semanticDirty && !layoutDirty) || saveState === "saving" || saveConflict) return null;
    let workflowToSave = workflow;
    const imageCorrections = singleImageInputCorrections(workflow);
    if (imageCorrections.length > 0) {
      const repaired = applyRecoveryBatch(workflow, layout, recoveryCommandBatch(workflow.revision, "form", imageCorrections));
      if (!repaired.ok || !repaired.workflow) { setDiagnostics(repaired.diagnostics); return null; }
      workflowToSave = repaired.workflow;
    }
    const containment = validateRecoveryAuthoringRoundTrip(workflowToSave);
    if (!containment.ok) {
      setDiagnostics(containment.diagnostics);
      setSaveState("error");
      setSaveMessage("This workflow cannot be reconstructed from its engineering source, so nothing was saved.");
      return null;
    }
    setSaveState("saving");
    setSaveMessage("");
    try {
      const saved = await onSave(formatRecoveryAuthoringSource(workflowToSave).text, cloneLayout(layout));
      if (typeof saved?.source !== "string"
        || !Number.isInteger(saved.definition_revision)
        || saved.definition_revision < 1
        || !/^[a-f0-9]{64}$/.test(saved.storage_digest)) {
        throw new Error("Wright did not confirm the stored workflow revision and digest. Your local edits were kept.");
      }
      const storedResult = workflowFromSource(saved.source, saved.definition_revision);
      if (!storedResult.ok || storedResult.workflow === null
        || contentIdentity(storedResult.workflow) !== contentIdentity(workflowToSave)) {
        throw new Error("Wright returned a stored workflow that does not match these edits. Your local edits were kept.");
      }
      const rebasedWorkflow = storedResult.workflow;
      const rebasedLayout = saved.layout ? hydrateAuthoringLayout(rebasedWorkflow, saved.layout) : cloneLayout(layout);
      rebasedLayout.semanticRevision = saved.definition_revision;
      setWorkflow(rebasedWorkflow);
      setLayout(rebasedLayout);
      setSavedLayoutIdentity(canonicalLayoutPositionBytes(rebasedLayout));
      setHostDefinitionRevision(saved.definition_revision);
      setPersistedSubject(persistedRunSubject(rebasedWorkflow, saved.storage_digest));
      setSavedSemanticIdentity(contentIdentity(rebasedWorkflow));
      setSourceDraft(saved.source);
      setSourceDirty(false);
      setSaveState("saved");
      setSaveMessage("Saved in workspace");
      setSaveConflict(false);
      setStoredComparison(null);
      setConflictActionMessage("");
      return persistedRunSubject(rebasedWorkflow, saved.storage_digest);
    } catch (error) {
      const conflict = typeof error === "object" && error !== null && "code" in error && error.code === "workflow_source_conflict";
      if (conflict) setSaveConflict(true);
      setSaveState(conflict ? "conflict" : "error");
      setSaveMessage(conflict
        ? "The workspace file changed elsewhere. Your local edits are still here; reload or compare before saving again."
        : error instanceof Error ? error.message : "The workflow could not be saved. Your local edits are still here.");
      return null;
    }
  };

  const copyLocalWorkflowSource = async () => {
    setConflictAction("copying");
    setConflictActionMessage("");
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard access is unavailable in this browser.");
      await navigator.clipboard.writeText(sourceDraft);
      setConflictActionMessage("Local workflow source copied. The editor and stored file were not changed.");
    } catch (error) {
      setConflictActionMessage(error instanceof Error ? error.message : "The local workflow source could not be copied.");
    } finally {
      setConflictAction("idle");
    }
  };

  const compareStoredWorkflowSource = async () => {
    if (!onReadStoredSource) return;
    setConflictAction("comparing");
    setConflictActionMessage("");
    try {
      const current = await onReadStoredSource();
      setStoredComparison(current);
      setModal("source-compare");
    } catch (error) {
      setConflictActionMessage(error instanceof Error ? error.message : "The stored workflow source could not be read. Local edits were kept.");
    } finally {
      setConflictAction("idle");
    }
  };

  const reloadStoredWorkflowSource = async () => {
    if (!onReloadStoredSource) return;
    setConflictAction("reloading");
    setConflictActionMessage("");
    try {
      await onReloadStoredSource();
    } catch (error) {
      setConflictActionMessage(error instanceof Error ? error.message : "The stored workflow could not be reloaded. Local edits were kept.");
      setConflictAction("idle");
    }
  };

  return (
    <section
      className="workflow-recovery workflow-recovery--redesign"
      data-testid="workflow-recovery-concept"
      data-revision={workflow.revision}
      data-semantic-digest={semanticDigest}
      data-layout-digest={layoutDigest}
    >
      <header className="recovery-filebar" data-testid="workflow-recovery-filebar">
        <div className="recovery-filebar__identity">
          <div>
            <h1 title={`${visibleFileName} · ${visibleFileStatus}`}>{workflow.metadata.title}</h1>
          </div>
        </div>
        {simulationPreview && <div className="recovery-authority" data-testid="workflow-recovery-authority" data-revision={hostDefinitionRevision} data-semantic-digest={semanticDigest} data-layout-digest={layoutDigest}>
          <b>Provisional</b>
          <details className="recovery-technical-details"><summary data-testid="workflow-recovery-file-technical-details">Details</summary><span>{onRun ? "Native workspace execution available" : simulationPreview ? "Internal simulation preview" : "Authoring available · execution not connected"}</span><span>{sourceValid && !sourceDirty ? "Workflow checks pass" : "Source edit has issues · current diagram retained"}</span><span>Definition revision {hostDefinitionRevision}</span><span>Integrity {semanticDigest}</span>{simulationPreview && simulationIssue && <span data-testid="workflow-recovery-simulation-issue">{simulationIssue}</span>}<button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-port-lab-open" onClick={() => setModal("port-lab")}>Connection style preview</button></details>
        </div>}
      <div className="recovery-toolbar">
        <select className="recovery-view-select" data-testid="workflow-recovery-view-select" aria-label="Workflow view" value={view} onChange={e => setView(e.target.value as typeof view)}><option value="diagram">Diagram</option><option value="code">Source</option><option value="split">Side by side</option></select>
        <div className="recovery-tabs" role="tablist" aria-label="Workflow view">
          {(["diagram", "code", "split"] as const).map((mode) => <button key={mode} type="button" role="tab" aria-selected={view === mode} data-testid={`workflow-recovery-view-${mode}`} onClick={() => setView(mode)}>{mode === "diagram" ? "Diagram" : mode === "code" ? "Source" : "Side by side"}</button>)}
        </div>
        <div className="recovery-toolbar__actions">
          {onSave && <span className={`recovery-save-status recovery-save-status--${visibleSaveState}`} data-testid="workflow-recovery-save-status" title={visibleSaveMessage} aria-label={visibleSaveMessage} role={visibleSaveState === "error" || visibleSaveState === "conflict" ? "alert" : "status"}>{visibleSaveState === "saving" ? "Saving…" : visibleSaveState === "error" || visibleSaveState === "conflict" ? visibleSaveMessage : semanticDirty || sourceDirty || layoutDirty ? "Unsaved" : "Saved"}</span>}
          <button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-undo" aria-label="Undo" title="Undo" disabled={workflowRunPending || undoStack.length === 0} onClick={() => restore(undoStack.at(-1)!, "undo")}>↶</button>
          <button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-redo" aria-label="Redo" title="Redo" disabled={workflowRunPending || redoStack.length === 0} onClick={() => restore(redoStack.at(-1)!, "redo")}>↷</button>
          {onSave && <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-save" disabled={workflowRunPending || (!semanticDirty && !layoutDirty) || sourceDirty || !sourceValid || saveState === "saving" || saveConflict} onClick={() => void saveWorkflow()}>{saveState === "saving" ? "Saving…" : "Save"}</button>}
          {saveConflict && <section className="recovery-conflict-actions" role="group" aria-label="Resolve stored workflow conflict" data-testid="workflow-recovery-conflict-actions">
            <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-conflict-copy-local" disabled={conflictAction !== "idle"} onClick={() => void copyLocalWorkflowSource()}>{conflictAction === "copying" ? "Copying…" : "Copy local source"}</button>
            <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-conflict-compare" disabled={conflictAction !== "idle" || !onReadStoredSource} onClick={() => void compareStoredWorkflowSource()}>{conflictAction === "comparing" ? "Reading stored file…" : "Compare stored file"}</button>
            <button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-conflict-reload" disabled={conflictAction !== "idle" || !onReloadStoredSource} onClick={() => { setConflictActionMessage(""); setModal("reload-stored"); }}>Discard local edits and reload…</button>
            {conflictActionMessage && <span className="recovery-conflict-actions__message" data-testid="workflow-recovery-conflict-action-message" role="status">{conflictActionMessage}</span>}
          </section>}
          <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-validate" ref={checkButtonRef} onClick={() => { const parsed = parseRecoveryAuthoringSource(sourceDraft, workflow); setDiagnostics([...parsed.diagnostics, ...(parsed.ok && parsed.workflow ? [disconnectedProcessDiagnostic(parsed.workflow)].filter((issue): issue is RecoveryDiagnostic => issue !== null) : [])]); }}>✓ Check</button>
          {workflowRunPending && <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-run-cancel" onClick={() => runAbort.current?.abort()}>Cancel run</button>}
          <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-run-start" disabled={presentedPending || (observer.enabled && (!observer.checked || Boolean(observer.error && !observer.record))) || saveState === "saving" || (simulationPreview && !canRun)} title={onRun ? "Run the saved workspace workflow" : simulationPreview ? (canRun ? "Run the fixed local example. No AI, CAD, or external tool is executed." : runDisabledReason) : "Check required inputs and execution availability"} onClick={runStage === 0 ? () => void startRun() : undefined}>{presentedPending ? "Running…" : onRun ? semanticDirty || layoutDirty ? "Save & run" : "▶ Run" : !simulationPreview ? "▶ Run" : runStage === 0 ? "▶ Simulate" : `Simulation · ${runStateLabel[run.state]}`}</button>
        </div>
      </div>
      {fileActions}
      </header>

      <div className={`recovery-workbench ${hasInspection ? "recovery-workbench--inspecting" : ""}`}>
        <AuthoringCreateRail onCreateServer={(server) => { const commands = createMcpServerBlock(server, workflow, layout, selectedOwner?.id); const add = commands[0]; if (add?.kind === "add_block" && applyCommands("graph", commands)) selectObject(add.block.id, "definition"); }} sessionId={workspaceSessionId} disabled={proposal !== null || workflowRunPending || runStage > 0 || sourceDirty} onCreate={(templateId) => { const command = createAuthoringObject(templateId, workflow, layout, { selectedBlockId: selectedOwner?.id }); if (applyCommands("graph", [command])) selectObject(command.block.id, "definition"); }} />

        <div className={`recovery-stage recovery-stage--${view}`}>
          {view !== "code" && <div className="recovery-canvas-tools"><AuthoringInputsNavigator workflow={workflow} onSelect={(id) => selectObject(id)} /><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-focus-path" aria-pressed={focusPath} disabled={!selectedId} onClick={() => setFocusPath(!focusPath)}>Focus path</button><button type="button" className="recovery-button recovery-button--ai" data-testid="workflow-recovery-ai-request" onClick={requestProposal}>✦ Example suggestion</button>{!inspectorOpen && selectedId && <button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-inspector-open" onClick={() => setInspectorOpen(true)}>Inspector</button>}</div>}
          {(view === "diagram" || view === "split") && (
            <RecoveryCanvasRuntimeProvider value={{ hiddenPorts, outputLabels: cadOutputs.labels, outputGroups: cadOutputs.groups, canConnect: isConnectionAllowed, connectionIssue: (sourceId,targetId)=>engineeringConnectionIssue(workflow,sourceId,targetId,connectionCapabilities), readOnly: proposal !== null || workflowRunPending || runStage > 0 || saveState === "saving", run: canvasRun, blockIcons, focusPath, runSubject: runStage > 0 && runSubject !== null ? { workflowId: runSubject.workflow.workflowId, workflowRevision: runSubject.workflow.revision, semanticSha256: runSubject.semanticSha256 } : null, proposedBlockIds: new Set(proposalResult?.workflow?.blocks.filter((block) => !workflow.blocks.some((accepted) => accepted.id === block.id)).map((block) => block.id) ?? []), portArtifactIds: portArtifacts, relationshipLabels: Object.fromEntries(candidateWorkflow.relationships.map((relationship) => [relationship.id, relationship.label])), overlayRelationships: candidateWorkflow.relationships.filter((relationship) => relationship.kind === "control" || relationship.kind === "decision"), portTreatment, onArtifactInspect: (portId) => selectObject(portId, findPort(candidateWorkflow, portId)?.direction === "input" ? "inputs" : "outputs") }}>
              <ReactFlowRecoveryCanvas key={proposal === null ? "accepted" : "candidate"} projection={projection} selectedSemanticId={selectedId} onIntent={proposal === null ? handleIntent : (intent) => { if (intent.type === "select") handleIntent(intent); }} />
            </RecoveryCanvasRuntimeProvider>
          )}
          {(view === "code" || view === "split") && <section className="recovery-code">
            <header><div><span>ENGINEERING SOURCE</span><b>Readable workflow script · checked changes become workflow commands</b></div><div>{parsedSource.ok ? "✓ source valid" : "! source has issues"}</div></header>
            <textarea ref={sourceRef} spellCheck={false} aria-label="Workflow source" data-testid="workflow-recovery-source-editor" value={sourceDraft} onChange={(event) => { setSourceDraft(event.target.value); setSourceDirty(event.target.value !== formatted.text); setSaveState("saved"); setSaveMessage(""); }} onSelect={(event) => { const offset = event.currentTarget.selectionStart; const sourceMap = sourceDirty ? parsedSource.sourceMap : formatted.sourceMap; const semanticId = recoveryAuthoringSemanticIdAtOffset(sourceMap, offset); if (semanticId) setSelectedId(semanticId); }} />
            <footer><span>{sourceDirty ? "Unapplied source edit" : semanticDirty ? "Applied locally · not saved" : "Matches the saved workflow"}</span><details className="recovery-code__managed"><summary data-testid="workflow-recovery-source-managed-details">Managed by Wright</summary><span>Definition revision {hostDefinitionRevision} · integrity {semanticDigest}</span></details><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-source-apply" onClick={applySource}>Apply checked edit</button></footer>
          </section>}
          {diagnostics.length > 0 && <div className="recovery-diagnostics" role="alert"><button type="button" className="recovery-diagnostics__dismiss" data-testid="workflow-recovery-dismiss-diagnostics" aria-label="Dismiss workflow messages" onClick={() => { setDiagnostics([]); checkButtonRef.current?.focus(); }}>Dismiss ×</button>{diagnostics.map((item, index) => <article key={`${item.code}-${index}`} role={item.semanticId ? "button" : undefined} tabIndex={item.semanticId ? 0 : undefined} onClick={() => { if (item.semanticId) { setSelectedId(item.semanticId); const range = parsedSource.sourceMap[item.semanticId]; if (range && sourceRef.current) { sourceRef.current.focus(); sourceRef.current.setSelectionRange(range.startOffset, range.endOffset); } } }} onKeyDown={(event) => { if (item.semanticId && (event.key === "Enter" || event.key === " ")) event.currentTarget.click(); }} data-testid={`workflow-recovery-diagnostic-${item.code}`} data-semantic-id={item.semanticId ?? ""} data-source-line={item.line ?? ""}><b>{item.code}</b><span>{item.explanation}</span><small>Correction: {item.correction}</small></article>)}</div>}
        </div>

        {hasInspection && <aside className="recovery-inspector" data-testid="workflow-recovery-inspector">
          <div className="recovery-inspector__titlebar"><b>Inspector</b><button type="button" data-testid="workflow-recovery-inspector-close" aria-label="Collapse Inspector" onClick={() => setInspectorOpen(false)}>⌄</button></div>
          <div className="recovery-panel-heading"><span>{candidateSelection ? "EXAMPLE SUGGESTION · READ-ONLY" : proposal !== null ? "REVIEW MODE · READ-ONLY" : selectedPort ? "CONNECTION ENDPOINT" : ""}</span>{selectedBlock ? <BlockNameHeading key={selectedBlock.id} title={selectedBlock.title} readOnly={candidateSelection || proposal !== null || workflowRunPending || runStage > 0 || sourceDirty || saveState === "saving"} onRename={(title) => applyCommands("form", [{ kind: "set_block_title", blockId: selectedBlock.id, title }])} /> : <h2>{selectedPort?.name ?? selectedRelationship?.label}</h2>}<small>{selectedBlock ? selectedBlock.configuration.authoring_template === "mcp-task" ? "AI task · MCP" : isPromptBlock(selectedBlock) ? "AI prompt" : isMcpBlock(selectedBlock) ? "MCP tool" : selectedBlock.executionKind === "ai_capable" ? "AI task" : selectedBlock.executionKind === "human" ? "Engineer review" : "Task" : selectedPort ? selectedOwner?.title : "Connection between steps"}</small></div>
          {!selectedBlock && <div className={`recovery-inspector__tabs ${selectedBlock?.executionKind === "ai_capable" && selectedBlock.kind === "work" ? "recovery-inspector__tabs--prompt" : ""}`} role="tablist" aria-label="Step detail sections">
            {((selectedBlock?.executionKind === "ai_capable" && selectedBlock.kind === "work" ? ["definition", "inputs", "outputs"] : ["overview", "definition", "inputs", "outputs"]) as InspectorTab[]).map((tab) => <button key={tab} type="button" role="tab" aria-selected={inspectorTab === tab} data-testid={`workflow-recovery-inspector-tab-${tab}`} onClick={() => setInspectorTab(tab)}>{tab === "definition" && selectedBlock?.executionKind === "ai_capable" && selectedBlock.kind === "work" ? "Prompt" : inspectorTabLabel[tab]}</button>)}
          </div>}
          <div className="recovery-inspector__body">
            {selectedBlock && recoveryAuthoringSectionKind(selectedBlock) === "input" && <InputBlockEditor isImage={selectedBlock.outputPortIds.some(id => findPort(inspectionWorkflow, id)?.typeId === "type.image.reference-set")} key={selectedBlock.id} block={selectedBlock} sessionId={workspaceSessionId} onListFiles={onListWorkspaceFiles} readOnly={blockEditorReadOnly} onApply={(commands) => applyCommands("form", commands)} />}
            {selectedBlock && isMcpBlock(selectedBlock) && <McpBlockEditor key={selectedBlock.id} block={selectedBlock} workflow={inspectionWorkflow} sessionId={workspaceSessionId} readOnly={blockEditorReadOnly} onApply={(commands) => applyCommands("form", commands)} />}
            {selectedBlock && isPromptBlock(selectedBlock) && <PromptBlockEditor sessionId={workspaceSessionId} key={selectedBlock.id} block={selectedBlock} workflow={inspectionWorkflow} readOnly={blockEditorReadOnly} onApply={(commands) => applyCommands("form", commands)} />}
            {selectedBlock && !isPromptBlock(selectedBlock) && !isMcpBlock(selectedBlock) && recoveryAuthoringSectionKind(selectedBlock) !== "input" && <>
              <AuthoringSettings direct key={selectedBlock.id} block={selectedBlock} workflow={inspectionWorkflow} readOnly={blockEditorReadOnly} onApply={(commands) => applyCommands("form", commands)} onDelete={() => requestDelete(selectedBlock.id)} />
              {(selectedBlock.inputPortIds.length > 0 || selectedBlock.outputPortIds.length > 0) && <details key={`connections-${selectedBlock.id}`} className="recovery-technical-details" open={inspectorTab === "inputs" || inspectorTab === "outputs"}>
                <summary data-testid="workflow-recovery-block-connections">Connections</summary>
                {selectedBlock.inputPortIds.length > 0 && <><h3>Inputs</h3><PortInspector direction="input" workflow={inspectionWorkflow} blockId={selectedBlock.id} run={run} onSelect={(id) => selectObject(id)} /></>}
                {selectedBlock.outputPortIds.length > 0 && <><h3>Outputs</h3><PortInspector direction="output" workflow={inspectionWorkflow} blockId={selectedBlock.id} run={run} onSelect={(id) => selectObject(id)} onOutput={() => setModal("output")} /></>}
              </details>}
            </>}
            {(inspectorTab === "definition" || inspectorTab === "overview") && selectedRelationship && <RelationshipInspector relationshipId={selectedRelationship.id} workflow={inspectionWorkflow} readOnly={proposal !== null} onApply={(commands) => applyCommands("form", commands)} onDisconnect={() => handleIntent({ type: "delete-connection", semanticId: selectedRelationship.id })} />}
            {inspectorTab === "overview" && selectedPort && <AuthoringPortConnections workflow={inspectionWorkflow} portId={selectedPort.id} onSelect={(id) => selectObject(id)} />}
            {inspectorTab === "definition" && selectedPort && <section><div className="recovery-fact"><span>Item</span><b>{selectedPort.name}</b></div><div className="recovery-fact"><span>How it is used</span><b>{selectedPort.direction === "input" ? "Used by this step" : "Created by this step"}</b></div><div className="recovery-fact"><span>Requirement</span><b>{selectedPort.required ? "Required" : "Optional"}</b></div><p>{selectedPort.description}</p><details className="recovery-technical-details"><summary data-testid={`workflow-recovery-port-technical-${selectedPort.id}`}>Technical details</summary><code>{selectedPort.typeId}</code><code>{selectedPort.id}</code></details></section>}
            {!selectedBlock && inspectorTab === "inputs" && !isPromptBlock(selectedBlock) && !isMcpBlock(selectedBlock) && !(selectedBlock && recoveryAuthoringSectionKind(selectedBlock) === "input") && selectedBlock?.configuration.authoring_template !== "manual-review" && <PortInspector direction="input" workflow={inspectionWorkflow} blockId={selectedOwner?.id ?? null} run={run} onSelect={(id) => selectObject(id)} />}
            {!selectedBlock && inspectorTab === "outputs" && !isPromptBlock(selectedBlock) && !isMcpBlock(selectedBlock) && !(selectedBlock && recoveryAuthoringSectionKind(selectedBlock) === "input") && selectedBlock?.configuration.authoring_template !== "manual-review" && <PortInspector direction="output" workflow={inspectionWorkflow} blockId={selectedOwner?.id ?? null} run={run} onSelect={(id) => selectObject(id)} onOutput={() => setModal("output")} />}
            {inspectorTab === "activity" && <section>{run.activity.length === 0 ? <p>No simulated activity yet.</p> : run.activity.map((item) => <div className="recovery-activity" key={`${item.at}-${item.label}`}><time>{item.at}</time><div><b>{item.label}</b><span>{item.detail}</span></div></div>)}{selectedStep && <div className={`recovery-run-detail recovery-run-detail--${selectedStep.state}`} data-testid={`workflow-recovery-run-step-${selectedBlock?.id}`}><b>{selectedStep.label}</b><span>{selectedStep.detail}</span></div>}</section>}
            {inspectorTab === "diagnosis" && <section><div className="recovery-diagnosis"><b>{run.state === "needs-input" ? "Design decision is missing" : run.state === "failed" ? "Simulated export failed" : run.state === "stale" ? "Output revision is stale" : "No unresolved diagnosis"}</b><p>{run.state === "needs-input" ? "Material and temper are not stated in the design intent. The design specification cannot be accepted, so CAD and downstream work remain blocked." : "This projection is isolated from the accepted definition."}</p></div>{simulationPreview && <><button type="button" data-testid="workflow-recovery-diagnosis-show-failed" onClick={() => setRunOverride("failed")}>Show failed projection</button><button type="button" data-testid="workflow-recovery-diagnosis-show-stale" onClick={() => setRunOverride("stale")}>Show stale projection</button></>}</section>}
          </div>
          {selectedBlock?.bindingId && <details className="recovery-binding"><summary data-testid="workflow-recovery-binding-disclosure">Automation details</summary>{(() => { const binding = inspectionWorkflow.bindings.find((item) => item.id === selectedBlock.bindingId); return binding ? <div><code>{binding.id}</code><span>{binding.kind} · {binding.capabilityName}</span><span>{binding.serverId ?? "internal"} / {binding.toolId}</span><span>Schema {binding.schemaDigest}</span><span>Approval: {binding.approvalPolicy}</span><b>Exact argument map</b>{binding.argumentMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}<b>Exact result map</b>{binding.resultMap.map((item) => <code key={`${item.semanticSource}-${item.implementationTarget}`}>{item.semanticSource} → {item.implementationTarget}</code>)}</div> : null; })()}</details>}
        </aside>}
      </div>

      <section className={`recovery-run-drawer ${runDetailsOpen ? "is-open" : ""}`} data-testid="workflow-recovery-run-drawer"><button type="button" className="recovery-run-drawer__toggle" data-testid="workflow-recovery-run-details-toggle" aria-expanded={runDetailsOpen} onClick={() => setRunDetailsOpen(!runDetailsOpen)}><b>▷ Run details</b><span>{onRun ? observedStatus ? observedStatus.label : presentedPending ? `Running saved workflow…${observer.error ? " · Status not refreshed" : ""}` : reviewPresentation ? reviewPresentation.label : presentedRun ? `Completed · ${presentedRun.outputPath}` : presentedError ? presentedError.startsWith("Workflow cancelled.") ? "Run cancelled" : "Run failed" : "Ready to run" : runStage > 0 ? `Simulation · ${runStateLabel[run.state]}` : simulationPreview ? "No run · local simulation available for the unchanged example" : "No run · execution not connected"}</span><span aria-hidden="true">{runDetailsOpen ? "⌄" : "⌃"}</span></button>
        {runDetailsOpen && <div className="recovery-run-drawer__body">{onRun ? <NativeRunPanel reviews={documentReviews} onOpenFile={onOpenFile} pending={presentedPending} result={presentedRun} error={presentedError} prompt={nativeRunInput?.prompt ?? ""} executionKind={observed?.execution?.last_progress?.execution_kind ?? nativeRunInput?.executionKind} taskTitle={observed ? observed.execution?.last_progress?.task_title ?? "the active step" : nativeRunInput?.taskTitle ?? nativeRunBlock?.title ?? "the active step"} workflowPath={nativeRunInput?.workflowPath ?? workflowFilePath} workspaceSessionId={workspaceSessionId} storageDigest={observed?.source_digest ?? nativeRunInput?.storageDigest} startedAt={presentedStartedAt} completedAt={presentedCompletedAt} events={presentedEvents} partialResults={observed?.results ?? nativePartialResults} runLogPath={presentedRunLogPath} observed={observed} statusPresentation={observedStatus} sourceMismatch={observedSourceMismatch} refreshError={observer.error} onRefresh={observer.refresh} /> : runStage === 0 ? <p>{simulationPreview ? "No engineering tool has run. Simulation replays a fixed example and never creates engineering evidence." : "This build supports process authoring. Automatic execution through MCP tools is not connected yet; no process has been queued."}{simulationPreview && simulationIssue && ` ${simulationIssue}`}</p> : <section className="recovery-runbar" data-testid="workflow-recovery-run-mode" data-subject-revision={run.workflowRevision} data-subject-semantic-digest={run.semanticSha256} data-subject-storage-digest={runSubject?.storageDigest ?? ""}>
          <div><b>SIMULATION · NO EXTERNAL TOOLS</b><span>Workflow version {run.workflowRevision} · {runStateLabel[run.state]}</span></div>
          <details className="recovery-technical-details"><summary data-testid="workflow-recovery-run-subject-details">Run subject</summary><span>Definition semantic SHA-256 {run.semanticSha256}</span><span>Stored file SHA-256 {runSubject?.storageDigest}</span></details>
          <span data-testid="workflow-recovery-run-definition-lock">End this test before changing the workflow definition. Canvas layout moves remain available.</span>
          <div className="recovery-runbar__actions">{run.state === "needs-input" && <button type="button" data-testid="workflow-recovery-run-recover" onClick={() => { setMaterialSupplied(true); setRunStage(4); }}>Simulate supplying 6061-T6</button>}{runStage < 10 && run.state !== "needs-input" && <button type="button" data-testid="workflow-recovery-run-advance" onClick={nextRun}>Advance simulation</button>}{runStage >= 7 && <><button type="button" data-testid="workflow-recovery-run-project-failed" onClick={() => setRunOverride("failed")}>Preview failed run</button><button type="button" data-testid="workflow-recovery-run-project-stale" onClick={() => setRunOverride("stale")}>Preview out-of-date result</button></>}<button type="button" data-testid="workflow-recovery-run-end" onClick={endRun}>End test</button></div>
          <div className="recovery-runbar__navigation"><button type="button" data-testid="workflow-recovery-inspector-tab-activity" onClick={() => { selectObject(run.activeBlockId ?? selectedOwner?.id ?? "block.export-step", "activity"); }}>Run log</button><button type="button" data-testid="workflow-recovery-inspector-tab-diagnosis" onClick={() => { selectObject(run.activeBlockId ?? selectedOwner?.id ?? "block.export-step", "diagnosis"); }}>Issues</button>{run.outputsReady && <button type="button" data-testid="workflow-recovery-run-output" onClick={() => setModal("output")}>Open demo output</button>}</div>
        </section>}</div>}
      </section>

      {proposal && proposalResult && <section className="recovery-proposal" data-testid="workflow-recovery-proposal" data-base-revision={proposal.baseRevision} data-validation={proposalResult.ok ? "valid" : "invalid"}>
        <header><div><span>EXAMPLE SUGGESTION · NO LIVE AI CALL</span><h2>Add drawing creation and review</h2></div><b>{proposalResult.ok ? "✓ workflow checks pass" : "! suggestion has issues"}</b></header>
        <div className="recovery-proposal__grid"><div><h3>Assumptions</h3><ul><li>The approved CAD model is the drawing source.</li><li>ASME Y14.5 and A3 are suggested review defaults, not hidden commitments.</li></ul><h3>Warnings</h3><ul><li>No drawing template or automation is selected.</li><li>Adding these steps does not run or approve them.</li></ul></div><div data-testid="workflow-recovery-proposal-change-list"><h3>Changes</h3>{proposalChangeSummaries(proposal, candidateWorkflow).map((line) => <p key={line}>＋ {line}</p>)}<details className="recovery-technical-details"><summary data-testid="workflow-recovery-proposal-technical-diff">Technical details</summary><pre>{proposalResult.diff.join("\n")}</pre></details></div><div className="recovery-proposal__preview" data-testid="workflow-recovery-proposal-preview"><h3>Suggested workflow steps</h3><span>The diagram previews the full suggestion. New steps are dashed and clearly marked until you add them.</span><b>Approved CAD model ┄▷ Create manufacturing drawing</b><b>Manufacturing drawing ┄▷ Review manufacturing drawing</b><small>Preview only · not part of the current workflow</small><details><summary data-testid="workflow-recovery-proposal-code-disclosure">View suggested source</summary><pre>{proposalResult.workflow ? formatRecoveryAuthoringSource(proposalResult.workflow).text : "Suggestion has issues"}</pre></details></div></div>
        <footer><button type="button" className="recovery-button recovery-button--quiet" data-testid="workflow-recovery-proposal-reject" onClick={() => { setProposal(null); setProposalResult(null); }}>Discard suggestion</button><button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-proposal-accept" disabled={!proposalResult.ok || sourceDirty} onClick={() => { if (!sourceDirty && applyBatch(proposal)) { setProposal(null); setProposalResult(null); } }}>Add suggested steps</button></footer>
      </section>}

      {modal !== "none" && createPortal(<div className="recovery-modal-backdrop workflow-recovery-modal-theme" data-testid="workflow-recovery-modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) { event.preventDefault(); setModal("none"); } }} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); setModal("none"); return; } if (event.key === "Tab" && modalRef.current) { const focusable = [...modalRef.current.querySelectorAll<HTMLElement>('button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]; if (focusable.length === 0) return; const first = focusable[0]!; const last = focusable.at(-1)!; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } } }}><section ref={modalRef} className={`recovery-modal recovery-modal--${modal}`} role="dialog" aria-modal="true" aria-labelledby="recovery-modal-title">
        <header><div><span>{modal === "source-compare" || modal === "reload-stored" ? "WORKSPACE FILE CONFLICT" : modal === "run-preflight" ? "RUN CHECK" : "LOCAL CONCEPT PREVIEW"}</span><h2 id="recovery-modal-title">{modal === "port-lab" ? "Connection style preview" : modal === "delete" ? "Delete workflow step" : modal === "output" ? "Mounting bracket STEP file" : modal === "run-preflight" ? "Process cannot start" : modal === "source-compare" ? "Compare workflow sources" : "Reload stored workflow?"}</h2></div><button type="button" data-testid="workflow-recovery-modal-close" aria-label="Close dialog" onClick={() => setModal("none")}>×</button></header>
        {modal === "port-lab" && <div data-testid="workflow-port-lab"><p className="recovery-modal__lead">Compare how an engineer connects required items between steps and separately opens the related file, CAD model, or report.</p><div className="port-lab-grid"><TreatmentCard treatment="dot" selected={portTreatment === "dot"} onSelect={() => setPortTreatment("dot")} /><TreatmentCard treatment="terminal" selected={portTreatment === "terminal"} onSelect={() => setPortTreatment("terminal")} /><TreatmentCard treatment="hybrid" selected={portTreatment === "hybrid"} onSelect={() => setPortTreatment("hybrid")} /></div><div className="port-lab-result"><b>Current connection style: {portTreatment}</b><span>This changes only the local concept preview.</span></div></div>}
        {modal === "run-preflight" && <div className="recovery-run-preflight" data-testid="workflow-recovery-run-preflight">
          <div role="alert"><b>Nothing was started or queued.</b>
            {missingInputs.length > 0 && <p>{missingInputs.length} input{missingInputs.length === 1 ? " needs" : "s need"} configuration. Choose an input below, supply its value in Settings, and click Apply settings.</p>}
            {(sourceDirty || !sourceValid || semanticDirty || saveConflict || saveState !== "saved") && <p>{runDisabledReason}</p>}
          </div>
          <ul>{missingInputs.map((input) => <li key={input.blockId}><div><b>{input.title}</b><p>{input.reason}</p></div><button type="button" className="recovery-button" data-testid={`workflow-recovery-run-fix-${input.blockId}`} onClick={() => { setModal("none"); selectObject(input.blockId, "definition"); }}>Configure {input.title}</button></li>)}</ul>
          <p data-testid="workflow-recovery-execution-unavailable"><b>Automatic execution is not available in this build.</b> The process runner still needs to be connected to MCP tools. This requires an implementation update; configuring inputs alone will not enable execution.</p>
        </div>}
        {modal === "delete" && deleteTargetId && <div className="recovery-delete-confirmation"><p>Delete <b>{findBlock(workflow, deleteTargetId)?.title}</b>?</p><p>{deleteImpact?.relationships.length ?? 0} connection(s) will be removed with this object in one change. You can undo the complete change.</p>{deleteImpact?.blockedReason && <p role="alert">{deleteImpact.blockedReason}</p>}<div><button type="button" data-testid="workflow-recovery-delete-cancel" onClick={() => setModal("none")}>Keep step</button><button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-delete-confirm" disabled={Boolean(deleteImpact?.blockedReason)} onClick={() => { try { if (applyCommands("graph", buildDeletionCommands(workflow, deleteTargetId))) { setModal("none"); selectObject(null); } } catch (error) { setDiagnostics([{ code: "WFR-DELETE-BLOCKED", semanticId: deleteTargetId, line: null, explanation: error instanceof Error ? error.message : "This object cannot be deleted safely.", correction: "Review its dependencies before retrying." }]); } }}>Delete step and connections</button></div></div>}
        {modal === "output" && <div className="output-preview"><img src={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.svg`} alt="Isometric L-shaped mounting bracket with four holes" /><aside><b>mounting-bracket-simulated-fixture.step</b><span>STEP AP242 file</span><span>Demo STEP file. This simulated workflow did not create this file.</span><span>Workflow test version {run.workflowRevision}</span>{stepArtifact && <><span>Recorded demo output</span><span>File sha256:{stepArtifact.digestSha256}</span></>}<div className="recovery-lineage" data-testid="workflow-recovery-output-lineage"><b>Created from</b><span>Approved CAD model and design-review decision</span><span>Bracket CAD model and manufacturing check report</span><span>Reviewed design specification</span><span>Design intent + reference images + company standards and context</span></div><div><a className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-output-open-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/manufacturability-report.html`} target="_blank" rel="noreferrer">Open demo manufacturing report</a><a className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-download-artifact.step" href={`${import.meta.env.BASE_URL}recovery-concept/mounting-bracket.step`} download="mounting-bracket-simulated-fixture.step">Download demo STEP file</a></div></aside></div>}
        {modal === "source-compare" && storedComparison && <div className="recovery-source-compare" data-testid="workflow-recovery-source-comparison">
          <p>The local source on the left is unchanged. The workspace file on the right was read again for this comparison; neither version has been applied or saved.</p>
          <div className="recovery-source-compare__grid">
            <section><header><h3>Local unsaved source</h3><span>Protected in this editor</span></header><textarea data-testid="workflow-recovery-source-comparison-local" aria-label="Local unsaved workflow source" readOnly value={sourceDraft} /></section>
            <section><header><h3>Current stored source</h3><span>Workflow version {storedComparison.definition_revision}</span></header><textarea data-testid="workflow-recovery-source-comparison-stored" aria-label="Current stored workflow source" readOnly value={storedComparison.source} /></section>
          </div>
          <small>Comparing does not resolve the conflict. Copy the local source if you need to preserve it outside this editor, or explicitly reload the stored file.</small>
        </div>}
        {modal === "reload-stored" && <div className="recovery-reload-confirmation" data-testid="workflow-recovery-reload-confirmation">
          <p><b>This will discard the unsaved local workflow edits in this editor.</b></p>
          <p>The latest workflow file will be read from the current workspace and the editor will be initialized from that exact stored version. Nothing is overwritten.</p>
          {conflictActionMessage && <p role="alert" data-testid="workflow-recovery-reload-error">{conflictActionMessage}</p>}
          <div><button type="button" className="recovery-button recovery-button--secondary" data-testid="workflow-recovery-conflict-reload-cancel" disabled={conflictAction === "reloading"} onClick={() => setModal("none")}>Keep local edits</button><button type="button" className="recovery-button recovery-button--danger" data-testid="workflow-recovery-conflict-reload-confirm" disabled={conflictAction === "reloading" || !onReloadStoredSource} onClick={() => void reloadStoredWorkflowSource()}>{conflictAction === "reloading" ? "Reloading stored file…" : "Discard local edits and reload stored file"}</button></div>
        </div>}
      </section></div>, document.body)}
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


function PortInspector({ direction, workflow, blockId, run, onOutput, onSelect }: { readonly direction: "input" | "output"; readonly workflow: RecoveryWorkflow; readonly blockId: string | null; readonly run: RecoveryRunProjection; readonly onOutput?: () => void; readonly onSelect: (id: string) => void }) {
  const block = findBlock(workflow, blockId);
  if (!block) return <p>Select a step to see its {direction === "input" ? "inputs" : "outputs"}.</p>;
  const ids = direction === "input" ? block.inputPortIds : block.outputPortIds;
  return <section>{ids.length === 0 ? <p>{direction === "input" ? "This step is driven by its prompt; it does not consume a separate workflow input." : "This step does not declare an output yet."}</p> : ids.map((id) => { const port = findPort(workflow, id)!; const artifact = workflow.artifactContracts.find((item) => item.id === port.artifactContractId); const outputReady = direction === "output" && run.outputsReady && port.id === "port.step-out"; return <article className="recovery-port-card" key={id}><header><b>{port.name}</b><span>{port.required ? "Required" : "Optional"}</span></header><p>{port.description}</p><AuthoringPortConnections workflow={workflow} portId={port.id} onSelect={onSelect} />{artifact && <small>{mediaLabel(artifact.mediaType)} · {direction === "input" ? "Used by this step" : "Created by this step"}</small>}<details className="recovery-technical-details"><summary data-testid={`workflow-recovery-port-details-${port.id}`}>Technical details</summary><code>{port.typeId}</code><code>{port.artifactContractId ?? "No stored item contract"}</code>{artifact && <code>{artifact.mediaType}</code>}</details>{outputReady && <button type="button" className="recovery-button recovery-button--primary" data-testid="workflow-recovery-output-artifact.step" onClick={onOutput}>Open STEP file</button>}{port.id === "port.design-intent-in" && run.state === "needs-input" && <div className="recovery-port-card__missing">! Material and temper are not stated in the design intent. Add the decision before the design specification can be accepted.</div>}</article>; })}</section>;
}

export default WorkflowRecoveryConcept;
