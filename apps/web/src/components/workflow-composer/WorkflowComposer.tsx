import { useCallback, useEffect, useMemo, useState } from "react";

import {
  readWorkflowDraft,
  saveWorkflowDraft,
  validateWorkflowDraft,
  WorkflowDraftClientError,
  type WorkflowDraft,
  type WorkflowDraftResult,
  type WorkflowDraftValidation,
} from "../../services/workflow-drafts";
import { DraftInspector } from "./DraftInspector";
import { DraftTextProjection } from "./DraftTextProjection";
import { FirstPartyDraftCanvas } from "./FirstPartyDraftCanvas";
import type { DraftCanvasIntent } from "./draft-intents";
import { buildDraftProjection } from "./draft-projection";
import type { DraftCanvasRenderer } from "./renderer-types";
import {
  addRepresentativeRole,
  nextRepresentativeRole,
  type RepresentativeRole,
} from "./representative-workflow";
import "./workflow-composer.css";

type ComposerView = "split" | "diagram" | "text";

export interface WorkflowComposerProps {
  readonly initialDraft: WorkflowDraft;
  readonly initialEtag?: string;
  readonly renderer?: DraftCanvasRenderer;
}

const PALETTE = [
  { role: "input", label: "Capture input", symbol: "↳" },
  { role: "work", label: "Engineering work", symbol: "◆" },
  { role: "review", label: "Review", symbol: "◇" },
  { role: "release", label: "Release boundary", symbol: "▣" },
] as const;

