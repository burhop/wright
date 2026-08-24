import { useMemo, useState } from "react";
import type { ReactNode } from "react";

import {
  engineeringCapabilityCategories,
  engineeringCapabilityTemplates,
} from "./fixtures/engineering-capability-library";
import { drillBitHolderWorkflow } from "./fixtures/drill-bit-holder-workflow";
import {
  blockDimensions,
  type WorkflowBlockRole,
  type WorkflowPreviewBlock,
  type WorkflowPreviewConnection,
  type WorkflowPreviewPhase,
  type WorkflowPreview,
} from "./workflow-preview-model";

import "./engineering-workflow-visual-slice.css";

const CANVAS_WIDTH = 1360;

const roleLabels: Record<WorkflowBlockRole, string> = {
  input: "Input",
  "ai-task": "AI task",
  "mcp-action": "MCP action",
  artifact: "Artifact",
  decision: "Review",
  notification: "Notification",
};

const roleIcons: Record<WorkflowBlockRole, string> = {
  input: "↥",
  "ai-task": "✦",
  "mcp-action": "⌘",
  artifact: "▤",
  decision: "✓",
  notification: "↗",
};

const paletteGroups = [
  {
    label: "Inputs",
    items: ["File upload", "Text input", "Company context"],
    role: "input" as const,
  },
  {
    label: "AI Tasks",
    items: ["Generate document", "Plan work", "Review results"],
    role: "ai-task" as const,
  },
  {
    label: "Pinned capabilities",
    items: ["Parametric CAD", "Structural FEA", "CAM & toolpaths"],
    role: "mcp-action" as const,
  },
  {
    label: "Documents",
    items: ["Specification", "Model or dataset", "Report or drawing"],
    role: "artifact" as const,
  },
  {
    label: "Review Gates",
    items: ["Decision gate", "Approval", "Quality check"],
    role: "decision" as const,
  },
];

function WrightMark() {
  return (
    <svg
      className="ewp-brand__mark"
      viewBox="0 0 32 28"
      role="img"
      aria-label="Wright"
    >
      <path d="M2 6 7 1l6 6-5 6z" />
      <path d="m10 14 5-5 6 6-5 6z" />
      <path d="m18 6 5-5 6 6-5 6z" />
    </svg>
  );
}

function RoleIcon({ role }: { role: WorkflowBlockRole }) {
  return (
    <span className="ewp-role-icon" data-role={role} aria-hidden="true">
      {roleIcons[role]}
    </span>
  );
}

export function WorkflowBlock({
  block,
  selected,
  onSelect,
}: {
  block: WorkflowPreviewBlock;
  selected: boolean;
  onSelect: (blockId: string) => void;
}) {
  const { width, height } = blockDimensions(block);
  const style = {
    left: block.position.x,
    top: block.position.y,
    width,
    height,
  };

  if (block.role === "decision") {
    return (
      <button
        type="button"
        className={`ewp-decision${selected ? " is-selected" : ""}`}
        style={style}
        aria-label={`Review: ${block.title}`}
        aria-pressed={selected}
        onClick={() => onSelect(block.blockId)}
      >
        <span className="ewp-decision__shape">
          <span className="ewp-decision__content">
            <RoleIcon role={block.role} />
            <strong>{block.title}</strong>
            <small>{block.purpose}</small>
          </span>
        </span>
      </button>
    );
  }

  return (
    <button
      type="button"
      className={`ewp-node${selected ? " is-selected" : ""}`}
      data-role={block.role}
      style={style}
      aria-label={`${roleLabels[block.role]} ${block.sequence ? `${block.sequence}. ` : ""}${block.title}`}
      aria-pressed={selected}
      onClick={() => onSelect(block.blockId)}
    >
      <span className="ewp-node__heading">
        <RoleIcon role={block.role} />
        <strong>
          {block.sequence ? `${block.sequence}. ` : ""}
          {block.title}
        </strong>
      </span>
      <span className="ewp-node__purpose">{block.purpose}</span>
      <span className="ewp-node__footer">
        <span className="ewp-node__port">IN</span>
        {block.badge ? (
          <span className="ewp-node__badge">{block.badge}</span>
        ) : (
          <span />
        )}
        <span className="ewp-node__port">OUT</span>
      </span>
      {block.status ? (
        <span className="ewp-node__status">{block.status}</span>
      ) : null}
    </button>
  );
}

