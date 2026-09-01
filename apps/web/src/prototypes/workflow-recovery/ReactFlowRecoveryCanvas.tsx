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
  type Connection,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeChange,
  type NodeProps,
} from "@xyflow/react";
import { createContext, memo, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
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

interface RecoveryCanvasRuntime {
  readonly run: RecoveryRunProjection;
  readonly runSubject: RecoveryRunSubject | null;
  readonly proposedBlockIds: ReadonlySet<string>;
  readonly portArtifactIds: Readonly<Record<string, string>>;
  readonly relationshipLabels: Readonly<Record<string, string>>;
  readonly overlayRelationships: readonly RecoveryRelationship[];
  readonly portTreatment: "dot" | "terminal" | "hybrid";
  readonly onArtifactInspect: (portId: string) => void;
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
  work: "step",
  review: "design review",
  release: "output",
};

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
  return (
    <article
      className={`recovery-block recovery-block--${block.role}${data.selected ? " is-selected" : ""}${data.active ? " is-active" : ""}${data.proposed ? " is-proposed" : ""}`}
      data-testid={`workflow-recovery-block-${block.semanticId}`}
      data-semantic-id={block.semanticId}
      data-selected={data.selected}
      data-run-state={data.runState}
      data-active={data.active}
      data-component-collapsed={data.componentState?.collapsed ?? undefined}
      data-detail-level={data.detailLevel}
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
      {data.active && <div className="recovery-block__active">▶ ACTIVE STEP</div>}
      {data.proposed && <div className="recovery-block__proposal">AI SUGGESTION · REVIEW BEFORE ADDING</div>}
      <header>
        <span className="recovery-block__kind">{roleLabel[block.role]}</span>
        <span className={`recovery-state recovery-state--${data.runState}`} aria-label={`Run state ${data.runState}`}>
          {stateGlyph[data.runState]}{data.runState === "idle" ? "" : ` ${data.runState.replace("-", " ")}`}
        </span>
      </header>
      <h3>{block.title}</h3>
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
        {block.outputs.map((port) => <PortRow key={port.semanticId} port={port} side="output" keyboardSource={data.keyboardSource} onPortKey={data.onPortKey} />)}
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
}

type RecoveryFlowEdge = Edge<RecoveryEdgeData, "recovery">;

function RecoveryEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, sourceHandleId, targetHandleId, markerEnd, label, data, selected }: EdgeProps<RecoveryFlowEdge>) {
  const [path, labelX, labelY] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, curvature: data?.kind === "feedback" ? 0.5 : 0.24 });
  const active = Boolean(data?.active);
  const stableLabelLane = [...id].reduce((sum, character) => sum + character.charCodeAt(0), 0) % 5 - 2;
  const labelOffsetY = (data?.kind === "decision" ? -20 : data?.kind === "data" ? 10 : 0) + stableLabelLane * 14;
  return (
    <g
      className={`recovery-edge${active ? " is-active" : ""}${data?.kind === "feedback" ? " is-feedback" : ""}${selected ? " is-selected" : ""}`}
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
  const blocks = useMemo(() => projection.phases.flatMap((phase) => phase.blocks), [projection]);
  const [expandedComponentIds, setExpandedComponentIds] = useState<ReadonlySet<string>>(() => new Set());
  const detailLevel = graphDetailLevel(blocks.length);
  const componentTargets = useMemo(
    () => Object.values(runtime.run.steps).flatMap((step) => step.componentScope === undefined ? [] : [step.componentScope]),
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

  const portLookup = useMemo(() => new Map(blocks.flatMap((block) => [...block.inputs, ...block.outputs]).map((port) => [port.semanticId, port])), [blocks]);
  const blockIds = useMemo(() => new Set(blocks.map((block) => block.semanticId)), [blocks]);
  const requireBlockEndpoint = (semanticId: string, relationshipId: string, endpoint: "source" | "target") => {
    if (!blockIds.has(semanticId)) throw new Error(`RECOVERY_EDGE_${endpoint.toUpperCase()}_BLOCK_MISSING:${relationshipId}:${semanticId}`);
    return semanticId;
  };
  const onPortKey = useCallback((port: DraftPortProjection) => {
    if (port.direction === "output") {
      setKeyboardSource((current) => current === port.semanticId ? null : port.semanticId);
      return;
    }
    if (keyboardSource !== null) {
      onIntent({ type: "create-connection", sourcePortId: keyboardSource, targetPortId: port.semanticId });
      setKeyboardSource(null);
    }
  }, [keyboardSource, onIntent]);

  const projectedNodes = useMemo<RecoveryFlowNode[]>(() => blocks.map((block) => ({
      id: block.semanticId,
      type: "recovery",
      position: { x: block.position.x, y: block.position.y },
      selected: selectedSemanticId === block.semanticId,
      data: {
        block,
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
      },
    })), [
      blocks,
      componentStates,
      detailLevel,
      keyboardSource,
      onIntent,
      onPortKey,
      runtime.proposedBlockIds,
      runtime.run.activeBlockId,
      runtime.run.steps,
      selectedSemanticId,
      toggleComponent,
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
  ];

  const connect = (connection: Connection) => {
    if (!connection.sourceHandle || !connection.targetHandle) return;
    const source = portLookup.get(connection.sourceHandle);
    const target = portLookup.get(connection.targetHandle);
    if (source?.direction !== "output" || target?.direction !== "input") return;
    onIntent({ type: "create-connection", sourcePortId: source.semanticId, targetPortId: target.semanticId });
  };

  return (
    <div className={`recovery-canvas recovery-canvas--${runtime.portTreatment}`} data-testid="workflow-recovery-canvas" data-port-treatment={runtime.portTreatment} data-detail-level={detailLevel} aria-label="Mounting bracket workflow diagram">
      {keyboardSource && <div className="recovery-keyboard-connection" role="status">Connection started. Focus a compatible input and press Enter; Escape cancels.</div>}
      <ReactFlow
        data-testid="workflow-recovery-reactflow-pane"
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        minZoom={0.35}
        maxZoom={1.4}
        proOptions={{ hideAttribution: true }}
        fitView
        fitViewOptions={{ padding: 0.12 }}
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
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            setKeyboardSource(null);
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
        <MiniMap
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
        />
        <div className="recovery-minimap-key nodrag nopan" aria-hidden="true">Blue frame = current view</div>
        <RecoveryCanvasNavigator
          projection={projection}
          onSelect={(semanticId) => onIntent({ type: "select", semanticId })}
          showSearch={detailLevel === "compact"}
        />
        <RecoveryCanvasControls />
      </ReactFlow>
    </div>
  );
};
