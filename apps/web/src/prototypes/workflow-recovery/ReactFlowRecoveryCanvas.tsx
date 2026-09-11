import {
  Background,
  BaseEdge,
  ControlButton,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  getBezierPath,
  useReactFlow,
  useNodesState,
  useNodesInitialized,
  useStore,
  useUpdateNodeInternals,
  type Connection,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeChange,
  type NodeProps,
} from "@xyflow/react";
import { createContext, memo, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import "@xyflow/react/dist/style.css";

import type { DraftBlockProjection, DraftPortProjection } from "../../components/workflow-composer/draft-projection";
import type { DraftCanvasRenderer } from "../../components/workflow-composer/renderer-types";
import {
  findBlockByIdentity,
  graphDetailLevel,
  projectComponentStates,
  type DraftComponentState,
} from "../../components/workflow-composer/component-graph";
import { validateRecoveryRunProjection, type RecoveryRelationship, type RecoveryRunProjection, type RecoveryRunState, type RecoveryRunSubject } from "./model";
import { WorkflowObjectIcon } from "./WorkflowObjectIcon";
import { canConnectAuthoringPorts } from "./authoring-objects";

interface RecoveryCanvasRuntime {
  readonly outputLabels?: Readonly<Record<string,string>>;
  readonly outputGroups?: Readonly<Record<string,string>>;
  readonly hiddenPorts?: ReadonlySet<string>;
  readonly run: RecoveryRunProjection;
  readonly runSubject: RecoveryRunSubject | null;
  readonly proposedBlockIds: ReadonlySet<string>;
  readonly portArtifactIds: Readonly<Record<string, string>>;
  readonly relationshipLabels: Readonly<Record<string, string>>;
  readonly overlayRelationships: readonly RecoveryRelationship[];
  readonly portTreatment: "dot" | "terminal" | "hybrid";
  readonly onArtifactInspect: (portId: string) => void;
  readonly focusPath?: boolean;
  readonly blockIcons?: Readonly<Record<string, string>>;
  readonly readOnly?: boolean;
  readonly canConnect?: (sourcePortId: string, targetPortId: string) => boolean;
  readonly connectionIssue?: (sourcePortId: string, targetPortId: string) => string | null | undefined;
}

const emptyRun: RecoveryRunProjection = {
  documentKind: "workflow-run",
  schemaVersion: "1.0.0-recovery.1",
  runId: "run.none",
  workflowId: "workflow.none",
  workflowRevision: 0,
  semanticSha256: "",
  createdAt: "",
  completedAt: null,
  mode: "simulated",
  state: "idle",
  activeBlockId: null,
  activeRelationshipId: null,
  steps: {},
  activity: [],
  artifactRecords: [],
  materialSupplied: false,
  outputsReady: false,
};

const RuntimeContext = createContext<RecoveryCanvasRuntime>({
  run: emptyRun,
  runSubject: null,
  proposedBlockIds: new Set(),
  portArtifactIds: {},
  relationshipLabels: {},
  overlayRelationships: [],
  portTreatment: "dot",
  onArtifactInspect: () => undefined,
});

export function RecoveryCanvasRuntimeProvider({
  children,
  value,
}: {
  readonly children: ReactNode;
  readonly value: RecoveryCanvasRuntime;
}) {
  return <RuntimeContext.Provider value={value}>{children}</RuntimeContext.Provider>;
}

interface RecoveryNodeData extends Record<string, unknown> {
  readonly outputGroups?: Readonly<Record<string,string>>;
  readonly block: DraftBlockProjection;
  readonly selected: boolean;
  readonly runState: RecoveryRunState;
  readonly active: boolean;
  readonly proposed: boolean;
  readonly componentState: DraftComponentState | null;
  readonly detailLevel: "detailed" | "compact";
  readonly keyboardSource: string | null;
  readonly onSelect: (semanticId: string) => void;
  readonly onPortKey: (port: DraftPortProjection) => void;
  readonly onToggleComponent: (semanticId: string) => void;
  readonly muted: boolean;
  readonly iconKind: string;
  readonly readOnly: boolean;
  readonly onRename: (title: string) => void;
  readonly onDelete: () => void;
}

type RecoveryFlowNode = Node<RecoveryNodeData, "recovery">;

const stateGlyph: Record<RecoveryRunState, string> = {
  idle: "○",
  queued: "◷",
  running: "▶",
  "needs-input": "!",
  succeeded: "✓",
  failed: "×",
  blocked: "⊘",
  stale: "↺",
};

const roleLabel: Record<DraftBlockProjection["role"], string> = {
  input: "input source",
  work: "task",
  review: "design review",
  release: "output",
};

const SHORT_VIEWPORT_QUERY = "(max-height: 550px)";

function blockIcon(block: DraftBlockProjection): string {
  const types = [...block.inputs, ...block.outputs].map((port) => port.value_type_id).join(" ");
  if (block.role === "input") return types.includes("image") ? "image" : types.includes("context") ? "context" : types.includes("file.workspace") ? "file" : "text";
  if (block.role === "release") return "output";
  if (block.role === "review") return types.includes("geometry") ? "review" : "llm-document";
  if (types.includes("drawing")) return "drawing";
  if (types.includes("toolpath")) return "fdm";
  if (block.outputs.some((port) => port.value_type_id.includes("report"))) return "3d-check";
  if (block.outputs.some((port) => port.value_type_id.includes("geometry"))) return "model";
  // Port types alone do not establish whether a generic step invokes AI or a
  // tool. The host supplies canonical operation-aware icons through runtime.
  return "more";
}

function componentAddressLabel(semanticId: string, conceptKind: string): string {
  if (semanticId.endsWith(".block.evaluate")) return "Evaluate the design review";
  if (semanticId.endsWith(".relationship.accept")) return "Accept the reviewed design";
  if (semanticId.endsWith(".artifact.approved")) return "Approved design record";
  if (semanticId.endsWith(".port.approved")) return "Approved CAD model output";
  return conceptKind.replace("_", " ");
}

type RecoveryRoutingKind = "flow" | "feedback";
type RecoveryRoutingDirection = "source" | "target";

export function recoveryRelationshipHandleId(
  blockId: string,
  kind: RecoveryRoutingKind,
  direction: RecoveryRoutingDirection,
): string {
  return `routing.${kind}.${direction}.${blockId}`;
}

export function recoveryRelationshipHandleBinding(
  kind: RecoveryRoutingKind,
  sourceBlockId: string,
  targetBlockId: string,
): { readonly sourceHandle: string; readonly targetHandle: string } {
  return {
    sourceHandle: recoveryRelationshipHandleId(sourceBlockId, kind, "source"),
    targetHandle: recoveryRelationshipHandleId(targetBlockId, kind, "target"),
  };
}

function RelationshipRoutingHandles({ blockId }: { readonly blockId: string }) {
  return <>
    {(["flow", "feedback"] as const).flatMap((kind) => (["source", "target"] as const).map((direction) => {
      const id = recoveryRelationshipHandleId(blockId, kind, direction);
      const isFeedback = kind === "feedback";
      return (
        <Handle
          key={id}
          id={id}
          type={direction}
          position={isFeedback ? Position.Bottom : direction === "source" ? Position.Right : Position.Left}
          className={`recovery-routing-handle recovery-routing-handle--${kind}-${direction}`}
          data-testid={`workflow-recovery-routing-handle-${kind}-${direction}-${blockId}`}
          data-routing-kind={kind}
          data-routing-direction={direction}
          aria-hidden="true"
          tabIndex={-1}
          isConnectable={false}
        />
      );
    }))}
  </>;
}

function PortRow({
  port,
  side,
  keyboardSource,
  onPortKey,
}: {
  readonly port: DraftPortProjection;
  readonly side: "input" | "output";
  readonly keyboardSource: string | null;
  readonly onPortKey: (port: DraftPortProjection) => void;
}) {
  const handle = (
    <Handle
      id={port.semanticId}
      type={side === "input" ? "target" : "source"}
      position={side === "input" ? Position.Left : Position.Right}
      className={`recovery-port__handle recovery-port__handle--${side}`}
      data-testid={`workflow-recovery-handle-${port.semanticId}`}
      data-port-direction={side}
      data-port-type={port.value_type_id}
      data-required={port.required}
      data-cardinality={port.cardinality}
      aria-label={`${side === "input" ? "Connect to" : "Connect from"} ${port.name} ${side}`}
      role="button"
      aria-pressed={keyboardSource === port.semanticId}
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          event.stopPropagation();
          onPortKey(port);
        }
      }}
    />
  );
  return (
    <div className={`recovery-port recovery-port--${side}`} data-semantic-id={port.semanticId} title={port.name}>
      {side === "input" && handle}
      <span className="recovery-port__tooltip" aria-hidden="true">{port.name}</span>
      {side === "output" && handle}
    </div>
  );
}

