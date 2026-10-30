import { useEffect, useId, useMemo, useRef, useState } from "react";

import {
  workspaceService,
  type EngineeringWorkflowTemplate,
  type EngineeringWorkflowTemplateDetail,
} from "../../services/workspace-service";
import "./engineering-template-dialog.css";
import { TemplateToolSetup } from "./TemplateToolSetup";

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
  ready: "Ready in qualified setup",
  verified: "Verified example",
};

const previewLabels = {
  supplied_sketch: "Supplied sketch",
  workflow_illustration: "Workflow illustration",
  recorded_result: "Recorded result",
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
  const [setupShown, setSetupShown] = useState(false);
  const [detail, setDetail] = useState<EngineeringWorkflowTemplateDetail>();
  const [detailError, setDetailError] = useState("");
  const [detailRequest, setDetailRequest] = useState(0);
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
    setTemplates([]);
    setSelectedId("");
    setName("");
    setSetupShown(false);
    void workspaceService
      .getEngineeringWorkflowTemplates()
      .then((items) => {
        if (!current) return;
        setTemplates(items);
        const initial = items.find((item) => item.exploration) ?? items[0];
        setSelectedId(initial?.template_id ?? "");
        setName(initial?.title ?? "");
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

  useEffect(() => {
    setDetail(undefined);
    setDetailError("");
    if (!open || !selected) return;
    let current = true;
    void workspaceService
      .getEngineeringWorkflowTemplate(selected.template_id, selected.version)
      .then((loaded) => {
        if (!current) return;
        if (
          loaded.template_id !== selected.template_id ||
          loaded.version !== selected.version ||
          loaded.source_digest !== selected.source_digest
        )
          throw new Error(
            "The starter changed while its requirements were loading. Reopen the example list before creating a copy.",
          );
        setDetail(loaded);
      })
      .catch((reason: unknown) => {
        if (!current) return;
        setDetailError(
          reason instanceof Error
            ? reason.message
            : "Unable to load this job's setup requirements.",
        );
      });
    return () => {
      current = false;
    };
  }, [open, selected, detailRequest]);

  const choose = (template: EngineeringWorkflowTemplate) => {
    setSelectedId(template.template_id);
    setName(template.title);
    setError("");
    setSetupShown(false);
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
            Explore a job, its inputs and its results before setting up tools.
            Browsing does not run an engineering process.
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
        <p role="status">Loading engineering workflows…</p>
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
              <h3>{selected.title}</h3>
              <p>{selected.summary}</p>
              {detailError && (
                <div role="status">
                  <p>
                    Tool setup information could not be loaded. You can still
                    browse the example.
                  </p>
                  <button
                    type="button"
                    onClick={() => setDetailRequest((request) => request + 1)}
                  >
                    Retry tool setup
                  </button>
                </div>
              )}
              {detail?.template_id === selected.template_id &&
                detail.source_digest === selected.source_digest && (
                  <TemplateToolSetup
                    key={`${sessionId}:${workspaceId}:${selected.template_id}:${selected.version}:${selected.source_digest}`}
                    requirements={detail.capability_requirements}
                  />
                )}
              <figure className="engineering-template-dialog__preview">
                <img
                  src={`/api/workspace/workflow-source-templates/${encodeURIComponent(selected.template_id)}/preview?version=${encodeURIComponent(selected.version)}`}
                  alt={selected.preview.alt}
                />
                <figcaption>
                  <strong>
                    {selected.exploration
                      ? previewLabels[selected.exploration.preview_kind]
                      : "Workflow illustration"}
                  </strong>
                  {selected.exploration && (
                    <span>{selected.exploration.preview_caption}</span>
                  )}
                </figcaption>
              </figure>
              {selected.exploration && (
                <>
                  <section
                    className="engineering-template-dialog__outcome"
                    data-testid="workflow-template-outcome"
                    aria-label="Example outcome"
                  >
                    <h4>
                      {selected.exploration.outcome_status === "recorded"
                        ? "Recorded outcome"
                        : "Recorded outcome pending"}
                    </h4>
                    <p>{selected.exploration.outcome_summary}</p>
                    {selected.exploration.outcome_status === "recorded" &&
                      selected.exploration.recorded_result && (
                        <details>
                          <summary data-testid="workflow-template-recorded-evidence">
                            Recorded result evidence
                          </summary>
                          <p>{selected.exploration.recorded_result.scope}</p>
                          <dl>
                            <div>
                              <dt>Run</dt>
                              <dd>
                                {selected.exploration.recorded_result.run_id}
                              </dd>
                            </div>
                            <div>
                              <dt>Source digest</dt>
                              <dd>
                                {
                                  selected.exploration.recorded_result
                                    .source_digest
                                }
                              </dd>
                            </div>
                            <div>
                              <dt>Artifact digest</dt>
                              <dd>
                                {
                                  selected.exploration.recorded_result
                                    .artifact_digest
                                }
                              </dd>
                            </div>
                            <div>
                              <dt>Evidence</dt>
                              <dd>
                                {
                                  selected.exploration.recorded_result
                                    .evidence_reference
                                }
                              </dd>
                            </div>
                          </dl>
                        </details>
                      )}
                    <p>
                      Live results appear in the working view after you start
                      your own run.
                    </p>
                  </section>
                  <section aria-label="Engineering tool handoffs">
                    <h4>How the tools work together</h4>
                    <ol className="engineering-template-dialog__stages">
                      {selected.exploration.stages.map((stage, index) => (
                        <li key={`${index}-${stage.title}`}>
                          <strong>{stage.title}</strong>
                          <p>
                            {stage.tool} — {stage.contribution}
                          </p>
                          <dl>
                            <div>
                              <dt>Receives</dt>
                              <dd>{stage.input}</dd>
                            </div>
                            <div>
                              <dt>Produces</dt>
                              <dd>{stage.output}</dd>
                            </div>
                          </dl>
                        </li>
                      ))}
                    </ol>
                  </section>
                  {selected.exploration.limitations.length > 0 && (
                    <section aria-label="Example limitations">
                      <h4>What this example establishes</h4>
                      <ul>
                        {selected.exploration.limitations.map((limit) => (
                          <li key={limit}>{limit}</li>
                        ))}
                      </ul>
                    </section>
                  )}
                </>
              )}
              <div
                data-testid="workflow-template-readiness"
                className="engineering-template-dialog__readiness"
              >
                <p>Packaged starter status</p>
                <b>{readinessLabels[selected.readiness.state]}</b>
                {selected.readiness.blocking_reasons.map((reason) => (
                  <p key={reason}>{reason}</p>
                ))}
                <p>
                  Your workspace's current tools and inputs are checked in the
                  working view before a run.
                </p>
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
              <button
                type="button"
                className="recovery-button recovery-button--secondary"
                data-testid="workflow-template-setup"
                aria-expanded={setupShown}
                aria-controls={`${id}-setup`}
                onClick={() => setSetupShown((shown) => !shown)}
              >
                {setupShown ? "Hide setup requirements" : "Set up this job"}
              </button>
              {setupShown && (
                <section
                  id={`${id}-setup`}
                  className="engineering-template-dialog__setup"
                  aria-label="Setup requirements"
                >
                  <h4>Tools for this process</h4>
                  <p>
                    {selected.template_id === "replacement-drawer-handle"
                      ? "Create an editable copy, then choose Set up this job in its editor. Select your local tools and exact profile files, inspect and accept the proposed revision, then open its working view and choose Prepare and check inputs."
                      : "Create an editable copy, review its inputs, then open its working view and choose Prepare and check inputs."}{" "}
                    Creating a copy does not install tools or start work.
                  </p>
                  {!detail && !detailError && (
                    <p role="status">Loading packaged requirements…</p>
                  )}
                  {detailError && (
                    <>
                      <p role="alert">{detailError}</p>
                      <button
                        type="button"
                        data-testid="workflow-template-setup-retry"
                        className="recovery-button recovery-button--secondary"
                        onClick={() =>
                          setDetailRequest((request) => request + 1)
                        }
                      >
                        Retry requirements
                      </button>
                    </>
                  )}
                  {detail && (
                    <>
                      <ul>
                        {detail.capability_requirements.map(
                          (requirement, index) => (
                            <li key={index}>
                              <strong>
                                {String(
                                  requirement.title ??
                                    requirement.operation ??
                                    "Engineering capability",
                                ).replaceAll("_", " ")}
                              </strong>
                              {typeof requirement.description === "string" && (
                                <p>{requirement.description}</p>
                              )}
                              {typeof requirement.qualification ===
                                "string" && (
                                <span>
                                  {" "}
                                  · Qualification: {requirement.qualification}
                                </span>
                              )}
                            </li>
                          ),
                        )}
                      </ul>
                      {detail.readiness.facts.length > 0 && (
                        <ul aria-label="Recorded qualification facts">
                          {detail.readiness.facts.map((fact) => (
                            <li key={fact.code}>
                              {fact.label}:{" "}
                              {fact.satisfied ? "recorded" : "still needed"}
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  )}
                </section>
              )}
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
