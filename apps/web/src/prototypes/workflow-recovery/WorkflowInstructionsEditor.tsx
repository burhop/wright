import { useState } from "react";
import type {
  WorkflowInstructionDefaultsDocument,
  WorkflowInstructionUpgradeProposal,
} from "../../services/workspace-service";
import { workspaceService } from "../../services/workspace-service";
import {
  normalizeWorkflowInstructions,
  type WorkflowInstructionSet,
  type WorkflowInstructionOverride,
} from "./workflow-instructions";
import "./workflow-recovery.css";

const authorOrigin = "workflow-author";
const defaultRoles = ["workflow-task", "image-generation", "mcp-task"] as const;
const pretty = (value: unknown) => JSON.stringify(value, null, 2);
const actionIntentLabel = (instructions?: WorkflowInstructionSet) =>
  instructions?.action_intent_contract ?? "Not declared in this saved profile";

export function workflowInstructionPreview(
  instructions: WorkflowInstructionSet,
  role: string,
) {
  const binding = instructions.bindings.find((item) => item.role === role);
  if (!binding) return null;
  const assets = binding.asset_ids.map((id) =>
    instructions.assets.find((asset) => asset.id === id)!,
  );
  let text = assets.map((asset) => asset.body).join("\n\n");
  let policy = instructions.policy.assumption_policy;
  const origins = assets.map((asset) => asset.origin);
  for (const layer of instructions.layers) {
    if (!layer.roles.some((item) => item === role)) continue;
    if (layer.text.trim())
      text = layer.mode === "replace" ? layer.text : `${text}\n\n${layer.text}`;
    if (layer.assumption_policy !== null) policy = layer.assumption_policy;
    origins.push(layer.origin);
  }
  return {
    text,
    policy,
    origins,
    variables: [...new Set(assets.flatMap((asset) => asset.variables))],
  };
}

export function updateInstructionDefaultsPreservingLayers(
  current: WorkflowInstructionSet | undefined,
  defaults: WorkflowInstructionSet,
): WorkflowInstructionSet {
  if (!current) return normalizeWorkflowInstructions(defaults);
  // Workspace layers come from the current workspace, author layers remain the author's edits.
  const authorLayers = current.layers.filter(
    (layer) => !["workspace-context", "global-settings"].includes(layer.origin),
  );
  const defaultLayers = defaults.layers.filter(
    (layer) => !authorLayers.some((saved) => saved.origin === layer.origin),
  );
  return normalizeWorkflowInstructions({
    ...defaults,
    policy: current.policy,
    layers: [...defaultLayers, ...authorLayers],
  });
}

async function materializeBodyEdits(
  instructions: WorkflowInstructionSet,
  original: WorkflowInstructionSet,
  origin: string,
) {
  const assets = await Promise.all(
    instructions.assets.map(async (asset) => {
      if (
        original.assets.find((saved) => saved.id === asset.id)?.body ===
        asset.body
      )
        return asset;
      const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(asset.body),
      );
      const body_digest = Array.from(new Uint8Array(digest), (byte) =>
        byte.toString(16).padStart(2, "0"),
      ).join("");
      return { ...asset, body_digest, origin };
    }),
  );
  return normalizeWorkflowInstructions({
    ...instructions,
    assets,
    policy: {
      ...instructions.policy,
      protected_requirements: instructions.policy.protected_requirements.filter(
        (value) => value.trim(),
      ),
    },
  });
}

