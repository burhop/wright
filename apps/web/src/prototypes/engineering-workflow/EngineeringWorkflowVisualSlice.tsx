import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import type { ReactNode } from "react";
import type {
  HeadlessBlockName,
  HeadlessStepRecord,
} from "./evaluation/headless-four-block-runner.mjs";

import { KnowledgeLookupEditor } from "./KnowledgeLookupEditor";
import { PromptRequestRequirements } from "./PromptRequestRequirements";
import { DiagnosticLlmPanel } from "./DiagnosticLlmPanel";
import { DiagnosticPanel } from "./DiagnosticPanel";
import { DiagnosticRunMonitor } from "./DiagnosticRunMonitor";
import { DiagnosticWorkflowOutputs } from "./DiagnosticWorkflowOutputs";
import { DiagnosticMcpQuickBinding } from "./DiagnosticMcpQuickBinding";
import {
  DiagnosticMcpBindingPanel,
  type DiagnosticMcpBindingSummary,
} from "./DiagnosticMcpBindingPanel";
import { WorkflowCodeExperiment } from "./WorkflowCodeExperiment";
import {
  createDiagnosticDemoState,
  diagnosticRequestIssues,
  diagnosticBlockOverlay,
  diagnosticStatusMessage,
  reduceDiagnosticDemoState,
  type DiagnosticDemoAction,
  type DiagnosticDemoState,
  type DiagnosticScenario,
} from "./domain/diagnostic-demo";
import {
  diagnosticRequiredToolInputs,
  resolveExplicitDiagnosticMcpBinding,
  suggestDiagnosticMcpBinding,
  type DiagnosticMcpCatalog,
  type DiagnosticMcpServerOption,
  type DiagnosticMcpToolOption,
} from "./domain/diagnostic-mcp-binding";
import {
  promptRequestOutputLabels,
  promptRequestRouteCanRun,
  promptRequestRouteIssues,
  type PromptRequestOutputKind,
} from "./domain/prompt-request-routing";
import {
  workflowOutputsFrom,
  type WorkflowOutputAction,
  type WorkflowOutputReference,
} from "./domain/workflow-output";
import {
  parseWorkflowCodeDocument,
  serializeWorkflowCodeDocument,
  type WorkflowCodeParseResult,
} from "./domain/workflow-code-experiment";
import {
  createKnowledgeLookupHistory,
  reduceKnowledgeLookupHistory,
  type KnowledgeLookupHistory,
  type KnowledgeLookupHistoryAction,
} from "./domain/knowledge-lookup-draft";
import {
  engineeringCapabilityCategories,
  engineeringCapabilityTemplates,
} from "./fixtures/engineering-capability-library";
import {
  createDesignInputHistory,
  reduceDesignInputHistory,
  type DesignInputDocumentDraft,
  type DesignInputHistory,
  type DesignInputHistoryAction,
} from "./domain/design-input-draft";
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
  knowledgeLookupSourceIds,
  knowledgeLookupSources,
} from "./fixtures/knowledge-lookup-sources";
import {
  deterministicDiagnosticLlmAdapter,
  type DiagnosticLlmAdapter,
  type DiagnosticLlmProgress,
  type DiagnosticLlmModelGroup,
  type DiagnosticLlmModelOption,
  type DiagnosticThinkingLevel,
} from "./services/diagnostic-llm-adapter";
import {
  deterministicDiagnosticMcpCatalogAdapter,
  type DiagnosticMcpCatalogAdapter,
} from "./services/diagnostic-mcp-catalog-adapter";
import {
  executeDiagnosticFourBlockChain,
  type DiagnosticOutputActionResult,
  type DiagnosticFourBlockRun,
  type DiagnosticMcpRuntimeAdapter,
} from "./services/diagnostic-four-block-executor";
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
import "./diagnostic-demo.css";

const CANVAS_WIDTH = 1360;
const DIAGNOSTIC_AI_ACCEPTED_OUTPUTS = [
  "request",
  "text",
] as const satisfies readonly PromptRequestOutputKind[];

function diagnosticBlockIdForStep(
  scenario: DiagnosticScenario,
  step: HeadlessBlockName,
): string {
  if (step === "request") return scenario.request.blockId;
  if (step === "ai") return scenario.executorBlockId;
  if (step === "mcp") return scenario.mcpBlockId;
  return scenario.evaluationBlockId;
}

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

function formatFileSize(bytes: number): string {
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
          (file.type || "Image file") + " · " + formatFileSize(file.size),
        alt: "Uploaded reference image " + file.name,
        thumbnailUrl: reader.result,
      });
    };
    reader.readAsDataURL(file);
  });
}
const DESIGN_DOCUMENT_ACCEPT =
  ".txt,.md,.markdown,.csv,.json,.yaml,.yml,.xml,.rtf,.pdf,.doc,.docx";
const READABLE_DOCUMENT_EXTENSIONS = new Set([
  "txt",
  "md",
  "markdown",
  "csv",
  "json",
  "yaml",
  "yml",
  "xml",
  "rtf",
  "pdf",
  "doc",
  "docx",
]);
const TEXT_PREVIEW_EXTENSIONS = new Set([
  "txt",
  "md",
  "markdown",
  "csv",
  "json",
  "yaml",
  "yml",
  "xml",
  "rtf",
]);
const DESIGN_DOCUMENT_PREVIEW_LIMIT = 480;

function fileExtension(fileName: string): string {
  return fileName.split(".").at(-1)?.toLowerCase() ?? "";
}

function isReadableDesignDocument(file: File): boolean {
  return READABLE_DOCUMENT_EXTENSIONS.has(fileExtension(file.name));
}

function canPreviewDesignDocument(file: File): boolean {
  return (
    file.type.startsWith("text/") ||
    TEXT_PREVIEW_EXTENSIONS.has(fileExtension(file.name))
  );
}

function readDocumentText(file: Blob, fileName: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () =>
      reject(new Error("Wright could not read " + fileName + "."));
    reader.onload = () => {
      if (typeof reader.result !== "string") {
        reject(new Error("Wright could not preview " + fileName + "."));
        return;
      }
      resolve(reader.result);
    };
    reader.readAsText(file);
  });
}

async function readUploadedDesignDocument(
  file: File,
  documentId: string,
): Promise<DesignInputDocumentDraft> {
  const text = canPreviewDesignDocument(file)
    ? await readDocumentText(
        file.slice(0, DESIGN_DOCUMENT_PREVIEW_LIMIT + 1),
        file.name,
      )
    : null;
  const normalizedText = text?.trim() ?? null;
  return {
    documentId,
    name: file.name,
    mediaType: file.type || "Document",
    sizeBytes: file.size,
    textPreview:
      normalizedText === null
        ? null
        : normalizedText.slice(0, DESIGN_DOCUMENT_PREVIEW_LIMIT),
    textPreviewTruncated:
      normalizedText !== null &&
      (normalizedText.length > DESIGN_DOCUMENT_PREVIEW_LIMIT ||
        file.size > DESIGN_DOCUMENT_PREVIEW_LIMIT + 1),
  };
}
function reduceKnowledgeLookupDraft(
  history: KnowledgeLookupHistory,
  action: KnowledgeLookupHistoryAction,
): KnowledgeLookupHistory {
  return reduceKnowledgeLookupHistory(
    history,
    action,
    knowledgeLookupSourceIds,
  );
}

