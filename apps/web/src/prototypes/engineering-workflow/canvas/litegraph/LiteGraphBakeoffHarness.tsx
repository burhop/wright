import { useEffect, useMemo, useRef, useState } from "react";
import {
  LGraph,
  LGraphCanvas,
  LGraphNode,
  LiteGraph,
  type LLink,
} from "litegraph.js";

import {
  EngineeringWorkflowVisualSlice,
  type EngineeringWorkflowCanvasRenderProps,
} from "../../EngineeringWorkflowVisualSlice";
import type {
  WorkflowBlockRole,
  WorkflowConnectionSemantics,
} from "../../workflow-preview-model";
import {
  projectWorkflowToCanvas,
  type CanvasProjection,
} from "../canvas-adapter";
import {
  projectLiteGraphCandidate,
  type LiteGraphCandidateLink,
  type LiteGraphCandidateNode,
} from "./litegraph-projection";

import "./litegraph-bakeoff.css";

const roleColors: Record<
  WorkflowBlockRole,
  { border: string; body: string; title: string }
> = {
  input: { border: "#159cff", body: "#06213b", title: "#0d72ba" },
  "ai-task": { border: "#9b4cff", body: "#251342", title: "#7130ba" },
  "mcp-action": { border: "#11c7c1", body: "#073539", title: "#087d7c" },
  artifact: { border: "#13c985", body: "#07382d", title: "#0b7c58" },
  decision: { border: "#ffb20b", body: "#30250a", title: "#9b6a00" },
  notification: { border: "#78dc48", body: "#173c20", title: "#478c27" },
};

const semanticsColors: Record<WorkflowConnectionSemantics, string> = {
  data: "#159cff",
  control: "#12c881",
  feedback: "#ff4058",
};

type MutableLiteGraphCanvas = LGraphCanvas & {
  clear_background_color: string;
};

type ColoredLiteGraphLink = LLink & { color?: string };

interface LiteGraphRuntime {
  canvas: MutableLiteGraphCanvas;
  nodes: Map<string, LGraphNode>;
  destroy: () => void;
  fit: () => void;
  zoomBy: (factor: number) => void;
}

function truncate(value: string, maximum: number): string {
  return value.length <= maximum ? value : `${value.slice(0, maximum - 1)}…`;
}

function drawPhaseLanes(
  context: CanvasRenderingContext2D,
  projection: CanvasProjection,
) {
  const tones = {
    define: {
      border: "#137dc2",
      fill: "rgba(3, 24, 43, 0.92)",
      header: "rgba(12, 92, 150, 0.92)",
      marker: "#69baff",
    },
    verify: {
      border: "#069b9b",
      fill: "rgba(3, 32, 38, 0.92)",
      header: "rgba(5, 117, 116, 0.92)",
      marker: "#25d3cc",
    },
    manufacture: {
      border: "#7650db",
      fill: "rgba(25, 16, 48, 0.92)",
      header: "rgba(78, 47, 150, 0.94)",
      marker: "#a981ff",
    },
  } as const;

  context.save();
  for (const { phase, position, size } of projection.phases) {
    const tone = tones[phase.tone];
    context.beginPath();
    context.roundRect(position.x, position.y, size.width, size.height, 12);
    context.fillStyle = tone.fill;
    context.fill();
    context.strokeStyle = tone.border;
    context.lineWidth = 1.5;
    context.stroke();

    context.save();
    context.beginPath();
    context.roundRect(position.x, position.y, size.width, 38, [12, 12, 0, 0]);
    context.clip();
    context.fillStyle = tone.header;
    context.fillRect(position.x, position.y, size.width, 38);
    context.restore();

    context.beginPath();
    context.arc(position.x + 20, position.y + 19, 15, 0, Math.PI * 2);
    context.fillStyle = tone.marker;
    context.fill();
    context.fillStyle = "#07111e";
    context.font = "700 16px Segoe UI";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(String(phase.index), position.x + 20, position.y + 19);

    context.textAlign = "left";
    context.fillStyle = "#f2f8ff";
    context.font = "800 16px Segoe UI";
    context.fillText(
      phase.label.toUpperCase(),
      position.x + 44,
      position.y + 18,
    );
    context.fillStyle = "rgba(235, 246, 255, 0.7)";
    context.font = "9px Segoe UI";
    context.fillText(phase.description, position.x + 44, position.y + 31);
  }
  context.restore();
}

