import { useMemo, useReducer, useRef, useState } from "react";
import type { ReactNode } from "react";

import {
  engineeringCapabilityCategories,
  engineeringCapabilityTemplates,
} from "./fixtures/engineering-capability-library";
import {
  createReferenceImageHistory,
  reduceReferenceImageHistory,
  type ReferenceImageHistory,
  type ReferenceImageHistoryAction,
} from "./domain/reference-image-draft";
import {
  ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION,
  engineeringWorkflowCssVariables,
  workflowRoleIcons,
  workflowRoleLabels,
} from "./engineering-workflow-visual-contract";
import {
  prototypeViewStateCopy,
  type EngineeringWorkflowPrototypeViewState,
} from "./prototype-review-state";
import { drillBitHolderWorkflow } from "./fixtures/drill-bit-holder-workflow";
import {
  blockDimensions,
  type WorkflowBlockRole,
  type WorkflowPreviewBlock,
  type WorkflowPreviewConnection,
  type WorkflowPreviewPhase,
  type WorkflowPreview,
  type WorkflowReferenceImageOption,
} from "./workflow-preview-model";

import "./engineering-workflow-visual-slice.css";

const CANVAS_WIDTH = 1360;

interface ReferenceImageDraftState {
  history: ReferenceImageHistory;
  images: WorkflowReferenceImageOption[];
}

type ReferenceImageDraftAction =
  | { type: "edit"; action: ReferenceImageHistoryAction }
  | { type: "upload"; images: readonly WorkflowReferenceImageOption[] };

function createReferenceImageDraft(): ReferenceImageDraftState {
  return {
    history: createReferenceImageHistory(),
    images: [],
  };
}

function reduceReferenceImageDraft(
  state: ReferenceImageDraftState,
  action: ReferenceImageDraftAction,
): ReferenceImageDraftState {
  if (action.type === "edit") {
    return {
      ...state,
      history: reduceReferenceImageHistory(
        state.history,
        action.action,
        state.images.map(({ imageId }) => imageId),
      ),
    };
  }

  const existingIds = new Set(state.images.map(({ imageId }) => imageId));
  const uploadedImages = action.images.filter(
    ({ imageId }) => !existingIds.has(imageId),
  );
  if (uploadedImages.length === 0) return state;

  const images = [...state.images, ...uploadedImages];
  const allowedImageIds = images.map(({ imageId }) => imageId);
  const history = uploadedImages.reduce(
    (currentHistory, image) =>
      reduceReferenceImageHistory(
        currentHistory,
        {
          type: "apply",
          command: { type: "add", imageId: image.imageId },
        },
        allowedImageIds,
      ),
    state.history,
  );

  return { history, images };
}

function formatImageFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return Math.round(bytes / 1024) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function readUploadedReferenceImage(
  file: File,
  imageId: string,
): Promise<WorkflowReferenceImageOption> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () =>
      reject(new Error("Wright could not read " + file.name + "."));
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Wright could not preview " + file.name + "."));
        return;
      }
      resolve({
        imageId,
        title: file.name,
        description:
          (file.type || "Image file") + " · " + formatImageFileSize(file.size),
        alt: "Uploaded reference image " + file.name,
        thumbnailUrl: reader.result,
      });
    };
    reader.readAsDataURL(file);
  });
}
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
      {workflowRoleIcons[role]}
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
      aria-label={`${workflowRoleLabels[block.role]} ${block.sequence ? `${block.sequence}. ` : ""}${block.title}`}
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
      {block.imagePreviews?.length ? (
        <span
          className="ewp-node__image-strip"
          aria-label={`${block.imagePreviews.length} selected reference images`}
        >
          {block.imagePreviews.slice(0, 3).map((image) => (
            <img
              key={image.imageId}
              src={image.thumbnailUrl}
              alt=""
              title={image.title}
            />
          ))}
        </span>
      ) : (
        <span className="ewp-node__purpose">{block.purpose}</span>
      )}
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

