import { useEffect, useMemo, useRef, useState } from "react";
import {
  CapabilityApiError,
  mcpService,
  type ImportPreview,
  type InstallPlan,
  type OnboardingRun,
} from "../../services/mcp-service";

type SourceKind = "catalog" | "import" | "remote" | "local" | "host";
type WizardStep =
  "source" | "normalizing" | "review" | "credentials" | "applying" | "complete";

function errorMessage(error: unknown): string {
  if (error instanceof CapabilityApiError) {
    return `${error.message} (${error.errorCode})${error.recovery ? ` ${error.recovery}` : ""}`;
  }
  return "The onboarding step could not be completed.";
}

export function OnboardingWizard({
  isOpen,
  onClose,
  onCompleted,
  initialCapabilityId = "",
}: {
  isOpen: boolean;
  onClose: () => void;
  onCompleted?: () => void;
  initialCapabilityId?: string;
}) {
  const [step, setStep] = useState<WizardStep>("source");
  const [sourceKind, setSourceKind] = useState<SourceKind>("catalog");
  const [capabilityId, setCapabilityId] = useState(initialCapabilityId);
  const [configuration, setConfiguration] = useState("");
  const [name, setName] = useState("Imported MCP");
  const [endpoint, setEndpoint] = useState("");
  const [command, setCommand] = useState("");
  const [argumentsText, setArgumentsText] = useState("");
  const [scope, setScope] = useState<"global_registered" | "workspace">(
    "global_registered",
  );
  const [workspaceId, setWorkspaceId] = useState("");
  const [externalCompleted, setExternalCompleted] = useState(false);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [plan, setPlan] = useState<InstallPlan | null>(null);
  const [run, setRun] = useState<OnboardingRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeButton = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen) closeButton.current?.focus();
  }, [isOpen]);

  const normalizedConfiguration = useMemo(() => {
    if (sourceKind === "import") return configuration;
    if (sourceKind === "remote") {
      return JSON.stringify({ name, type: "http", url: endpoint });
    }
    if (sourceKind === "local") {
      return JSON.stringify({
        name,
        command,
        args: argumentsText.split(/\s+/).filter(Boolean),
      });
    }
    return "";
  }, [argumentsText, command, configuration, endpoint, name, sourceKind]);

  if (!isOpen) return null;

  const resetAndClose = () => {
    setStep("source");
    setPreview(null);
    setPlan(null);
    setRun(null);
    setError(null);
    onClose();
  };

  const buildPlan = async () => {
    setError(null);
    setStep("normalizing");
    try {
      const sourceRequest: Record<string, string> = {};
      if (sourceKind === "catalog" || sourceKind === "host") {
        sourceRequest.capability_id = capabilityId.trim();
      } else {
        const normalized = await mcpService.previewImport(
          normalizedConfiguration,
        );
        setPreview(normalized);
        const draft = normalized.drafts[0];
        if (!draft)
          throw new Error("No MCP server was found in the configuration.");
        sourceRequest.import_preview_id = normalized.preview_id;
        sourceRequest.draft_id = draft.draft_id;
        sourceRequest.draft_digest = draft.draft_digest;
      }
      const created = await mcpService.createInstallPlan({
        ...sourceRequest,
        requested_scope: scope,
        workspace_id: scope === "workspace" ? workspaceId.trim() : undefined,
        independently_completed_license: externalCompleted,
      });
      setPlan(created);
      setStep("review");
    } catch (caught) {
      setError(errorMessage(caught));
      setStep("source");
    }
  };

  const applyPlan = async () => {
    if (!plan) return;
    setStep("applying");
    setError(null);
    try {
      const approved = await mcpService.approveInstallPlan(
        plan.plan_id,
        plan.plan_digest,
      );
      setPlan(approved);
      const result = await mcpService.applyInstallPlan(
        approved.plan_id,
        approved.plan_digest,
      );
      setRun(result);
      setStep("complete");
      if (result.state === "completed") onCompleted?.();
    } catch (caught) {
      setError(errorMessage(caught));
      setStep("review");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-wizard-title"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 1200,
        background: "rgba(0, 0, 0, 0.66)",
        display: "grid",
        placeItems: "center",
        padding: "var(--space-lg)",
      }}
    >
      <section
        style={{
          width: "min(760px, 100%)",
          maxHeight: "90vh",
          overflowY: "auto",
          background: "var(--color-neutral)",
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--space-xl)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            gap: "var(--space-lg)",
          }}
        >
          <div>
            <h2 id="onboarding-wizard-title" style={{ margin: 0 }}>
              Add an engineering capability
            </h2>
            <p style={{ color: "var(--color-text-muted)" }}>
              Review an exact plan before Wright makes any change.
            </p>
          </div>
          <button
            ref={closeButton}
            type="button"
            onClick={resetAndClose}
            aria-label="Close onboarding"
          >
            Close
          </button>
        </div>

        <div role="status" aria-live="polite">
          Step: {step}
        </div>
        {error && <div role="alert">{error}</div>}

        {step === "source" && (
          <div style={{ display: "grid", gap: "var(--space-md)" }}>
            <label>
              Source
              <select
                value={sourceKind}
                onChange={(event) =>
                  setSourceKind(event.target.value as SourceKind)
                }
              >
                <option value="catalog">Capability Library</option>
                <option value="import">Paste MCP configuration</option>
                <option value="remote">Remote MCP endpoint</option>
                <option value="local">Advanced local command</option>
                <option value="host">Engineering host bridge</option>
              </select>
            </label>
            {(sourceKind === "catalog" || sourceKind === "host") && (
              <label>
                Capability ID
                <input
                  value={capabilityId}
                  onChange={(event) => setCapabilityId(event.target.value)}
                />
              </label>
            )}
            {sourceKind === "import" && (
              <label>
                MCP configuration JSON
                <textarea
                  rows={9}
                  value={configuration}
                  onChange={(event) => setConfiguration(event.target.value)}
                />
              </label>
            )}
            {(sourceKind === "remote" || sourceKind === "local") && (
              <label>
                Display name
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                />
              </label>
            )}
            {sourceKind === "remote" && (
              <label>
                HTTPS MCP endpoint
                <input
                  value={endpoint}
                  onChange={(event) => setEndpoint(event.target.value)}
                />
              </label>
            )}
            {sourceKind === "local" && (
              <>
                <label>
                  Literal executable
                  <input
                    value={command}
                    onChange={(event) => setCommand(event.target.value)}
                  />
                </label>
                <label>
                  Literal arguments
                  <input
                    value={argumentsText}
                    onChange={(event) => setArgumentsText(event.target.value)}
                  />
                </label>
              </>
            )}
            <label>
              Availability
              <select
                value={scope}
                onChange={(event) =>
                  setScope(event.target.value as typeof scope)
                }
              >
                <option value="global_registered">Register only</option>
                <option value="workspace">One workspace</option>
              </select>
            </label>
            {scope === "workspace" && (
              <label>
                Workspace ID
                <input
                  value={workspaceId}
                  onChange={(event) => setWorkspaceId(event.target.value)}
                />
              </label>
            )}
            {(sourceKind === "catalog" || sourceKind === "host") && (
              <label>
                <input
                  type="checkbox"
                  checked={externalCompleted}
                  onChange={(event) =>
                    setExternalCompleted(event.target.checked)
                  }
                />{" "}
                I independently completed any publisher terms shown in the
                Capability Library
              </label>
            )}
            <button type="button" onClick={buildPlan}>
              Create read-only plan
            </button>
          </div>
        )}

        {step === "normalizing" && (
          <p role="status">
            Normalizing the source and checking this machine without installing
            or connecting…
          </p>
        )}

        {step === "review" && plan && (
          <div data-testid="onboarding-plan-review">
            <h3>Review exact plan</h3>
            <p>
              Backend: <strong>{plan.backend_kind}</strong> · State:{" "}
              <strong>{plan.state}</strong>
            </p>
            {preview && (
              <p>Normalized {preview.drafts.length} imported MCP definition.</p>
            )}
            <h4>Planned effects</h4>
            <ol>
              {plan.effects.map((effect) => (
                <li key={String(effect.step_id)}>
                  {String(effect.description)}
                </li>
              ))}
            </ol>
            {plan.blocking_reasons.length > 0 && (
              <div role="alert">
                <h4>Plan is blocked</h4>
                {plan.blocking_reasons.map((reason) => (
                  <p key={reason.code}>
                    {reason.message} {reason.recovery}
                  </p>
                ))}
              </div>
            )}
            <button type="button" onClick={() => setStep("source")}>
              Back
            </button>{" "}
            <button
              type="button"
              disabled={plan.state !== "reviewable"}
              onClick={() => setStep("credentials")}
            >
              Continue to credentials
            </button>
          </div>
        )}

        {step === "credentials" && plan && (
          <div>
            <h3>Credential boundary</h3>
            {plan.requirements.credentials.length ? (
              <p>
                Required credential names:{" "}
                {plan.requirements.credentials.join(", ")}. Values are saved
                only through Wright&apos;s secure credential flow and are never
                included in this plan.
              </p>
            ) : (
              <p>This plan does not declare credential values.</p>
            )}
            <button type="button" onClick={() => setStep("review")}>
              Back to plan
            </button>{" "}
            <button type="button" onClick={applyPlan}>
              Approve and apply exact plan
            </button>
          </div>
        )}

        {step === "applying" && (
          <p role="status">
            Applying the approved plan with rollback tracking…
          </p>
        )}

        {step === "complete" && run && (
          <div>
            <h3>Onboarding {run.state}</h3>
            <p>
              Run {run.run_id} finished with rollback state{" "}
              {run.rollback_state || "not needed"}.
            </p>
            <button type="button" onClick={resetAndClose}>
              Done
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