export function WorkflowInstructionsEditor({
  instructions,
  readOnly = false,
  onApply,
  onLoadDefaults,
  onReviewActionIntentUpgrade,
  onExport,
  exportReady = false,
  mode = "workflow",
}: {
  instructions?: WorkflowInstructionSet;
  readOnly?: boolean;
  onApply: (
    value: WorkflowInstructionSet,
    reviewedRevision?: string,
  ) => boolean | Promise<boolean>;
  onLoadDefaults?: () => Promise<WorkflowInstructionDefaultsDocument>;
  onReviewActionIntentUpgrade?: (
    current: WorkflowInstructionSet,
  ) => Promise<WorkflowInstructionUpgradeProposal>;
  onExport?: () => void | Promise<void>;
  exportReady?: boolean;
  mode?: "workflow" | "global";
}) {
  const [draft, setDraft] = useState(instructions);
  const [proposed, setProposed] =
    useState<WorkflowInstructionDefaultsDocument | null>(null);
  const [upgrade, setUpgrade] =
    useState<WorkflowInstructionUpgradeProposal | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [role, setRole] = useState(
    instructions?.bindings[0]?.role ?? "workflow-task",
  );
  const editingOrigin = mode === "global" ? "global-settings" : authorOrigin;
  const disabled = readOnly || busy;
  const authorLayer = draft?.layers.find(
    (layer) => layer.origin === editingOrigin,
  );
  const change = (value: WorkflowInstructionSet) => {
    setDraft(value);
    setMessage("");
    setError("");
  };
  const setAuthorLayer = (patch: Partial<WorkflowInstructionOverride>) => {
    if (!draft || disabled) return;
    const layer: WorkflowInstructionOverride = {
      origin: editingOrigin,
      roles: [...defaultRoles],
      mode: "append",
      text: "",
      assumption_policy: null,
      ...authorLayer,
      ...patch,
    };
    const index = draft.layers.findIndex(
      (item) => item.origin === editingOrigin,
    );
    change({
      ...draft,
      layers:
        index < 0
          ? [...draft.layers, layer]
          : draft.layers.map((item, i) => (i === index ? layer : item)),
    });
  };
  const save = async (
    candidate: WorkflowInstructionSet,
    reviewedRevision?: string,
  ) => {
    if (disabled) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const normalized = await materializeBodyEdits(
        candidate,
        reviewedRevision ? candidate : (instructions ?? candidate),
        editingOrigin,
      );
      if (!(await onApply(normalized, reviewedRevision)))
        throw new Error(
          "The instruction change was not applied. Inspect the workflow diagnostics.",
        );
      setDraft(normalized);
      setProposed(null);
      setUpgrade(null);
      setMessage(
        mode === "global"
          ? "Instruction defaults saved. Existing workflows retain their saved instructions."
          : "Instructions applied to the draft. Save the workflow to accept this change.",
      );
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not apply instructions.",
      );
    } finally {
      setBusy(false);
    }
  };
  const preview = draft ? workflowInstructionPreview(draft, role) : null;
  let pending: WorkflowInstructionSet | null = null;
  let proposalError = "";
  if (proposed) {
    try {
      pending = updateInstructionDefaultsPreservingLayers(
        draft
          ? {
              ...draft,
              policy: {
                ...draft.policy,
                protected_requirements:
                  draft.policy.protected_requirements.filter((value) =>
                    value.trim(),
                  ),
              },
            }
          : undefined,
        proposed.instructions,
      );
    } catch {
      proposalError =
        "Resolve invalid instruction edits before comparing current defaults.";
    }
  }
  if (upgrade) pending = upgrade.instructions;
  return (
    <section
      className="wright-instruction-editor"
      data-testid="workflow-instructions-editor"
    >
      <p>
        {mode === "global"
          ? "New workflows start with these AI instructions. Changing them does not change saved workflows or work already running."
          : "These are the AI instructions saved with this workflow. They are included when you export it. Changes apply when you save a new revision, not to work already running."}
      </p>
      {!draft && (
        <p role="status">
          This older workflow uses this installation's default AI instructions.
          Save instructions with the workflow before exporting it so another
          installation can use the same instructions.
        </p>
      )}
      {draft && (
        <>
          <p>
            Choose how AI handles missing design choices and add any guidance
            below. Saved instructions and their versions remain available to
            inspect.
          </p>
          <details>
            <summary>Instruction version and compatibility</summary>
            <p>
              <strong>Instruction set:</strong> {draft.profile_id} ·{" "}
              {draft.profile_version}
            </p>
            <section aria-label="Saved tool action contract">
              <p data-testid="workflow-instructions-action-intent">
                <strong>Tool communication format:</strong>{" "}
                {actionIntentLabel(draft)}
              </p>
              <p>
                {draft.action_intent_contract
                  ? "Before using an engineering tool, AI describes the action it intends to take. Wright checks that it is allowed by the workflow's saved limits and permissions."
                  : "These older instructions may need a reviewed update before engineering tools can be used."}{" "}
                These instructions do not grant new permissions or replace
                required reviews.
              </p>
            </section>
            {onReviewActionIntentUpgrade && (
              <button
                type="button"
                className="recovery-button recovery-button--secondary"
                disabled={disabled}
                data-testid="workflow-instructions-review-action-upgrade"
                onClick={async () => {
                  if (disabled) return;
                  setBusy(true);
                  setError("");
                  setMessage("");
                  try {
                    // The server proposes only a protocol migration; customized text and policy remain intact.
                    const current = await materializeBodyEdits(
                      draft,
                      instructions ?? draft,
                      editingOrigin,
                    );
                    const result = await onReviewActionIntentUpgrade(current);
                    setProposed(null);
                    setUpgrade(result);
                  } catch (error) {
                    setError(
                      error instanceof Error
                        ? error.message
                        : "Could not prepare the instruction upgrade.",
                    );
                  } finally {
                    setBusy(false);
                  }
                }}
              >
                Review instruction update…
              </button>
            )}
          </details>
          <label>
            Unspecified design choices
            <select
              value={draft.policy.assumption_policy}
              data-testid="workflow-instructions-policy"
              disabled={disabled}
              onChange={(event) =>
                change({
                  ...draft,
                  policy: {
                    ...draft.policy,
                    assumption_policy: event.target
                      .value as WorkflowInstructionSet["policy"]["assumption_policy"],
                  },
                })
              }
            >
              <option value="document_reasonable">
                Document reasonable assumptions
              </option>
              <option value="require_specified">
                Require specified values
              </option>
            </select>
          </label>
          <p>
            AI must preserve your requirements. Add a Request input step
            wherever the workflow should wait for an answer from you.
          </p>
          <label>
            Protected requirements (one identifier per line)
            <textarea
              rows={3}
              data-testid="workflow-instructions-protected-requirements"
              value={draft.policy.protected_requirements.join("\n")}
              disabled={disabled}
              onChange={(event) =>
                change({
                  ...draft,
                  policy: {
                    ...draft.policy,
                    protected_requirements: event.target.value.split("\n"),
                  },
                })
              }
            />
          </label>
          <label>
            Additional workflow guidance
            <textarea
              rows={4}
              value={authorLayer?.text ?? ""}
              data-testid="workflow-instructions-guidance"
              disabled={disabled}
              onChange={(event) => setAuthorLayer({ text: event.target.value })}
            />
          </label>
          <label>
            Guidance mode
            <select
              value={authorLayer?.mode ?? "append"}
              data-testid="workflow-instructions-mode"
              disabled={disabled}
              onChange={(event) =>
                setAuthorLayer({
                  mode: event.target.value as "append" | "replace",
                })
              }
            >
              <option value="append">Append to saved instructions</option>
              <option value="replace">Replace task guidance</option>
            </select>
          </label>
          <p>
            This guidance applies to AI steps, image steps and engineering-tool
            steps. Other saved instructions remain unchanged and can be
            inspected below.
          </p>
          <details>
            <summary data-testid="workflow-instructions-preview-toggle">
              Instructions used by AI
            </summary>
            <label>
              Instruction role
              <select
                value={role}
                data-testid="workflow-instructions-role"
                onChange={(event) => setRole(event.target.value as typeof role)}
              >
                {draft.bindings.map((binding) => (
                  <option key={binding.role} value={binding.role}>
                    {binding.role}
                  </option>
                ))}
              </select>
            </label>
            {preview && (
              <>
                <p>Origins: {preview.origins.join(" → ")}</p>
                <p>
                  Effective assumption policy:{" "}
                  {preview.policy === "document_reasonable"
                    ? "Document reasonable assumptions"
                    : "Require specified values"}
                </p>
                {!!preview.variables.length && (
                  <p>
                    Run values fill these declared template variables:{" "}
                    {preview.variables.join(", ")}. This preview retains their
                    placeholders.
                  </p>
                )}
                <textarea
                  aria-label="Effective instruction template"
                  data-testid="workflow-instructions-preview"
                  value={preview.text}
                  readOnly
                  rows={10}
                />
              </>
            )}
            {draft.layers
              .filter((layer) => layer.origin !== editingOrigin)
              .map((layer, index) => (
                <p key={index}>
                  Retained layer {layer.origin}: {layer.mode} ·{" "}
                  {layer.roles.join(", ")}
                </p>
              ))}
          </details>
          <details>
            <summary data-testid="workflow-instructions-resources-toggle">
              Saved instruction resources
            </summary>
            {draft.assets.map((asset) => (
              <details key={asset.id}>
                <summary
                  data-testid={`workflow-instructions-resource-${asset.id}`}
                >
                  {asset.id} · {asset.role}
                </summary>
                <p>
                  Version {asset.version} · Origin {asset.origin} · SHA-256{" "}
                  {asset.body_digest}
                </p>
                <label>
                  {asset.id} instruction body
                  <textarea
                    rows={8}
                    value={asset.body}
                    data-testid={`workflow-instructions-resource-body-${asset.id}`}
                    disabled={disabled || asset.role === "protocol"}
                    onChange={(event) =>
                      change({
                        ...draft,
                        assets: draft.assets.map((item) =>
                          item.id === asset.id
                            ? { ...item, body: event.target.value }
                            : item,
                        ),
                      })
                    }
                  />
                </label>
                {asset.role === "protocol" && (
                  <p>
                    These instructions define how AI communicates with Wright.
                    They are read-only here; changes require a compatible
                    instruction update.
                  </p>
                )}
              </details>
            ))}
          </details>
          <button
            type="button"
            className="recovery-button recovery-button--primary"
            disabled={disabled}
            onClick={() => void save(draft)}
            data-testid="workflow-instructions-apply"
          >
            {busy
              ? "Applying…"
              : mode === "global"
                ? "Save instruction defaults"
                : "Apply workflow instructions"}
          </button>
        </>
      )}
      {onLoadDefaults && (
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          disabled={disabled}
          onClick={async () => {
            // Compare first; loading defaults never updates the accepted process.
            if (disabled) return;
            setBusy(true);
            setUpgrade(null);
            setError("");
            setMessage("");
            try {
              setProposed(await onLoadDefaults());
            } catch (error) {
              setError(
                error instanceof Error
                  ? error.message
                  : "Could not load current defaults.",
              );
            } finally {
              setBusy(false);
            }
          }}
        >
          {instructions
            ? "Update from current defaults…"
            : "Make instructions explicit…"}
        </button>
      )}
      {pending && (
        <section
          aria-label="Review instruction update"
          className="wright-instruction-diff"
        >
          <h3>Review instruction update</h3>
          <p>
            {upgrade
              ? "Compare the current collection with the proposed instruction compatibility upgrade. Missing versioned helper resources are added; your customized instruction text, role bindings, guidance and policy are retained."
              : "Compare the saved collection with the proposed current defaults. Your workflow guidance and assumption policy are retained."}
          </p>
          <p data-testid="workflow-instructions-action-intent-diff">
            MCP action intent contract: {actionIntentLabel(draft)} →{" "}
            {actionIntentLabel(pending)}
          </p>
          {upgrade && !upgrade.available && (
            <p role="status">
              This collection already includes the current instruction contracts
              and helper resources. No upgrade is needed.
            </p>
          )}
          <label>
            Current instructions
            <textarea
              readOnly
              rows={10}
              value={pretty(
                draft ?? { legacy: "Instruction text was not saved." },
              )}
            />
          </label>
          <label>
            Proposed instructions
            <textarea
              data-testid="workflow-instructions-proposed-collection"
              readOnly
              rows={10}
              value={pretty(pending)}
            />
          </label>
          <button
            type="button"
            className="recovery-button recovery-button--primary"
            disabled={disabled || upgrade?.available === false}
            onClick={() =>
              void save(
                pending,
                upgrade?.current_revision ?? proposed?.revision,
              )
            }
            data-testid="workflow-instructions-apply-update"
          >
            Apply reviewed instruction update
          </button>
          <button
            type="button"
            className="recovery-button recovery-button--quiet"
            disabled={disabled}
            onClick={() => {
              setProposed(null);
              setUpgrade(null);
            }}
            data-testid="workflow-instructions-cancel-update"
          >
            Cancel instruction update
          </button>
        </section>
      )}
      {onExport && (
        <>
          <button
            type="button"
            className="recovery-button recovery-button--secondary"
            disabled={!instructions || !exportReady || busy}
            data-testid="workflow-instructions-export-source"
            onClick={async () => {
              setError("");
              try {
                await onExport();
              } catch (error) {
                setError(
                  error instanceof Error
                    ? error.message
                    : "Could not export workflow.",
                );
              }
            }}
          >
            Export saved workflow source
          </button>
          <p>
            Source includes the accepted instructions. Reference files, provider
            setup and saved working interfaces need their own package. Save any
            workflow edits before exporting.
          </p>
        </>
      )}
      {proposalError && <p role="alert">{proposalError}</p>}
      {error && <p role="alert">{error}</p>}
      {message && <p role="status">{message}</p>}
    </section>
  );
}

