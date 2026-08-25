import { useMemo } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
} from "@xyflow/react";

import {
  WorkflowBlock,
  type EngineeringWorkflowCanvasRenderProps,
} from "../../EngineeringWorkflowVisualSlice";
import { engineeringWorkflowVisualContract } from "../../engineering-workflow-visual-contract";
import {
  projectWorkflowToCanvas,
  type CanvasProjection,
} from "../canvas-adapter";
import type {
  WorkflowPreviewBlock,
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

type PhaseLaneFlowNode = Node<PhaseLaneNodeData, "phaseLane">;
type EngineeringBlockFlowNode = Node<
  EngineeringBlockNodeData,
  "engineeringBlock"
>;
type WorkflowFlowNode = PhaseLaneFlowNode | EngineeringBlockFlowNode;

const edgeColor = engineeringWorkflowVisualContract.connectionColors;

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

const nodeTypes: NodeTypes = {
  phaseLane: PhaseLaneNode,
  engineeringBlock: EngineeringBlockNode,
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

function projectReactFlowEdges(projection: CanvasProjection): Edge[] {
  return projection.connections.map(({ connection }) => {
    const color = edgeColor[connection.semantics];
    return {
      id: connection.connectionId,
      source: connection.sourceBlockId,
      sourceHandle: "out",
      target: connection.targetBlockId,
      targetHandle: "in",
      type: "step",
      label: connection.label,
      className: `ewp-rf-edge ewp-rf-edge--${connection.semantics}`,
      style: {
        stroke: color,
        strokeWidth: connection.semantics === "feedback" ? 3 : 2.5,
        strokeDasharray:
          connection.semantics === "feedback" ? "8 5" : undefined,
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
  const projection = useMemo(
    () => projectWorkflowToCanvas(workflow),
    [workflow],
  );
  const nodes = useMemo(
    () => projectReactFlowNodes(projection, selectedBlockId, onSelectBlock),
    [onSelectBlock, projection, selectedBlockId],
  );
  const edges = useMemo(() => projectReactFlowEdges(projection), [projection]);
  const blockTitleById = useMemo(
    () => new Map(workflow.blocks.map((block) => [block.blockId, block.title])),
    [workflow.blocks],
  );

  return (
    <div className="ewp-rf-canvas" data-testid="react-flow-workflow-canvas">
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
      <ReactFlow<WorkflowFlowNode, Edge>
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        minZoom={0.35}
        maxZoom={1.35}
        fitView
        fitViewOptions={{ padding: 0.04, minZoom: 0.35, maxZoom: 1 }}
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