function connectionPath(
  connection: WorkflowPreviewConnection,
  phase: WorkflowPreviewPhase,
  blocks: Map<string, WorkflowPreviewBlock>,
): string {
  const source = blocks.get(connection.sourceBlockId);
  const target = blocks.get(connection.targetBlockId);
  if (!source || !target) return "";

  const sourceSize = blockDimensions(source);
  const targetSize = blockDimensions(target);

  if (connection.semantics === "feedback") {
    const startX = source.position.x + sourceSize.width / 2;
    const startY = source.position.y + sourceSize.height;
    const endX = target.position.x + targetSize.width / 2;
    const endY = target.position.y + targetSize.height;
    const railY = phase.height - 11;
    return `M ${startX} ${startY} V ${railY} H ${endX} V ${endY}`;
  }

  const verticallyAligned =
    Math.abs(source.position.x - target.position.x) < 24 &&
    target.position.y > source.position.y;
  if (verticallyAligned) {
    const x = source.position.x + sourceSize.width / 2;
    return `M ${x} ${source.position.y + sourceSize.height} V ${target.position.y}`;
  }

  const startX = source.position.x + sourceSize.width;
  const startY = source.position.y + sourceSize.height / 2;
  const endX = target.position.x;
  const endY = target.position.y + targetSize.height / 2;
  const middleX = startX + Math.max(18, (endX - startX) / 2);
  return `M ${startX} ${startY} H ${middleX} V ${endY} H ${endX}`;
}

