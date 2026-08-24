import { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import { ClassicPreset, NodeEditor, type GetSchemes } from "rete";
import { AreaExtensions, AreaPlugin } from "rete-area-plugin";
import {
  Presets,
  ReactPlugin,
  type ReactArea2D,
  type RenderEmit,
} from "rete-react-plugin";

import {
  EngineeringWorkflowVisualSlice,
  WorkflowBlock,
  type EngineeringWorkflowCanvasRenderProps,
} from "../../EngineeringWorkflowVisualSlice";
import {
  projectWorkflowToCanvas,
  type CanvasProjection,
  type CanvasViewport,
} from "../canvas-adapter";
import type {
  WorkflowConnectionSemantics,
  WorkflowPreviewBlock,
  WorkflowPreviewConnection,
} from "../../workflow-preview-model";

import "./rete-bakeoff.css";

const reteSocket = new ClassicPreset.Socket("workflow-artifact");

class EngineeringReteNode extends ClassicPreset.Node<
  { in: ClassicPreset.Socket },
  { out: ClassicPreset.Socket }
> {
  readonly block: WorkflowPreviewBlock;
  readonly width: number;
  readonly height: number;
  readonly onSelectBlock: (blockId: string) => void;

  constructor(
    block: WorkflowPreviewBlock,
    width: number,
    height: number,
    onSelectBlock: (blockId: string) => void,
  ) {
    super(block.title);
    this.id = block.blockId;
    this.block = block;
    this.width = width;
    this.height = height;
    this.onSelectBlock = onSelectBlock;
    this.addInput("in", new ClassicPreset.Input(reteSocket, "IN", true));
    this.addOutput("out", new ClassicPreset.Output(reteSocket, "OUT", true));
  }
}

class EngineeringReteConnection extends ClassicPreset.Connection<
  EngineeringReteNode,
  EngineeringReteNode
> {
  readonly semantics: WorkflowConnectionSemantics;
  readonly label: string | undefined;

  constructor(
    source: EngineeringReteNode,
    target: EngineeringReteNode,
    connection: WorkflowPreviewConnection,
  ) {
    super(source, "out", target, "in");
    this.id = connection.connectionId;
    this.semantics = connection.semantics;
    this.label = connection.label;
  }
}

type Schemes = GetSchemes<EngineeringReteNode, EngineeringReteConnection>;
type AreaExtra = ReactArea2D<Schemes>;

function ReteEngineeringNode({
  data,
  emit,
}: {
  data: EngineeringReteNode;
  emit: RenderEmit<Schemes>;
}) {
  const localBlock = {
    ...data.block,
    position: { ...data.block.position, x: 0, y: 0 },
  };

  return (
    <div
      className="ewp-rete-node"
      style={{ width: data.width, height: data.height }}
      onPointerDown={(event) => event.stopPropagation()}
    >
      <Presets.classic.RefSocket<Schemes>
        name="ewp-rete-socket ewp-rete-socket--input"
        side="input"
        socketKey="in"
        nodeId={data.id}
        emit={emit}
        payload={data.inputs.in!.socket}
      />
      <WorkflowBlock
        block={localBlock}
        selected={data.selected ?? false}
        onSelect={data.onSelectBlock}
      />
      <Presets.classic.RefSocket<Schemes>
        name="ewp-rete-socket ewp-rete-socket--output"
        side="output"
        socketKey="out"
        nodeId={data.id}
        emit={emit}
        payload={data.outputs.out!.socket}
      />
    </div>
  );
}

function ReteEngineeringConnection({
  data,
}: {
  data: EngineeringReteConnection;
}) {
  const { end, path, start } = Presets.classic.useConnection();
  const color =
    data.semantics === "feedback"
      ? "#ff4058"
      : data.semantics === "control"
        ? "#12c881"
        : "#159cff";

  if (!start || !end || !path) return null;

  const feedbackRouteY =
    data.id === "model-revise"
      ? Math.min(start.y, end.y) - 78
      : Math.max(start.y, end.y) + (data.id === "quote-rejected" ? 88 : 76);

  const renderedPath =
    data.semantics === "feedback"
      ? [
          `M ${start.x} ${start.y}`,
          `C ${start.x + 24} ${start.y}, ${start.x + 24} ${feedbackRouteY}, ${start.x} ${feedbackRouteY}`,
          `L ${end.x} ${feedbackRouteY}`,
          `C ${end.x - 24} ${feedbackRouteY}, ${end.x - 24} ${end.y}, ${end.x} ${end.y}`,
        ].join(" ")
      : path;
  const markerId = `ewp-rete-arrow-${data.id}`;

  return (
    <svg className="ewp-rete-connection" data-semantics={data.semantics}>
      <defs>
        <marker
          id={markerId}
          markerUnits="userSpaceOnUse"
          markerWidth="8"
          markerHeight="8"
          refX="7"
          refY="4"
          orient="auto"
        >
          <path d="M 0 0 L 8 4 L 0 8 z" fill={color} />
        </marker>
      </defs>
      <path
        d={renderedPath}
        markerEnd={`url(#${markerId})`}
        style={{
          stroke: color,
          strokeWidth: data.semantics === "feedback" ? 4 : 3,
          strokeDasharray: data.semantics === "feedback" ? "8 5" : undefined,
        }}
      />
      {data.label ? (
        <text
          className="ewp-rete-connection__label"
          x={(start.x + end.x) / 2}
          y={
            data.semantics === "feedback"
              ? feedbackRouteY - 8
              : (start.y + end.y) / 2 - 8
          }
          style={{ fill: color }}
        >
          {data.label}
        </text>
      ) : null}
    </svg>
  );
}

function ReteEngineeringSocket() {
  return <span className="ewp-rete-port" />;
}

interface ReteRuntime {
  editor: NodeEditor<Schemes>;
  area: AreaPlugin<Schemes, AreaExtra>;
  destroy: () => void;
  fit: () => Promise<void>;
  zoomBy: (factor: number) => Promise<void>;
}

async function nextFrame(): Promise<void> {
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
}

async function createReteRuntime(
  container: HTMLElement,
  projection: CanvasProjection,
  onSelectBlock: (blockId: string) => void,
  onViewportChanged: (viewport: CanvasViewport) => void,
): Promise<ReteRuntime> {
  const editor = new NodeEditor<Schemes>();
  const area = new AreaPlugin<Schemes, AreaExtra>(container);
  const render = new ReactPlugin<Schemes, AreaExtra>({ createRoot });

  render.addPreset(
    Presets.classic.setup({
      customize: {
        node: () => ReteEngineeringNode,
        connection: () => ReteEngineeringConnection,
        socket: () => ReteEngineeringSocket,
      },
    }),
  );

  editor.use(area);
  area.use(render);

  const nodes = new Map<string, EngineeringReteNode>();
  for (const { block, absolutePosition, size } of projection.blocks) {
    const node = new EngineeringReteNode(
      block,
      size.width,
      size.height,
      onSelectBlock,
    );
    nodes.set(node.id, node);
    await editor.addNode(node);
    await area.translate(node.id, absolutePosition);
    await area.resize(node.id, size.width, size.height);
  }

  for (const { connection } of projection.connections) {
    const source = nodes.get(connection.sourceBlockId);
    const target = nodes.get(connection.targetBlockId);
    if (!source || !target) {
      throw new Error(`Rete projection lost ${connection.connectionId}.`);
    }
    await editor.addConnection(
      new EngineeringReteConnection(source, target, connection),
    );
  }

  const publishViewport = () => {
    const { x, y, k } = area.area.transform;
    onViewportChanged({ x, y, zoom: k });
  };

  area.addPipe((context) => {
    if (context.type === "nodetranslate") return;
    if (context.type === "translated" || context.type === "zoomed") {
      queueMicrotask(publishViewport);
    }
    return context;
  });

  const fit = async () => {
    await nextFrame();
    await AreaExtensions.zoomAt(area, editor.getNodes(), { scale: 0.92 });
    publishViewport();
  };
  const zoomBy = async (factor: number) => {
    const bounds = container.getBoundingClientRect();
    await area.area.zoom(
      Math.min(1.35, Math.max(0.35, area.area.transform.k * factor)),
      bounds.width / 2,
      bounds.height / 2,
    );
    publishViewport();
  };

  await fit();

  return {
    editor,
    area,
    fit,
    zoomBy,
    destroy: () => area.destroy(),
  };
}

function PhaseLaneLayer({
  projection,
  viewport,
}: {
  projection: CanvasProjection;
  viewport: CanvasViewport;
}) {
  return (
    <div
      className="ewp-rete-lanes"
      style={{
        width: projection.size.width,
        height: projection.size.height,
        transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`,
      }}
    >
      {projection.phases.map(({ phase, position, size }) => (
        <section
          key={phase.phaseId}
          className="ewp-rete-phase"
          data-tone={phase.tone}
          aria-label={`${phase.label} phase: ${phase.description}`}
          style={{
            left: position.x,
            top: position.y,
            width: size.width,
            height: size.height,
          }}
        >
          <header>
            <span className="ewp-rete-phase__number">{phase.index}</span>
            <span>
              <strong>{phase.label}</strong>
              <small>{phase.description}</small>
            </span>
          </header>
        </section>
      ))}
    </div>
  );
}

export function ReteCanvas({
  workflow,
  selectedBlockId,
  onSelectBlock,
}: EngineeringWorkflowCanvasRenderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const projection = useMemo(
    () => projectWorkflowToCanvas(workflow),
    [workflow],
  );
  const [runtime, setRuntime] = useState<ReteRuntime | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [viewport, setViewport] = useState<CanvasViewport>({
    x: 0,
    y: 0,
    zoom: 1,
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    let cancelled = false;
    let createdRuntime: ReteRuntime | null = null;

    setStatus("loading");
    void createReteRuntime(container, projection, onSelectBlock, setViewport)
      .then((created) => {
        if (cancelled) {
          created.destroy();
          return;
        }
        createdRuntime = created;
        setRuntime(created);
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          console.error("Rete bakeoff candidate failed to initialize.", error);
          setStatus("error");
        }
      });

    return () => {
      cancelled = true;
      createdRuntime?.destroy();
      setRuntime(null);
    };
  }, [onSelectBlock, projection]);

  useEffect(() => {
    if (!runtime) return;
    for (const node of runtime.editor.getNodes()) {
      node.selected = node.id === selectedBlockId;
      void runtime.area.update("node", node.id);
    }
  }, [runtime, selectedBlockId]);

  return (
    <div className="ewp-rete-canvas" data-testid="rete-bakeoff-canvas">
      <PhaseLaneLayer projection={projection} viewport={viewport} />
      <div
        ref={containerRef}
        className="ewp-rete-editor"
        aria-label="Rete engineering workflow bakeoff"
      />
      <div className="ewp-rete-candidate-note" role="status">
        <strong>Rete.js 2</strong>
        <span>
          {status === "ready"
            ? "Read-only CP1B candidate · Wright model remains canonical"
            : status === "error"
              ? "Candidate failed to initialize"
              : "Initializing candidate"}
        </span>
      </div>
      <div className="ewp-rete-controls" aria-label="Rete viewport controls">
        <button
          type="button"
          aria-label="Zoom Rete workflow in"
          disabled={!runtime}
          onClick={() => void runtime?.zoomBy(1.15)}
        >
          +
        </button>
        <button
          type="button"
          aria-label="Zoom Rete workflow out"
          disabled={!runtime}
          onClick={() => void runtime?.zoomBy(0.87)}
        >
          −
        </button>
        <button
          type="button"
          aria-label="Fit Rete workflow"
          disabled={!runtime}
          onClick={() => void runtime?.fit()}
        >
          ⛶
        </button>
      </div>
    </div>
  );
}

export function ReteBakeoffHarness() {
  return (
    <EngineeringWorkflowVisualSlice
      badge="CP1B · Rete.js"
      renderCanvas={(props) => <ReteCanvas {...props} />}
    />
  );
}

export default ReteBakeoffHarness;
