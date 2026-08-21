import { useEffect, useRef, type KeyboardEvent } from "react";
import type { CapabilityView } from "../../services/mcp-service";
import {
  CompatibilityBadge,
  EvidenceBadge,
  getSetupStatus,
} from "./CapabilityBadges";
import { WindowsQualificationSummary } from "./WindowsQualificationSummary";

export function CapabilityDetails({
  capability,
  observing,
  onObserve,
  onPlan,
  onClose,
}: {
  capability: CapabilityView;
  observing: boolean;
  onObserve: () => void;
  onPlan?: () => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const dataTouched = capability.data_touched || [];
  const examples = capability.examples || [];
  const validationHistory = capability.validation_history || [];
  const hostSoftware = capability.requirements.host_software || [];
  const credentials = capability.requirements.credentials || [];
  const approvalGates = capability.requirements.approval_gates || [];
  const dependencies = capability.requirements.dependencies || {};
  const supportedPlatforms = capability.requirements.supported_platforms || {};
  const firstReason = capability.compatibility.reasons[0];
  const summaries = capability.capability_summary.length
    ? capability.capability_summary
    : [capability.description];
  const setupStatus = getSetupStatus(capability);

  useEffect(() => {
    previousFocus.current = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    return () => previousFocus.current?.focus();
  }, []);

  const keepFocusInDialog = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Escape") {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key !== "Tab") return;
    const focusable = Array.from(
      dialog.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), a[href], summary, [tabindex]:not([tabindex="-1"])',
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

  return (
    <>
      <div
        className="capability-dialog-backdrop"
        data-testid="capability-details-backdrop"
        aria-hidden="true"
        onClick={onClose}
      />
      <aside
        ref={dialog}
        className="capability-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="capability-details-title"
        onKeyDown={keepFocusInDialog}
      >
        <header className="capability-dialog__header">
          <div className="capability-dialog__identity">
            <div className="capability-dialog__eyebrow">MCP server</div>
            <h2 id="capability-details-title">{capability.name}</h2>
            <p>By {capability.vendor}</p>
            <div className="capability-dialog__badges">
              <EvidenceBadge value={capability.evidence_class} />
              <CompatibilityBadge capability={capability} />
            </div>
          </div>
          <button
            ref={closeButton}
            className="capability-dialog__close"
            type="button"
            data-testid="capability-details-close"
            onClick={onClose}
            aria-label="Close MCP server details"
            title="Close"
          >
            ×
          </button>
        </header>

        <div className="capability-dialog__content">
          <section className="capability-dialog__overview">
            <p className="capability-dialog__description">
              {capability.description}
            </p>
            <h3>What this server can do</h3>
            <ul className="capability-dialog__capabilities">
              {summaries.map((summary) => (
                <li key={summary}>
                  <span aria-hidden="true">✓</span>
                  <span>{summary}</span>
                </li>
              ))}
            </ul>
            <div className="capability-dialog__data-notice">
              <strong>Data it may access</strong>
              <p>
                {dataTouched.length
                  ? dataTouched.join(", ")
                  : "The available evidence does not specify what data it reads or changes."}
              </p>
            </div>
            {capability.windows_qualification ? (
              <WindowsQualificationSummary
                summary={capability.windows_qualification}
              />
            ) : null}
          </section>

          <aside
            className="capability-dialog__sidebar"
            aria-label="Setup summary"
          >
            <section className="capability-dialog__fit">
              <div className="capability-dialog__section-label">
                This computer
              </div>
              <h3 data-testid="capability-fit-summary">{setupStatus.label}</h3>
              <p>{setupStatus.summary}</p>
              {firstReason?.message ? <p>{firstReason.message}</p> : null}
              {firstReason?.recovery ? (
                <p className="capability-dialog__recovery">
                  {firstReason.recovery}
                </p>
              ) : null}
              <button
                type="button"
                className="capability-dialog__check"
                data-testid="capability-observe-machine"
                disabled={observing}
                onClick={onObserve}
              >
                {observing ? "Checking…" : "Check this computer"}
              </button>
            </section>

            <section className="capability-dialog__requirements">
              <div className="capability-dialog__section-label">
                Requirements
              </div>
              <dl data-testid="capability-simple-requirements">
                <div>
                  <dt>Software</dt>
                  <dd>
                    {hostSoftware.length
                      ? hostSoftware.join(", ")
                      : "No additional software listed"}
                  </dd>
                </div>
                <div>
                  <dt>Account or keys</dt>
                  <dd>
                    {credentials.length
                      ? credentials.join(", ")
                      : "None listed"}
                  </dd>
                </div>
                <div>
                  <dt>License</dt>
                  <dd>
                    {capability.requirements.license ||
                      "Not specified by the publisher"}
                  </dd>
                </div>
              </dl>
            </section>
          </aside>
        </div>

        <details className="capability-dialog__technical">
          <summary>Technical evidence and requirements</summary>
          <div className="capability-dialog__technical-grid">
            <section>
              <h3>Examples</h3>
              {examples.length ? (
                <ul>
                  {examples.map((example) => (
                    <li key={example}>{example}</li>
                  ))}
                </ul>
              ) : (
                <p>No reviewed examples are available.</p>
              )}
              <h3>Policy requirements</h3>
              <dl>
                <dt>Approval gates</dt>
                <dd>
                  {approvalGates.length
                    ? approvalGates.join(", ")
                    : "None listed"}
                </dd>
                <dt>Dependencies</dt>
                <dd>
                  {Object.values(dependencies).flat().length
                    ? Object.entries(dependencies)
                        .filter(([, values]) => values.length)
                        .map(
                          ([kind, values]) => `${kind}: ${values.join(", ")}`,
                        )
                        .join("; ")
                    : "None listed"}
                </dd>
              </dl>
            </section>
            <section>
              <h3>Supported platforms</h3>
              {Object.keys(supportedPlatforms).length ? (
                <ul>
                  {Object.entries(supportedPlatforms).map(
                    ([platform, support]) => (
                      <li key={platform}>
                        {platform}: {support.status}
                        {support.notes ? ` — ${support.notes}` : ""}
                      </li>
                    ),
                  )}
                </ul>
              ) : (
                <p>No platform claims are available.</p>
              )}
              <h3>Validation</h3>
              <p>{capability.validation_result.message}</p>
              <ul data-testid="capability-validation-history">
                {validationHistory.map((item, index) => (
                  <li key={`${String(item.status)}-${index}`}>
                    {String(item.status)}
                    {item.message ? ` — ${String(item.message)}` : ""}
                  </li>
                ))}
              </ul>
              {capability.local_validation ? (
                <div data-testid="local-validation-summary">
                  <p>
                    Local validation:{" "}
                    <strong>{capability.local_validation.state}</strong>
                    {` at ${capability.local_validation.observed_at}`}
                  </p>
                  {capability.local_validation.limitation ? (
                    <p>Limitation: {capability.local_validation.limitation}</p>
                  ) : null}
                </div>
              ) : (
                <p>
                  No current local MCP protocol validation has been recorded.
                </p>
              )}
            </section>
          </div>
          <h3>Sources</h3>
          <ul>
            {capability.source_records.map((source) => (
              <li key={source.url}>
                <a
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  data-testid="capability-source-link"
                >
                  {source.kind.replace("_", " ")} · {source.authority}
                </a>
                {source.notes ? ` — ${source.notes}` : ""}
              </li>
            ))}
          </ul>
          <h3>Field provenance</h3>
          <dl>
            {Object.entries(capability.field_provenance || {}).map(
              ([field, source]) => (
                <div key={field}>
                  <dt>{field.replaceAll("_", " ")}</dt>
                  <dd>{source.replaceAll("_", " ")}</dd>
                </div>
              ),
            )}
          </dl>
          {capability.alternatives.length ? (
            <>
              <h3>Compatible alternatives</h3>
              <p>{capability.alternatives.join(", ")}</p>
            </>
          ) : null}
          {capability.user_state.enabled_workspaces.length ? (
            <>
              <h3>Available in workspaces</h3>
              <ul>
                {capability.user_state.enabled_workspaces.map((workspace) => (
                  <li key={workspace.workspace_id}>{workspace.label}</li>
                ))}
              </ul>
              <p>
                Workspace availability does not approve individual tool calls or
                destructive actions.
              </p>
            </>
          ) : null}
        </details>

        <footer className="capability-dialog__footer">
          <button
            type="button"
            className="capability-dialog__secondary"
            onClick={onClose}
          >
            Not now
          </button>
          {onPlan ? (
            <button
              type="button"
              className="capability-dialog__install"
              data-testid="capability-plan"
              onClick={onPlan}
            >
              Install MCP server
            </button>
          ) : null}
        </footer>
      </aside>
    </>
  );
}
