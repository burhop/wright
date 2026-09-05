import { useEffect, useMemo, useRef, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  type Node,
  type NodeProps,
  type NodeChange,
  type ReactFlowInstance,
} from "@xyflow/react";
import type { NativeDocument, NativePort } from "../../services/native-process";
import "@xyflow/react/dist/style.css";

type StepNode = Node<
  {
    title: string;
    operation: string;
    ports: NativePort[];
    choosePort: (id: string) => void;
    selectedPort: string | null;
  },
  "nativeStep"
>;
function ProcessNode({ data }: NodeProps<StepNode>) {
  return (
    <div className="native-node">
      <strong>{data.title}</strong>
      <span className="native-operation">{data.operation}</span>
      {data.ports.map((port) => (
        <div
          key={port.id}
          className={`native-node-port native-node-port--${port.direction}`}
        >
          <Handle
            type={port.direction === "input" ? "target" : "source"}
            position={
              port.direction === "input" ? Position.Left : Position.Right
            }
            id={port.id}
            aria-hidden="true"
          />
          <button
            className="nodrag nopan"
            type="button"
            data-testid={`native-port-${port.id}`}
            aria-pressed={data.selectedPort === port.id}
            onClick={() => data.choosePort(port.id)}
            aria-label={`${port.direction === "output" ? "Connect from" : "Connect to"} ${data.title}: ${port.label}, ${port.type}`}
          >
            {port.direction === "input" ? "← " : ""}
            {port.label} <small>{port.type}</small>
            {port.direction === "output" ? " →" : ""}
          </button>
        </div>
      ))}
    </div>
  );
}
const nodeTypes = { nativeStep: ProcessNode };
interface Props {
  document: NativeDocument;
  selected: string | null;
  selectedPort: string | null;
  select: (id: string) => void;
  choosePort: (id: string) => void;
  connect: (source: string, target: string) => void;
  move: (id: string, x: number, y: number) => void;
}
export function NativeCanvas({
  document,
  selected,
  selectedPort,
  select,
  choosePort,
  connect,
  move,
}: Props) {
  const canvas = useRef<HTMLDivElement>(null);
  const [flow, setFlow] = useState<ReactFlowInstance<StepNode> | null>(null);
  const [dragPositions, setDragPositions] = useState<
    Record<string, { x: number; y: number }>
  >({});
  useEffect(() => {
    let frame = 0;
    const fit = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        frame = requestAnimationFrame(() => {
          void flow?.fitView({ padding: 0.18, maxZoom: 1 });
        });
      });
    };
    fit();
    const observer = new ResizeObserver(fit);
    if (canvas.current) observer.observe(canvas.current);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [flow, document.definition.id, document.definition.steps.length]);
  const nodes = useMemo<StepNode[]>(
    () =>
      document.definition.steps.map((step, index) => ({
        id: step.id,
        type: "nativeStep",
        selected: step.id === selected,
        position: dragPositions[step.id] ??
          document.presentation[step.id] ?? {
            x: (index % 3) * 300,
            y: Math.floor(index / 3) * 220,
          },
        data: {
          title: step.title,
          operation: step.operation,
          ports: document.definition.ports.filter(
            (port) => port.step_id === step.id,
          ),
          choosePort,
          selectedPort,
        },
        ariaLabel: `${step.title}, ${step.operation}. Select to configure. Arrow keys move the step.`,
      })),
    [document, selected, dragPositions, choosePort, selectedPort],
  );
  const edges = useMemo(
    () =>
      document.definition.connections.map((connection) => {
        const source = document.definition.ports.find(
          (port) => port.id === connection.source_port_id,
        )!;
        const target = document.definition.ports.find(
          (port) => port.id === connection.target_port_id,
        )!;
        return {
          id: connection.id,
          source: source.step_id,
          target: target.step_id,
          sourceHandle: source.id,
          targetHandle: target.id,
          ariaLabel: `${source.label} to ${target.label}, ${source.type}`,
        };
      }),
    [document.definition],
  );
  function changes(items: NodeChange<StepNode>[]) {
    for (const item of items) {
      if (item.type === "select" && item.selected) select(item.id);
      if (item.type === "position" && item.position) {
        if (item.dragging)
          setDragPositions((previous) => ({
            ...previous,
            [item.id]: item.position!,
          }));
        else {
          move(item.id, item.position.x, item.position.y);
          setDragPositions((previous) => {
            const next = { ...previous };
            delete next[item.id];
            return next;
          });
        }
      }
    }
  }
  return (
    <div
      ref={canvas}
      className="native-canvas"
      data-testid="native-canvas"
      role="group"
      aria-label="Process canvas"
    >
      <ReactFlow
        onInit={setFlow}
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={changes}
        onNodeClick={(_, node) => select(node.id)}
        onConnect={(connection) => {
          if (connection.sourceHandle && connection.targetHandle)
            connect(connection.sourceHandle, connection.targetHandle);
        }}
        onNodeDragStop={(_, node) => {
          move(node.id, node.position.x, node.position.y);
          setDragPositions((previous) => {
            const next = { ...previous };
            delete next[node.id];
            return next;
          });
        }}
        fitView
        minZoom={0.2}
        maxZoom={2}
        deleteKeyCode={null}
        multiSelectionKeyCode={null}
        nodesConnectable
        nodesFocusable
        edgesFocusable
        ariaLabelConfig={{
          "controls.zoomIn.ariaLabel": "Zoom canvas in",
          "controls.zoomOut.ariaLabel": "Zoom canvas out",
          "controls.fitView.ariaLabel": "Fit process to canvas",
        }}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
      {!nodes.length && (
        <p className="native-canvas-empty">Add a step to start your process.</p>
      )}
    </div>
  );
}
