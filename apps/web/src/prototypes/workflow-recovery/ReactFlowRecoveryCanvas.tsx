import {
  Background,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  getBezierPath,
  type Connection,
  type Edge,
  type EdgeProps,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { createContext, memo, useContext, useMemo, useState, type ReactNode } from "react";
import "@xyflow/react/dist/style.css";

import type { DraftBlockProjection, DraftPortProjection } from "../../components/workflow-composer/draft-projection";
import type { DraftCanvasRenderer } from "../../components/workflow-composer/renderer-types";
import type { RecoveryRelationship, RecoveryRunProjection, RecoveryRunState } from "./model";

interface RecoveryCanvasRuntime {
  readonly run: RecoveryRunProjection;
  readonly proposedBlockIds: ReadonlySet<string>;
  readonly portArtifactIds: Readonly<Record<string, string>>;
  readonly relationshipLabels: Readonly<Record<string, string>>;
  readonly overlayRelationships: readonly RecoveryRelationship[];
  readonly portTreatment: "dot" | "terminal" | "hybrid";
  readonly onArtifactInspect: (portId: string) => void;
}

const emptyRun: RecoveryRunProjection = {
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
  proposedBlockIds: new Set(),
  portArtifactIds: {},
  relationshipLabels: {},
  overlayRelationships: [],
  portTreatment: "hybrid",
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
  readonly keyboardSource: string | null;
  readonly onSelect: (semanticId: string) => void;
  readonly onPortKey: (port: DraftPortProjection) => void;
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

function portQualifier(port: DraftPortProjection): string {
  const required = port.required ? "required" : "optional";
  return `${required} · ${port.cardinality}`;
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
  const runtime = useContext(RuntimeContext);
  const artifactId = runtime.portArtifactIds[port.semanticId];
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
    <div className={`recovery-port recovery-port--${side}`} data-semantic-id={port.semanticId}>
      {side === "input" && handle}
      <div className="recovery-port__copy">
        <strong>{port.name}</strong>
        <span>{port.value_type_id.replace("type.", "")}</span>
        <small>{portQualifier(port)}</small>
      </div>
      {artifactId && (
        <button
          type="button"
          className="recovery-port__artifact nodrag nopan"
          data-testid={`workflow-recovery-artifact-${port.semanticId}`}
          aria-label={`Inspect ${port.name} ${side} artifact`}
          onClick={(event) => {
            event.stopPropagation();
            runtime.onArtifactInspect(port.semanticId);
          }}
        >
          ▧ <span>artifact</span>
        </button>
      )}
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
      role="group"
      aria-label={`${block.title} workflow block`}
      tabIndex={0}
      onClick={() => data.onSelect(block.semanticId)}
      onKeyDown={(event) => {
        if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) {
          event.preventDefault();
          data.onSelect(block.semanticId);
        }
      }}
    >
      {data.active && <div className="recovery-block__active">▶ ACTIVE STEP</div>}
      {data.proposed && <div className="recovery-block__proposal">AI CANDIDATE · NOT ACCEPTED</div>}
      <header>
        <span className="recovery-block__kind">{block.role}</span>
        <span className={`recovery-state recovery-state--${data.runState}`} aria-label={`Run state ${data.runState}`}>
          {stateGlyph[data.runState]} {data.runState.replace("-", " ")}
        </span>
      </header>
      <h3>{block.title}</h3>
      <p>{block.purpose}</p>
      <div className="recovery-block__ports recovery-block__ports--inputs">
        {block.inputs.map((port) => <PortRow key={port.semanticId} port={port} side="input" keyboardSource={data.keyboardSource} onPortKey={data.onPortKey} />)}
      </div>
      <div className="recovery-block__ports recovery-block__ports--outputs">
        {block.outputs.map((port) => <PortRow key={port.semanticId} port={port} side="output" keyboardSource={data.keyboardSource} onPortKey={data.onPortKey} />)}
      </div>
      {block.gates.length > 0 && <div className="recovery-block__gate">◇ Approval gate · explicit decision</div>}
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

function RecoveryEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, markerEnd, label, data, selected }: EdgeProps<RecoveryFlowEdge>) {
  const [path, labelX, labelY] = getBezierPath({ sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, curvature: data?.kind === "feedback" ? 0.5 : 0.24 });
  const active = Boolean(data?.active);
  const labelOffsetY = data?.kind === "decision" ? -20 : data?.kind === "data" ? 10 : 0;
  return (
    <g
      className={`recovery-edge${active ? " is-active" : ""}${data?.kind === "feedback" ? " is-feedback" : ""}${selected ? " is-selected" : ""}`}
      data-testid={`workflow-recovery-edge-${data?.semanticId ?? id}`}
      data-semantic-id={data?.semanticId ?? id}
      data-kind={data?.kind ?? "data"}
      data-active={active}
      onClick={(event) => {
        event.stopPropagation();
        data?.onSelect(data.semanticId);
      }}
    >
      <BaseEdge id={id} path={path} markerEnd={markerEnd} interactionWidth={22} />
      <EdgeLabelRenderer>
        <button
          type="button"
          className="recovery-edge__label nodrag nopan"
          style={{ transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + labelOffsetY}px)` }}
          data-testid={`workflow-recovery-edge-select-${data?.semanticId ?? id}`}
          aria-label={`Select relationship ${String(label ?? data?.semanticId ?? id)}`}
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

export const ReactFlowRecoveryCanvas: DraftCanvasRenderer = ({ projection, selectedSemanticId, onIntent }) => {
  const runtime = useContext(RuntimeContext);
  const [keyboardSource, setKeyboardSource] = useState<string | null>(null);
  const blocks = projection.phases.flatMap((phase) => phase.blocks);
  const gateOwners = useMemo(() => new Map(blocks.flatMap((block) => block.gates.map((gate) => [gate.semanticId, block.semanticId] as const))), [blocks]);

  const portLookup = useMemo(() => new Map(blocks.flatMap((block) => [...block.inputs, ...block.outputs]).map((port) => [port.semanticId, port])), [blocks]);
  const onPortKey = (port: DraftPortProjection) => {
    if (port.direction === "output") {
      setKeyboardSource((current) => current === port.semanticId ? null : port.semanticId);
      return;
    }
    if (keyboardSource !== null) {
      onIntent({ type: "create-connection", sourcePortId: keyboardSource, targetPortId: port.semanticId });
      setKeyboardSource(null);
    }
  };

  const nodes: RecoveryFlowNode[] = blocks.map((block) => ({
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
      keyboardSource,
      onSelect: (semanticId) => onIntent({ type: "select", semanticId }),
      onPortKey,
    },
  }));

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
    ...projection.feedbackPaths.map((feedback) => ({
      id: feedback.semanticId,
      type: "recovery" as const,
      source: gateOwners.get(feedback.from_gate_id) ?? feedback.from_gate_id,
      target: feedback.to_block_id,
      label: feedback.label,
      selected: selectedSemanticId === feedback.semanticId,
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      data: { semanticId: feedback.semanticId, kind: "feedback" as const, active: runtime.run.activeRelationshipId === feedback.semanticId, onSelect: (semanticId: string) => onIntent({ type: "select", semanticId }) },
    })),
    ...runtime.overlayRelationships.map((relationship) => ({
      id: relationship.id,
      type: "recovery" as const,
      source: relationship.sourceId,
      target: relationship.targetId,
      label: relationship.label,
      selected: selectedSemanticId === relationship.id,
      markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
      data: { semanticId: relationship.id, kind: relationship.kind as "control" | "decision", active: runtime.run.activeRelationshipId === relationship.id, onSelect: (semanticId: string) => onIntent({ type: "select", semanticId }) },
    })),
  ];

  const connect = (connection: Connection) => {
    if (!connection.sourceHandle || !connection.targetHandle) return;
    const source = portLookup.get(connection.sourceHandle);
    const target = portLookup.get(connection.targetHandle);
    if (source?.direction !== "output" || target?.direction !== "input") return;
    onIntent({ type: "create-connection", sourcePortId: source.semanticId, targetPortId: target.semanticId });
  };

  return (
    <div className={`recovery-canvas recovery-canvas--${runtime.portTreatment}`} data-testid="workflow-recovery-canvas" data-port-treatment={runtime.portTreatment} aria-label="Mounting bracket workflow diagram">
      <div className="recovery-phase-stripe recovery-phase-stripe--define"><b>01 · Define</b><span>Requirements and geometry</span></div>
      <div className="recovery-phase-stripe recovery-phase-stripe--verify"><b>02 · Verify</b><span>Evidence and approval</span></div>
      <div className="recovery-phase-stripe recovery-phase-stripe--deliver"><b>03 · Deliver</b><span>Neutral output package</span></div>
      {keyboardSource && <div className="recovery-keyboard-connection" role="status">Connection started. Focus a compatible input and press Enter; Escape cancels.</div>}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        minZoom={0.35}
        maxZoom={1.4}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        deleteKeyCode={["Backspace", "Delete"]}
        nodesConnectable
        nodesDraggable
        edgesReconnectable={false}
        onPaneClick={() => onIntent({ type: "select", semanticId: null })}
        onNodeClick={(_, node) => onIntent({ type: "select", semanticId: node.id })}
        onEdgeClick={(_, edge) => onIntent({ type: "select", semanticId: edge.id })}
        onNodeDragStop={(_, node) => onIntent({ type: "move-block", semanticId: node.id, x: Math.round(node.position.x), y: Math.round(node.position.y) })}
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
          }
        }}
      >
        <Background color="var(--recovery-grid)" gap={24} size={1} />
        <MiniMap pannable zoomable nodeStrokeWidth={3} ariaLabel="Workflow overview map" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
};