function ReferenceImageEditor({
  history,
  dispatch,
  images,
  onFilesSelected,
  uploadError,
}: {
  history: ReferenceImageHistory;
  dispatch: (action: ReferenceImageHistoryAction) => void;
  images: readonly WorkflowReferenceImageOption[];
  onFilesSelected: (files: readonly File[]) => void;
  uploadError: string | null;
}) {
  const imagesById = new Map(images.map((image) => [image.imageId, image]));
  const selectedImages = history.present.imageIds
    .map((imageId) => imagesById.get(imageId))
    .filter(
      (image): image is WorkflowReferenceImageOption => image !== undefined,
    );
  const count = selectedImages.length;

  return (
    <section
      className="ewp-reference-images"
      aria-labelledby="ewp-reference-images-title"
    >
      <header className="ewp-reference-images__header">
        <span>
          <h2 id="ewp-reference-images-title">Reference images</h2>
          <small>Local CP3A draft · resets on reload</small>
        </span>
        <strong>{count} selected</strong>
      </header>

      <div className="ewp-reference-images__history">
        <button
          type="button"
          disabled={history.past.length === 0}
          onClick={() => dispatch({ type: "undo" })}
        >
          Undo
        </button>
        <button
          type="button"
          disabled={history.future.length === 0}
          onClick={() => dispatch({ type: "redo" })}
        >
          Redo
        </button>
        <output aria-live="polite">
          {count === 0
            ? "No images selected"
            : count + " image" + (count === 1 ? "" : "s") + " selected"}
        </output>
      </div>

      {selectedImages.length ? (
        <ol
          className="ewp-reference-images__selected"
          aria-label="Selected reference images"
        >
          {selectedImages.map((image, index) => (
            <li key={image.imageId}>
              <img src={image.thumbnailUrl} alt={image.alt} />
              <span>
                <strong>{image.title}</strong>
                <small>{image.description}</small>
              </span>
              <div aria-label={"Reorder or remove " + image.title}>
                <button
                  type="button"
                  aria-label={"Move " + image.title + " earlier"}
                  disabled={index === 0}
                  onClick={() =>
                    dispatch({
                      type: "apply",
                      command: {
                        type: "move",
                        imageId: image.imageId,
                        direction: "earlier",
                      },
                    })
                  }
                >
                  ↑
                </button>
                <button
                  type="button"
                  aria-label={"Move " + image.title + " later"}
                  disabled={index === selectedImages.length - 1}
                  onClick={() =>
                    dispatch({
                      type: "apply",
                      command: {
                        type: "move",
                        imageId: image.imageId,
                        direction: "later",
                      },
                    })
                  }
                >
                  ↓
                </button>
                <button
                  type="button"
                  aria-label={"Remove " + image.title}
                  onClick={() =>
                    dispatch({
                      type: "apply",
                      command: { type: "remove", imageId: image.imageId },
                    })
                  }
                >
                  ×
                </button>
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <p className="ewp-reference-images__empty">
          Upload one or more photos or other image files. They remain in this
          browser tab and can be used as inputs by later workflow steps.
        </p>
      )}

      <label className="ewp-reference-images__upload">
        <input
          type="file"
          accept="image/*"
          multiple
          aria-label="Upload reference images"
          onChange={(event) => {
            const files = Array.from(event.currentTarget.files ?? []);
            if (files.length > 0) onFilesSelected(files);
            event.currentTarget.value = "";
          }}
        />
        <span>{count === 0 ? "Upload images" : "Add more images"}</span>
        <small>Select one or more image files · session only</small>
      </label>
      {uploadError ? (
        <p className="ewp-reference-images__upload-error" role="alert">
          {uploadError}
        </p>
      ) : null}
    </section>
  );
}
function Inspector({
  workflow,
  block,
  outgoing,
  referenceImageHistory,
  onReferenceImageAction,
  referenceImages,
  onReferenceImageFilesSelected,
  referenceImageUploadError,
}: {
  workflow: WorkflowPreview;
  block: WorkflowPreviewBlock;
  outgoing: WorkflowPreviewBlock[];
  referenceImageHistory: ReferenceImageHistory;
  onReferenceImageAction: (action: ReferenceImageHistoryAction) => void;
  referenceImages: readonly WorkflowReferenceImageOption[];
  onReferenceImageFilesSelected: (files: readonly File[]) => void;
  referenceImageUploadError: string | null;
}) {
  const [activeTab, setActiveTab] = useState<"details" | "evidence">("details");
  const detailsTabId = "ewp-inspector-details-tab";
  const evidenceTabId = "ewp-inspector-evidence-tab";

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
          <small>{workflowRoleLabels[block.role]}</small>
        </span>
      </div>
      <div
        className="ewp-inspector__tabs"
        role="tablist"
        aria-label="Block detail sections"
      >
        <button
          id={detailsTabId}
          type="button"
          role="tab"
          aria-selected={activeTab === "details"}
          aria-controls="ewp-inspector-details-panel"
          tabIndex={activeTab === "details" ? 0 : -1}
          onClick={() => setActiveTab("details")}
        >
          Details
        </button>
        <button
          id={evidenceTabId}
          type="button"
          role="tab"
          aria-selected={activeTab === "evidence"}
          aria-controls="ewp-inspector-evidence-panel"
          tabIndex={activeTab === "evidence" ? 0 : -1}
          onClick={() => setActiveTab("evidence")}
        >
          Evidence
        </button>
      </div>
      {activeTab === "details" ? (
        <div
          id="ewp-inspector-details-panel"
          className="ewp-inspector__body"
          role="tabpanel"
          aria-labelledby={detailsTabId}
        >
          <p className="ewp-inspector__summary">
            {block.inspector?.summary ?? block.purpose}
          </p>
          {block.blockId === "reference-images" ? (
            <ReferenceImageEditor
              history={referenceImageHistory}
              dispatch={onReferenceImageAction}
              images={referenceImages}
              onFilesSelected={onReferenceImageFilesSelected}
              uploadError={referenceImageUploadError}
            />
          ) : null}
          {(
            block.inspector?.fields ?? [
              { label: "Purpose", value: block.purpose },
              { label: "Role", value: workflowRoleLabels[block.role] },
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
          {block.blockId !== "reference-images" ? (
            <button type="button" className="ewp-inspector__edit" disabled>
              Edit in a later CP3 increment
            </button>
          ) : null}
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
      ) : (
        <div
          id="ewp-inspector-evidence-panel"
          className="ewp-inspector__body"
          role="tabpanel"
          aria-labelledby={evidenceTabId}
        >
          <p className="ewp-inspector__summary">
            Deterministic preview evidence for this Wright-owned workflow
            projection. No engineering tool has been executed.
          </p>
          <dl className="ewp-inspector__evidence-grid">
            <div>
              <dt>Block identity</dt>
              <dd>{block.blockId}</dd>
            </div>
            <div>
              <dt>Workflow revision</dt>
              <dd>
                {workflow.workflowId} · r{workflow.revision}
              </dd>
            </div>
            <div>
              <dt>Projection status</dt>
              <dd>
                {block.blockId === "reference-images"
                  ? "Local CP3A draft · session only"
                  : "Validated fixture · read only"}
              </dd>
            </div>
            {block.blockId === "reference-images" ? (
              <div>
                <dt>Reference input draft</dt>
                <dd>
                  {referenceImageHistory.present.imageIds.length} image
                  {referenceImageHistory.present.imageIds.length === 1
                    ? ""
                    : "s"}{" "}
                  selected · not persisted
                </dd>
              </div>
            ) : null}
            <div>
              <dt>Execution status</dt>
              <dd>Not executed</dd>
            </div>
          </dl>
          <section className="ewp-inspector__evidence-policy">
            <h2>Execution boundary</h2>
            <p>
              {block.role === "mcp-action"
                ? "An exact workspace catalog tool must be bound before the generic MCP gateway can run this action. Capability categories never dispatch runtime services."
                : "This block does not invoke a tool. Any future execution evidence must come through the governed workflow runtime."}
            </p>
          </section>
          <section className="ewp-inspector__output">
            <h2>Evidence status</h2>
            <p>
              Run records and produced artifacts arrive in later governed MCP
              and integration checkpoints.
            </p>
          </section>
        </div>
      )}
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
          <i /> {workflowRoleLabels[role]}
        </span>
      ))}
      <span className="ewp-legend__feedback">
        <i /> Feedback
      </span>
    </div>
  );
}

function WorkflowCanvasReviewState({
  viewState,
}: {
  viewState: Exclude<EngineeringWorkflowPrototypeViewState, "ready">;
}) {
  const copy = prototypeViewStateCopy[viewState];
  return (
    <section
      className="ewp-canvas-state"
      data-state={viewState}
      role={viewState === "error" ? "alert" : "status"}
      aria-live={viewState === "error" ? "assertive" : "polite"}
    >
      <span className="ewp-canvas-state__icon" aria-hidden="true">
        {viewState === "loading" ? "◌" : viewState === "empty" ? "+" : "!"}
      </span>
      <h2>{copy.title}</h2>
      <p>{copy.description}</p>
      {viewState === "empty" ? (
        <button type="button" disabled>
          Add first block in CP3
        </button>
      ) : null}
      {viewState === "error" ? (
        <button type="button" disabled>
          Retry preview
        </button>
      ) : null}
    </section>
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
  viewState?: EngineeringWorkflowPrototypeViewState;
}

export function EngineeringWorkflowVisualSlice({
  badge = "Visual slice",
  renderCanvas,
  workflow = drillBitHolderWorkflow,
  viewState = "ready",
}: EngineeringWorkflowVisualSliceProps = {}) {
  const [selectedBlockId, setSelectedBlockId] = useState(
    () =>
      workflow.blocks.find(({ blockId }) => blockId === "analysis-definition")
        ?.blockId ?? workflow.blocks[0].blockId,
  );
  const [zoom, setZoom] = useState(0.9);
  const [capabilityLibraryOpen, setCapabilityLibraryOpen] = useState(false);
  const [referenceImageDraft, dispatchReferenceImageDraft] = useReducer(
    reduceReferenceImageDraft,
    createReferenceImageDraft(),
  );
  const [referenceImageUploadError, setReferenceImageUploadError] = useState<
    string | null
  >(null);
  const nextUploadedImageId = useRef(1);
  const referenceImageHistory = referenceImageDraft.history;

  const handleReferenceImageFilesSelected = async (
    files: readonly File[],
  ): Promise<void> => {
    const imageFiles = files.filter(({ type }) => type.startsWith("image/"));
    if (imageFiles.length !== files.length) {
      setReferenceImageUploadError(
        "Only image files can be added to Reference Images.",
      );
    } else {
      setReferenceImageUploadError(null);
    }
    if (imageFiles.length === 0) return;

    try {
      const images = await Promise.all(
        imageFiles.map((file) =>
          readUploadedReferenceImage(
            file,
            "uploaded-reference-" + nextUploadedImageId.current++,
          ),
        ),
      );
      dispatchReferenceImageDraft({ type: "upload", images });
    } catch (error) {
      setReferenceImageUploadError(
        error instanceof Error
          ? error.message
          : "Wright could not read the selected image files.",
      );
    }
  };

  const selectedReferenceImages = useMemo(() => {
    const imagesById = new Map(
      referenceImageDraft.images.map((image) => [image.imageId, image]),
    );
    return referenceImageHistory.present.imageIds
      .map((imageId) => imagesById.get(imageId))
      .filter(
        (image): image is WorkflowReferenceImageOption => image !== undefined,
      );
  }, [referenceImageDraft.images, referenceImageHistory.present.imageIds]);
  const displayWorkflow = useMemo<WorkflowPreview>(() => {
    const count = selectedReferenceImages.length;
    return {
      ...workflow,
      blocks: workflow.blocks.map((block) =>
        block.blockId === "reference-images"
          ? {
              ...block,
              purpose:
                count === 0
                  ? "Select image inputs in the inspector."
                  : block.purpose,
              badge: `${count} ${count === 1 ? "IMAGE" : "IMAGES"}`,
              status:
                count === 0
                  ? "No images selected"
                  : `${count} selected · session only`,
              imagePreviews: selectedReferenceImages.map((imageOption) => ({
                imageId: imageOption.imageId,
                title: imageOption.title,
                alt: imageOption.alt,
                thumbnailUrl: imageOption.thumbnailUrl,
              })),
            }
          : block,
      ),
    };
  }, [selectedReferenceImages, workflow]);

  const selectedBlock =
    displayWorkflow.blocks.find((block) => block.blockId === selectedBlockId) ??
    displayWorkflow.blocks[0];
  const outgoing = displayWorkflow.connections
    .filter((connection) => connection.sourceBlockId === selectedBlock.blockId)
    .map((connection) =>
      displayWorkflow.blocks.find(
        (block) => block.blockId === connection.targetBlockId,
      ),
    )
    .filter((block): block is WorkflowPreviewBlock => Boolean(block));
  const contentHeight = displayWorkflow.phases.reduce(
    (total, phase) => total + phase.height + 10,
    0,
  );

  return (
    <div
      className="ewp"
      data-testid="engineering-workflow-visual-slice"
      data-theme="dark"
      data-visual-contract={ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION}
      style={engineeringWorkflowCssVariables}
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
        <main
          className="ewp-canvas"
          data-view-state={viewState}
          aria-label="Engineering workflow preview"
        >
          {viewState !== "ready" ? (
            <WorkflowCanvasReviewState viewState={viewState} />
          ) : renderCanvas ? (
            renderCanvas({
              workflow: displayWorkflow,
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
                    {displayWorkflow.phases.map((phase) => {
                      const phaseBlocks = displayWorkflow.blocks.filter(
                        (block) => block.phaseId === phase.phaseId,
                      );
                      const blockIds = new Set(
                        phaseBlocks.map((block) => block.blockId),
                      );
                      const phaseConnections =
                        displayWorkflow.connections.filter(
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
        <Inspector
          workflow={displayWorkflow}
          block={selectedBlock}
          outgoing={outgoing}
          referenceImageHistory={referenceImageHistory}
          onReferenceImageAction={(action) =>
            dispatchReferenceImageDraft({ type: "edit", action })
          }
          referenceImages={referenceImageDraft.images}
          onReferenceImageFilesSelected={(files) =>
            void handleReferenceImageFilesSelected(files)
          }
          referenceImageUploadError={referenceImageUploadError}
        />
      </div>
      {capabilityLibraryOpen ? (
        <CapabilityLibrary onClose={() => setCapabilityLibraryOpen(false)} />
      ) : null}
    </div>
  );
}

export default EngineeringWorkflowVisualSlice;