function ConnectionLayer({
  phase,
  blocks,
  connections,
}: {
  phase: WorkflowPreviewPhase;
  blocks: WorkflowPreviewBlock[];
  connections: WorkflowPreviewConnection[];
}) {
  const blockMap = useMemo(
    () => new Map(blocks.map((block) => [block.blockId, block])),
    [blocks],
  );

  return (
    <svg
      className="ewp-connections"
      width={CANVAS_WIDTH}
      height={phase.height}
      viewBox={`0 0 ${CANVAS_WIDTH} ${phase.height}`}
      aria-hidden="true"
    >
      <defs>
        {(["data", "control", "feedback"] as const).map((semantics) => (
          <marker
            key={semantics}
            id={`ewp-arrow-${phase.phaseId}-${semantics}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path
              className={`ewp-arrow ewp-arrow--${semantics}`}
              d="M 0 0 L 10 5 L 0 10 z"
            />
          </marker>
        ))}
      </defs>
      {connections.map((connection) => {
        const path = connectionPath(connection, phase, blockMap);
        if (!path) return null;
        return (
          <g key={connection.connectionId}>
            <path
              className={`ewp-connection ewp-connection--${connection.semantics}`}
              d={path}
              markerEnd={`url(#ewp-arrow-${phase.phaseId}-${connection.semantics})`}
            />
            {connection.label ? (
              <text
                className={`ewp-connection__label ewp-connection__label--${connection.semantics}`}
                x={
                  connection.semantics === "feedback"
                    ? 660
                    : (() => {
                        const source = blockMap.get(connection.sourceBlockId);
                        const target = blockMap.get(connection.targetBlockId);
                        return source && target
                          ? (source.position.x + target.position.x) / 2 + 65
                          : 0;
                      })()
                }
                y={
                  connection.semantics === "feedback"
                    ? phase.height - 16
                    : (() => {
                        const source = blockMap.get(connection.sourceBlockId);
                        return source
                          ? source.position.y +
                              blockDimensions(source).height / 2 -
                              9
                          : 0;
                      })()
                }
              >
                {connection.label.toUpperCase()}
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

function PhaseLane({
  phase,
  blocks,
  connections,
  selectedBlockId,
  onSelectBlock,
}: {
  phase: WorkflowPreviewPhase;
  blocks: WorkflowPreviewBlock[];
  connections: WorkflowPreviewConnection[];
  selectedBlockId: string;
  onSelectBlock: (blockId: string) => void;
}) {
  return (
    <section
      className="ewp-phase"
      data-tone={phase.tone}
      style={{ height: phase.height }}
      aria-labelledby={`ewp-phase-${phase.phaseId}`}
    >
      <header className="ewp-phase__header">
        <span className="ewp-phase__number">{phase.index}</span>
        <span>
          <h2 id={`ewp-phase-${phase.phaseId}`}>{phase.label}</h2>
          <small>{phase.description}</small>
        </span>
        {phase.phaseId === "verify" ? (
          <span className="ewp-phase__handoff">
            <span data-state="feedback">
              Fail · revise geometry / thickness
            </span>
            <span data-state="pass">Pass · release to manufacturing</span>
          </span>
        ) : null}
      </header>
      <ConnectionLayer
        phase={phase}
        blocks={blocks}
        connections={connections}
      />
      {blocks.map((block) => (
        <WorkflowBlock
          key={block.blockId}
          block={block}
          selected={block.blockId === selectedBlockId}
          onSelect={onSelectBlock}
        />
      ))}
      <ol className="ewp-sr-only" aria-label={`${phase.label} connections`}>
        {connections.map((connection) => {
          const source = blocks.find(
            (block) => block.blockId === connection.sourceBlockId,
          );
          const target = blocks.find(
            (block) => block.blockId === connection.targetBlockId,
          );
          return source && target ? (
            <li key={connection.connectionId}>
              {source.title} to {target.title}, {connection.semantics}
              {connection.label ? `: ${connection.label}` : ""}
            </li>
          ) : null;
        })}
      </ol>
    </section>
  );
}

function Palette({
  onBrowseCapabilities,
}: {
  onBrowseCapabilities: () => void;
}) {
  return (
    <aside className="ewp-palette" aria-label="Engineering blocks">
      <div className="ewp-panel-title">Engineering blocks</div>
      <p className="ewp-palette__hint">
        Visual preview · drag and drop comes later
      </p>
      {paletteGroups.map((group) => (
        <section key={group.label} className="ewp-palette__group">
          <h2>{group.label}</h2>
          <ul>
            {group.items.map((item) => (
              <li key={item}>
                <span className="ewp-palette__item" data-role={group.role}>
                  <RoleIcon role={group.role} />
                  <span>{item}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      ))}
      <button
        type="button"
        className="ewp-palette__browse"
        onClick={onBrowseCapabilities}
      >
        Browse capability library
        <small>CAD, FEA, CFD, CAM, PLM, kinematics + more</small>
      </button>
    </aside>
  );
}

function CapabilityLibrary({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState("all");
  const normalizedQuery = query.trim().toLowerCase();
  const matches = engineeringCapabilityTemplates.filter((capability) => {
    if (categoryId !== "all" && capability.categoryId !== categoryId) {
      return false;
    }
    if (!normalizedQuery) return true;
    return [
      capability.title,
      capability.description,
      ...capability.keywords,
    ].some((value) => value.toLowerCase().includes(normalizedQuery));
  });

  return (
    <div className="ewp-capability-backdrop" role="presentation">
      <section
        className="ewp-capability-library"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ewp-capability-library-title"
      >
        <header className="ewp-capability-library__header">
          <div>
            <h2 id="ewp-capability-library-title">
              Engineering capability library
            </h2>
            <p>
              Choose an engineer-friendly template, then bind an exact MCP
              catalog tool later.
            </p>
          </div>
          <label>
            <span className="ewp-sr-only">Search capabilities</span>
            <input
              autoFocus
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search CAD, CFD, motion, inspection."
            />
          </label>
          <button
            type="button"
            className="ewp-capability-library__close"
            aria-label="Close capability library"
            onClick={onClose}
          >
            x
          </button>
        </header>
        <div className="ewp-capability-library__content">
          <nav
            className="ewp-capability-library__categories"
            aria-label="Capability categories"
          >
            {engineeringCapabilityCategories.map((category) => (
              <button
                key={category.categoryId}
                type="button"
                aria-pressed={categoryId === category.categoryId}
                onClick={() => setCategoryId(category.categoryId)}
              >
                {category.label}
              </button>
            ))}
          </nav>
          <div className="ewp-capability-library__results">
            <div className="ewp-capability-library__summary" aria-live="polite">
              <span>
                <strong>{matches.length}</strong> capability templates
              </span>
              <span>Discovery labels do not select runtime code</span>
            </div>
            <div className="ewp-capability-library__grid">
              {matches.map((capability) => (
                <article
                  key={capability.capabilityId}
                  className="ewp-capability-card"
                >
                  <div className="ewp-capability-card__heading">
                    <h3>{capability.title}</h3>
                    <span>{capability.catalogMatches} catalog matches</span>
                  </div>
                  <p>{capability.description}</p>
                  <dl>
                    <div>
                      <dt>Inputs</dt>
                      <dd>{capability.expectedInputs.join(" � ")}</dd>
                    </div>
                    <div>
                      <dt>Outputs</dt>
                      <dd>{capability.expectedOutputs.join(" � ")}</dd>
                    </div>
                  </dl>
                  <div className="ewp-capability-card__footer">
                    <small>Generic MCP action template</small>
                    <button type="button" disabled>
                      Add in CP3
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function Inspector({
  block,
  outgoing,
}: {
  block: WorkflowPreviewBlock;
  outgoing: WorkflowPreviewBlock[];
}) {
  return (
    <aside className="ewp-inspector" aria-label="Block properties">
      <div className="ewp-panel-title">
        Block properties <span aria-hidden="true">×</span>
      </div>
      <div className="ewp-inspector__identity">
        <RoleIcon role={block.role} />
        <span>
          <strong>
            {block.sequence ? `${block.sequence}. ` : ""}
            {block.title}
          </strong>
          <small>{roleLabels[block.role]}</small>
        </span>
      </div>
      <div
        className="ewp-inspector__tabs"
        role="tablist"
        aria-label="Block detail sections"
      >
        <button type="button" role="tab" aria-selected="true">
          Content
        </button>
        <button type="button" role="tab" aria-selected="false" disabled>
          Metadata
        </button>
      </div>
      <div className="ewp-inspector__body">
        <p className="ewp-inspector__summary">
          {block.inspector?.summary ?? block.purpose}
        </p>
        {(
          block.inspector?.fields ?? [
            { label: "Purpose", value: block.purpose },
            { label: "Role", value: roleLabels[block.role] },
            {
              label: "Current binding",
              value:
                block.role === "mcp-action"
                  ? "Exact catalog identity required"
                  : "Not applicable",
            },
          ]
        ).map((field) => (
          <label key={field.label} className="ewp-inspector__field">
            <span>{field.label}</span>
            <textarea
              value={field.value}
              readOnly
              rows={field.value.includes("\n") ? 4 : 2}
            />
          </label>
        ))}
        <button type="button" className="ewp-inspector__edit" disabled>
          Edit in CP3
        </button>
        <section className="ewp-inspector__output">
          <h2>Provides to</h2>
          {outgoing.length ? (
            <ul>
              {outgoing.map((target) => (
                <li key={target.blockId} data-role={target.role}>
                  <span /> {target.title}
                </li>
              ))}
            </ul>
          ) : (
            <p>Terminal workflow output</p>
          )}
        </section>
      </div>
      <MiniMap />
    </aside>
  );
}

function MiniMap() {
  return (
    <div className="ewp-minimap" role="img" aria-label="Workflow overview">
      <div data-phase="define">
        {Array.from({ length: 9 }, (_, index) => (
          <i key={index} />
        ))}
      </div>
      <div data-phase="verify">
        {Array.from({ length: 5 }, (_, index) => (
          <i key={index} />
        ))}
      </div>
      <div data-phase="manufacture">
        {Array.from({ length: 8 }, (_, index) => (
          <i key={index} />
        ))}
      </div>
      <span />
    </div>
  );
}

function Legend() {
  const roles: WorkflowBlockRole[] = [
    "input",
    "ai-task",
    "mcp-action",
    "artifact",
    "decision",
    "notification",
  ];
  return (
    <div className="ewp-legend" aria-label="Workflow legend">
      <strong>Legend</strong>
      {roles.map((role) => (
        <span key={role} data-role={role}>
          <i /> {roleLabels[role]}
        </span>
      ))}
      <span className="ewp-legend__feedback">
        <i /> Feedback
      </span>
    </div>
  );
}

export interface EngineeringWorkflowCanvasRenderProps {
  workflow: WorkflowPreview;
  selectedBlockId: string;
  onSelectBlock: (blockId: string) => void;
}

export interface EngineeringWorkflowVisualSliceProps {
  badge?: string;
  renderCanvas?: (props: EngineeringWorkflowCanvasRenderProps) => ReactNode;
  workflow?: WorkflowPreview;
}

export function EngineeringWorkflowVisualSlice({
  badge = "Visual slice",
  renderCanvas,
  workflow = drillBitHolderWorkflow,
}: EngineeringWorkflowVisualSliceProps = {}) {
  const [selectedBlockId, setSelectedBlockId] = useState(
    () =>
      workflow.blocks.find(({ blockId }) => blockId === "analysis-definition")
        ?.blockId ?? workflow.blocks[0].blockId,
  );
  const [zoom, setZoom] = useState(0.9);
  const [capabilityLibraryOpen, setCapabilityLibraryOpen] = useState(false);

  const selectedBlock =
    workflow.blocks.find((block) => block.blockId === selectedBlockId) ??
    workflow.blocks[0];
  const outgoing = workflow.connections
    .filter((connection) => connection.sourceBlockId === selectedBlock.blockId)
    .map((connection) =>
      workflow.blocks.find(
        (block) => block.blockId === connection.targetBlockId,
      ),
    )
    .filter((block): block is WorkflowPreviewBlock => Boolean(block));
  const contentHeight = workflow.phases.reduce(
    (total, phase) => total + phase.height + 10,
    0,
  );

  return (
    <div
      className="ewp"
      data-testid="engineering-workflow-visual-slice"
      data-theme="dark"
    >
      <header className="ewp-toolbar">
        <div className="ewp-brand">
          <WrightMark />
          <h1>{workflow.title}</h1>
          <span>{badge}</span>
        </div>
        <div className="ewp-toolbar__actions" aria-label="Workflow actions">
          <button type="button" className="is-primary" disabled>
            ▶ Run workflow
          </button>
          <button type="button" disabled>
            ▣ Save draft
          </button>
          <button type="button" disabled>
            ◴ History
          </button>
          <button
            type="button"
            className="is-icon"
            disabled
            aria-label="Settings"
          >
            ⚙
          </button>
          <span
            className="ewp-avatar"
            aria-label="Signed in as mechanical engineer"
          >
            ME
          </span>
        </div>
      </header>

      <div className="ewp-workspace">
        <Palette onBrowseCapabilities={() => setCapabilityLibraryOpen(true)} />
        <main className="ewp-canvas" aria-label="Engineering workflow preview">
          {renderCanvas ? (
            renderCanvas({
              workflow,
              selectedBlockId,
              onSelectBlock: setSelectedBlockId,
            })
          ) : (
            <>
              <div className="ewp-canvas__scroll">
                <div
                  className="ewp-board-frame"
                  style={{
                    width: CANVAS_WIDTH * zoom,
                    height: contentHeight * zoom,
                  }}
                >
                  <div
                    className="ewp-board"
                    style={{
                      width: CANVAS_WIDTH,
                      transform: `scale(${zoom})`,
                    }}
                  >
                    {workflow.phases.map((phase) => {
                      const phaseBlocks = workflow.blocks.filter(
                        (block) => block.phaseId === phase.phaseId,
                      );
                      const blockIds = new Set(
                        phaseBlocks.map((block) => block.blockId),
                      );
                      const phaseConnections = workflow.connections.filter(
                        (connection) =>
                          blockIds.has(connection.sourceBlockId) &&
                          blockIds.has(connection.targetBlockId),
                      );
                      return (
                        <PhaseLane
                          key={phase.phaseId}
                          phase={phase}
                          blocks={phaseBlocks}
                          connections={phaseConnections}
                          selectedBlockId={selectedBlockId}
                          onSelectBlock={setSelectedBlockId}
                        />
                      );
                    })}
                  </div>
                </div>
              </div>
              <div
                className="ewp-canvas__controls"
                aria-label="Preview zoom controls"
              >
                <button
                  type="button"
                  aria-label="Zoom in"
                  onClick={() => setZoom((value) => Math.min(1, value + 0.08))}
                >
                  +
                </button>
                <button
                  type="button"
                  aria-label="Zoom out"
                  onClick={() =>
                    setZoom((value) => Math.max(0.58, value - 0.08))
                  }
                >
                  −
                </button>
                <button
                  type="button"
                  aria-label="Fit workflow"
                  onClick={() => setZoom(0.9)}
                >
                  ⛶
                </button>
                <output aria-live="polite">{Math.round(zoom * 100)}%</output>
              </div>
            </>
          )}
          <Legend />
        </main>
        <Inspector block={selectedBlock} outgoing={outgoing} />
      </div>
      {capabilityLibraryOpen ? (
        <CapabilityLibrary onClose={() => setCapabilityLibraryOpen(false)} />
      ) : null}
    </div>
  );
}

export default EngineeringWorkflowVisualSlice;
