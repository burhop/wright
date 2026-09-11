import type { CapabilityView } from "../../services/mcp-service";
import { CompatibilityBadge, EvidenceBadge } from "./CapabilityBadges";
import { capabilityFacts } from "./CapabilityFacts";

export function CapabilityCard({
  capability,
  onOpen,
  onInstall,
}: {
  capability: CapabilityView;
  onOpen: (capability: CapabilityView) => void;
  onInstall?: (capabilityId: string) => void;
}) {
  const firstReason = capability.compatibility.reasons[0];
  const facts = capabilityFacts(capability);
  return (
    <article
      data-testid={`capability-card-${capability.capability_id}`}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-md)",
        minHeight: "250px",
        padding: "var(--space-lg)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        background: "var(--color-surface-subtle)",
      }}
    >
      <div
        style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}
      >
        <EvidenceBadge value={capability.evidence_class} />
        {capability.curation && (
          <span data-testid="capability-curation-status">
            {
              {
                curated: "Curated",
                follow_up: "Follow up",
                removed: "Removed from discovery",
              }[capability.curation.effective_disposition]
            }
          </span>
        )}
        <CompatibilityBadge capability={capability} />
        {facts.openSource && <span>Open source</span>}
        {facts.commercial && <span>Commercial software / service</span>}
      </div>
      <div>
        <h2 style={{ fontSize: "1.08rem", margin: 0 }}>{capability.name}</h2>
        <p style={{ color: "var(--color-text-muted)", margin: "4px 0 0" }}>
          {capability.vendor} · {capability.transport.replace("_", " ")}
        </p>
      </div>
      <p style={{ margin: 0, lineHeight: 1.5 }}>{capability.description}</p>
      <dl
        style={{
          display: "grid",
          gridTemplateColumns: "65px 1fr",
          gap: "6px 12px",
          margin: 0,
          fontSize: "0.85rem",
        }}
      >
        <dt style={{ color: "var(--color-text-muted)" }}>Cost</dt>
        <dd style={{ margin: 0 }}>{facts.cost}</dd>
        <dt style={{ color: "var(--color-text-muted)" }}>Login</dt>
        <dd style={{ margin: 0 }}>{facts.login}</dd>
        <dt style={{ color: "var(--color-text-muted)" }}>Runs on</dt>
        <dd style={{ margin: 0 }}>{facts.location}</dd>
      </dl>
      {capability.curation && (
        <p
          style={{
            margin: 0,
            color: "var(--color-text-muted)",
            fontSize: "0.85rem",
          }}
        >
          {capability.curation.reason}
          {capability.curation.review_overdue && " Review overdue."}
        </p>
      )}
      {firstReason && (
        <p
          data-testid="capability-primary-reason"
          style={{
            margin: 0,
            color: "var(--color-text-muted)",
            fontSize: "0.85rem",
          }}
        >
          {firstReason.message}
        </p>
      )}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {capability.domains.map((domain) => (
          <span
            key={domain}
            style={{ fontSize: "0.75rem", color: "var(--color-secondary)" }}
          >
            {domain.toUpperCase()}
          </span>
        ))}
      </div>
      <div
        style={{
          marginTop: "auto",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span style={{ fontSize: "0.78rem", color: "var(--color-text-muted)" }}>
          {capability.user_state.installed
            ? `Installed${capability.user_state.installed_version ? ` · ${capability.user_state.installed_version}` : ""}`
            : "Not installed"}
        </span>
        {onInstall &&
          !capability.user_state.installed &&
          capability.available_actions.includes("plan_onboarding") && (
            <button
              type="button"
              onClick={() => onInstall(capability.capability_id)}
              aria-label={`Install ${capability.name}`}
              style={{ color: "var(--color-secondary)", padding: "8px 12px" }}
            >
              Install
            </button>
          )}
        <button
          type="button"
          data-testid={`capability-details-open-${capability.capability_id}`}
          onClick={() => onOpen(capability)}
          aria-label={`View MCP server details for ${capability.name}`}
          style={{
            border: "1px solid var(--color-secondary)",
            borderRadius: "var(--radius-lg)",
            background: "transparent",
            color: "var(--color-secondary)",
            padding: "8px 12px",
            cursor: "pointer",
          }}
        >
          View details
        </button>
      </div>
    </article>
  );
}