export function WorkflowInstructionDefaultsCard() {
  const [document, setDocument] =
    useState<WorkflowInstructionDefaultsDocument | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [expectedRevision, setExpectedRevision] = useState("");
  const [message, setMessage] = useState("");
  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await workspaceService.getWorkflowInstructionDefaults();
      setDocument(result);
      setExpectedRevision(result.revision);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Could not load instruction defaults.",
      );
    } finally {
      setLoading(false);
    }
  };
  return (
    <section
      className="wright-instruction-defaults-card"
      aria-labelledby="instruction-defaults-title"
    >
      <h2 id="instruction-defaults-title">Workflow instruction defaults</h2>
      <p>
        Set how new workflows handle assumptions and AI instructions. These
        settings are stored by Wright and shared across browsers.
      </p>
      {!document && (
        <button
          type="button"
          className="recovery-button recovery-button--secondary"
          disabled={loading}
          onClick={() => void load()}
          data-testid="workflow-instruction-defaults-load"
        >
          {loading
            ? "Loading instruction defaults…"
            : "Load instruction defaults"}
        </button>
      )}
      {error && <p role="alert">{error}</p>}
      {document && (
        <WorkflowInstructionsEditor
          key={document.revision}
          mode="global"
          instructions={document.instructions}
          readOnly={loading}
          onLoadDefaults={async () => {
            const latest =
              await workspaceService.getWorkflowInstructionDefaults();
            return latest;
          }}
          onReviewActionIntentUpgrade={(current) =>
            workspaceService.proposeWorkflowActionIntentUpgrade(current)
          }
          onApply={async (value, reviewedRevision) => {
            const saved =
              await workspaceService.saveWorkflowInstructionDefaults(
                value,
                reviewedRevision ?? expectedRevision,
              );
            setDocument(saved);
            setExpectedRevision(saved.revision);
            setMessage(
              "Instruction defaults saved. Existing workflows retain their saved instructions.",
            );
            return true;
          }}
        />
      )}
      {message && <p role="status">{message}</p>}
    </section>
  );
}
