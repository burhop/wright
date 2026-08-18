import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import {
  CapabilityApiError,
  mcpService,
  type ImportPreview,
  type InstallPlan,
  type OnboardingRun,
  type CapabilityValidationEvidence,
  type CredentialStatusResponse,
  type WorkspaceCapabilityEnablement,
} from "../../services/mcp-service";
import {
  workspaceService,
  type WorkspaceInfo,
} from "../../services/workspace-service";

type SourceKind = "catalog" | "import" | "remote" | "local" | "host";
type WizardStep =
  | "source"
  | "normalizing"
  | "review"
  | "credentials"
  | "applying"
  | "validating"
  | "workspace"
  | "enabling"
  | "complete";

export interface CapabilityOnboardingHandoff {
  capabilityId: string;
  workspaceId: string;
  state: "workspace-enabled";
}

function errorMessage(error: unknown): string {
  if (error instanceof CapabilityApiError) {
    if (error.errorCode === "install_plan_source_invalid") {
      return "Choose an MCP server before continuing.";
    }
    if (error.errorCode === "onboarding_adapter_missing") {
      return "Wright could not start this installer. Return to requirements and create a fresh installation plan.";
    }
    return `${error.message} (${error.errorCode})${error.recovery ? ` ${error.recovery}` : ""}`;
  }
  return "The onboarding step could not be completed.";
}

const setupSteps: Array<{ step: WizardStep; label: string }> = [
  { step: "source", label: "Requirements" },
  { step: "review", label: "Review" },
  { step: "credentials", label: "Install" },
  { step: "workspace", label: "Workspace" },
];

const backendLabels: Record<string, string> = {
  host_bridge: "Engineering application bridge",
  remote_endpoint: "Remote MCP connection",
  local_package: "Local MCP package",
  local_command: "Local MCP command",
};