export function WorkflowComposer({ initialDraft, initialEtag, renderer: Renderer = FirstPartyDraftCanvas }: WorkflowComposerProps): React.ReactNode {
  const [draft, setDraft] = useState(initialDraft);
  const [etag, setEtag] = useState<string | null>(initialEtag ?? null);
  const [selectedSemanticId, setSelectedSemanticId] = useState<string | null>(null);
  const [view, setView] = useState<ComposerView>("split");
  const [notice, setNotice] = useState<string | null>(null);
  const [closed, setClosed] = useState(false);
  const [busyAction, setBusyAction] = useState<"validate" | "save" | "reopen" | null>(null);
  const [paletteBusy, setPaletteBusy] = useState(false);
  const [validation, setValidation] = useState<WorkflowDraftValidation | null>(null);
  const [staleCurrent, setStaleCurrent] = useState<WorkflowDraftResult | null>(null);
  const projection = useMemo(() => buildDraftProjection(draft), [draft]);
  const nextRole = nextRepresentativeRole(draft);

  useEffect(() => {
    setDraft(initialDraft);
    setEtag(initialEtag ?? null);
    setClosed(false);
    setSelectedSemanticId(null);
    setValidation(null);
    setStaleCurrent(null);
  }, [initialDraft, initialEtag]);

  const handleIntent = useCallback((intent: DraftCanvasIntent) => {
    if (intent.type === "select") {
      setSelectedSemanticId(intent.semanticId);
      setNotice(null);
      return;
    }
    setNotice("Direct semantic editing is introduced in the next safe-edit checkpoint.");
  }, []);

  const addBoundedBlock = async (role: RepresentativeRole): Promise<void> => {
    setPaletteBusy(true);
    setNotice(null);
    try {
      const nextDraft = await addRepresentativeRole(draft, role);
      setDraft(nextDraft);
      setValidation(null);
      setStaleCurrent(null);
      const remaining = nextRepresentativeRole(nextDraft);
      setNotice(remaining === null
        ? "Representative four-block composition is complete. Validate and save this working draft."
        : `Added ${nextDraft.semantic.blocks.at(-1)?.title}. Continue with the next bounded block.`);
    } catch {
      setNotice("That block cannot be added in the bounded composition order. The working draft was not changed.");
    } finally {
      setPaletteBusy(false);
    }
  };

  const validate = async (): Promise<void> => {
    setBusyAction("validate");
    setNotice(null);
    try {
      const result = await validateWorkflowDraft(draft);
      setValidation(result);
      setNotice(result.valid
        ? "Validation passed. The working draft is structurally valid."
        : `Validation found ${result.diagnostics.length} diagnostic${result.diagnostics.length === 1 ? "" : "s"}.`);
    } catch {
      setNotice("Validation could not complete. The current working draft was not changed.");
    } finally {
      setBusyAction(null);
    }
  };

  const save = async (): Promise<void> => {
    if (etag === null) {
      setNotice("This local projection has no save identity. Reopen it from the draft service before saving.");
      return;
    }
    setBusyAction("save");
    setNotice(null);
    try {
      const result = await validateWorkflowDraft(draft);
      setValidation(result);
      if (!result.valid) {
        setNotice(`Save stopped: resolve ${result.diagnostics.length} validation diagnostic${result.diagnostics.length === 1 ? "" : "s"}.`);
        return;
      }
      const saved = await saveWorkflowDraft(draft, etag);
      setDraft(saved.draft);
      setEtag(saved.etag);
      setStaleCurrent(null);
      setNotice(`Saved revision ${saved.draft.revision}.`);
    } catch (error) {
      if (error instanceof WorkflowDraftClientError && error.errorCode === "WORKFLOW_DRAFT_STALE_REVISION") {
        try {
          const current = await readWorkflowDraft(draft.draft_id);
          setStaleCurrent(current);
          setNotice(`Save stopped because the draft changed. Your local candidate is preserved; current saved revision ${current.draft.revision} is available to load explicitly.`);
        } catch {
          setNotice("Save stopped because the draft changed. Reopen the current draft before retrying.");
        }
      } else {
        setNotice("Save failed. The prior valid revision remains current.");
      }
    } finally {
      setBusyAction(null);
    }
  };

  const reopen = async (): Promise<void> => {
    setBusyAction("reopen");
    setNotice(null);
    try {
      const current = await readWorkflowDraft(draft.draft_id);
      setDraft(current.draft);
      setEtag(current.etag);
      setStaleCurrent(null);
      setValidation(null);
      setClosed(false);
      setSelectedSemanticId(null);
      setNotice(`Reopened revision ${current.draft.revision} with its saved semantic and layout identities.`);
    } catch {
      setNotice("The saved draft could not be reopened. No local draft bytes were replaced.");
    } finally {
      setBusyAction(null);
    }
  };

  if (closed) {
    return (
      <section className="workflow-composer workflow-composer__closed" data-testid="workflow-composer-closed">
        <p className="workflow-composer__eyebrow">Working draft closed</p>
        <h1>{draft.semantic.title}</h1>
        <p>The editor session is closed. Saved revision {draft.revision} remains in Wright's local draft store.</p>
        <dl>
          <dt>Draft</dt><dd><code>{draft.draft_id}</code></dd>
          <dt>Semantic digest</dt><dd><code>{draft.semantic_sha256}</code></dd>
          <dt>Layout digest</dt><dd><code>{draft.layout_sha256}</code></dd>
        </dl>
        <button data-testid="workflow-composer-reopen" type="button" disabled={busyAction !== null} onClick={() => void reopen()}>
          {busyAction === "reopen" ? "Reopening…" : "Reopen saved draft"}
        </button>
        {notice !== null && <p className="workflow-composer__notice" role="status">{notice}</p>}
      </section>
    );
  }

  return (
    <section className="workflow-composer" data-testid="workflow-composer">
      <header className="workflow-composer__header">
        <div>
          <p className="workflow-composer__eyebrow">Workflow Composer · provisional</p>
          <h1>{projection.title}</h1>
          <p>{projection.purpose}</p>
        </div>
        <div className="workflow-composer__authority" role="note" aria-label="Working draft authority">
          <strong>Working draft</strong>
          <span>Revision {projection.revision}</span>
          <span>Not released · Not executable</span>
          <code title="Semantic digest">S {draft.semantic_sha256}</code>
          <code title="Layout digest">L {draft.layout_sha256}</code>
        </div>
      </header>

      <nav className="workflow-composer__commandbar" aria-label="Composer controls">
        <div className="workflow-composer__palette" aria-label="Block palette">
          <span>Block palette</span>
          {PALETTE.map((item) => (
            (() => {
              const added = draft.semantic.blocks.some((block) => block.role === item.role);
              const enabled = nextRole === item.role && busyAction === null && !paletteBusy;
              return (
            <button
              data-testid={`workflow-composer-palette-${item.role}`}
              disabled={!enabled}
              key={item.role}
              type="button"
              onClick={() => void addBoundedBlock(item.role)}
            >
              <b aria-hidden="true">{added ? "✓" : item.symbol}</b> {item.label}{added ? " · added" : ""}
            </button>
              );
            })()
          ))}
        </div>
        <div className="workflow-composer__view-controls" aria-label="Projection view">
          {(["split", "diagram", "text"] as const).map((value) => (
            <button
              aria-pressed={view === value}
              data-testid={`workflow-composer-view-${value}`}
              key={value}
              type="button"
              onClick={() => setView(value)}
            >
              {value === "split" ? "Diagram + text" : value[0]?.toUpperCase() + value.slice(1)}
            </button>
          ))}
          <button data-testid="workflow-composer-validate" type="button" disabled={busyAction !== null} onClick={() => void validate()}>
            {busyAction === "validate" ? "Validating…" : "Validate"}
          </button>
          <button data-testid="workflow-composer-save" type="button" disabled={busyAction !== null || etag === null || staleCurrent !== null} onClick={() => void save()}>
            {busyAction === "save" ? "Saving…" : "Save draft"}
          </button>
          <button data-testid="workflow-composer-close" type="button" disabled={busyAction !== null} onClick={() => { setClosed(true); setNotice(null); }}>
            Close
          </button>
        </div>
      </nav>

      {notice !== null && <p className="workflow-composer__notice" role="status">{notice}</p>}
      {staleCurrent !== null && (
        <div className="workflow-composer__stale" role="alert">
          <strong>Newer saved revision detected</strong>
          <p>Your local candidate remains visible. Loading revision {staleCurrent.draft.revision} will replace it.</p>
          <button
            data-testid="workflow-composer-use-current"
            type="button"
            onClick={() => {
              setDraft(staleCurrent.draft);
              setEtag(staleCurrent.etag);
              setStaleCurrent(null);
              setValidation(null);
              setNotice(`Loaded current saved revision ${staleCurrent.draft.revision}.`);
            }}
          >
            Load saved revision {staleCurrent.draft.revision}
          </button>
        </div>
      )}

      <div className={`workflow-composer__workspace workflow-composer__workspace--${view}`}>
        {view !== "text" && (
          <div className="workflow-composer__diagram-panel">
            <Renderer projection={projection} selectedSemanticId={selectedSemanticId} onIntent={handleIntent} />
          </div>
        )}
        {view !== "diagram" && <DraftTextProjection projection={projection} />}
        <DraftInspector projection={projection} selectedSemanticId={selectedSemanticId} validation={validation} />
      </div>
    </section>
  );
}
