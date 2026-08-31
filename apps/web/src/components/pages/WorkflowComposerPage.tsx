import { type FormEvent, useEffect, useState } from "react";

import { WorkflowComposer } from "../workflow-composer/WorkflowComposer";
import {
  createWorkflowDraft,
  readWorkflowDraft,
  type WorkflowDraftResult,
} from "../../services/workflow-drafts";

type PageState =
  | { readonly kind: "start" }
  | { readonly kind: "loading"; readonly message: string }
  | { readonly kind: "ready"; readonly result: WorkflowDraftResult }
  | { readonly kind: "error"; readonly message: string };

function draftFromLocation(): string | null {
  return new URLSearchParams(window.location.search).get("draft");
}

export default function WorkflowComposerPage(): React.ReactNode {
  const [state, setState] = useState<PageState>(() => draftFromLocation() === null
    ? { kind: "start" }
    : { kind: "loading", message: "Reopening working draft…" });
  const [title, setTitle] = useState("Product definition draft");
  const [purpose, setPurpose] = useState("Capture, define, review, and release one product definition.");

  useEffect(() => {
    const draftId = draftFromLocation();
    if (draftId === null) return;
    const controller = new AbortController();
    void readWorkflowDraft(draftId)
      .then((result) => {
        if (!controller.signal.aborted) setState({ kind: "ready", result });
      })
      .catch(() => {
        if (!controller.signal.aborted) setState({ kind: "error", message: "The requested working draft could not be reopened." });
      });
    return () => controller.abort();
  }, []);

  const create = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    setState({ kind: "loading", message: "Creating an empty working draft…" });
    try {
      const result = await createWorkflowDraft(title.trim(), purpose.trim());
      const next = new URL(window.location.href);
      next.searchParams.set("draft", result.draft.draft_id);
      window.history.replaceState({}, "", next);
      setState({ kind: "ready", result });
    } catch {
      setState({ kind: "error", message: "Workflow Composer could not create a draft. Confirm that both composer feature flags are enabled." });
    }
  };

  if (state.kind === "ready") {
    return (
      <main data-testid="page-workflow-composer">
        <WorkflowComposer
          initialDraft={state.result.draft}
          initialEtag={state.result.etag}
        />
      </main>
    );
  }

  return (
    <main className="workflow-composer workflow-composer__start" data-testid="page-workflow-composer">
      <header>
        <p className="workflow-composer__eyebrow">Workflow Composer · provisional</p>
        <h1>Compose an inspectable engineering workflow</h1>
        <p>Create a separate working draft. The released Process Definition remains read-only and unchanged.</p>
      </header>

      {state.kind === "loading" && <p role="status" aria-live="polite" aria-busy="true">{state.message}</p>}
      {state.kind === "error" && (
        <div className="workflow-composer__notice" role="alert">
          <strong>Draft unavailable</strong>
          <p>{state.message}</p>
          <button type="button" onClick={() => setState({ kind: "start" })}>Try again</button>
        </div>
      )}
      {state.kind === "start" && (
        <form className="workflow-composer__create" onSubmit={(event) => void create(event)}>
          <h2>Create an empty draft</h2>
          <label>
            Draft title
            <input data-testid="workflow-composer-create-title" required maxLength={500} value={title} onChange={(event) => setTitle(event.currentTarget.value)} />
          </label>
          <label>
            Purpose
            <textarea data-testid="workflow-composer-create-purpose" required maxLength={500} rows={3} value={purpose} onChange={(event) => setPurpose(event.currentTarget.value)} />
          </label>
          <p className="workflow-composer__boundary"><strong>Draft authority only.</strong> This creates no run, release, approval, or published artifact.</p>
          <button data-testid="workflow-composer-create" type="submit">Create working draft</button>
        </form>
      )}
    </main>
  );
}