const RecoveryBlockNode = memo(function RecoveryBlockNode({ data }: NodeProps<RecoveryFlowNode>) {
  const block = data.block;
  const updateInternals = useUpdateNodeInternals();
  const portIdentity = [...block.inputs, ...block.outputs].map(port => port.semanticId).join("|");
  useEffect(() => { updateInternals(block.semanticId); }, [block.semanticId, portIdentity, updateInternals]);
  const [renaming, setRenaming] = useState(false);
  const [title, setTitle] = useState(block.title);
  const startRename = () => {
    if (data.readOnly) return;
    setTitle(block.title);
    setRenaming(true);
  };
  const finishRename = () => {
    setRenaming(false);
    if (!data.readOnly && title.trim() && title.trim() !== block.title) data.onRename(title.trim());
  };
  return (
    <article
      className={`recovery-block recovery-block--${block.role}${data.selected ? " is-selected" : ""}${data.active ? " is-active" : ""}${data.proposed ? " is-proposed" : ""}${data.muted ? " is-muted" : ""}`}
      data-testid={`workflow-recovery-block-${block.semanticId}`}
      data-semantic-id={block.semanticId}
      data-selected={data.selected}
      data-run-state={data.runState}
      data-active={data.active}
      aria-busy={data.runState === "running"}
      data-component-collapsed={data.componentState?.collapsed ?? undefined}
      data-detail-level={data.detailLevel}
      data-endpoints-visible={data.selected || data.keyboardSource !== null}
      role="group"
      aria-label={`${block.title} workflow step`}
      aria-expanded={data.componentState === null ? undefined : !data.componentState.collapsed}
      aria-description={data.componentState === null ? undefined : "Use Right Arrow to show grouped review details and Left Arrow to hide them."}
      tabIndex={0}
      onClick={() => data.onSelect(block.semanticId)}
      onKeyDown={(event) => {
        if (event.target === event.currentTarget) {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            data.onSelect(block.semanticId);
          } else if (event.key === "F2") {
            event.preventDefault();
            event.stopPropagation();
            startRename();
          } else if (event.key === "Delete" || event.key === "Backspace") {
            event.preventDefault();
            event.stopPropagation();
            if (!data.readOnly) data.onDelete();
          } else if (data.componentState !== null && event.key === "ArrowRight" && data.componentState.collapsed) {
            event.preventDefault();
            data.onToggleComponent(block.semanticId);
          } else if (data.componentState !== null && event.key === "ArrowLeft" && !data.componentState.collapsed) {
            event.preventDefault();
            data.onToggleComponent(block.semanticId);
          }
        }
      }}
    >
      <RelationshipRoutingHandles blockId={block.semanticId} />
      {data.active && <div className="recovery-block__active">▶ ACTIVE TASK</div>}
      {data.proposed && <div className="recovery-block__proposal">AI SUGGESTION · REVIEW BEFORE ADDING</div>}
      <header className="recovery-block__heading">
        <span className="recovery-block__icon"><WorkflowObjectIcon kind={data.iconKind} /></span>
        <div className="recovery-block__identity"><span className="recovery-block__kind">{roleLabel[block.role]}</span>{renaming && !data.readOnly ? <input className="recovery-block__title-editor nodrag nopan" data-testid={`workflow-recovery-rename-${block.semanticId}`} aria-label="Step name" autoFocus value={title} onFocus={(event) => event.currentTarget.select()} onChange={(event) => setTitle(event.target.value)} onClick={(event) => event.stopPropagation()} onBlur={finishRename} onKeyDown={(event) => {
          event.stopPropagation();
          if (event.key === "Enter") { event.preventDefault(); finishRename(); }
          if (event.key === "Escape") { event.preventDefault(); setRenaming(false); }
        }} /> : <h3 title={data.readOnly ? undefined : "Double-click to rename · F2"} onDoubleClick={(event) => { event.stopPropagation(); startRename(); }}>{block.title}</h3>}</div>
        <span className={`recovery-state recovery-state--${data.runState}`} aria-label={`Run state ${data.runState}`}>
          {stateGlyph[data.runState]}{data.runState === "idle" ? "" : ` ${data.runState.replace("-", " ")}`}
        </span>
      </header>
      <div className="recovery-block__io-summary" aria-label={`${block.inputs.length} inputs and ${block.outputs.length} outputs`}>
        {block.inputs.length} in <span aria-hidden="true">→</span> {block.outputs.length} out
      </div>
      {data.componentState !== null && (
        <section className={`recovery-component${data.componentState.collapsed ? " is-collapsed" : ""}`} aria-label={`${data.componentState.component.title} grouped review details`}>
          <header>
            <strong>Review group</strong>
            <button
              className="nodrag nopan"
              data-testid={`workflow-recovery-component-toggle-${block.semanticId}`}
              type="button"
              tabIndex={0}
              aria-expanded={!data.componentState.collapsed}
              onClick={(event) => {
                event.stopPropagation();
                data.onToggleComponent(block.semanticId);
              }}
              onKeyDown={(event) => {
                event.stopPropagation();
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  data.onToggleComponent(block.semanticId);
                }
              }}
            >
              {data.componentState.collapsed ? "Details" : "Hide details"}
            </button>
          </header>
          {data.componentState.targetedInternalSemanticIds.length > 0 && (
            <div className="recovery-component__targets" role="note">
              <b>{data.componentState.targetedInternalSemanticIds.length} issue{data.componentState.targetedInternalSemanticIds.length === 1 ? "" : "s"}</b>
              {!data.componentState.collapsed && data.componentState.targetedInternalSemanticIds.map((id) => {
                const address = data.componentState?.component.internalAddresses.find((item) => item.semanticId === id);
                return <span key={id}>{componentAddressLabel(id, address?.conceptKind ?? "review item")}</span>;
              })}
            </div>
          )}
          {!data.componentState.collapsed && (
            <div className="recovery-component__details">
              <small>{data.componentState.internalAddressCount} technical review items</small>
              <ul data-testid={`workflow-recovery-component-addresses-${block.semanticId}`}>
                {data.componentState.component.internalAddresses.map((address) => (
                  <li data-semantic-id={address.semanticId} key={address.semanticId}>
                    <span>{componentAddressLabel(address.semanticId, address.conceptKind)}</span>
                    <small>{address.conceptKind.replace("_", " ")}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
      <div className="recovery-block__ports recovery-block__ports--inputs">
        {block.inputs.map((port) => <PortRow key={port.semanticId} port={port} side="input" keyboardSource={data.keyboardSource} onPortKey={data.onPortKey} />)}
      </div>
      <div className="recovery-block__ports recovery-block__ports--outputs">
        {block.outputs.map((port,index) => <div key={port.semanticId}>
          {data.outputGroups?.[port.semanticId] && (index===0 || data.outputGroups[port.semanticId]!==data.outputGroups[block.outputs[index-1].semanticId]) && <small className="recovery-output-group">{data.outputGroups[port.semanticId]}</small>}
          <PortRow port={port} side="output" keyboardSource={data.keyboardSource} onPortKey={data.onPortKey} />
        </div>)}
      </div>
      {block.gates.length > 0 && <div className="recovery-block__gate">◇ Approval required</div>}
    </article>
  );
});

interface RecoveryEdgeData extends Record<string, unknown> {
  readonly semanticId: string;
  readonly kind: "data" | "feedback" | "control" | "decision";
  readonly active: boolean;
  readonly onSelect: (semanticId: string) => void;
  readonly traced?: boolean;
  readonly muted?: boolean;
}

type RecoveryFlowEdge = Edge<RecoveryEdgeData, "recovery">;

function RecoveryEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, sourceHandleId, targetHandleId, markerEnd, label, data, selected }: EdgeProps<RecoveryFlowEdge>) {
  const [path, labelX, labelY] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, curvature: data?.kind === "feedback" ? 0.5 : 0.24 });
  const active = Boolean(data?.active);
  const stableLabelLane = [...id].reduce((sum, character) => sum + character.charCodeAt(0), 0) % 5 - 2;
  const labelOffsetY = (data?.kind === "decision" ? -20 : data?.kind === "data" ? 10 : 0) + stableLabelLane * 14;
  return (
    <g
      className={`recovery-edge${active ? " is-active" : ""}${data?.kind === "feedback" ? " is-feedback" : ""}${selected ? " is-selected" : ""}${data?.traced ? " is-traced" : ""}${data?.muted ? " is-muted" : ""}`}
      data-testid={`workflow-recovery-edge-${data?.semanticId ?? id}`}
      data-semantic-id={data?.semanticId ?? id}
      data-kind={data?.kind ?? "data"}
      data-active={active}
      data-source-handle={sourceHandleId ?? ""}
      data-target-handle={targetHandleId ?? ""}
      onClick={(event) => {
        event.stopPropagation();
        data?.onSelect(data.semanticId);
      }}
    >
      <BaseEdge id={id} path={path} markerEnd={markerEnd} interactionWidth={22} />
      <title>{String(label ?? data?.semanticId ?? id)}</title>
      <EdgeLabelRenderer>
        <button
          type="button"
          className={`recovery-edge__label nodrag nopan${selected || active ? " is-visible" : ""}`}
          style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + labelOffsetY}px)` }}
          data-testid={`workflow-recovery-edge-select-${data?.semanticId ?? id}`}
          aria-label={`Select connection ${String(label ?? data?.semanticId ?? id)}`}
          onClick={(event) => {
            event.stopPropagation();
            if (data) data.onSelect(data.semanticId);
          }}
        >
          {active ? "▶ Active flow · " : ""}{String(label ?? "")}
        </button>
      </EdgeLabelRenderer>
    </g>
  );
}

const nodeTypes = { recovery: RecoveryBlockNode };
const edgeTypes = { recovery: RecoveryEdge };

function RecoveryCanvasControls() {
  const { fitView, zoomIn, zoomOut } = useReactFlow();
  return (
    <Controls showZoom={false} showFitView={false} showInteractive={false} data-testid="workflow-recovery-canvas-controls">
      <ControlButton data-testid="workflow-recovery-canvas-zoom-in" aria-label="Zoom in" title="Zoom in" onClick={() => void zoomIn()}>＋</ControlButton>
      <ControlButton data-testid="workflow-recovery-canvas-zoom-out" aria-label="Zoom out" title="Zoom out" onClick={() => void zoomOut()}>−</ControlButton>
      <ControlButton data-testid="workflow-recovery-canvas-fit" aria-label="Fit workflow to view" title="Fit workflow to view" onClick={() => void fitView({ padding: 0.12 })}>⌗</ControlButton>
    </Controls>
  );
}

function RecoveryCanvasViewport({ selectedNodeId }: { readonly selectedNodeId: string | null }) {
  const { getNodes, getNode, getViewport, setViewport, fitView } = useReactFlow();
  const initialized = useNodesInitialized();
  const width = useStore((state) => state.width);
  const height = useStore((state) => state.height);
  const didInitialize = useRef(false);
  useEffect(() => {
    if (!initialized || !width || !height || didInitialize.current) return;
    didInitialize.current = true;
    const nodes = getNodes();
    const left = Math.min(...nodes.map((node) => node.position.x));
    const top = Math.min(...nodes.map((node) => node.position.y));
    const right = Math.max(...nodes.map((node) => node.position.x + (node.measured?.width ?? 220)));
    const bottom = Math.max(...nodes.map((node) => node.position.y + (node.measured?.height ?? 110)));
    if ((right - left) * .9 < width - 80 && (bottom - top) * .9 < height - 120) {
      void fitView({ padding: .12, minZoom: .9, maxZoom: 1 });
    } else {
      // Begin with readable objects and the input side in view. Fit remains an
      // explicit overview action; narrow windows don't silently shrink all text.
      void setViewport({ x: 40 - left * .9, y: Math.max(90, (height - (bottom - top) * .9) / 2) - top * .9, zoom: .9 });
    }
  }, [initialized, width, height, getNodes, fitView, setViewport]);
  useEffect(() => {
    if (!initialized || !selectedNodeId || !width || !height) return;
    const node = getNode(selectedNodeId);
    if (!node) return;
    const viewport = getViewport();
    const left = node.position.x * viewport.zoom + viewport.x;
    const top = node.position.y * viewport.zoom + viewport.y;
    const right = left + (node.measured?.width ?? 220) * viewport.zoom;
    const bottom = top + (node.measured?.height ?? 160) * viewport.zoom;
    const dx = left < 30 ? 30 - left : right > width - 30 ? width - 30 - right : 0;
    const dy = top < 70 ? 70 - top : bottom > height - 45 ? height - 45 - bottom : 0;
    if (dx || dy) void setViewport({ ...viewport, x: viewport.x + dx, y: viewport.y + dy }, { duration: window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? 0 : 180 });
  }, [initialized, selectedNodeId, width, height, getNode, getViewport, setViewport]);
  return null;
}

function RecoveryCanvasNavigator({
  projection,
  onSelect,
  showSearch,
}: {
  readonly projection: Parameters<typeof findBlockByIdentity>[0];
  readonly onSelect: (semanticId: string) => void;
  readonly showSearch: boolean;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const { getNode, setCenter } = useReactFlow();
  const focus = () => {
    const block = findBlockByIdentity(projection, query);
    if (block === null) {
      setStatus(`No workflow step matches ${query.trim() || "the empty query"}.`);
      return;
    }
    onSelect(block.semanticId);
    const node = getNode(block.semanticId);
    if (node !== undefined) {
      void setCenter(
        node.position.x + (node.measured?.width ?? 260) / 2,
        node.position.y + (node.measured?.height ?? 180) / 2,
        { zoom: 1, duration: 250 },
      );
    }
    setStatus(`Focused ${block.title}.`);
  };
  return <>
    {showSearch && (
      <form className="recovery-canvas__find nodrag nopan" onSubmit={(event) => { event.preventDefault(); focus(); }}>
        <label htmlFor="workflow-recovery-find">Find step</label>
        <input
          id="workflow-recovery-find"
          data-testid="workflow-recovery-find-input"
          value={query}
          placeholder="Step name"
          onChange={(event) => setQuery(event.currentTarget.value)}
        />
        <button data-testid="workflow-recovery-find-submit" type="submit">Show</button>
        {status !== "" && <output role="status" aria-live="polite">{status}</output>}
      </form>
    )}
  </>;
}

export const ReactFlowRecoveryCanvas: DraftCanvasRenderer = ({ projection, selectedSemanticId, onIntent }) => {
  const runtime = useContext(RuntimeContext);
  const runIssue = validateRecoveryRunProjection(runtime.run, runtime.runSubject)[0];
  if (runIssue) throw new Error(runIssue.code);
  const [keyboardSource, setKeyboardSource] = useState<string | null>(null);
  const [minimapVisible, setMinimapVisible] = useState(() => typeof window.matchMedia !== "function" || !window.matchMedia(SHORT_VIEWPORT_QUERY).matches);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(SHORT_VIEWPORT_QUERY);
    const onChange = (event: MediaQueryListEvent) => {
      // Entering a short effective viewport (including browser zoom) frees
      // canvas space. An explicit Show remains available until the next entry.
      if (event.matches) setMinimapVisible(false);
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);
  const blocks = useMemo(() => projection.phases.flatMap((phase) => phase.blocks), [projection]);
  const [expandedComponentIds, setExpandedComponentIds] = useState<ReadonlySet<string>>(() => new Set());
  const detailLevel = graphDetailLevel(blocks.length);
  const componentTargets = useMemo(
    () => Object.values(runtime.run.steps).flatMap((step) => step.componentScope === undefined || !["failed", "blocked", "needs-input"].includes(step.state) ? [] : [step.componentScope]),
    [runtime.run.steps],
  );
  const collapsedComponentIds = useMemo(
    () => new Set(blocks
      .filter((block) => block.componentRef !== null && block.componentRef !== undefined && !expandedComponentIds.has(block.semanticId))
      .map((block) => block.semanticId)),
    [blocks, expandedComponentIds],
  );
  const componentStates = useMemo(
    () => new Map(projectComponentStates(projection, collapsedComponentIds, componentTargets).map((state) => [state.instanceSemanticId, state])),
    [projection, collapsedComponentIds, componentTargets],
  );
  const toggleComponent = useCallback((semanticId: string) => setExpandedComponentIds((current) => {
    const next = new Set(current);
    if (next.has(semanticId)) next.delete(semanticId);
    else next.add(semanticId);
    return next;
  }), []);
  const gateOwners = useMemo(() => new Map(blocks.flatMap((block) => block.gates.map((gate) => [gate.semanticId, block.semanticId] as const))), [blocks]);

  const focusedPath = useMemo(() => {
    const relations = [
      ...projection.connections.map((connection) => ({ id: connection.semanticId, source: connection.sourceBlockId, target: connection.targetBlockId })),
      ...projection.feedbackPaths.map((path) => ({ id: path.semanticId, source: gateOwners.get(path.from_gate_id) ?? path.from_gate_id, target: path.to_block_id })),
      ...runtime.overlayRelationships.map((relationship) => ({ id: relationship.id, source: relationship.sourceId, target: relationship.targetId })),
    ];
    const selectedRelation = relations.find((item) => item.id === selectedSemanticId);
    const seeds = selectedRelation ? [selectedRelation.source, selectedRelation.target] : selectedSemanticId ? [selectedSemanticId] : [];
    const visited = new Set(seeds);
    // Trace each direction separately: siblings sharing an upstream source are not
    // part of the selected object's path unless they also lead to it.
    for (const direction of ["upstream", "downstream"] as const) {
      const frontier = [...seeds];
      const seen = new Set(seeds);
      while (frontier.length) {
        const current = frontier.pop();
        for (const relation of relations) {
          const next = direction === "upstream" && relation.target === current ? relation.source : direction === "downstream" && relation.source === current ? relation.target : null;
          if (next !== null && !seen.has(next)) { seen.add(next); visited.add(next); frontier.push(next); }
        }
      }
    }
    return { blocks: visited, edges: new Set(relations.filter((item) => visited.has(item.source) && visited.has(item.target)).map((item) => item.id)) };
  }, [gateOwners, projection.connections, projection.feedbackPaths, runtime.overlayRelationships, selectedSemanticId]);
  const focusPath = Boolean(runtime.focusPath && selectedSemanticId !== null);

  const portLookup = useMemo(() => new Map(blocks.flatMap((block) => [...block.inputs, ...block.outputs]).map((port) => [port.semanticId, port])), [blocks]);
  const canConnect = useCallback((sourceId: string, targetId: string) => {
    if (runtime.readOnly) return false;
    if (runtime.canConnect) return runtime.canConnect(sourceId, targetId);
    const source = portLookup.get(sourceId);
    const target = portLookup.get(targetId);
    return canConnectAuthoringPorts(source && { ...source, typeId: source.value_type_id, ownerBlockId: source.owner_block_id }, target && { ...target, typeId: target.value_type_id, ownerBlockId: target.owner_block_id });
  }, [portLookup, runtime.readOnly, runtime.canConnect]);
  const [connectionMessage, setConnectionMessage] = useState("");
  const blockIds = useMemo(() => new Set(blocks.map((block) => block.semanticId)), [blocks]);
  const requireBlockEndpoint = (semanticId: string, relationshipId: string, endpoint: "source" | "target") => {
    if (!blockIds.has(semanticId)) throw new Error(`RECOVERY_EDGE_${endpoint.toUpperCase()}_BLOCK_MISSING:${relationshipId}:${semanticId}`);
    return semanticId;
  };
  const onPortKey = useCallback((port: DraftPortProjection) => {
    if (runtime.readOnly) return;
    if (port.direction === "output") {
      setConnectionMessage("");
      setKeyboardSource((current) => current === port.semanticId ? null : port.semanticId);
      return;
    }
    if (keyboardSource !== null) {
      if (!canConnect(keyboardSource, port.semanticId)) {
        setConnectionMessage(runtime.connectionIssue?.(keyboardSource,port.semanticId) || (portLookup.get(keyboardSource)?.value_type_id.startsWith("type.image.") ? "Connect the image to an input that accepts images." : "Choose an input that accepts this output type."));
        return;
      }
      onIntent({ type: "create-connection", sourcePortId: keyboardSource, targetPortId: port.semanticId });
      setConnectionMessage("");
      setKeyboardSource(null);
    }
  }, [keyboardSource, onIntent, canConnect, portLookup, runtime.readOnly, runtime.connectionIssue]);

  const projectedNodes = useMemo<RecoveryFlowNode[]>(() => blocks.map((block) => ({
      id: block.semanticId,
      type: "recovery",
      position: { x: block.position.x, y: block.position.y },
      selected: selectedSemanticId === block.semanticId,
      data: {
        block: { ...block, inputs: block.inputs.filter(port => !runtime.hiddenPorts?.has(port.semanticId)), outputs:block.outputs.filter(port=>!runtime.hiddenPorts?.has(port.semanticId)).map(port=>({...port,name:runtime.outputLabels?.[port.semanticId]??port.name})) },
        outputGroups: runtime.outputGroups,
        readOnly: runtime.readOnly ?? false,
        onRename: (title) => onIntent({ type: "edit-block", semanticId: block.semanticId, title, purpose: block.purpose }),
        onDelete: () => onIntent({ type: "delete-concept", semanticId: block.semanticId }),
        iconKind: runtime.blockIcons?.[block.semanticId] ?? blockIcon(block),
        selected: selectedSemanticId === block.semanticId,
        runState: runtime.run.steps[block.semanticId]?.state ?? "idle",
        active: runtime.run.activeBlockId === block.semanticId,
        proposed: runtime.proposedBlockIds.has(block.semanticId),
        componentState: componentStates.get(block.semanticId) ?? null,
        detailLevel,
        keyboardSource,
        onSelect: (semanticId) => onIntent({ type: "select", semanticId }),
        onPortKey,
        onToggleComponent: toggleComponent,
        muted: focusPath && !focusedPath.blocks.has(block.semanticId),
      },
    })), [
      blocks,
      componentStates,
      detailLevel,
      keyboardSource,
      onIntent,
      onPortKey,
      runtime.proposedBlockIds,
      runtime.blockIcons,
      runtime.hiddenPorts,
      runtime.outputLabels,
      runtime.outputGroups,
      runtime.readOnly,
      runtime.run.activeBlockId,
      runtime.run.steps,
      selectedSemanticId,
      toggleComponent,
      focusPath,
      focusedPath,
    ]);
  const [nodes, setNodes, applyPreviewNodeChanges] = useNodesState<RecoveryFlowNode>(projectedNodes);

  useEffect(() => {
    setNodes((current) => {
      const currentById = new Map(current.map((node) => [node.id, node]));
      return projectedNodes.map((projected) => {
        const existing = currentById.get(projected.id);
        if (existing === undefined) return projected;
        return {
          ...projected,
          measured: existing.measured,
          width: existing.width,
          height: existing.height,
          position: existing.dragging ? existing.position : projected.position,
          dragging: existing.dragging,
        };
      });
    });
  }, [projectedNodes, setNodes]);

  const previewNodeChanges = useCallback((changes: NodeChange<RecoveryFlowNode>[]) => {
    applyPreviewNodeChanges(changes.filter((change) => change.type === "position" || change.type === "dimensions"));
  }, [applyPreviewNodeChanges]);

  const edges: RecoveryFlowEdge[] = [
    ...projection.connections.map((connection) => ({
      id: connection.semanticId,
      type: "recovery" as const,
      source: connection.sourceBlockId,
      target: connection.targetBlockId,
      sourceHandle: connection.source_port_id,
      targetHandle: connection.target_port_id,
      label: runtime.relationshipLabels[connection.semanticId] ?? connection.semanticId,
      selected: selectedSemanticId === connection.semanticId,
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      data: { semanticId: connection.semanticId, kind: "data" as const, active: runtime.run.activeRelationshipId === connection.semanticId, onSelect: (semanticId: string) => onIntent({ type: "select", semanticId }) },
    })),
    ...projection.feedbackPaths.map((feedback) => {
      const source = requireBlockEndpoint(gateOwners.get(feedback.from_gate_id) ?? feedback.from_gate_id, feedback.semanticId, "source");
      const target = requireBlockEndpoint(feedback.to_block_id, feedback.semanticId, "target");
      return {
        id: feedback.semanticId,
        type: "recovery" as const,
        source,
        target,
        ...recoveryRelationshipHandleBinding("feedback", source, target),
        label: feedback.label,
        selected: selectedSemanticId === feedback.semanticId,
        markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
        data: { semanticId: feedback.semanticId, kind: "feedback" as const, active: runtime.run.activeRelationshipId === feedback.semanticId, onSelect: (semanticId: string) => onIntent({ type: "select", semanticId }) },
      };
    }),
    ...runtime.overlayRelationships.map((relationship) => {
      const source = requireBlockEndpoint(relationship.sourceId, relationship.id, "source");
      const target = requireBlockEndpoint(relationship.targetId, relationship.id, "target");
      return {
        id: relationship.id,
        type: "recovery" as const,
        source,
        target,
        ...recoveryRelationshipHandleBinding("flow", source, target),
        label: relationship.label,
        selected: selectedSemanticId === relationship.id,
        markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
        data: { semanticId: relationship.id, kind: relationship.kind as "control" | "decision", active: runtime.run.activeRelationshipId === relationship.id, onSelect: (semanticId: string) => onIntent({ type: "select", semanticId }) },
      };
    }),
  ].map((edge) => ({ ...edge, data: { ...edge.data, traced: focusPath && focusedPath.edges.has(edge.id), muted: focusPath && !focusedPath.edges.has(edge.id) } }));

  const connect = (connection: Connection) => {
    if (!connection.sourceHandle || !connection.targetHandle) return;
    const source = portLookup.get(connection.sourceHandle);
    const target = portLookup.get(connection.targetHandle);
    if (!source || !target || !canConnect(source.semanticId, target.semanticId)) return;
    onIntent({ type: "create-connection", sourcePortId: source.semanticId, targetPortId: target.semanticId });
  };

  return (
    <div className={`recovery-canvas recovery-canvas--${runtime.portTreatment}`} data-testid="workflow-recovery-canvas" data-port-treatment={runtime.portTreatment} data-detail-level={detailLevel} data-focus-path={focusPath} aria-label={`${projection.title} diagram`}>
      {(keyboardSource || connectionMessage) && <div className="recovery-keyboard-connection" role="status">{connectionMessage || "Connection started. Focus a compatible input and press Enter; Escape cancels."}</div>}
      <ReactFlow
        data-testid="workflow-recovery-reactflow-pane"
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        minZoom={0.4}
        maxZoom={1.8}
        proOptions={{ hideAttribution: true }}
        defaultViewport={{ x: 40, y: 90, zoom: .9 }}
        deleteKeyCode={["Backspace", "Delete"]}
        nodesConnectable
        nodesDraggable
        edgesReconnectable={false}
        onNodesChange={previewNodeChanges}
        onPaneClick={() => onIntent({ type: "select", semanticId: null })}
        onNodeClick={(_, node) => onIntent({ type: "select", semanticId: node.id })}
        onEdgeClick={(_, edge) => onIntent({ type: "select", semanticId: edge.id })}
        onNodeDragStop={(_, node) => {
          const x = Math.round(node.position.x);
          const y = Math.round(node.position.y);
          setNodes((current) => current.map((item) => item.id === node.id
            ? { ...item, position: { x, y }, dragging: false }
            : item));
          onIntent({ type: "move-block", semanticId: node.id, x, y });
        }}
        onEdgesDelete={(deleted) => deleted.forEach((edge) => onIntent({ type: "delete-connection", semanticId: edge.id }))}
        onNodesDelete={(deleted) => deleted.forEach((node) => onIntent({ type: "delete-concept", semanticId: node.id }))}
        onConnect={connect}
        onConnectStart={()=>setConnectionMessage("")}
        onConnectEnd={(_,state)=>{
          if(state.isValid||!state.fromHandle?.id||!state.toHandle?.id)return;
          const source=state.fromHandle.type==="source"?state.fromHandle.id:state.toHandle.id;
          const target=state.fromHandle.type==="target"?state.fromHandle.id:state.toHandle.id;
          setConnectionMessage(runtime.connectionIssue?.(source,target)||"Choose an input that accepts this output type.");
        }}
        isValidConnection={(connection) => Boolean(connection.sourceHandle && connection.targetHandle && canConnect(connection.sourceHandle, connection.targetHandle))}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            setKeyboardSource(null);
            setConnectionMessage("");
            return;
          }
          if (event.key === "Enter" || event.key === " ") {
            const target = event.target instanceof HTMLElement ? event.target : null;
            const node = target?.closest<HTMLElement>('.react-flow__node[data-id]');
            if (node && target === node) {
              event.preventDefault();
              onIntent({ type: "select", semanticId: node.dataset.id ?? null });
            }
            return;
          }
          if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
            const target = event.target instanceof HTMLElement ? event.target : null;
            const node = target?.closest<HTMLElement>('.react-flow__node[data-id]');
            const semanticId = node?.dataset.id;
            const componentState = semanticId === undefined ? undefined : componentStates.get(semanticId);
            if (node && target === node && componentState !== undefined) {
              const shouldExpand = event.key === "ArrowRight" && componentState.collapsed;
              const shouldCollapse = event.key === "ArrowLeft" && !componentState.collapsed;
              if (shouldExpand || shouldCollapse) {
                event.preventDefault();
                toggleComponent(componentState.instanceSemanticId);
              }
            }
          }
        }}
      >
        <Background color="var(--recovery-grid)" gap={24} size={1} />
        {minimapVisible && <MiniMap
          bgColor="#0b1628"
          nodeColor="#1e3a5f"
          nodeStrokeColor="#38bdf8"
          nodeStrokeWidth={3}
          maskColor="rgba(7, 17, 31, 0.48)"
          maskStrokeColor="#38bdf8"
          maskStrokeWidth={2}
          pannable
          zoomable
          ariaLabel="Workflow overview; blue frame shows the visible area"
          data-testid="workflow-recovery-minimap"
        />}
        <button type="button" className={`recovery-minimap-toggle nodrag nopan${minimapVisible ? " is-open" : ""}`} data-testid="workflow-recovery-minimap-toggle" aria-label={minimapVisible ? "Hide minimap" : "Show minimap"} aria-expanded={minimapVisible} onClick={() => setMinimapVisible((visible) => !visible)}>{minimapVisible ? "⌄" : "Overview map"}</button>
        <div className="recovery-minimap-key nodrag nopan" aria-hidden="true">Blue frame = current view</div>
        <RecoveryCanvasNavigator
          projection={projection}
          onSelect={(semanticId) => onIntent({ type: "select", semanticId })}
          showSearch={detailLevel === "compact"}
        />
        <RecoveryCanvasControls />
        <RecoveryCanvasViewport selectedNodeId={selectedSemanticId && (blockIds.has(selectedSemanticId) ? selectedSemanticId : portLookup.get(selectedSemanticId)?.owner_block_id ?? edges.find((edge) => edge.id === selectedSemanticId)?.source) || null} />
      </ReactFlow>
    </div>
  );
};
