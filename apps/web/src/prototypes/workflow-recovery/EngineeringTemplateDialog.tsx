import { useEffect, useId, useMemo, useRef, useState } from "react";

import {
  workspaceService,
  type EngineeringWorkflowTemplate,
} from "../../services/workspace-service";
import "./engineering-template-dialog.css";

interface EngineeringTemplateDialogProps {
  open: boolean;
  sessionId: string;
  workspaceId: string;
  workspaceName: string;
  onClose: () => void;
  onCreated: (path: string) => void;
}

function readable(value: unknown): string {
  if (value && typeof value === "object" && "name" in value)
    return String((value as { name: unknown }).name);
  return String(value);
}

function slugFor(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const readinessLabels: Record<
  EngineeringWorkflowTemplate["readiness"]["state"],
  string
> = {
  reference: "Reference workflow",
  setup_required: "Setup required",
  ready: "Ready to run",
  verified: "Verified runnable",
};

export function EngineeringTemplateDialog({
  open,
  sessionId,
  workspaceId,
  workspaceName,
  onClose,
  onCreated,
}: EngineeringTemplateDialogProps) {
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const [templates, setTemplates] = useState<EngineeringWorkflowTemplate[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "creating">("idle");
  const [error, setError] = useState("");
  const selected = useMemo(
    () =>
      templates.find((template) => template.template_id === selectedId) ?? null,
    [selectedId, templates],
  );

  useEffect(() => {
    const node = dialog.current;
    if (!node) return;
    if (open && !node.open) {
      if (node.showModal) node.showModal();
      else node.setAttribute("open", "");
    }
    if (!open && node.open) {
      if (node.close) node.close();
      else node.removeAttribute("open");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    let current = true;
    setState("loading");
    setError("");
    void workspaceService
      .getEngineeringWorkflowTemplates()
      .then((items) => {
        if (!current) return;
        setTemplates(items);
        setSelectedId(items[0]?.template_id ?? "");
        setName(items[0]?.title ?? "");
        setState("idle");
      })
      .catch((reason: unknown) => {
        if (!current) return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Unable to load engineering workflow templates.",
        );
        setState("idle");
      });
    return () => {
      current = false;
    };
  }, [open]);

  const choose = (template: EngineeringWorkflowTemplate) => {
    setSelectedId(template.template_id);
    setName(template.title);
    setError("");
  };

  const create = async () => {
    if (!selected) return;
    const slug = slugFor(name.trim());
    if (
      !name.trim() ||
      !/^[a-z0-9][a-z0-9-]{0,62}$/.test(slug) ||
      /^(aux|con|nul|prn|com[1-9]|lpt[1-9])$/.test(slug)
    ) {
      setError(
        "Use a short workflow name containing letters and numbers (up to 63 filename characters).",
      );
      return;
    }
    const path = `workflows/${slug}.workflow.wflow`;
    setState("creating");
    setError("");
    try {
      const created =
        await workspaceService.instantiateEngineeringWorkflowTemplate(
          sessionId,
          selected,
          path,
          crypto.randomUUID(),
        );
      if (created.workspace_id !== workspaceId || created.path !== path)
        throw new Error(
          "Wright returned a workflow for a different workspace.",
        );
      onClose();
      onCreated(path);
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to create this workflow. Existing files were kept.",
      );
    } finally {
      setState("idle");
    }
  };

  return (
    <dialog
      ref={dialog}
      className="engineering-template-dialog"
      aria-labelledby={`${id}-title`}
      onCancel={(event) => {
        event.preventDefault();
        if (state !== "creating") onClose();
      }}
      onClose={() => {
        if (open && state !== "creating") onClose();
      }}
    >
      <header>
        <div>
          <p className="engineering-template-dialog__eyebrow">
            {workspaceName} · Workflows
          </p>
          <h2 id={`${id}-title`}>Start from an engineering workflow</h2>
          <p>
            Choose an editable example. Readiness describes the current live
            tool path.
          </p>
        </div>
        <button
          type="button"
          className="engineering-template-dialog__close"
          aria-label="Close template picker"
          disabled={state === "creating"}
          onClick={onClose}
        >
          ×
        </button>
      </header>

      {state === "loading" ? (
        <p role="status">Loading ten engineering workflows…</p>
      ) : (
        <div className="engineering-template-dialog__body">
          <div
            className="engineering-template-dialog__list"
            data-testid="workflow-template-list"
            role="listbox"
            aria-label="Engineering workflow templates"
          >
            {templates.map((template, index) => (
              <button
                key={template.template_id}
                type="button"
                role="option"
                aria-selected={template.template_id === selectedId}
                data-testid={`workflow-template-option-${template.template_id}`}
                onClick={() => choose(template)}
                onKeyDown={(event) => {
                  if (
                    !["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)
                  )
                    return;
                  event.preventDefault();
                  const nextIndex =
                    event.key === "Home"
                      ? 0
                      : event.key === "End"
                        ? templates.length - 1
                        : (index +
                            (event.key === "ArrowDown" ? 1 : -1) +
                            templates.length) %
                          templates.length;
                  const next = templates[nextIndex];
                  if (next) {
                    choose(next);
                    event.currentTarget.parentElement
                      ?.querySelectorAll<HTMLButtonElement>('[role="option"]')
                      .item(nextIndex)
                      .focus();
                  }
                }}
              >
                <span>{template.title}</span>
                <small>{template.discipline}</small>
                <span
                  className={`engineering-template-state engineering-template-state--${template.readiness.state}`}
                >
                  {readinessLabels[template.readiness.state]}
                </span>
              </button>
            ))}
          </div>

          {selected && (
            <section
              className="engineering-template-dialog__details"
              data-testid="workflow-template-details"
              aria-live="polite"
            >
              <div className="engineering-template-dialog__preview">
                <img
                  src={`/api/workspace/workflow-source-templates/${encodeURIComponent(selected.template_id)}/preview?version=${encodeURIComponent(selected.version)}`}
                  alt={selected.preview.alt}
                />
              </div>
              <h3>{selected.title}</h3>
              <p>{selected.summary}</p>
              <div
                data-testid="workflow-template-readiness"
                className="engineering-template-dialog__readiness"
              >
                <b>{readinessLabels[selected.readiness.state]}</b>
                {selected.readiness.blocking_reasons.map((reason) => (
                  <p key={reason}>{reason}</p>
                ))}
              </div>
              <dl>
                <div>
                  <dt>Provided</dt>
                  <dd>
                    {selected.provided_inputs.length
                      ? selected.provided_inputs.map(readable).join(", ")
                      : "No packaged inputs"}
                  </dd>
                </div>
                <div>
                  <dt>You provide</dt>
                  <dd>{selected.requested_inputs.map(readable).join(", ")}</dd>
                </div>
                <div>
                  <dt>Outputs</dt>
                  <dd>{selected.expected_outputs.map(readable).join(", ")}</dd>
                </div>
                <div>
                  <dt>External effects</dt>
                  <dd>
                    {selected.external_effects.length
                      ? selected.external_effects
                          .join(", ")
                          .replaceAll("_", " ")
                      : "None"}
                  </dd>
                </div>
              </dl>
              <label htmlFor={`${id}-name`}>Workflow name</label>
              <input
                id={`${id}-name`}
                data-testid="workflow-template-name"
                value={name}
                maxLength={100}
                onChange={(event) => setName(event.target.value)}
              />
            </section>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="engineering-template-dialog__error">
          {error}
        </p>
      )}
      <footer>
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          data-testid="workflow-template-cancel"
          disabled={state === "creating"}
          onClick={onClose}
        >
          Cancel
        </button>
        <button
          type="button"
          className="recovery-button recovery-button--primary"
          data-testid="workflow-template-create"
          disabled={!selected || state !== "idle"}
          onClick={() => void create()}
        >
          {state === "creating" ? "Creating…" : "Create editable workflow"}
        </button>
      </footer>
    </dialog>
  );
}