function drawFeedbackRails(
  context: CanvasRenderingContext2D,
  candidateNodes: Map<string, LiteGraphCandidateNode>,
  links: LiteGraphCandidateLink[],
) {
  context.save();
  context.strokeStyle = semanticsColors.feedback;
  context.fillStyle = semanticsColors.feedback;
  context.lineWidth = 4;
  context.setLineDash([8, 5]);
  context.font = "800 9px Segoe UI";
  context.textAlign = "center";

  for (const link of links.filter(
    ({ semantics }) => semantics === "feedback",
  )) {
    const source = candidateNodes.get(link.sourceBlockId);
    const target = candidateNodes.get(link.targetBlockId);
    if (!source || !target) continue;

    const start = {
      x: source.position.x + source.size.width,
      y: source.position.y + source.size.height / 2,
    };
    const end = {
      x: target.position.x,
      y: target.position.y + target.size.height / 2,
    };
    const routeY =
      link.connectionId === "model-revise"
        ? Math.min(start.y, end.y) - 78
        : Math.max(start.y, end.y) +
          (link.connectionId === "quote-rejected" ? 88 : 76);

    context.beginPath();
    context.moveTo(start.x, start.y);
    context.bezierCurveTo(
      start.x + 24,
      start.y,
      start.x + 24,
      routeY,
      start.x,
      routeY,
    );
    context.lineTo(end.x, routeY);
    context.bezierCurveTo(end.x - 24, routeY, end.x - 24, end.y, end.x, end.y);
    context.stroke();

    context.setLineDash([]);
    context.beginPath();
    context.moveTo(end.x, end.y);
    context.lineTo(end.x - 8, end.y - 5);
    context.lineTo(end.x - 8, end.y + 5);
    context.closePath();
    context.fill();
    if (link.label) {
      context.fillText(
        link.label.toUpperCase(),
        (start.x + end.x) / 2,
        routeY - 8,
      );
    }
    context.setLineDash([8, 5]);
  }
  context.restore();
}

function drawForwardLabels(
  context: CanvasRenderingContext2D,
  candidateNodes: Map<string, LiteGraphCandidateNode>,
  links: LiteGraphCandidateLink[],
) {
  context.save();
  context.font = "800 9px Segoe UI";
  context.textAlign = "center";
  for (const link of links) {
    if (!link.label || link.semantics === "feedback") continue;
    const source = candidateNodes.get(link.sourceBlockId);
    const target = candidateNodes.get(link.targetBlockId);
    if (!source || !target) continue;
    context.fillStyle = semanticsColors[link.semantics];
    context.fillText(
      link.label.toUpperCase(),
      (source.position.x + source.size.width + target.position.x) / 2,
      (source.position.y + target.position.y) / 2 + 22,
    );
  }
  context.restore();
}

function configureNode(node: LGraphNode, candidate: LiteGraphCandidateNode) {
  const colors = roleColors[candidate.role];
  node.title = `${candidate.code}. ${truncate(candidate.title, 20)}`;
  node.pos = [candidate.position.x, candidate.position.y + 30];
  node.size = [candidate.size.width, Math.max(34, candidate.size.height - 30)];
  node.color = colors.title;
  node.bgcolor = colors.body;
  node.boxcolor = colors.border;
  node.shape = LiteGraph.CARD_SHAPE;
  node.resizable = false;
  node.properties = { workflowBlockId: candidate.blockId };
  node.addOutput("out", "workflow", {
    label: "OUT",
    color_on: colors.border,
    color_off: colors.border,
  });
  for (const connectionId of candidate.incomingConnectionIds) {
    node.addInput(connectionId, "workflow", {
      label: "IN",
      color_on: colors.border,
      color_off: colors.border,
    });
  }
  node.onDrawForeground = (context) => {
    context.save();
    context.fillStyle = "rgba(231, 242, 252, 0.78)";
    context.font = "8px Segoe UI";
    context.textAlign = "left";
    context.fillText(truncate(candidate.subtitle, 31), 16, 18);
    if (candidate.badge) {
      context.fillStyle = colors.border;
      context.font = "800 7px Segoe UI";
      context.textAlign = "right";
      context.fillText(
        truncate(candidate.badge.toUpperCase(), 18),
        node.size[0] - 9,
        node.size[1] - 7,
      );
    }
    context.restore();
  };
}

