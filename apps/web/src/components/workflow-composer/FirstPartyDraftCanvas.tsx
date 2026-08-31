import { useMemo, useState } from "react";

import type { DraftCanvasAdapterProps } from "./renderer-types";

const MIN_ZOOM = 60;
const MAX_ZOOM = 140;
const ZOOM_STEP = 20;

export function FirstPartyDraftCanvas({
  projection,
  selectedSemanticId,
  onIntent,
}: DraftCanvasAdapterProps): React.ReactNode {
  const [zoom, setZoom] = useState(100);
  const blocks = useMemo(
    () => projection.phases.flatMap((phase) => phase.blocks),
    [projection],
  );

  return (
    <section className="workflow-canvas" data-testid="workflow-composer-canvas" aria-label="Workflow draft diagram">
      <header className="workflow-canvas__toolbar">
        <div>
          <p className="workflow-composer__eyebrow">First-party diagram</p>
          <strong>{blocks.length} blocks · {projection.phases.length} phases</strong>
        </div>
        <div className="workflow-canvas__zoom" aria-label="Diagram zoom controls">
          <button data-testid="workflow-canvas-zoom-out" type="button" onClick={() => setZoom((value) => Math.max(MIN_ZOOM, value - ZOOM_STEP))} aria-label="Zoom out">−</button>
          <output aria-live="polite">{zoom}%</output>
          <button data-testid="workflow-canvas-zoom-in" type="button" onClick={() => setZoom((value) => Math.min(MAX_ZOOM, value + ZOOM_STEP))} aria-label="Zoom in">+</button>
          <button data-testid="workflow-canvas-fit" type="button" onClick={() => setZoom(100)}>Fit</button>
        </div>
      </header>

      <div className="workflow-canvas__viewport">
        <div className="workflow-canvas__board" style={{ "--workflow-canvas-zoom": zoom / 100 } as React.CSSProperties}>
          <div className="workflow-canvas__lanes">
            {projection.phases.map((phase) => (
              <section className="workflow-canvas__lane" data-semantic-id={phase.semanticId} key={phase.semanticId}>
                <header>
                  <span>Phase {phase.order + 1}</span>
                  <h3>{phase.name}</h3>
                  <code>{phase.semanticId}</code>
                  <p>{phase.purpose}</p>
                </header>
                <div className="workflow-canvas__blocks">
                  {phase.blocks.map((block) => (
                    <article
                      className="workflow-canvas__block"
                      data-role={block.role}
                      data-selected={selectedSemanticId === block.semanticId ? "true" : "false"}
                      data-semantic-id={block.semanticId}
                      key={block.semanticId}
                    >
                      <button
                        data-testid={`workflow-canvas-select-${block.semanticId}`}
                        type="button"
                        onClick={() => onIntent({ type: "select", semanticId: block.semanticId })}
                      >
                        <span>{block.role}</span>
                        <strong>{block.title}</strong>
                        <code>{block.semanticId}</code>
                      </button>
                      <p>{block.purpose}</p>
                      <div className="workflow-canvas__ports">
                        <div>
                          <small>Inputs</small>
                          {block.inputs.length > 0 ? block.inputs.map((port) => (
                            <span className="workflow-canvas__port" data-direction="input" data-semantic-id={port.semanticId} key={port.semanticId}>
                              <b>IN</b> {port.name}<code>{port.semanticId}</code>
                            </span>
                          )) : <em>None</em>}
                        </div>
                        <div>
                          <small>Outputs</small>
                          {block.outputs.length > 0 ? block.outputs.map((port) => (
                            <span className="workflow-canvas__port" data-direction="output" data-semantic-id={port.semanticId} key={port.semanticId}>
                              <b>OUT</b> {port.name}<code>{port.semanticId}</code>
                            </span>
                          )) : <em>None</em>}
                        </div>
                      </div>
                      {block.gates.map((gate) => (
                        <section className="workflow-canvas__gate" data-semantic-id={gate.semanticId} key={gate.semanticId}>
                          <strong>◇ Approval gate</strong>
                          <code>{gate.semanticId}</code>
                          <span>{gate.condition}</span>
                          <span>Proceed → {gate.proceed_target_block_id}</span>
                          <span>Revise ↩ {gate.revise_target_block_id}</span>
                        </section>
                      ))}
                      {block.artifacts.map((artifact) => (
                        <section className="workflow-canvas__artifact" data-semantic-id={artifact.semanticId} key={artifact.semanticId}>
                          <strong>▱ Intended artifact</strong>
                          <span>{artifact.title}</span>
                          <code>{artifact.semanticId}</code>
                        </section>
                      ))}
                    </article>
                  ))}
                  {phase.blocks.length === 0 && <p className="workflow-canvas__empty">Choose a block from the palette to begin this provisional phase.</p>}
                </div>
              </section>
            ))}
          </div>

          <section className="workflow-canvas__relationships" aria-label="Declared relationships">
            <div>
              <h3>Directed connections</h3>
              {projection.connections.map((connection) => (
                <p data-semantic-id={connection.semanticId} key={connection.semanticId}>
                  <strong>→</strong> <code>{connection.semanticId}</code>
                  <span>{connection.source_port_id} → {connection.target_port_id}</span>
                </p>
              ))}
            </div>
            <div>
              <h3>Feedback</h3>
              {projection.feedbackPaths.map((feedback) => (
                <p data-semantic-id={feedback.semanticId} key={feedback.semanticId}>
                  <strong>↩</strong> <code>{feedback.semanticId}</code>
                  <span>{feedback.from_gate_id} → {feedback.to_block_id}</span>
                  <span>{feedback.label}</span>
                </p>
              ))}
            </div>
          </section>
        </div>
      </div>
    </section>
  );
}
