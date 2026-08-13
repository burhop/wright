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
  const hostSoftware = capability.requirements.host_software || [];
  const credentials = capability.requirements.credentials || [];
  return (
    <aside
      role="dialog"
      aria-modal="true"
      aria-labelledby="capability-details-title"
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
          type="button"
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
      <button type="button" disabled={observing} onClick={onObserve}>
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
      </dl>

      <h3>Evidence and validation</h3>
      <p>{capability.validation_result.message}</p>
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
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.kind.replace("_", " ")} · {source.authority}
            </a>
            {source.notes ? ` — ${source.notes}` : ""}
          </li>
        ))}
      </ul>

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