function createLiteGraphRuntime(
  canvasElement: HTMLCanvasElement,
  container: HTMLElement,
  projection: CanvasProjection,
  onSelectBlock: (blockId: string) => void,
  onZoomChanged: (zoom: number) => void,
): LiteGraphRuntime {
  const candidate = projectLiteGraphCandidate(projection);
  const candidateNodes = new Map(
    candidate.nodes.map((node) => [node.blockId, node]),
  );
  const graph = new LGraph();
  const graphCanvas = new LGraphCanvas(
    canvasElement,
    graph,
  ) as MutableLiteGraphCanvas;
  const nodes = new Map<string, LGraphNode>();

  graphCanvas.clear_background_color = "rgba(2, 10, 19, 0.86)";
  graphCanvas.allow_dragcanvas = true;
  graphCanvas.allow_dragnodes = false;
  graphCanvas.allow_interaction = true;
  graphCanvas.allow_reconnect_links = false;
  graphCanvas.connections_width = 3;
  graphCanvas.render_connection_arrows = true;
  graphCanvas.render_connections_border = false;
  graphCanvas.render_connections_shadows = false;
  graphCanvas.render_shadows = false;
  graphCanvas.show_info = false;
  graphCanvas.title_text_font = "700 10px Segoe UI";
  graphCanvas.inner_text_font = "8px Segoe UI";
  graphCanvas.links_render_mode = LiteGraph.SPLINE_LINK;
  graphCanvas.onDrawBackground = (context) => {
    drawPhaseLanes(context, projection);
    drawFeedbackRails(context, candidateNodes, candidate.links);
    drawForwardLabels(context, candidateNodes, candidate.links);
  };
  graphCanvas.onNodeSelected = (node) => {
    const blockId = node.properties.workflowBlockId;
    if (typeof blockId === "string") onSelectBlock(blockId);
  };

  for (const candidateNode of candidate.nodes) {
    const node = new LGraphNode();
    configureNode(node, candidateNode);
    graph.add(node);
    nodes.set(candidateNode.blockId, node);
  }

  for (const candidateLink of candidate.links) {
    const source = nodes.get(candidateLink.sourceBlockId);
    const target = nodes.get(candidateLink.targetBlockId);
    if (!source || !target) {
      throw new Error(
        `LiteGraph projection lost ${candidateLink.connectionId}.`,
      );
    }
    const link = source.connect<LLink>(0, target, candidateLink.targetSlot);
    if (!link) {
      throw new Error(
        `LiteGraph rejected connection ${candidateLink.connectionId}.`,
      );
    }
    (link as ColoredLiteGraphLink).color =
      candidateLink.semantics === "feedback"
        ? "rgba(0, 0, 0, 0)"
        : semanticsColors[candidateLink.semantics];
  }

  const syncCanvasSize = () => {
    const width = Math.max(1, Math.floor(container.clientWidth));
    const height = Math.max(1, Math.floor(container.clientHeight));
    if (canvasElement.width !== width) canvasElement.width = width;
    if (canvasElement.height !== height) canvasElement.height = height;
  };
  const fit = () => {
    syncCanvasSize();
    const scale = Math.min(
      1,
      (canvasElement.width - 34) / projection.size.width,
      (canvasElement.height - 34) / projection.size.height,
    );
    graphCanvas.ds.scale = Math.max(0.35, scale);
    graphCanvas.ds.offset = [
      (canvasElement.width / graphCanvas.ds.scale - projection.size.width) / 2,
      (canvasElement.height / graphCanvas.ds.scale - projection.size.height) /
        2,
    ];
    graphCanvas.setDirty(true, true);
    graphCanvas.draw(true, true);
    onZoomChanged(graphCanvas.ds.scale);
  };
  const zoomBy = (factor: number) => {
    const nextZoom = Math.min(
      1.35,
      Math.max(0.35, graphCanvas.ds.scale * factor),
    );
    graphCanvas.setZoom(nextZoom, [
      canvasElement.width / 2,
      canvasElement.height / 2,
    ]);
    graphCanvas.draw(true, true);
    onZoomChanged(nextZoom);
  };

  const resizeObserver = new ResizeObserver(() => fit());
  resizeObserver.observe(container);
  fit();
  graphCanvas.startRendering();

  return {
    canvas: graphCanvas,
    nodes,
    fit,
    zoomBy,
    destroy: () => {
      resizeObserver.disconnect();
      graphCanvas.stopRendering();
      graphCanvas.unbindEvents();
      graph.detachCanvas(graphCanvas);
      graph.clear();
    },
  };
}