export function OnboardingWizard({
  isOpen,
  onClose,
  onCompleted,
  initialCapabilityId = "",
}: {
  isOpen: boolean;
  onClose: () => void;
  onCompleted?: (handoff: CapabilityOnboardingHandoff) => void;
  initialCapabilityId?: string;
}) {
  const [step, setStep] = useState<WizardStep>("source");
  const [sourceKind, setSourceKind] = useState<SourceKind>(
    initialCapabilityId ? "catalog" : "import",
  );
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
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [plan, setPlan] = useState<InstallPlan | null>(null);
  const [run, setRun] = useState<OnboardingRun | null>(null);
  const [credentialStatus, setCredentialStatus] =
    useState<CredentialStatusResponse | null>(null);
  const [validation, setValidation] =
    useState<CapabilityValidationEvidence | null>(null);
  const [workspaces, setWorkspaces] = useState<WorkspaceInfo[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [enablement, setEnablement] =
    useState<WorkspaceCapabilityEnablement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const dialog = useRef<HTMLDivElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setCapabilityId(initialCapabilityId);
      setSourceKind(initialCapabilityId ? "catalog" : "import");
      previousFocus.current = document.activeElement as HTMLElement | null;
      closeButton.current?.focus();
    }
  }, [initialCapabilityId, isOpen]);

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
  const catalogSelection = Boolean(initialCapabilityId);

  if (!isOpen) return null;

  const resetAndClose = () => {
    setStep("source");
    setPreview(null);
    setPlan(null);
    setRun(null);
    setCredentialStatus(null);
    setValidation(null);
    setWorkspaces([]);
    setSelectedWorkspaceId("");
    setEnablement(null);
    setError(null);
    onClose();
    window.setTimeout(() => previousFocus.current?.focus(), 0);
  };

  const keepFocusInDialog = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      resetAndClose();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(
      dialog.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
      ) || [],
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
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
        independently_completed_license: true,
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
      if (result.state !== "completed") {
        setStep("complete");
        return;
      }
      setStep("validating");
      const evidence = await mcpService.runCapabilityValidation(
        plan.capability_id,
      );
      setValidation(evidence);
      if (evidence.state !== "passed") {
        setStep("complete");
        return;
      }
      const availableWorkspaces = await workspaceService.getAllWorkspaces();
      setWorkspaces(availableWorkspaces);
      setSelectedWorkspaceId(
        plan.workspace_id || availableWorkspaces[0]?.workspace_id || "",
      );
      setStep(availableWorkspaces.length ? "workspace" : "complete");
    } catch (caught) {
      setError(errorMessage(caught));
      setStep("review");
    }
  };

  const continueToCredentials = async () => {
    if (!plan) return;
    setError(null);
    try {
      const status = await mcpService.getCredentialStatus(plan.capability_id);
      setCredentialStatus(status);
    } catch {
      setCredentialStatus(null);
    }
    setStep("credentials");
  };

  const enableWorkspace = async () => {
    if (!plan || !selectedWorkspaceId) return;
    setStep("enabling");
    setError(null);
    try {
      const result = await mcpService.enableCapabilityForWorkspace(
        plan.capability_id,
        selectedWorkspaceId,
      );
      setEnablement(result);
      setStep("complete");
      onCompleted?.({
        capabilityId: plan.capability_id,
        workspaceId: selectedWorkspaceId,
        state: "workspace-enabled",
      });
    } catch (caught) {
      setError(errorMessage(caught));
      setStep("workspace");
    }
  };

  return (
    <div
      ref={dialog}
      className="mcp-onboarding-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="onboarding-wizard-title"
      onKeyDown={keepFocusInDialog}
    >
      <section className="wright-form mcp-onboarding">
        <header className="mcp-onboarding__header">
          <div>
            <div className="mcp-onboarding__eyebrow">MCP server setup</div>
            <h2 id="onboarding-wizard-title">
              {catalogSelection
                ? "Install MCP server"
                : "Add custom MCP server"}
            </h2>
            <p>
              {catalogSelection
                ? "Review what Wright will add before anything changes."
                : "Add an MCP server that is not already in the library."}
            </p>
          </div>
          <button
            ref={closeButton}
            type="button"
            data-testid="onboarding-close"
            onClick={resetAndClose}
            aria-label="Close onboarding"
            className="mcp-onboarding__close"
          >
            <span aria-hidden="true">×</span>
          </button>
        </header>

        <nav className="mcp-onboarding__steps" aria-label="Setup progress">
          {setupSteps.map((item, index) => {
            const activeIndex = Math.max(
              0,
              setupSteps.findIndex((candidate) => candidate.step === step),
            );
            const isActive = item.step === step;
            const isComplete = index < activeIndex;
            return (
              <div
                key={item.step}
                className={`mcp-onboarding__step${isActive ? " is-active" : ""}${isComplete ? " is-complete" : ""}`}
                aria-current={isActive ? "step" : undefined}
              >
                <span>{isComplete ? "✓" : index + 1}</span>
                {item.label}
              </div>
            );
          })}
        </nav>
        {error && (
          <div role="alert" className="mcp-onboarding__alert">
            {error}
          </div>
        )}

        <div className="mcp-onboarding__body">
          {step === "source" && (
            <div style={{ display: "grid", gap: "var(--space-md)" }}>
              {catalogSelection ? (
                <div
                  data-testid="onboarding-selected-server"
                  style={{
                    padding: "var(--space-md)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-lg)",
                    background: "var(--color-surface-subtle)",
                  }}
                >
                  <strong>Selected server</strong>
                  <div style={{ marginTop: 4 }}>{capabilityId}</div>
                </div>
              ) : (
                <>
                  <p>
                    This check is read-only. It does not install software,
                    connect an account, or enable tools.
                  </p>
                  <label>
                    Source
                    <select
                      data-testid="onboarding-source-kind"
                      value={sourceKind}
                      onChange={(event) =>
                        setSourceKind(event.target.value as SourceKind)
                      }
                    >
                      <option value="import">Paste MCP configuration</option>
                      <option value="remote">Remote MCP endpoint</option>
                      <option value="local">Advanced local command</option>
                      <option value="host">Engineering host bridge</option>
                    </select>
                  </label>
                </>
              )}
              {(sourceKind === "catalog" || sourceKind === "host") && (
                <label
                  style={{ display: catalogSelection ? "none" : undefined }}
                >
                  MCP server ID
                  <input
                    data-testid="onboarding-capability-id"
                    value={capabilityId}
                    onChange={(event) => setCapabilityId(event.target.value)}
                    readOnly={catalogSelection}
                  />
                </label>
              )}
              {sourceKind === "import" && (
                <label>
                  MCP configuration JSON
                  <textarea
                    data-testid="onboarding-configuration"
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
                    data-testid="onboarding-display-name"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                  />
                </label>
              )}
              {sourceKind === "remote" && (
                <label>
                  HTTPS MCP endpoint
                  <input
                    data-testid="onboarding-endpoint"
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
                      data-testid="onboarding-command"
                      value={command}
                      onChange={(event) => setCommand(event.target.value)}
                    />
                  </label>
                  <label>
                    Literal arguments
                    <input
                      data-testid="onboarding-arguments"
                      value={argumentsText}
                      onChange={(event) => setArgumentsText(event.target.value)}
                    />
                  </label>
                </>
              )}
              <label>
                Use in
                <select
                  data-testid="onboarding-scope"
                  value={scope}
                  onChange={(event) =>
                    setScope(event.target.value as typeof scope)
                  }
                >
                  <option value="global_registered">All workspaces</option>
                  <option value="workspace">One workspace now</option>
                </select>
              </label>
              {scope === "workspace" && (
                <label>
                  Workspace ID
                  <input
                    data-testid="onboarding-workspace-id"
                    value={workspaceId}
                    onChange={(event) => setWorkspaceId(event.target.value)}
                  />
                </label>
              )}
              <button
                type="button"
                className="wright-form__primary"
                data-testid="onboarding-create-plan"
                onClick={buildPlan}
                disabled={
                  (sourceKind === "catalog" || sourceKind === "host") &&
                  !capabilityId.trim()
                }
              >
                Review install plan
              </button>
            </div>
          )}

          {step === "normalizing" && (
            <p role="status">
              Normalizing the source and checking this machine without
              installing or connecting…
            </p>
          )}

          {step === "review" && plan && (
            <div
              data-testid="onboarding-plan-review"
              className="mcp-plan-review"
            >
              <div className="mcp-plan-review__heading">
                <div>
                  <div className="mcp-onboarding__eyebrow">
                    Ready for review
                  </div>
                  <h3>Confirm this installation</h3>
                </div>
                <span className={`mcp-plan-review__state ${plan.state}`}>
                  {plan.state === "reviewable" ? "Ready" : "Needs attention"}
                </span>
              </div>
              <p className="mcp-plan-review__intro">
                {plan.state === "reviewable"
                  ? "Nothing has been installed yet. Review the changes below, then continue when they look right."
                  : "One requirement needs attention before installation can continue."}
              </p>
              {preview && (
                <p>
                  Normalized {preview.drafts.length} imported MCP definition.
                </p>
              )}
              <div className="mcp-plan-review__summary">
                <div>
                  <span>Server</span>
                  <strong>{capabilityId || "Custom MCP server"}</strong>
                </div>
                <div>
                  <span>Connection</span>
                  <strong>
                    {backendLabels[plan.backend_kind] || "MCP server"}
                  </strong>
                </div>
                <div>
                  <span>Available in</span>
                  <strong>
                    {scope === "workspace"
                      ? workspaceId || "Selected workspace"
                      : "All workspaces"}
                  </strong>
                </div>
              </div>
              <h4>What Wright will do</h4>
              <ol className="mcp-plan-review__effects">
                {plan.effects.map((effect) => (
                  <li key={String(effect.step_id)}>
                    <span aria-hidden="true">✓</span>
                    <div>{String(effect.description)}</div>
                  </li>
                ))}
              </ol>
              {plan.blocking_reasons.length > 0 && (
                <div role="alert" className="mcp-plan-review__blocker">
                  <h4>Why installation cannot continue yet</h4>
                  {plan.blocking_reasons.map((reason) => (
                    <div key={reason.code}>
                      <p>
                        <strong>Reason:</strong> {reason.message}
                      </p>
                      <p>
                        <strong>What to do:</strong> {reason.recovery}
                      </p>
                    </div>
                  ))}
                </div>
              )}
              <footer className="mcp-onboarding__footer">
                {plan.state !== "reviewable" ? (
                  <button
                    type="button"
                    className="wright-form__primary"
                    data-testid="onboarding-review-back"
                    onClick={() => setStep("source")}
                  >
                    Return to requirements
                  </button>
                ) : (
                  <>
                    <button
                      type="button"
                      data-testid="onboarding-review-back"
                      onClick={() => setStep("source")}
                    >
                      Back to requirements
                    </button>{" "}
                    <button
                      type="button"
                      className="wright-form__primary"
                      data-testid="onboarding-review-continue"
                      onClick={continueToCredentials}
                    >
                      Continue to installation
                    </button>
                  </>
                )}
              </footer>
            </div>
          )}

          {step === "credentials" && plan && (
            <div>
              <h3>Credential boundary</h3>
              {plan.requirements.credentials.length ? (
                <>
                  <p>
                    Required credential names:{" "}
                    {plan.requirements.credentials.join(", ")}. Values are saved
                    only through Wright&apos;s secure credential flow and are
                    never included in this plan.
                  </p>
                  <ul data-testid="credential-configuration-status">
                    {plan.requirements.credentials.map((credential) => (
                      <li key={credential}>
                        {credential}:{" "}
                        {credentialStatus?.configured[credential]
                          ? "configured"
                          : "not configured"}
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p>This plan does not declare credential values.</p>
              )}
              <button
                type="button"
                data-testid="onboarding-credentials-back"
                onClick={() => setStep("review")}
              >
                Back to plan
              </button>{" "}
              <button
                type="button"
                className="wright-form__primary"
                data-testid="onboarding-apply-plan"
                onClick={applyPlan}
              >
                Install MCP server
              </button>
            </div>
          )}

          {step === "applying" && (
            <p role="status">
              Applying the approved plan with rollback tracking…
            </p>
          )}

          {step === "validating" && (
            <p role="status">
              Validating MCP initialize, initialized notification, tool
              discovery, and any catalog-approved read-only probe…
            </p>
          )}

          {step === "workspace" && validation?.state === "passed" && (
            <div data-testid="workspace-selection">
              <h3>Choose one workspace</h3>
              <p>
                Validation passed with {validation.tool_count ?? 0} discovered
                tools. Available in a workspace does not mean approved to run
                every tool.
              </p>
              <label>
                Workspace
                <select
                  data-testid="onboarding-workspace-select"
                  value={selectedWorkspaceId}
                  onChange={(event) =>
                    setSelectedWorkspaceId(event.target.value)
                  }
                >
                  {workspaces.map((workspace) => (
                    <option
                      key={workspace.workspace_id}
                      value={workspace.workspace_id}
                    >
                      {workspace.workspace_name || workspace.workspace_id}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="wright-form__primary"
                data-testid="onboarding-enable-workspace"
                onClick={enableWorkspace}
              >
                Make available in this workspace
              </button>
            </div>
          )}

          {step === "enabling" && (
            <p role="status">
              Making this MCP server available in one workspace only…
            </p>
          )}

          {step === "complete" && run && (
            <div>
              <h3>
                {validation && validation.state !== "passed"
                  ? "Installation completed; validation failed"
                  : `Onboarding ${run.state}`}
              </h3>
              <p>
                Run {run.run_id} finished with rollback state{" "}
                {run.rollback_state || "not needed"}.
              </p>
              {validation && validation.state !== "passed" && (
                <p role="alert">
                  Wright registered the MCP server, but could not complete the
                  protocol validation. It was not enabled in a workspace. Review
                  the validation result and retry after the server is available
                  and authenticated.
                </p>
              )}
              {validation && (
                <p>
                  Validation: {validation.state}
                  {validation.read_only_probe
                    ? ` — ${validation.read_only_probe.limitation}`
                    : ""}
                </p>
              )}
              {enablement && <p>{enablement.message}</p>}
              <button
                type="button"
                data-testid="onboarding-done"
                onClick={resetAndClose}
              >
                Done
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
