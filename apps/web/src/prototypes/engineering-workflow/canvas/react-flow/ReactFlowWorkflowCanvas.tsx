import { useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  BackgroundVariant,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type EdgeProps,
  type EdgeTypes,
  type Node,
  type NodeProps,
  type NodeTypes,
  type ReactFlowInstance,
} from "@xyflow/react";

import {
  WorkflowBlock,
  type EngineeringWorkflowCanvasRenderProps,
} from "../../EngineeringWorkflowVisualSlice";
import { engineeringWorkflowVisualContract } from "../../engineering-workflow-visual-contract";
import {
  focusCanvasProjection,
  projectWorkflowToCanvas,
  type CanvasProjection,
} from "../canvas-adapter";
import type {
  WorkflowPreviewBlock,
  WorkflowPreviewConnection,
  WorkflowPreviewPhase,
} from "../../workflow-preview-model";

import "@xyflow/react/dist/base.css";
import "./react-flow-workflow-canvas.css";

interface PhaseLaneNodeData extends Record<string, unknown> {
  phase: WorkflowPreviewPhase;
}

interface EngineeringBlockNodeData extends Record<string, unknown> {
  block: WorkflowPreviewBlock;
  selected: boolean;
  onSelectBlock: (blockId: string) => void;
}

interface WorkflowEdgeData extends Record<string, unknown> {
  semantics: WorkflowPreviewConnection["semantics"];
  feedbackRailY?: number;
}

type PhaseLaneFlowNode = Node<PhaseLaneNodeData, "phaseLane">;
type EngineeringBlockFlowNode = Node<
  EngineeringBlockNodeData,
  "engineeringBlock"
>;
type WorkflowFlowNode = PhaseLaneFlowNode | EngineeringBlockFlowNode;
type WorkflowFlowEdge = Edge<WorkflowEdgeData, "step" | "workflowFeedback">;

const edgeColor = engineeringWorkflowVisualContract.connectionColors;
const LARGE_WORKFLOW_THRESHOLD = 25;
const LARGE_OVERVIEW_THRESHOLD = 50;
const LARGE_OVERVIEW_MAX_ZOOM = 0.35;

function PhaseLaneNode({ data }: NodeProps<PhaseLaneFlowNode>) {
  return (
    <section
      className="ewp-rf-phase"
      data-tone={data.phase.tone}
      aria-label={`${data.phase.label} phase: ${data.phase.description}`}
    >
      <header>
        <span className="ewp-rf-phase__number">{data.phase.index}</span>
        <span>
          <strong>{data.phase.label}</strong>
          <small>{data.phase.description}</small>
        </span>
      </header>
    </section>
  );
}

function EngineeringBlockNode({ data }: NodeProps<EngineeringBlockFlowNode>) {
  const localBlock = {
    ...data.block,
    position: { ...data.block.position, x: 0, y: 0 },
  };

  return (
    <div className="ewp-rf-block">
      <Handle
        id="in"
        type="target"
        position={Position.Left}
        isConnectable={false}
        aria-hidden="true"
      />
      <WorkflowBlock
        block={localBlock}
        selected={data.selected}
        onSelect={data.onSelectBlock}
      />
      <Handle
        id="out"
        type="source"
        position={Position.Right}
        isConnectable={false}
        aria-hidden="true"
      />
    </div>
  );
}

function WorkflowFeedbackEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  markerEnd,
  style,
  label,
  data,
  interactionWidth,
}: EdgeProps<WorkflowFlowEdge>) {
  const railY = data?.feedbackRailY ?? Math.max(sourceY, targetY) + 32;
  const sourceLeadX = sourceX + 24;
  const targetLeadX = targetX - 24;
  const labelX = (sourceLeadX + targetLeadX) / 2;
  const path = [
    `M ${sourceX} ${sourceY}`,
    `L ${sourceLeadX} ${sourceY}`,
    `L ${sourceLeadX} ${railY}`,
    `L ${targetLeadX} ${railY}`,
    `L ${targetLeadX} ${targetY}`,
    `L ${targetX} ${targetY}`,
  ].join(" ");

  return (
    <>
      <BaseEdge
        id={id}
        path={path}
        markerEnd={markerEnd}
        style={style}
        interactionWidth={interactionWidth}
      />
      {label ? (
        <EdgeLabelRenderer>
          <span
            aria-hidden="true"
            className="ewp-rf-feedback-label nodrag nopan"
            style={{
              transform: `translate(-50%, -100%) translate(${labelX}px, ${railY - 6}px)`,
            }}
          >
            {label}
          </span>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
}

const nodeTypes: NodeTypes = {
  phaseLane: PhaseLaneNode,
  engineeringBlock: EngineeringBlockNode,
};

const edgeTypes: EdgeTypes = {
  workflowFeedback: WorkflowFeedbackEdge,
};

function projectReactFlowNodes(
  projection: CanvasProjection,
  selectedBlockId: string,
  onSelectBlock: (blockId: string) => void,
): WorkflowFlowNode[] {
  const phaseNodes: PhaseLaneFlowNode[] = projection.phases.map(
    ({ phase, position, size }) => ({
      id: `phase:${phase.phaseId}`,
      type: "phaseLane",
      position,
      data: { phase },
      width: size.width,
      height: size.height,
      style: size,
      draggable: false,
      selectable: false,
      connectable: false,
      zIndex: 0,
      ariaLabel: `${phase.label} phase`,
    }),
  );
  const blockNodes: EngineeringBlockFlowNode[] = projection.blocks.map(
    ({ block, absolutePosition, size }) => ({
      id: block.blockId,
      type: "engineeringBlock",
      position: absolutePosition,
      data: {
        block,
        selected: block.blockId === selectedBlockId,
        onSelectBlock,
      },
      width: size.width,
      height: size.height,
      style: size,
      draggable: false,
      selectable: true,
      connectable: false,
      zIndex: 2,
      ariaLabel: block.title,
    }),
  );

  return [...phaseNodes, ...blockNodes];
}

function feedbackRailYForConnection(
  projection: CanvasProjection,
  connection: WorkflowPreviewConnection,
): number {
  const sourceBlock = projection.blocks.find(
    ({ block }) => block.blockId === connection.sourceBlockId,
  );
  const targetBlock = projection.blocks.find(
    ({ block }) => block.blockId === connection.targetBlockId,
  );
  if (!sourceBlock || !targetBlock) {
    throw new Error(
      `Cannot route unknown feedback edge ${connection.connectionId}.`,
    );
  }

  const sourcePhase = projection.phases.find(
    ({ phase }) => phase.phaseId === sourceBlock.phaseId,
  );
  const targetPhase = projection.phases.find(
    ({ phase }) => phase.phaseId === targetBlock.phaseId,
  );
  if (!sourcePhase || !targetPhase) {
    throw new Error(
      `Cannot route feedback edge ${connection.connectionId} without phases.`,
    );
  }

  if (sourcePhase.phase.phaseId === targetPhase.phase.phaseId) {
    return sourcePhase.position.y + sourcePhase.size.height - 14;
  }

  const sourceCenterY =
    sourceBlock.absolutePosition.y + sourceBlock.size.height / 2;
  const targetCenterY =
    targetBlock.absolutePosition.y + targetBlock.size.height / 2;
  return targetCenterY < sourceCenterY
    ? sourcePhase.position.y - 5
    : sourcePhase.position.y + sourcePhase.size.height + 5;
}

export function projectReactFlowEdges(
  projection: CanvasProjection,
): WorkflowFlowEdge[] {
  return projection.connections.map(({ connection }) => {
    const color = edgeColor[connection.semantics];
    const isFeedback = connection.semantics === "feedback";
    return {
      id: connection.connectionId,
      source: connection.sourceBlockId,
      sourceHandle: "out",
      target: connection.targetBlockId,
      targetHandle: "in",
      type: isFeedback ? "workflowFeedback" : "step",
      label: connection.label,
      data: {
        semantics: connection.semantics,
        ...(isFeedback
          ? {
              feedbackRailY: feedbackRailYForConnection(projection, connection),
            }
          : {}),
      },
      className: `ewp-rf-edge ewp-rf-edge--${connection.semantics}`,
      style: {
        stroke: color,
        strokeWidth: isFeedback ? 3 : 2.5,
        strokeDasharray: isFeedback ? "8 5" : undefined,
      },
      labelStyle: { fill: color, fontSize: 9, fontWeight: 800 },
      markerEnd: { type: MarkerType.ArrowClosed, color },
      selectable: false,
      focusable: false,
      zIndex: 1,
    };
  });
}

export function ReactFlowWorkflowCanvas({
  workflow,
  selectedBlockId,
  onSelectBlock,
}: EngineeringWorkflowCanvasRenderProps) {
  const [requestedPhaseId, setRequestedPhaseId] = useState<string | null>(null);
  const reactFlowInstance = useRef<ReactFlowInstance<
    WorkflowFlowNode,
    WorkflowFlowEdge
  > | null>(null);
  const projection = useMemo(
    () => projectWorkflowToCanvas(workflow),
    [workflow],
  );
  const focusedPhaseId =
    requestedPhaseId !== null &&
    projection.phases.some(({ phase }) => phase.phaseId === requestedPhaseId)
      ? requestedPhaseId
      : null;
  const visibleProjection = useMemo(
    () => focusCanvasProjection(projection, focusedPhaseId),
    [focusedPhaseId, projection],
  );
  const nodes = useMemo(
    () =>
      projectReactFlowNodes(visibleProjection, selectedBlockId, onSelectBlock),
    [onSelectBlock, selectedBlockId, visibleProjection],
  );
  const edges = useMemo(
    () => projectReactFlowEdges(visibleProjection),
    [visibleProjection],
  );
  const blockTitleById = useMemo(
    () => new Map(workflow.blocks.map((block) => [block.blockId, block.title])),
    [workflow.blocks],
  );
  const showPhaseNavigation =
    workflow.blocks.length >= LARGE_WORKFLOW_THRESHOLD;
  const fitViewMaxZoom =
    focusedPhaseId === null &&
    workflow.blocks.length >= LARGE_OVERVIEW_THRESHOLD
      ? LARGE_OVERVIEW_MAX_ZOOM
      : 1;

  useEffect(() => {
    void reactFlowInstance.current?.fitView({
      padding: 0.08,
      minZoom: 0.35,
      maxZoom: fitViewMaxZoom,
    });
  }, [fitViewMaxZoom, focusedPhaseId]);

  const choosePhase = (phaseId: string | null) => {
    setRequestedPhaseId(phaseId);
    if (phaseId === null) return;

    const firstBlock = workflow.blocks.find(
      (block) => block.phaseId === phaseId,
    );
    if (firstBlock) onSelectBlock(firstBlock.blockId);
  };

  return (
    <div
      className="ewp-rf-canvas"
      data-testid="react-flow-workflow-canvas"
      data-phase-navigation={showPhaseNavigation ? "true" : undefined}
    >
      <section className="ewp-sr-only" aria-label="Workflow phase summary">
        <h2>Workflow phases</h2>
        <ol>
          {projection.phases.map(({ phase }) => (
            <li key={phase.phaseId}>
              {phase.index}. {phase.label}: {phase.description}
            </li>
          ))}
        </ol>
      </section>
      <ol className="ewp-sr-only" aria-label="Workflow connections">
        {workflow.connections.map((connection) => (
          <li key={connection.connectionId}>
            {blockTitleById.get(connection.sourceBlockId) ??
              connection.sourceBlockId}{" "}
            to{" "}
            {blockTitleById.get(connection.targetBlockId) ??
              connection.targetBlockId}{" "}
            ({connection.label ?? connection.semantics})
          </li>
        ))}
      </ol>
      <div className="ewp-rf-status" role="status">
        <strong>React Flow 12.11.3</strong>
        <span>CP2 selected canvas · Wright model remains canonical</span>
      </div>
      {showPhaseNavigation ? (
        <nav className="ewp-rf-phase-focus" aria-label="Large workflow view">
          <span className="ewp-rf-phase-focus__label">Focus</span>
          <button
            type="button"
            aria-pressed={focusedPhaseId === null}
            onClick={() => choosePhase(null)}
          >
            All phases
          </button>
          {projection.phases.map(({ phase }) => (
            <button
              key={phase.phaseId}
              type="button"
              aria-label={`Focus ${phase.label} phase`}
              aria-pressed={focusedPhaseId === phase.phaseId}
              onClick={() => choosePhase(phase.phaseId)}
            >
              {phase.label}
            </button>
          ))}
          <output aria-live="polite">
            Showing {visibleProjection.blocks.length} of{" "}
            {workflow.blocks.length} blocks
          </output>
        </nav>
      ) : null}
      <ReactFlow<WorkflowFlowNode, WorkflowFlowEdge>
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        minZoom={0.35}
        maxZoom={1.35}
        fitView
        fitViewOptions={{
          padding: 0.04,
          minZoom: 0.35,
          maxZoom: fitViewMaxZoom,
        }}
        onInit={(instance) => {
          reactFlowInstance.current = instance;
          void instance.fitView({
            padding: 0.08,
            minZoom: 0.35,
            maxZoom: fitViewMaxZoom,
          });
        }}
        onNodeClick={(_, node) => {
          if (node.type === "engineeringBlock") onSelectBlock(node.id);
        }}
        colorMode="dark"
        aria-label="React Flow engineering workflow canvas"
      >
        <Background variant={BackgroundVariant.Dots} gap={14} size={1} />
        <Controls showInteractive={false} position="bottom-left" />
        <MiniMap
          position="top-right"
          pannable
          zoomable
          nodeColor={(node) =>
            node.type === "phaseLane"
              ? "#0b2038"
              : engineeringWorkflowVisualContract.colors.input
          }
          nodeStrokeColor={(node) =>
            node.type === "phaseLane"
              ? "#315b7f"
              : engineeringWorkflowVisualContract.colors.focus
          }
          nodeStrokeWidth={3}
          style={{ width: 168, height: 96, marginTop: 8 }}
          ariaLabel="React Flow workflow overview"
        />
      </ReactFlow>
    </div>
  );
}

export default ReactFlowWorkflowCanvas;
