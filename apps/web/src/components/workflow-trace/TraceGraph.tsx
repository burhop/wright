import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import { useMemo } from "react";
import "@xyflow/react/dist/style.css";

import type { RivetRunInspection } from "../../services/workspace-service";

export type TraceGraphSelection =
  { kind: "node"; id: string } | { kind: "connection"; id: string };

export function TraceGraph({
  inspection,
  onSelect,
}: {
  inspection: RivetRunInspection;
  onSelect: (selection: TraceGraphSelection) => void;
}) {
  const graph = inspection.graph;
  const stateByNode = useMemo(
    () =>
      new Map(
        inspection.steps
          .filter((step) => step.node_id)
          .map((step) => [step.node_id!, step.state]),
      ),
    [inspection.steps],
  );
  const nodes = useMemo<Node[]>(
    () =>
      (graph?.nodes || []).map((node) => ({
        id: node.node_id,
        position: { x: node.x, y: node.y },
        data: {
          label: (
            <span>
              <strong>{node.label || node.node_type}</strong>
              <small>{stateByNode.get(node.node_id) || "not run"}</small>
            </span>
          ),
        },
        style: { width: Math.min(node.width, 280) },
        className: `workflow-trace-node workflow-trace-node--${stateByNode.get(node.node_id) || "not-run"}`,
      })),
    [graph?.nodes, stateByNode],
  );
  const edges = useMemo<Edge[]>(
    () =>
      (graph?.connections || []).map((connection) => ({
        id: connection.connection_id,
        source: connection.source_node_id,
        target: connection.target_node_id,
        label: connection.label,
      })),
    [graph?.connections],
  );
  if (!graph) {
    return (
      <p className="workflow-trace__empty">
        The executed graph was not retained for this historical run. Recorded
        steps remain available below.
      </p>
    );
  }
  return (
    <div
      className="workflow-trace__graph"
      aria-label={`Executed graph ${graph.name}`}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.25}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={(_event, node) => onSelect({ kind: "node", id: node.id })}
        onEdgeClick={(_event, edge) =>
          onSelect({ kind: "connection", id: edge.id })
        }
      >
        <Background gap={20} size={1} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
