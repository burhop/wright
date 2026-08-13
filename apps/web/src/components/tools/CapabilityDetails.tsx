import { useEffect, useRef, type KeyboardEvent } from "react";
import type { CapabilityView } from "../../services/mcp-service";
import { CompatibilityBadge, EvidenceBadge } from "./CapabilityBadges";

export function CapabilityDetails({
  capability,
  observing,
  onObserve,
  onClose,
}: {
  capability: CapabilityView;
  observing: boolean;
  onObserve: () => void;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLElement>(null);
  const closeButton = useRef<HTMLButtonElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const dataTouched = capability.data_touched || [];
  const examples = capability.examples || [];
  const validationHistory = capability.validation_history || [];
  const fieldProvenance = capability.field_provenance || {};
  const hostSoftware = capability.requirements.host_software || [];
  const credentials = capability.requirements.credentials || [];
  const approvalGates = capability.requirements.approval_gates || [];
  const dependencies = capability.requirements.dependencies || {};
  const supportedPlatforms = capability.requirements.supported_platforms || {};

  useEffect(() => {
    previousFocus.current = document.activeElement as HTMLElement | null;
    closeButton.current?.focus();
    return () => {
      previousFocus.current?.focus();
    };
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
  return (
    <aside
      ref={dialog}
      role="dialog"
      aria-modal="true"
      aria-labelledby="capability-details-title"
      onKeyDown={keepFocusInDialog}
      style={{
        position: "fixed",
        inset: "5vh 3vw 5vh auto",
        width: "min(560px, 90vw)",
        overflowY: "auto",
        zIndex: 100,
        padding: "var(--space-xl)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        background: "var(--color-neutral)",
        boxShadow: "var(--shadow-elevated)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: "var(--space-md)",
        }}
      >
        <div>
          <h2 id="capability-details-title" style={{ marginTop: 0 }}>
            {capability.name}
          </h2>
          <p style={{ color: "var(--color-text-dim)" }}>{capability.vendor}</p>
        </div>
        <button
          ref={closeButton}
          type="button"
          data-testid="capability-details-close"
          onClick={onClose}
          aria-label="Close capability details"
        >
          Close
        </button>
      </div>
      <div
        style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}
      >
        <EvidenceBadge value={capability.evidence_class} />
        <CompatibilityBadge value={capability.compatibility.status} />
      </div>

      <h3>What it can do</h3>
      <ul>
        {(capability.capability_summary.length
          ? capability.capability_summary
          : [capability.description]
        ).map((summary) => (
          <li key={summary}>{summary}</li>
        ))}
      </ul>

      <h3>Data touched</h3>
      {dataTouched.length ? (
        <ul>
          {dataTouched.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>Not specified by the available catalog evidence.</p>
      )}

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

      <h3>Current machine</h3>
      <p>{capability.compatibility.platform_key}</p>
      {capability.compatibility.reasons.length ? (
        <ul>
          {capability.compatibility.reasons.map((reason) => (
            <li key={`${reason.code}-${reason.message}`}>
              <strong>{reason.message}</strong>
              <br />
              <span>{reason.recovery}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>All mandatory observed requirements are satisfied.</p>
      )}
      <button
        type="button"
        data-testid="capability-observe-machine"
        disabled={observing}
        onClick={onObserve}
      >
        {observing ? "Checking this machine…" : "Check this machine again"}
      </button>

      <h3>Requirements</h3>
      <dl>
        <dt>Host software</dt>
        <dd>{hostSoftware.length ? hostSoftware.join(", ") : "None listed"}</dd>
        <dt>Credentials</dt>
        <dd>{credentials.length ? credentials.join(", ") : "None listed"}</dd>
        <dt>License or terms</dt>
        <dd>{capability.requirements.license || "Not specified"}</dd>
        <dt>Approval gates</dt>
        <dd>
          {approvalGates.length ? approvalGates.join(", ") : "None listed"}
        </dd>
        <dt>Dependencies</dt>
        <dd>
          {Object.values(dependencies).flat().length
            ? Object.entries(dependencies)
                .filter(([, values]) => values.length)
                .map(([kind, values]) => `${kind}: ${values.join(", ")}`)
                .join("; ")
            : "None listed"}
        </dd>
      </dl>

      <h3>Supported platforms</h3>
      {Object.keys(supportedPlatforms).length ? (
        <ul>
          {Object.entries(supportedPlatforms).map(([platform, support]) => (
            <li key={platform}>
              {platform}: {support.status}
              {support.notes ? ` — ${support.notes}` : ""}
            </li>
          ))}
        </ul>
      ) : (
        <p>No platform claims are available.</p>
      )}

      <h3>Evidence and validation</h3>
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
            <strong>{capability.local_validation.state}</strong> at{" "}
            {capability.local_validation.observed_at}
          </p>
          {capability.local_validation.limitation && (
            <p>Limitation: {capability.local_validation.limitation}</p>
          )}
          {capability.local_validation.reason_codes.length > 0 && (
            <p>
              Reasons: {capability.local_validation.reason_codes.join(", ")}
            </p>
          )}
        </div>
      ) : (
        <p>No current local MCP protocol validation has been recorded.</p>
      )}
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
        {Object.entries(fieldProvenance).map(([field, source]) => (
          <div key={field}>
            <dt>{field.replaceAll("_", " ")}</dt>
            <dd>{source.replaceAll("_", " ")}</dd>
          </div>
        ))}
      </dl>

      {capability.alternatives.length > 0 && (
        <>
          <h3>Compatible alternatives</h3>
          <p>{capability.alternatives.join(", ")}</p>
        </>
      )}
      {capability.user_state.enabled_workspaces.length > 0 && (
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
      )}
    </aside>
  );
}