function AccessibleWorkflowIndex({
  workflow,
  selectedBlockId,
  onSelectBlock,
}: EngineeringWorkflowCanvasRenderProps) {
  return (
    <div className="ewp-sr-only">
      {workflow.phases.map((phase) => (
        <section
          key={phase.phaseId}
          aria-label={`${phase.label} phase: ${phase.description}`}
        >
          <h2>{phase.label}</h2>
          {workflow.blocks
            .filter(({ phaseId }) => phaseId === phase.phaseId)
            .map((block) => (
              <button
                key={block.blockId}
                type="button"
                aria-pressed={block.blockId === selectedBlockId}
                onClick={() => onSelectBlock(block.blockId)}
              >
                {block.sequence}. {block.title}: {block.purpose}
              </button>
            ))}
        </section>
      ))}
    </div>
  );
}

export function LiteGraphCanvas({
  workflow,
  selectedBlockId,
  onSelectBlock,
}: EngineeringWorkflowCanvasRenderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const projection = useMemo(
    () => projectWorkflowToCanvas(workflow),
    [workflow],
  );
  const [runtime, setRuntime] = useState<LiteGraphRuntime | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    const canvasElement = canvasRef.current;
    const container = containerRef.current;
    if (!canvasElement || !container) return;

    let created: LiteGraphRuntime | null = null;
    setStatus("loading");
    try {
      created = createLiteGraphRuntime(
        canvasElement,
        container,
        projection,
        onSelectBlock,
        setZoom,
      );
      setRuntime(created);
      setStatus("ready");
    } catch (error) {
      console.error("LiteGraph bakeoff candidate failed to initialize.", error);
      setStatus("error");
    }

    return () => {
      created?.destroy();
    };
  }, [onSelectBlock, projection]);

  useEffect(() => {
    if (!runtime) return;
    const node = runtime.nodes.get(selectedBlockId);
    if (!node || node.is_selected) return;
    runtime.canvas.deselectAllNodes();
    runtime.canvas.selectNode(node);
  }, [runtime, selectedBlockId]);

  return (
    <div
      ref={containerRef}
      className="ewp-lg-canvas"
      data-testid="litegraph-bakeoff-canvas"
    >
      <canvas ref={canvasRef} aria-label="LiteGraph engineering workflow" />
      <AccessibleWorkflowIndex
        workflow={workflow}
        selectedBlockId={selectedBlockId}
        onSelectBlock={onSelectBlock}
      />
      <div className="ewp-lg-candidate-note" role="status">
        <strong>LiteGraph.js 0.7.18</strong>
        <span>
          {status === "ready"
            ? "Native canvas CP1B candidate · Wright model remains canonical"
            : status === "error"
              ? "Candidate failed to initialize"
              : "Initializing candidate"}
        </span>
      </div>
      <div className="ewp-lg-controls" aria-label="LiteGraph viewport controls">
        <button
          type="button"
          aria-label="Zoom LiteGraph workflow in"
          disabled={!runtime}
          onClick={() => runtime?.zoomBy(1.15)}
        >
          +
        </button>
        <button
          type="button"
          aria-label="Zoom LiteGraph workflow out"
          disabled={!runtime}
          onClick={() => runtime?.zoomBy(0.87)}
        >
          −
        </button>
        <button
          type="button"
          aria-label="Fit LiteGraph workflow"
          disabled={!runtime}
          onClick={() => runtime?.fit()}
        >
          ⛶
        </button>
        <output aria-live="polite">{Math.round(zoom * 100)}%</output>
      </div>
    </div>
  );
}

export function LiteGraphBakeoffHarness() {
  return (
    <EngineeringWorkflowVisualSlice
      badge="CP1B · LiteGraph.js"
      renderCanvas={(props) => <LiteGraphCanvas {...props} />}
    />
  );
}

export default LiteGraphBakeoffHarness;