const paletteGroups = [
  {
    label: "Inputs",
    items: ["File upload", "Text input", "Knowledge lookup"],
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
        data-run-state={block.runState}
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
            {block.status ? (
              <span className="ewp-decision__status">{block.status}</span>
            ) : null}
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
      data-run-state={block.runState}
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
  title = "Reference images",
}: {
  history: ReferenceImageHistory;
  dispatch: (action: ReferenceImageHistoryAction) => void;
  images: readonly WorkflowReferenceImageOption[];
  onFilesSelected: (files: readonly File[]) => void;
  uploadError: string | null;
  title?: string;
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
          <h2 id="ewp-reference-images-title">{title}</h2>
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
function DesignInputEditor({
  history,
  dispatch,
  onFilesSelected,
  uploadError,
  title = "Design input",
  promptAriaLabel = "Design prompt",
  documentAriaLabel = "Attach design documents",
}: {
  history: DesignInputHistory;
  dispatch: (action: DesignInputHistoryAction) => void;
  onFilesSelected: (files: readonly File[]) => void;
  uploadError: string | null;
  title?: string;
  promptAriaLabel?: string;
  documentAriaLabel?: string;
}) {
  const [promptDraft, setPromptDraft] = useState(history.present.prompt);

  useEffect(() => {
    setPromptDraft(history.present.prompt);
  }, [history.present.prompt]);

  const promptChanged = promptDraft !== history.present.prompt;
  const documentCount = history.present.documents.length;

  return (
    <section
      className="ewp-design-input"
      aria-labelledby="ewp-design-input-title"
    >
      <header className="ewp-design-input__header">
        <span>
          <h2 id="ewp-design-input-title">{title}</h2>
          <small>Prompt + readable documents · session only</small>
        </span>
        <strong>
          {documentCount} document{documentCount === 1 ? "" : "s"}
        </strong>
      </header>

      <div className="ewp-design-input__history">
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
          Draft revision {history.present.revision}
        </output>
      </div>

      <label className="ewp-design-input__prompt">
        <span>Prompt</span>
        <textarea
          aria-label={promptAriaLabel}
          value={promptDraft}
          rows={6}
          placeholder="Describe the goal, intended use, constraints, priorities, and what a good result should accomplish."
          onChange={(event) => setPromptDraft(event.currentTarget.value)}
        />
      </label>
      <div className="ewp-design-input__prompt-actions">
        <button
          type="button"
          disabled={!promptChanged}
          onClick={() =>
            dispatch({
              type: "apply",
              command: { type: "replace-prompt", prompt: promptDraft },
            })
          }
        >
          Apply prompt
        </button>
        <small>
          {promptDraft.length} characters
          {promptChanged ? " · changes not applied" : " · applied"}
        </small>
      </div>

      <label className="ewp-design-input__upload">
        <input
          type="file"
          accept={DESIGN_DOCUMENT_ACCEPT}
          multiple
          aria-label={documentAriaLabel}
          onChange={(event) => {
            const files = Array.from(event.currentTarget.files ?? []);
            if (files.length > 0) onFilesSelected(files);
            event.currentTarget.value = "";
          }}
        />
        <span>
          {documentCount === 0
            ? "Attach readable documents"
            : "Attach more documents"}
        </span>
        <small>Text, Markdown, PDF, Word, CSV, JSON, YAML, XML, or RTF</small>
      </label>
      <p className="ewp-design-input__boundary">
        Text formats show a bounded local preview. PDF and Word extraction,
        reusable workspace sources, and downstream AI use come later.
      </p>
      {uploadError ? (
        <p className="ewp-design-input__upload-error" role="alert">
          {uploadError}
        </p>
      ) : null}

      {history.present.documents.length ? (
        <ol
          className="ewp-design-input__documents"
          aria-label="Attached design documents"
        >
          {history.present.documents.map((document) => (
            <li key={document.documentId}>
              <div>
                <strong>{document.name}</strong>
                <small>
                  {document.mediaType} · {formatFileSize(document.sizeBytes)}
                </small>
                <small>
                  {document.textPreview === null
                    ? "Attached · parser required in a later checkpoint"
                    : "Readable text preview available"}
                </small>
              </div>
              <button
                type="button"
                aria-label={"Remove " + document.name}
                onClick={() =>
                  dispatch({
                    type: "apply",
                    command: {
                      type: "remove-document",
                      documentId: document.documentId,
                    },
                  })
                }
              >
                ×
              </button>
              {document.textPreview !== null ? (
                <blockquote aria-label={"Text preview for " + document.name}>
                  {document.textPreview || "Empty text document"}
                  {document.textPreviewTruncated ? "…" : ""}
                </blockquote>
              ) : null}
            </li>
          ))}
        </ol>
      ) : (
        <p className="ewp-design-input__empty">
          No documents attached. A prompt, documents, or both can feed later
          workflow steps.
        </p>
      )}
    </section>
  );
}
function diagnosticRunValue(value: unknown): string {
  if (typeof value === "string") return value;
  if (value === null || value === undefined) return "No value recorded";
  return JSON.stringify(value, null, 2);
}

function diagnosticRunDisplayValue(value: unknown): unknown {
  if (typeof value !== "string") return value;
  const trimmed = value.trim();
  if (!trimmed || (!trimmed.startsWith("{") && !trimmed.startsWith("["))) {
    return value;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function diagnosticRunFieldLabel(value: string): string {
  const words = value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .trim();
  return words ? words[0].toUpperCase() + words.slice(1) : value;
}

function diagnosticRunSummaryFields(
  value: unknown,
): readonly { label: string; value: string }[] {
  const displayed = diagnosticRunDisplayValue(value);
  if (!displayed || typeof displayed !== "object" || Array.isArray(displayed)) {
    return [];
  }
  return Object.entries(displayed)
    .filter(([, fieldValue]) =>
      ["string", "number", "boolean"].includes(typeof fieldValue),
    )
    .slice(0, 6)
    .map(([key, fieldValue]) => ({
      label: diagnosticRunFieldLabel(key),
      value: String(fieldValue),
    }));
}

function diagnosticRunDuration(step: HeadlessStepRecord): string {
  if (!step.finishedAt) return "In progress";
  const durationMs =
    new Date(step.finishedAt).getTime() - new Date(step.startedAt).getTime();
  if (!Number.isFinite(durationMs) || durationMs < 0) return "Unavailable";
  if (durationMs < 1000) return `${durationMs} ms`;
  return `${(durationMs / 1000).toFixed(durationMs < 10_000 ? 1 : 0)} s`;
}

function diagnosticRunTime(iso: string): string {
  const date = new Date(iso);
  if (!Number.isFinite(date.getTime())) return iso;
  return date.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  });
}

function diagnosticRunErrorSummary(error: string | null): string {
  if (!error) return "No error explanation was recorded.";
  const compact = error.replace(/\s+/g, " ").trim();
  const withoutEmptyList = compact.replace(/[\s,:;]{3,}$/, "").trim();
  if (!withoutEmptyList) return "The block returned an unreadable error.";
  return /[.!?]$/.test(withoutEmptyList)
    ? withoutEmptyList
    : `${withoutEmptyList}.`;
}

function DiagnosticRunOutputSummary({ value }: { value: unknown }) {
  const displayed = diagnosticRunDisplayValue(value);
  const fields = diagnosticRunSummaryFields(displayed);
  if (displayed === null || displayed === undefined) {
    return <p className="ewp-run-result__empty">No output was recorded.</p>;
  }
  if (fields.length) {
    return (
      <dl className="ewp-run-result__summary-fields">
        {fields.map((field) => (
          <div key={field.label}>
            <dt>{field.label}</dt>
            <dd>{field.value}</dd>
          </div>
        ))}
      </dl>
    );
  }
  if (typeof displayed === "string") {
    return <p className="ewp-run-result__text-preview">{displayed}</p>;
  }
  return (
    <p className="ewp-run-result__empty">
      Structured data was produced. Open Produced data below to inspect it.
    </p>
  );
}

function DiagnosticBlockRunResult({
  step,
  blockId,
  workflowIdentity,
  onOutputAction,
}: {
  step: HeadlessStepRecord | null;
  blockId: string;
  workflowIdentity: string;
  onOutputAction: (
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ) => Promise<string | void>;
}) {
  if (!step) {
    return (
      <section className="ewp-inspector__run-result" data-state="idle">
        <header className="ewp-run-result__status">
          <span className="ewp-run-result__status-icon" aria-hidden="true">
            ·
          </span>
          <span>
            <small>Run status</small>
            <h2>Not run yet</h2>
          </span>
        </header>
        <p>
          Run the workflow to see this block's result, duration, and supporting
          evidence here.
        </p>
      </section>
    );
  }

  const failed = step.status === "failed";
  const running = step.status === "running";
  const statusLabel = failed
    ? "Needs attention"
    : running
      ? "In progress"
      : "Completed";
  const outputs = workflowOutputsFrom(step.output);

  return (
    <section
      className="ewp-inspector__run-result"
      data-state={step.status}
      aria-label="Selected block run result"
    >
      <header className="ewp-run-result__status">
        <span className="ewp-run-result__status-icon" aria-hidden="true">
          {failed ? "!" : running ? "…" : "✓"}
        </span>
        <span>
          <small>Run status</small>
          <h2>{statusLabel}</h2>
        </span>
        <strong>{diagnosticRunDuration(step)}</strong>
      </header>

      <section className="ewp-run-result__summary">
        <h3>{failed ? "What stopped the workflow" : "Result summary"}</h3>
        {failed ? (
          <div className="ewp-run-result__problem" role="alert">
            <strong>This block did not produce a valid result.</strong>
            <p>{diagnosticRunErrorSummary(step.error)}</p>
          </div>
        ) : (
          <DiagnosticRunOutputSummary value={step.output} />
        )}
      </section>

      {outputs.length ? (
        <DiagnosticWorkflowOutputs
          outputs={outputs}
          compact
          onAction={onOutputAction}
        />
      ) : null}

      {failed ? (
        <section className="ewp-run-result__next-step">
          <small>Recommended next step</small>
          <p>
            Review this block's settings and upstream inputs. Correct the
            reported issue, then use <strong>Retry</strong> to run the workflow
            again.
          </p>
        </section>
      ) : null}

      <details className="ewp-run-result__details">
        <summary>Produced data</summary>
        <pre>{diagnosticRunValue(step.output)}</pre>
      </details>
      <details className="ewp-run-result__details">
        <summary>Technical details and evidence</summary>
        <dl>
          <div>
            <dt>Block</dt>
            <dd>{blockId}</dd>
          </div>
          <div>
            <dt>Workflow</dt>
            <dd>{workflowIdentity}</dd>
          </div>
          <div>
            <dt>Started</dt>
            <dd>
              <time dateTime={step.startedAt} title={step.startedAt}>
                {diagnosticRunTime(step.startedAt)}
              </time>
            </dd>
          </div>
          <div>
            <dt>Finished</dt>
            <dd>
              {step.finishedAt ? (
                <time dateTime={step.finishedAt} title={step.finishedAt}>
                  {diagnosticRunTime(step.finishedAt)}
                </time>
              ) : (
                "Still running"
              )}
            </dd>
          </div>
        </dl>
        {step.error ? (
          <>
            <h3>Exact error</h3>
            <pre>{step.error}</pre>
          </>
        ) : null}
        <h3>Evidence</h3>
        <pre>{diagnosticRunValue(step.evidence)}</pre>
      </details>
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
  designInputHistory,
  onDesignInputAction,
  onDesignInputFilesSelected,
  designInputUploadError,
  knowledgeLookupHistory,
  onKnowledgeLookupAction,
  diagnosticScenario,
  diagnosticState,
  onDiagnosticCorrection,
  diagnosticOutput,
  onDiagnosticOutput,
  readableDiagnosticDocumentCount,
  diagnosticModelGroups,
  diagnosticModelsLoading,
  diagnosticModelError,
  selectedDiagnosticModel,
  diagnosticThinkingLevel,
  onSelectDiagnosticModel,
  onSelectDiagnosticThinkingLevel,
  diagnosticMcpCatalog,
  diagnosticMcpCatalogLoading,
  diagnosticMcpCatalogError,
  diagnosticMcpSuggestion,
  selectedDiagnosticMcpServerId,
  selectedDiagnosticMcpToolId,
  onSelectDiagnosticMcpServer,
  onSelectDiagnosticMcpTool,
  diagnosticMcpBinding,
  diagnosticRunStep,
  diagnosticRuntimeReady,
  onDiagnosticOutputAction,
}: {
  workflow: WorkflowPreview;
  block: WorkflowPreviewBlock;
  outgoing: WorkflowPreviewBlock[];
  referenceImageHistory: ReferenceImageHistory;
  onReferenceImageAction: (action: ReferenceImageHistoryAction) => void;
  referenceImages: readonly WorkflowReferenceImageOption[];
  onReferenceImageFilesSelected: (files: readonly File[]) => void;
  referenceImageUploadError: string | null;
  designInputHistory: DesignInputHistory;
  onDesignInputAction: (action: DesignInputHistoryAction) => void;
  onDesignInputFilesSelected: (files: readonly File[]) => void;
  designInputUploadError: string | null;
  knowledgeLookupHistory: KnowledgeLookupHistory;
  onKnowledgeLookupAction: (action: KnowledgeLookupHistoryAction) => void;
  diagnosticScenario?: DiagnosticScenario;
  diagnosticState: DiagnosticDemoState;
  onDiagnosticCorrection: (correctionId: string) => void;
  diagnosticOutput: PromptRequestOutputKind;
  onDiagnosticOutput: (output: PromptRequestOutputKind) => void;
  readableDiagnosticDocumentCount: number;
  diagnosticModelGroups: readonly DiagnosticLlmModelGroup[];
  diagnosticModelsLoading: boolean;
  diagnosticModelError: string | null;
  selectedDiagnosticModel: DiagnosticLlmModelOption | null;
  diagnosticThinkingLevel: DiagnosticThinkingLevel;
  onSelectDiagnosticModel: (model: DiagnosticLlmModelOption) => void;
  onSelectDiagnosticThinkingLevel: (level: DiagnosticThinkingLevel) => void;
  diagnosticMcpCatalog: DiagnosticMcpCatalog | null;
  diagnosticMcpCatalogLoading: boolean;
  diagnosticMcpCatalogError: string | null;
  diagnosticMcpSuggestion: ReturnType<typeof suggestDiagnosticMcpBinding>;
  selectedDiagnosticMcpServerId: string | null;
  selectedDiagnosticMcpToolId: string | null;
  onSelectDiagnosticMcpServer: (serverId: string | null) => void;
  onSelectDiagnosticMcpTool: (toolId: string | null) => void;
  diagnosticMcpBinding: DiagnosticMcpBindingSummary | null;
  diagnosticRunStep: HeadlessStepRecord | null;
  diagnosticRuntimeReady: boolean;
  onDiagnosticOutputAction: (
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ) => Promise<string | void>;
}) {
  const [activeTab, setActiveTab] = useState<
    "details" | "evidence" | "diagnosis"
  >("details");
  const detailsTabId = "ewp-inspector-details-tab";
  const evidenceTabId = "ewp-inspector-evidence-tab";
  const diagnosisTabId = "ewp-inspector-diagnosis-tab";
  const isPromptRequestBlock =
    diagnosticScenario?.request.blockId === block.blockId;
  const isDiagnosticAiBlock =
    diagnosticScenario?.executorBlockId === block.blockId;
  const isDiagnosticMcpBlock = diagnosticScenario?.mcpBlockId === block.blockId;
  const promptRequestValue = {
    prompt: designInputHistory.present.prompt,
    imageCount: referenceImageHistory.present.imageIds.length,
    documentCount: designInputHistory.present.documents.length,
  };

  useEffect(() => {
    if (diagnosticScenario && diagnosticState.status === "blocked") {
      setActiveTab(
        diagnosticState.blockedAtBlockId ===
          diagnosticScenario.request.blockId ||
          diagnosticState.blockedAtBlockId === diagnosticScenario.mcpBlockId
          ? "details"
          : "diagnosis",
      );
    } else if (diagnosticScenario && diagnosticState.status === "failed") {
      setActiveTab("diagnosis");
    }
  }, [
    diagnosticScenario,
    diagnosticState.blockedAtBlockId,
    diagnosticState.runs.length,
    diagnosticState.status,
  ]);
  useEffect(() => {
    if (diagnosticScenario && diagnosticRunStep) setActiveTab("evidence");
  }, [block.blockId, diagnosticRunStep, diagnosticScenario]);

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
        data-has-diagnosis={diagnosticScenario ? "true" : undefined}
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
          {diagnosticScenario ? "Run result" : "Evidence"}
        </button>
        {diagnosticScenario ? (
          <button
            id={diagnosisTabId}
            type="button"
            role="tab"
            aria-selected={activeTab === "diagnosis"}
            aria-controls="ewp-inspector-diagnosis-panel"
            tabIndex={activeTab === "diagnosis" ? 0 : -1}
            onClick={() => setActiveTab("diagnosis")}
          >
            Diagnosis
          </button>
        ) : null}
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
          {isPromptRequestBlock && diagnosticScenario ? (
            <>
              <PromptRequestRequirements
                definition={diagnosticScenario.request}
                value={promptRequestValue}
                readableDocumentCount={readableDiagnosticDocumentCount}
                output={diagnosticOutput}
                acceptedOutputs={DIAGNOSTIC_AI_ACCEPTED_OUTPUTS}
                onSelectOutput={onDiagnosticOutput}
              />
              <DesignInputEditor
                history={designInputHistory}
                dispatch={onDesignInputAction}
                onFilesSelected={onDesignInputFilesSelected}
                uploadError={designInputUploadError}
                title="Prompt and readable files"
                promptAriaLabel="Request prompt"
                documentAriaLabel="Attach request documents"
              />
              <ReferenceImageEditor
                history={referenceImageHistory}
                dispatch={onReferenceImageAction}
                images={referenceImages}
                onFilesSelected={onReferenceImageFilesSelected}
                uploadError={referenceImageUploadError}
                title="Images"
              />
            </>
          ) : null}
          {isDiagnosticAiBlock ? (
            <DiagnosticLlmPanel
              groups={diagnosticModelGroups}
              loading={diagnosticModelsLoading}
              loadError={diagnosticModelError}
              selectedModel={selectedDiagnosticModel}
              thinkingLevel={diagnosticThinkingLevel}
              running={
                diagnosticRunStep
                  ? diagnosticRunStep.status === "running"
                  : diagnosticState.status === "running"
              }
              resultText={
                diagnosticState.llmResult?.text ??
                (diagnosticRunStep?.output
                  ? diagnosticRunValue(diagnosticRunStep.output)
                  : null)
              }
              executionError={diagnosticRunStep?.error ?? null}
              onSelectModel={onSelectDiagnosticModel}
              onSelectThinkingLevel={onSelectDiagnosticThinkingLevel}
            />
          ) : null}
          {isDiagnosticMcpBlock ? (
            <DiagnosticMcpBindingPanel
              catalog={diagnosticMcpCatalog}
              loading={diagnosticMcpCatalogLoading}
              loadError={diagnosticMcpCatalogError}
              selectedServerId={selectedDiagnosticMcpServerId}
              selectedToolId={selectedDiagnosticMcpToolId}
              suggestion={diagnosticMcpSuggestion}
              configuredDefault={diagnosticScenario?.mcpBindingDefault}
              runtimeReady={diagnosticRuntimeReady}
              onSelectServer={onSelectDiagnosticMcpServer}
              onSelectTool={onSelectDiagnosticMcpTool}
            />
          ) : null}
          {block.blockId === "reference-images" ? (
            <ReferenceImageEditor
              history={referenceImageHistory}
              dispatch={onReferenceImageAction}
              images={referenceImages}
              onFilesSelected={onReferenceImageFilesSelected}
              uploadError={referenceImageUploadError}
            />
          ) : null}
          {block.blockId === "design-intent" ? (
            <DesignInputEditor
              history={designInputHistory}
              dispatch={onDesignInputAction}
              onFilesSelected={onDesignInputFilesSelected}
              uploadError={designInputUploadError}
            />
          ) : null}
          {block.blockId === "knowledge-lookup" ? (
            <KnowledgeLookupEditor
              history={knowledgeLookupHistory}
              dispatch={onKnowledgeLookupAction}
              sources={knowledgeLookupSources}
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
          {!isPromptRequestBlock &&
          !isDiagnosticAiBlock &&
          block.blockId !== "reference-images" &&
          block.blockId !== "design-intent" &&
          block.blockId !== "knowledge-lookup" ? (
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
      ) : activeTab === "evidence" ? (
        <div
          id="ewp-inspector-evidence-panel"
          className="ewp-inspector__body"
          role="tabpanel"
          aria-labelledby={evidenceTabId}
        >
          {diagnosticScenario ? (
            <DiagnosticBlockRunResult
              step={diagnosticRunStep}
              blockId={block.blockId}
              workflowIdentity={`${workflow.workflowId} · r${workflow.revision}`}
              onOutputAction={onDiagnosticOutputAction}
            />
          ) : (
            <p className="ewp-inspector__summary">
              Deterministic preview evidence for this Wright-owned workflow
              projection. No engineering tool has been executed.
            </p>
          )}
          {!diagnosticScenario ? (
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
                    : block.blockId === "design-intent"
                      ? "Local CP3B draft · session only"
                      : block.blockId === "knowledge-lookup"
                        ? "Local CP3C draft · session only"
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
              {block.blockId === "design-intent" ? (
                <div>
                  <dt>Design input draft</dt>
                  <dd>
                    {designInputHistory.present.prompt.length} prompt characters
                    · {designInputHistory.present.documents.length} document
                    {designInputHistory.present.documents.length === 1
                      ? ""
                      : "s"}{" "}
                    attached · not persisted
                  </dd>
                </div>
              ) : null}
              {block.blockId === "knowledge-lookup" ? (
                <div>
                  <dt>Knowledge lookup draft</dt>
                  <dd>
                    {knowledgeLookupHistory.present.query.length} prompt
                    characters ·{" "}
                    {knowledgeLookupHistory.present.sourceIds.length} source
                    {knowledgeLookupHistory.present.sourceIds.length === 1
                      ? ""
                      : "s"}{" "}
                    selected · not persisted
                  </dd>
                </div>
              ) : null}
              <div>
                <dt>Execution status</dt>
                <dd>{diagnosticRunStep?.status ?? "Not executed"}</dd>
              </div>
            </dl>
          ) : null}
          {!diagnosticScenario ? (
            <section className="ewp-inspector__evidence-policy">
              <h2>Execution boundary</h2>
              <p>
                {block.role === "mcp-action"
                  ? "An exact workspace catalog tool must be bound before the generic MCP gateway can run this action. Capability categories never dispatch runtime services."
                  : block.blockId === "knowledge-lookup"
                    ? "This draft has not searched any source. Future retrieval must honor workspace permissions and return citations and evidence through a governed generic boundary."
                    : "This block does not invoke a tool. Any future execution evidence must come through the governed workflow runtime."}
              </p>
            </section>
          ) : null}
          {!diagnosticScenario ? (
            <section className="ewp-inspector__output">
              <h2>Evidence status</h2>
              <p>
                Run records and produced artifacts arrive in later governed MCP
                and integration checkpoints.
              </p>
            </section>
          ) : null}
        </div>
      ) : diagnosticScenario ? (
        <div
          id="ewp-inspector-diagnosis-panel"
          className="ewp-inspector__body"
          role="tabpanel"
          aria-labelledby={diagnosisTabId}
        >
          <DiagnosticPanel
            scenario={diagnosticScenario}
            state={diagnosticState}
            mcpBinding={diagnosticMcpBinding}
            onApplyCorrection={onDiagnosticCorrection}
          />
        </div>
      ) : null}
      <MiniMap workflow={workflow} />
    </aside>
  );
}

function MiniMap({ workflow }: { workflow: WorkflowPreview }) {
  return (
    <div className="ewp-minimap" role="img" aria-label="Workflow overview">
      {workflow.phases.map((phase) => (
        <div key={phase.phaseId} data-phase={phase.tone}>
          {workflow.blocks
            .filter(({ phaseId }) => phaseId === phase.phaseId)
            .map(({ blockId }) => (
              <i key={blockId} />
            ))}
        </div>
      ))}
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
  diagnosticScenario?: DiagnosticScenario;
  diagnosticLlmAdapter?: DiagnosticLlmAdapter;
  diagnosticMcpCatalogAdapter?: DiagnosticMcpCatalogAdapter;
  diagnosticMcpRuntimeAdapter?: DiagnosticMcpRuntimeAdapter;
  renderCanvas?: (props: EngineeringWorkflowCanvasRenderProps) => ReactNode;
  workflow?: WorkflowPreview;
  viewState?: EngineeringWorkflowPrototypeViewState;
}

export function EngineeringWorkflowVisualSlice({
  badge = "Visual slice",
  diagnosticLlmAdapter = deterministicDiagnosticLlmAdapter,
  diagnosticMcpCatalogAdapter = deterministicDiagnosticMcpCatalogAdapter,
  diagnosticMcpRuntimeAdapter,
  diagnosticScenario,
  renderCanvas,
  workflow = drillBitHolderWorkflow,
  viewState = "ready",
}: EngineeringWorkflowVisualSliceProps = {}) {
  const [workflowRepresentation, setWorkflowRepresentation] = useState<
    "diagram" | "code"
  >("diagram");
  const [appliedWorkflow, setAppliedWorkflow] =
    useState<WorkflowPreview>(workflow);
  const [workflowCodeSource, setWorkflowCodeSource] = useState(() =>
    serializeWorkflowCodeDocument(workflow),
  );
  const [appliedWorkflowCodeSource, setAppliedWorkflowCodeSource] = useState(
    () => serializeWorkflowCodeDocument(workflow),
  );
  const workflowCodeResult: WorkflowCodeParseResult = parseWorkflowCodeDocument(
    workflowCodeSource,
    workflow,
    diagnosticScenario?.blockIds ?? [],
  );
  const workflowForDisplay = diagnosticScenario ? appliedWorkflow : workflow;
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
  const [designInputHistory, dispatchDesignInputAction] = useReducer(
    reduceDesignInputHistory,
    createDesignInputHistory(diagnosticScenario?.request.initialPrompt ?? ""),
  );
  const [designInputUploadError, setDesignInputUploadError] = useState<
    string | null
  >(null);
  const [knowledgeLookupHistory, dispatchKnowledgeLookupAction] = useReducer(
    reduceKnowledgeLookupDraft,
    createKnowledgeLookupHistory(),
  );
  const [diagnosticState, dispatchDiagnosticAction] = useReducer(
    (state: DiagnosticDemoState, action: DiagnosticDemoAction) =>
      diagnosticScenario
        ? reduceDiagnosticDemoState(state, action, diagnosticScenario)
        : state,
    createDiagnosticDemoState(),
  );
  const [diagnosticOutput, setDiagnosticOutput] =
    useState<PromptRequestOutputKind>("request");
  const [diagnosticModelGroups, setDiagnosticModelGroups] = useState<
    readonly DiagnosticLlmModelGroup[]
  >([]);
  const [diagnosticModelsLoading, setDiagnosticModelsLoading] = useState(false);
  const [diagnosticModelError, setDiagnosticModelError] = useState<
    string | null
  >(null);
  const [selectedDiagnosticModel, setSelectedDiagnosticModel] =
    useState<DiagnosticLlmModelOption | null>(null);
  const [diagnosticThinkingLevel, setDiagnosticThinkingLevel] =
    useState<DiagnosticThinkingLevel>("default");
  const [diagnosticLlmProgress, setDiagnosticLlmProgress] =
    useState<DiagnosticLlmProgress | null>(null);
  const [diagnosticRunStartedAt, setDiagnosticRunStartedAt] = useState<
    number | null
  >(null);
  const [diagnosticObservedAt, setDiagnosticObservedAt] = useState(Date.now());
  const [diagnosticStepRecords, setDiagnosticStepRecords] = useState<
    readonly HeadlessStepRecord[]
  >([]);
  const [diagnosticCompletedRun, setDiagnosticCompletedRun] =
    useState<DiagnosticFourBlockRun | null>(null);
  const [diagnosticOutputViewer, setDiagnosticOutputViewer] = useState<{
    output: WorkflowOutputReference;
    close: () => void;
  } | null>(null);
  const [diagnosticMcpCatalog, setDiagnosticMcpCatalog] =
    useState<DiagnosticMcpCatalog | null>(null);
  const [diagnosticMcpCatalogLoading, setDiagnosticMcpCatalogLoading] =
    useState(false);
  const [diagnosticMcpCatalogError, setDiagnosticMcpCatalogError] = useState<
    string | null
  >(null);
  const [selectedDiagnosticMcpServerId, setSelectedDiagnosticMcpServerId] =
    useState<string | null>(null);
  const [selectedDiagnosticMcpToolId, setSelectedDiagnosticMcpToolId] =
    useState<string | null>(null);
  const nextUploadedImageId = useRef(1);
  const nextUploadedDocumentId = useRef(1);
  const diagnosticMcpSelectionTouched = useRef(false);
  useEffect(() => {
    const source = serializeWorkflowCodeDocument(workflow);
    setAppliedWorkflow(workflow);
    setWorkflowCodeSource(source);
    setAppliedWorkflowCodeSource(source);
    setWorkflowRepresentation("diagram");
    setSelectedBlockId(workflow.blocks[0].blockId);
    setDiagnosticLlmProgress(null);
    setDiagnosticRunStartedAt(null);
    setDiagnosticStepRecords([]);
    setDiagnosticCompletedRun(null);
  }, [workflow]);
  useEffect(() => {
    if (diagnosticState.status !== "running") return undefined;
    const timer = window.setInterval(() => {
      setDiagnosticObservedAt(Date.now());
    }, 500);
    return () => window.clearInterval(timer);
  }, [diagnosticState.status]);
  const referenceImageHistory = referenceImageDraft.history;
  const diagnosticRequest = {
    prompt: designInputHistory.present.prompt,
    imageCount: referenceImageHistory.present.imageIds.length,
    documentCount: designInputHistory.present.documents.length,
  };
  const diagnosticInputIssues = diagnosticScenario
    ? diagnosticRequestIssues(
        diagnosticRequest,
        diagnosticScenario.request.requirements,
      )
    : [];
  const diagnosticRequestReady = diagnosticInputIssues.length === 0;
  const readableDiagnosticDocumentCount =
    designInputHistory.present.documents.filter(
      ({ textPreview }) => textPreview !== null,
    ).length;
  const diagnosticRouteIssues = promptRequestRouteIssues(
    {
      promptPresent: diagnosticRequest.prompt.trim().length > 0,
      imageCount: diagnosticRequest.imageCount,
      documentCount: diagnosticRequest.documentCount,
      readableDocumentCount: readableDiagnosticDocumentCount,
    },
    diagnosticOutput,
    DIAGNOSTIC_AI_ACCEPTED_OUTPUTS,
  );
  const diagnosticRouteReady = promptRequestRouteCanRun(diagnosticRouteIssues);
  const diagnosticMcpBlock = diagnosticScenario
    ? workflowForDisplay.blocks.find(
        ({ blockId }) => blockId === diagnosticScenario.mcpBlockId,
      )
    : undefined;
  const diagnosticMcpContext = [
    diagnosticMcpBlock?.title ?? "",
    diagnosticMcpBlock?.purpose ?? "",
    diagnosticRequest.prompt,
    diagnosticState.llmResult?.text ?? "",
  ].join("\n");
  const diagnosticMcpDefaultServerName =
    diagnosticScenario?.mcpBindingDefault?.serverName ?? null;
  const diagnosticMcpDefaultToolName =
    diagnosticScenario?.mcpBindingDefault?.toolName;
  const diagnosticMcpDefaultReason =
    diagnosticScenario?.mcpBindingDefault?.reason ?? "";
  const diagnosticMcpSuggestion = diagnosticMcpCatalog
    ? diagnosticMcpDefaultServerName
      ? resolveExplicitDiagnosticMcpBinding(diagnosticMcpCatalog, {
          serverName: diagnosticMcpDefaultServerName,
          toolName: diagnosticMcpDefaultToolName,
          reason: diagnosticMcpDefaultReason,
        })
      : suggestDiagnosticMcpBinding(diagnosticMcpCatalog, diagnosticMcpContext)
    : null;
  const suggestedDiagnosticMcpServerId = diagnosticMcpSuggestion?.serverId;
  const suggestedDiagnosticMcpToolId = diagnosticMcpSuggestion?.toolId;
  const selectedDiagnosticMcpServer: DiagnosticMcpServerOption | null =
    diagnosticMcpCatalog?.servers.find(
      ({ serverId }) => serverId === selectedDiagnosticMcpServerId,
    ) ?? null;
  const selectedDiagnosticMcpTool: DiagnosticMcpToolOption | null =
    diagnosticMcpCatalog?.tools.find(
      ({ toolId, serverId }) =>
        toolId === selectedDiagnosticMcpToolId &&
        serverId === selectedDiagnosticMcpServerId,
    ) ?? null;
  const diagnosticExactMcpBinding =
    selectedDiagnosticMcpServer && selectedDiagnosticMcpTool
      ? {
          server: selectedDiagnosticMcpServer,
          tool: selectedDiagnosticMcpTool,
        }
      : null;
  const diagnosticRuntimeReady = Boolean(
    diagnosticMcpRuntimeAdapter &&
    diagnosticExactMcpBinding &&
    selectedDiagnosticMcpServer?.active &&
    selectedDiagnosticMcpTool?.enabled &&
    diagnosticMcpRuntimeAdapter.supports(diagnosticExactMcpBinding),
  );
  let diagnosticMcpBinding: DiagnosticMcpBindingSummary | null = null;
  if (selectedDiagnosticMcpServer && selectedDiagnosticMcpTool) {
    const requiredInputs = diagnosticRequiredToolInputs(
      selectedDiagnosticMcpTool,
    );
    diagnosticMcpBinding = {
      serverName: selectedDiagnosticMcpServer.name,
      toolName: selectedDiagnosticMcpTool.name,
      toolId: selectedDiagnosticMcpTool.toolId,
      executable:
        selectedDiagnosticMcpServer.active && selectedDiagnosticMcpTool.enabled,
      requiredInputs,
      // A configured runtime adapter lets Step 2 generate and validate the
      // exact arguments. Without that adapter, required inputs stay honest
      // and unresolved instead of making the tool look runnable.
      unmappedInputs: diagnosticRuntimeReady ? [] : requiredInputs,
    };
  }
  const showDiagnosticMcpQuickBinding =
    diagnosticScenario !== undefined &&
    workflowRepresentation === "diagram" &&
    (selectedBlockId === diagnosticScenario.mcpBlockId ||
      (diagnosticState.status === "blocked" &&
        diagnosticState.blockedAtBlockId === diagnosticScenario.mcpBlockId));

  useEffect(() => {
    if (!diagnosticScenario) return undefined;
    let cancelled = false;
    setDiagnosticModelsLoading(true);
    setDiagnosticModelError(null);
    void diagnosticLlmAdapter
      .listModels()
      .then((groups) => {
        if (cancelled) return;
        setDiagnosticModelGroups(groups);
        const options = groups.flatMap((group) => group.options);
        setSelectedDiagnosticModel(
          options.find(({ isCurrent }) => isCurrent) ?? options[0] ?? null,
        );
        if (options.length === 0) {
          setDiagnosticModelError(
            "No configured AI models are available. Configure a provider in Wright, then retry.",
          );
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setDiagnosticModelGroups([]);
        setSelectedDiagnosticModel(null);
        setDiagnosticModelError(
          error instanceof Error
            ? error.message
            : "Wright could not load configured AI models.",
        );
      })
      .finally(() => {
        if (!cancelled) setDiagnosticModelsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [diagnosticLlmAdapter, diagnosticScenario]);

  useEffect(() => {
    if (!diagnosticScenario) return undefined;
    let cancelled = false;
    setDiagnosticMcpCatalogLoading(true);
    setDiagnosticMcpCatalogError(null);
    void diagnosticMcpCatalogAdapter
      .listCatalog()
      .then((catalog) => {
        if (cancelled) return;
        setDiagnosticMcpCatalog(catalog);
        if (catalog.servers.length === 0) {
          setDiagnosticMcpCatalogError(
            "Wright has no installed MCP servers to bind.",
          );
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setDiagnosticMcpCatalog(null);
        setDiagnosticMcpCatalogError(
          error instanceof Error
            ? error.message
            : "Wright could not load the installed MCP catalog.",
        );
      })
      .finally(() => {
        if (!cancelled) setDiagnosticMcpCatalogLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [diagnosticMcpCatalogAdapter, diagnosticScenario]);

  useEffect(() => {
    if (
      !suggestedDiagnosticMcpServerId ||
      diagnosticMcpSelectionTouched.current
    ) {
      return;
    }
    setSelectedDiagnosticMcpServerId(suggestedDiagnosticMcpServerId ?? null);
    setSelectedDiagnosticMcpToolId(suggestedDiagnosticMcpToolId ?? null);
  }, [suggestedDiagnosticMcpServerId, suggestedDiagnosticMcpToolId]);

  const closeDiagnosticOutputViewer = () => {
    diagnosticOutputViewer?.close();
    setDiagnosticOutputViewer(null);
  };

  const releaseDiagnosticRunOutputs = (run: DiagnosticFourBlockRun | null) => {
    const outputs = workflowOutputsFrom(run?.outcome);
    if (outputs.length && diagnosticMcpRuntimeAdapter?.releaseOutputs) {
      void diagnosticMcpRuntimeAdapter.releaseOutputs(outputs);
    }
  };

  const handleDiagnosticOutputAction = async (
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ): Promise<string> => {
    if (!action.available) {
      throw new Error(
        action.unavailableReason ?? "This output action is unavailable.",
      );
    }
    if (!diagnosticMcpRuntimeAdapter?.performOutputAction) {
      throw new Error(
        "The runtime that produced this output does not provide an opener.",
      );
    }
    const result: DiagnosticOutputActionResult =
      await diagnosticMcpRuntimeAdapter.performOutputAction(output, action);
    if (result.kind === "embedded") {
      diagnosticOutputViewer?.close();
      setDiagnosticOutputViewer({ output, close: result.close });
      return `Viewing ${output.title}.`;
    }
    return result.message;
  };

  const handleDiagnosticRun = async () => {
    if (!diagnosticScenario) return;
    if (!diagnosticRequestReady) {
      setDiagnosticLlmProgress(null);
      setDiagnosticRunStartedAt(null);
      dispatchDiagnosticAction({ type: "run", request: diagnosticRequest });
      setSelectedBlockId(diagnosticScenario.request.blockId);
      return;
    }
    if (!diagnosticRouteReady) {
      setSelectedBlockId(diagnosticScenario.request.blockId);
      return;
    }
    if (!selectedDiagnosticModel) {
      setSelectedBlockId(diagnosticScenario.executorBlockId);
      return;
    }
    if (
      diagnosticMcpRuntimeAdapter &&
      (!diagnosticExactMcpBinding || !diagnosticRuntimeReady)
    ) {
      setSelectedBlockId(diagnosticScenario.mcpBlockId);
      return;
    }

    const startedAt = Date.now();
    setDiagnosticRunStartedAt(startedAt);
    setDiagnosticObservedAt(startedAt);
    setDiagnosticLlmProgress({
      stage: "preparing",
      message: "Preparing the selected AI task.",
      partialText: "",
      observedAt: startedAt,
    });
    dispatchDiagnosticAction({ type: "run", request: diagnosticRequest });
    setSelectedBlockId(diagnosticScenario.executorBlockId);
    const llmRequest = {
      prompt: diagnosticRequest.prompt,
      output: diagnosticOutput,
      images: selectedReferenceImages.map((image) => ({
        name: image.title,
        dataUrl: image.thumbnailUrl,
      })),
      documents: designInputHistory.present.documents.map((document) => ({
        name: document.name,
        mediaType: document.mediaType,
        text: document.textPreview,
      })),
    };

    if (
      diagnosticMcpRuntimeAdapter &&
      diagnosticExactMcpBinding &&
      diagnosticRuntimeReady
    ) {
      setDiagnosticStepRecords([]);
      setDiagnosticCompletedRun(null);
      try {
        const run = await executeDiagnosticFourBlockChain({
          request: llmRequest,
          settings: {
            model: selectedDiagnosticModel,
            thinkingLevel: diagnosticThinkingLevel,
          },
          binding: diagnosticExactMcpBinding,
          llmAdapter: diagnosticLlmAdapter,
          mcpRuntimeAdapter: diagnosticMcpRuntimeAdapter,
          onStep(step) {
            setDiagnosticObservedAt(Date.now());
            setDiagnosticStepRecords((current) => {
              const existingIndex = current.findIndex(
                ({ block }) => block === step.block,
              );
              if (existingIndex < 0) return [...current, step];
              return current.map((candidate, index) =>
                index === existingIndex ? step : candidate,
              );
            });
            setSelectedBlockId(
              diagnosticBlockIdForStep(diagnosticScenario, step.block),
            );
          },
          llmObserver: {
            onProgress(progress) {
              setDiagnosticLlmProgress(progress);
              setDiagnosticObservedAt(progress.observedAt);
            },
          },
        });
        setDiagnosticCompletedRun(run);
        setDiagnosticStepRecords(run.steps);
        setDiagnosticObservedAt(Date.now());
        dispatchDiagnosticAction({
          type: "execution-succeeded",
          summary:
            run.outcome?.meaning ?? "All four workflow blocks completed.",
        });
        setSelectedBlockId(diagnosticScenario.evaluationBlockId);
      } catch (error) {
        const failedRun = (error as { run?: DiagnosticFourBlockRun }).run;
        if (failedRun) {
          setDiagnosticCompletedRun(failedRun);
          setDiagnosticStepRecords(failedRun.steps);
        }
        const failedStep = failedRun?.steps.find(
          ({ status }) => status === "failed",
        );
        const failedBlockId = failedStep
          ? diagnosticBlockIdForStep(diagnosticScenario, failedStep.block)
          : diagnosticScenario.executorBlockId;
        const message =
          error instanceof Error
            ? error.message
            : "The four-block workflow stopped unexpectedly.";
        setDiagnosticObservedAt(Date.now());
        dispatchDiagnosticAction({
          type: "execution-failed",
          blockId: failedBlockId,
          message,
        });
        setSelectedBlockId(failedBlockId);
      }
      return;
    }

    try {
      const result = await diagnosticLlmAdapter.execute(
        llmRequest,
        {
          model: selectedDiagnosticModel,
          thinkingLevel: diagnosticThinkingLevel,
        },
        {
          onProgress(progress) {
            setDiagnosticLlmProgress(progress);
            setDiagnosticObservedAt(progress.observedAt);
          },
        },
      );
      setDiagnosticObservedAt(Date.now());
      dispatchDiagnosticAction({ type: "llm-succeeded", result });
      setSelectedBlockId(diagnosticScenario.mcpBlockId);
    } catch (error) {
      setDiagnosticObservedAt(Date.now());
      dispatchDiagnosticAction({
        type: "llm-failed",
        message:
          error instanceof Error
            ? error.message
            : "The selected AI task failed.",
      });
      setSelectedBlockId(diagnosticScenario.executorBlockId);
    }
  };

  const handleDiagnosticCorrection = (correctionId: string) => {
    if (!diagnosticScenario) return;
    const correction = diagnosticScenario.corrections.find(
      (candidate) => candidate.correctionId === correctionId,
    );
    if (!correction) return;
    dispatchDiagnosticAction({ type: "apply-correction", correctionId });
    setSelectedBlockId(correction.targetBlockId);
  };

  const handleDiagnosticMcpServerSelection = (serverId: string | null) => {
    diagnosticMcpSelectionTouched.current = true;
    setSelectedDiagnosticMcpServerId(serverId);
    setSelectedDiagnosticMcpToolId(null);
  };

  const handleDiagnosticMcpToolSelection = (toolId: string | null) => {
    diagnosticMcpSelectionTouched.current = true;
    setSelectedDiagnosticMcpToolId(toolId);
  };

  const handleDiagnosticReset = () => {
    if (!diagnosticScenario) return;
    closeDiagnosticOutputViewer();
    releaseDiagnosticRunOutputs(diagnosticCompletedRun);
    dispatchDiagnosticAction({ type: "reset" });
    setDiagnosticLlmProgress(null);
    setDiagnosticRunStartedAt(null);
    setDiagnosticStepRecords([]);
    setDiagnosticCompletedRun(null);
    diagnosticMcpSelectionTouched.current = false;
    setSelectedDiagnosticMcpServerId(diagnosticMcpSuggestion?.serverId ?? null);
    setSelectedDiagnosticMcpToolId(diagnosticMcpSuggestion?.toolId ?? null);
    setSelectedBlockId(diagnosticScenario.blockIds[0]);
  };

  const handleWorkflowCodeApply = () => {
    if (!workflowCodeResult.ok) return;
    closeDiagnosticOutputViewer();
    releaseDiagnosticRunOutputs(diagnosticCompletedRun);
    setAppliedWorkflow(workflowCodeResult.workflow);
    setAppliedWorkflowCodeSource(workflowCodeSource);
    dispatchDiagnosticAction({ type: "reset" });
    setDiagnosticLlmProgress(null);
    setDiagnosticRunStartedAt(null);
    setDiagnosticStepRecords([]);
    setDiagnosticCompletedRun(null);
    setSelectedBlockId(workflowCodeResult.workflow.blocks[0].blockId);
  };

  const handleWorkflowCodeFormat = () => {
    if (!workflowCodeResult.ok) return;
    const wasApplied = workflowCodeSource === appliedWorkflowCodeSource;
    const formatted = JSON.stringify(workflowCodeResult.document, null, 2);
    setWorkflowCodeSource(formatted);
    if (wasApplied) setAppliedWorkflowCodeSource(formatted);
  };

  const handleWorkflowCodeReset = () => {
    closeDiagnosticOutputViewer();
    releaseDiagnosticRunOutputs(diagnosticCompletedRun);
    const source = serializeWorkflowCodeDocument(workflow);
    setAppliedWorkflow(workflow);
    setWorkflowCodeSource(source);
    setAppliedWorkflowCodeSource(source);
    dispatchDiagnosticAction({ type: "reset" });
    setDiagnosticLlmProgress(null);
    setDiagnosticRunStartedAt(null);
    setDiagnosticStepRecords([]);
    setDiagnosticCompletedRun(null);
    setSelectedBlockId(
      diagnosticScenario?.blockIds[0] ?? workflow.blocks[0].blockId,
    );
  };

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

  const handleDesignInputFilesSelected = async (
    files: readonly File[],
  ): Promise<void> => {
    const readableFiles = files.filter(isReadableDesignDocument);
    if (readableFiles.length !== files.length) {
      setDesignInputUploadError(
        "Attach text, Markdown, PDF, Word, CSV, JSON, YAML, XML, or RTF documents.",
      );
    } else {
      setDesignInputUploadError(null);
    }
    if (readableFiles.length === 0) return;

    try {
      const documents = await Promise.all(
        readableFiles.map((file) =>
          readUploadedDesignDocument(
            file,
            "design-document-" + nextUploadedDocumentId.current++,
          ),
        ),
      );
      dispatchDesignInputAction({
        type: "apply",
        command: { type: "add-documents", documents },
      });
    } catch (error) {
      setDesignInputUploadError(
        error instanceof Error
          ? error.message
          : "Wright could not read the selected design documents.",
      );
    }
  };

  const availableReferenceImages = referenceImageDraft.images;
  const selectedReferenceImageIds = referenceImageHistory.present.imageIds;
  const availableReferenceImagesById = new Map(
    availableReferenceImages.map((image) => [image.imageId, image]),
  );
  const selectedReferenceImages = selectedReferenceImageIds
    .map((imageId) => availableReferenceImagesById.get(imageId))
    .filter(
      (image): image is WorkflowReferenceImageOption => image !== undefined,
    );
  const displayWorkflow: WorkflowPreview = (() => {
    const imageCount = selectedReferenceImages.length;
    const promptPresent = designInputHistory.present.prompt.trim().length > 0;
    const documentCount = designInputHistory.present.documents.length;
    const designInputCount = Number(promptPresent) + documentCount;
    const lookupQueryPresent =
      knowledgeLookupHistory.present.query.trim().length > 0;
    const lookupSourceCount = knowledgeLookupHistory.present.sourceIds.length;
    return {
      ...workflowForDisplay,
      connections: workflowForDisplay.connections.map((connection) =>
        diagnosticScenario &&
        connection.sourceBlockId === diagnosticScenario.request.blockId &&
        connection.targetBlockId === diagnosticScenario.executorBlockId
          ? {
              ...connection,
              sourcePortId: diagnosticOutput,
              label: promptRequestOutputLabels[diagnosticOutput],
            }
          : connection,
      ),
      blocks: workflowForDisplay.blocks.map((block) => {
        if (block.blockId === "reference-images") {
          return {
            ...block,
            purpose:
              imageCount === 0
                ? "Select image inputs in the inspector."
                : block.purpose,
            badge: `${imageCount} ${imageCount === 1 ? "IMAGE" : "IMAGES"}`,
            status:
              imageCount === 0
                ? "No images selected"
                : `${imageCount} selected · session only`,
            imagePreviews: selectedReferenceImages.map((imageOption) => ({
              imageId: imageOption.imageId,
              title: imageOption.title,
              alt: imageOption.alt,
              thumbnailUrl: imageOption.thumbnailUrl,
            })),
          };
        }

        if (block.blockId === "design-intent") {
          const badgeParts = [
            promptPresent ? "PROMPT" : null,
            documentCount > 0
              ? `${documentCount} ${documentCount === 1 ? "FILE" : "FILES"}`
              : null,
          ].filter((part): part is string => part !== null);
          return {
            ...block,
            purpose:
              designInputCount === 0
                ? "Add a prompt or readable documents in the inspector."
                : "Prompt and documents for later workflow steps.",
            badge: badgeParts.length > 0 ? badgeParts.join(" + ") : "EMPTY",
            status:
              designInputCount === 0
                ? "No design input"
                : "Draft · session only",
          };
        }

        if (block.blockId === "knowledge-lookup") {
          const lookupConfigured = lookupQueryPresent && lookupSourceCount > 0;
          const lookupBadgeParts = [
            lookupQueryPresent ? "QUERY" : null,
            lookupSourceCount > 0
              ? `${lookupSourceCount} ${lookupSourceCount === 1 ? "SOURCE" : "SOURCES"}`
              : null,
          ].filter((part): part is string => part !== null);
          return {
            ...block,
            purpose: lookupConfigured
              ? "Find relevant information within selected source scopes."
              : "Add a lookup prompt and choose where Wright may search.",
            badge:
              lookupBadgeParts.length > 0
                ? lookupBadgeParts.join(" + ")
                : "EMPTY",
            status: lookupConfigured
              ? "Draft · retrieval not run"
              : lookupQueryPresent
                ? "Choose sources"
                : lookupSourceCount > 0
                  ? "Add lookup prompt"
                  : "No lookup configured",
          };
        }

        if (diagnosticScenario) {
          const executionStep = diagnosticStepRecords.find(
            ({ block: step }) =>
              diagnosticBlockIdForStep(diagnosticScenario, step) ===
              block.blockId,
          );
          const overlay = executionStep
            ? {
                runState:
                  executionStep.status === "completed" &&
                  block.blockId === diagnosticScenario.evaluationBlockId &&
                  diagnosticState.status === "passed"
                    ? ("passed" as const)
                    : executionStep.status,
                status:
                  executionStep.status === "failed"
                    ? (executionStep.error ?? "Execution failed")
                    : executionStep.status === "running"
                      ? "Running"
                      : "Completed · result available",
              }
            : diagnosticBlockOverlay(
                diagnosticState,
                diagnosticScenario,
                block.blockId,
              );
          if (block.blockId === diagnosticScenario.request.blockId) {
            const requestBadgeParts = [
              promptPresent ? "PROMPT" : null,
              `${imageCount} ${imageCount === 1 ? "IMAGE" : "IMAGES"}`,
              documentCount > 0
                ? `${documentCount} ${documentCount === 1 ? "FILE" : "FILES"}`
                : null,
            ].filter((part): part is string => part !== null);
            const requestOverlay =
              diagnosticState.status === "ready"
                ? diagnosticRequestReady
                  ? { runState: "idle" as const, status: "Ready to run" }
                  : {
                      runState: "warning" as const,
                      status: `${diagnosticInputIssues.length} required input missing`,
                    }
                : diagnosticState.status === "blocked" &&
                    diagnosticState.blockedAtBlockId ===
                      diagnosticScenario.request.blockId &&
                    diagnosticRequestReady
                  ? {
                      runState: "revised" as const,
                      status: "Inputs ready · continue",
                    }
                  : overlay;
            return {
              ...block,
              ...requestOverlay,
              badge: requestBadgeParts.join(" + "),
              purpose: diagnosticRequestReady
                ? "Multimodal request is ready for downstream processing."
                : "Add the required runtime inputs in the inspector.",
              outputPorts: block.outputPorts?.map((port) => ({
                ...port,
                count:
                  port.portId === "images"
                    ? imageCount
                    : port.portId === "documents"
                      ? documentCount
                      : port.count,
              })),
              imagePreviews: selectedReferenceImages.map((imageOption) => ({
                imageId: imageOption.imageId,
                title: imageOption.title,
                alt: imageOption.alt,
                thumbnailUrl: imageOption.thumbnailUrl,
              })),
            };
          }
          if (block.blockId === diagnosticScenario.executorBlockId) {
            const llmResult = diagnosticState.llmResult;
            const generatedOutput = executionStep?.output ?? null;
            return {
              ...block,
              ...overlay,
              badge:
                diagnosticState.status === "running"
                  ? "RUNNING"
                  : llmResult
                    ? "TEXT READY"
                    : generatedOutput
                      ? "ARGUMENTS READY"
                      : selectedDiagnosticModel
                        ? "MODEL READY"
                        : "SELECT MODEL",
              purpose:
                llmResult || generatedOutput
                  ? "Produced reviewable, schema-validated output for the next connection."
                  : "Run the selected AI without activating workspace MCP tools.",
              inspector: {
                summary:
                  "Select a configured model and thinking level. Wright does not activate workspace MCP tools for this AI task.",
                fields: [
                  {
                    label: "Executor",
                    value: selectedDiagnosticModel
                      ? selectedDiagnosticModel.provider +
                        " · " +
                        selectedDiagnosticModel.model
                      : "No configured model selected",
                  },
                  {
                    label: "Output",
                    value:
                      llmResult?.text ??
                      (generatedOutput
                        ? diagnosticRunValue(generatedOutput)
                        : "None · task has not completed"),
                  },
                ],
              },
            };
          }
          if (block.blockId === diagnosticScenario.mcpBlockId) {
            const unmappedInputs = diagnosticMcpBinding?.unmappedInputs ?? [];
            return {
              ...block,
              ...overlay,
              ...(diagnosticMcpBinding && !executionStep
                ? {
                    runState: "warning" as const,
                    status: !diagnosticMcpBinding.executable
                      ? "Exact tool selected · unavailable"
                      : unmappedInputs.length > 0
                        ? `Map required input${unmappedInputs.length === 1 ? "" : "s"}: ${unmappedInputs.join(", ")}`
                        : "Exact tool selected · execution disabled",
                  }
                : {}),
              badge: executionStep
                ? executionStep.status === "completed"
                  ? "RESULT READY"
                  : executionStep.status === "running"
                    ? "RUNNING"
                    : "FAILED"
                : diagnosticMcpBinding
                  ? unmappedInputs.length > 0
                    ? "MAP INPUTS"
                    : "TOOL BOUND"
                  : "SELECT TOOL",
              purpose: executionStep?.output
                ? "The exact MCP call completed; select this block to inspect its result and evidence."
                : diagnosticMcpBinding
                  ? `${diagnosticMcpBinding.serverName} · ${diagnosticMcpBinding.toolName}${
                      unmappedInputs.length > 0
                        ? ` · map ${unmappedInputs.join(", ")}`
                        : ""
                    }`
                  : "Choose an installed MCP and one exact catalog tool.",
              inspector: {
                summary:
                  "Select an installed MCP server and one exact tool. Tool execution remains disabled in this increment.",
                fields: [
                  {
                    label: "Current binding",
                    value: diagnosticMcpBinding
                      ? diagnosticMcpBinding.toolId
                      : "No exact tool selected",
                  },
                  {
                    label: "Execution",
                    value: executionStep
                      ? `${executionStep.status} · open Run result for output and evidence`
                      : !diagnosticMcpBinding?.executable
                        ? "Not executable"
                        : unmappedInputs.length > 0
                          ? `Blocked · map ${unmappedInputs.join(", ")}`
                          : "Binding ready · execution disabled",
                  },
                ],
              },
            };
          }
          return { ...block, ...overlay };
        }

        return block;
      }),
    };
  })();

  const diagnosticCompletedOutputs = workflowOutputsFrom(
    diagnosticCompletedRun?.outcome,
  );

  const selectedBlock =
    displayWorkflow.blocks.find((block) => block.blockId === selectedBlockId) ??
    displayWorkflow.blocks[0];
  const selectedDiagnosticRunStep = diagnosticScenario
    ? (diagnosticStepRecords.find(
        ({ block }) =>
          diagnosticBlockIdForStep(diagnosticScenario, block) ===
          selectedBlock.blockId,
      ) ?? null)
    : null;
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
  const diagnosticRunDisabled =
    !diagnosticScenario ||
    workflowCodeSource !== appliedWorkflowCodeSource ||
    diagnosticState.status === "running" ||
    diagnosticState.status === "failed" ||
    diagnosticState.status === "passed" ||
    (diagnosticState.status === "blocked" &&
      diagnosticState.blockedAtBlockId === diagnosticScenario.mcpBlockId &&
      !diagnosticMcpRuntimeAdapter) ||
    (diagnosticState.status === "blocked" &&
      diagnosticState.blockedAtBlockId === diagnosticScenario.request.blockId &&
      !diagnosticRequestReady) ||
    (diagnosticRequestReady &&
      (!diagnosticRouteReady ||
        diagnosticModelsLoading ||
        selectedDiagnosticModel === null)) ||
    Boolean(
      diagnosticMcpRuntimeAdapter &&
      (diagnosticMcpCatalogLoading || !diagnosticRuntimeReady),
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
          <h1>{workflowForDisplay.title}</h1>
          <span>{badge}</span>
        </div>
        <div className="ewp-toolbar__actions" aria-label="Workflow actions">
          <button
            type="button"
            className="is-primary"
            data-state={diagnosticScenario ? diagnosticState.status : undefined}
            disabled={diagnosticRunDisabled}
            onClick={() => void handleDiagnosticRun()}
          >
            {diagnosticScenario
              ? workflowCodeSource !== appliedWorkflowCodeSource
                ? workflowCodeResult.ok
                  ? "⚠ Apply workflow code"
                  : "⚠ Fix workflow code"
                : diagnosticState.status === "revised"
                  ? "▶ Run corrected workflow"
                  : diagnosticState.status === "failed"
                    ? `⚠ Run ${diagnosticState.runs.length} failed`
                    : diagnosticState.status === "running"
                      ? diagnosticMcpRuntimeAdapter
                        ? "◌ Running…"
                        : "◌ Running selected AI…"
                      : diagnosticState.status === "blocked"
                        ? diagnosticState.blockedAtBlockId ===
                          diagnosticScenario.mcpBlockId
                          ? diagnosticMcpBinding
                            ? diagnosticMcpBinding.executable
                              ? diagnosticMcpBinding.unmappedInputs.length > 0
                                ? `⚠ Map MCP input${diagnosticMcpBinding.unmappedInputs.length === 1 ? "" : "s"}: ${diagnosticMcpBinding.unmappedInputs.join(", ")}`
                                : diagnosticMcpRuntimeAdapter
                                  ? "▶ Retry"
                                  : "✓ MCP binding ready · execution disabled"
                              : "⚠ MCP selected · unavailable"
                            : "⚠ Select exact MCP tool"
                          : diagnosticState.blockedAtBlockId ===
                              diagnosticScenario.executorBlockId
                            ? diagnosticMcpRuntimeAdapter
                              ? "▶ Retry"
                              : "▶ Retry selected AI"
                            : diagnosticRequestReady
                              ? !diagnosticRouteReady
                                ? "⚠ Fix output connection"
                                : selectedDiagnosticModel
                                  ? "▶ Continue with selected AI"
                                  : "⚠ Select AI model"
                              : "⚠ Add required input"
                        : diagnosticState.status === "passed"
                          ? "✓ Demo complete"
                          : !diagnosticRequestReady
                            ? "▶ Run preflight"
                            : !diagnosticRouteReady
                              ? "⚠ Fix output connection"
                              : diagnosticModelsLoading
                                ? "◌ Loading current Wright model…"
                                : selectedDiagnosticModel
                                  ? diagnosticMcpRuntimeAdapter
                                    ? diagnosticRuntimeReady
                                      ? "▶ Run"
                                      : "▶ Run workflow"
                                    : "▶ Run selected AI"
                                  : "⚠ Current Wright model unavailable"
              : "▶ Run workflow"}
          </button>
          {diagnosticScenario ? (
            <button
              type="button"
              disabled={diagnosticState.status === "ready"}
              onClick={handleDiagnosticReset}
            >
              ↺ Reset demo
            </button>
          ) : (
            <button type="button" disabled>
              ▣ Save draft
            </button>
          )}
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
          data-mcp-quick-binding={
            showDiagnosticMcpQuickBinding ? "true" : undefined
          }
          aria-label="Engineering workflow preview"
        >
          {diagnosticScenario && showDiagnosticMcpQuickBinding ? (
            <DiagnosticMcpQuickBinding
              catalog={diagnosticMcpCatalog}
              loading={diagnosticMcpCatalogLoading}
              selectedServerId={selectedDiagnosticMcpServerId}
              selectedToolId={selectedDiagnosticMcpToolId}
              suggestion={diagnosticMcpSuggestion}
              runtimeReady={diagnosticRuntimeReady}
              onSelectServer={handleDiagnosticMcpServerSelection}
              onSelectTool={handleDiagnosticMcpToolSelection}
            />
          ) : diagnosticScenario ? (
            <div
              className="ewp-diagnostic-banner"
              data-state={diagnosticState.status}
              role="status"
            >
              <strong>Diagnostic demo</strong>
              <span>
                {diagnosticState.status === "blocked" &&
                diagnosticState.blockedAtBlockId ===
                  diagnosticScenario.mcpBlockId &&
                diagnosticMcpBinding
                  ? diagnosticMcpBinding.unmappedInputs.length > 0
                    ? `AI output ready · ${diagnosticMcpBinding.serverName} / ${diagnosticMcpBinding.toolName} selected · Map ${diagnosticMcpBinding.unmappedInputs.join(", ")} before invocation.`
                    : `AI output ready · ${diagnosticMcpBinding.serverName} / ${diagnosticMcpBinding.toolName} selected · Execution intentionally disabled.`
                  : diagnosticState.status === "passed" &&
                      diagnosticCompletedOutputs.length > 0
                    ? `Workflow complete · ${diagnosticCompletedOutputs.length} output${diagnosticCompletedOutputs.length === 1 ? "" : "s"} ready · View or download below.`
                    : diagnosticStatusMessage(
                        diagnosticState,
                        diagnosticScenario,
                      )}
              </span>
            </div>
          ) : null}
          {diagnosticScenario ? (
            <nav
              className="ewp-representation-switch"
              aria-label="Workflow representation"
            >
              <span>View</span>
              <button
                type="button"
                aria-pressed={workflowRepresentation === "diagram"}
                onClick={() => setWorkflowRepresentation("diagram")}
              >
                Diagram
              </button>
              <button
                type="button"
                aria-pressed={workflowRepresentation === "code"}
                onClick={() => setWorkflowRepresentation("code")}
              >
                Code
              </button>
              <output aria-live="polite">
                {workflowCodeResult.ok
                  ? workflowCodeSource === appliedWorkflowCodeSource
                    ? "Code and diagram match"
                    : "Valid code has unapplied changes"
                  : "Code has validation issues"}
              </output>
            </nav>
          ) : null}
          {diagnosticScenario && workflowRepresentation === "diagram" ? (
            <DiagnosticRunMonitor
              scenario={diagnosticScenario}
              state={diagnosticState}
              workflow={displayWorkflow}
              progress={diagnosticLlmProgress}
              startedAt={diagnosticRunStartedAt}
              observedAt={diagnosticObservedAt}
              steps={diagnosticStepRecords}
              completedRun={diagnosticCompletedRun}
              onSelectBlock={setSelectedBlockId}
              onOutputAction={handleDiagnosticOutputAction}
            />
          ) : null}
          {diagnosticScenario && workflowRepresentation === "code" ? (
            <WorkflowCodeExperiment
              source={workflowCodeSource}
              result={workflowCodeResult}
              applied={workflowCodeSource === appliedWorkflowCodeSource}
              onChange={setWorkflowCodeSource}
              onApply={handleWorkflowCodeApply}
              onFormat={handleWorkflowCodeFormat}
              onReset={handleWorkflowCodeReset}
            />
          ) : viewState !== "ready" ? (
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
          {!diagnosticScenario || workflowRepresentation === "diagram" ? (
            <Legend />
          ) : null}
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
          designInputHistory={designInputHistory}
          onDesignInputAction={dispatchDesignInputAction}
          onDesignInputFilesSelected={(files) =>
            void handleDesignInputFilesSelected(files)
          }
          designInputUploadError={designInputUploadError}
          knowledgeLookupHistory={knowledgeLookupHistory}
          onKnowledgeLookupAction={dispatchKnowledgeLookupAction}
          diagnosticScenario={diagnosticScenario}
          diagnosticState={diagnosticState}
          onDiagnosticCorrection={handleDiagnosticCorrection}
          diagnosticOutput={diagnosticOutput}
          onDiagnosticOutput={setDiagnosticOutput}
          readableDiagnosticDocumentCount={readableDiagnosticDocumentCount}
          diagnosticModelGroups={diagnosticModelGroups}
          diagnosticModelsLoading={diagnosticModelsLoading}
          diagnosticModelError={diagnosticModelError}
          selectedDiagnosticModel={selectedDiagnosticModel}
          diagnosticThinkingLevel={diagnosticThinkingLevel}
          onSelectDiagnosticModel={setSelectedDiagnosticModel}
          onSelectDiagnosticThinkingLevel={setDiagnosticThinkingLevel}
          diagnosticMcpCatalog={diagnosticMcpCatalog}
          diagnosticMcpCatalogLoading={diagnosticMcpCatalogLoading}
          diagnosticMcpCatalogError={diagnosticMcpCatalogError}
          diagnosticMcpSuggestion={diagnosticMcpSuggestion}
          selectedDiagnosticMcpServerId={selectedDiagnosticMcpServerId}
          selectedDiagnosticMcpToolId={selectedDiagnosticMcpToolId}
          onSelectDiagnosticMcpServer={handleDiagnosticMcpServerSelection}
          onSelectDiagnosticMcpTool={handleDiagnosticMcpToolSelection}
          diagnosticMcpBinding={diagnosticMcpBinding}
          diagnosticRunStep={selectedDiagnosticRunStep}
          diagnosticRuntimeReady={diagnosticRuntimeReady}
          onDiagnosticOutputAction={handleDiagnosticOutputAction}
        />
      </div>
      {diagnosticOutputViewer ? (
        <section
          className="ewp-output-viewer"
          role="dialog"
          aria-modal="true"
          aria-label={`Viewing ${diagnosticOutputViewer.output.title}`}
        >
          <header>
            <span>
              <small>Workflow output</small>
              <strong>{diagnosticOutputViewer.output.title}</strong>
            </span>
            <button type="button" onClick={closeDiagnosticOutputViewer}>
              Close viewer
            </button>
          </header>
          <p>
            This live viewer is owned by the application that produced the
            output. Closing it returns to the workflow without deleting the
            session model.
          </p>
        </section>
      ) : null}
      {capabilityLibraryOpen ? (
        <CapabilityLibrary onClose={() => setCapabilityLibraryOpen(false)} />
      ) : null}
    </div>
  );
}

export default EngineeringWorkflowVisualSlice;
