import type { CapabilityView } from "../../services/mcp-service";
import { CompatibilityBadge, EvidenceBadge } from "./CapabilityBadges";

export function CapabilityCard({
  capability,
  onOpen,
}: {
  capability: CapabilityView;
  onOpen: (capability: CapabilityView) => void;
}) {
  const firstReason = capability.compatibility.reasons[0];
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
        <CompatibilityBadge value={capability.compatibility.status} />
      </div>
      <div>
        <h2 style={{ fontSize: "1.08rem", margin: 0 }}>{capability.name}</h2>
        <p style={{ color: "var(--color-text-muted)", margin: "4px 0 0" }}>
          {capability.vendor} · {capability.transport.replace("_", " ")}
        </p>
      </div>
      <p style={{ margin: 0, lineHeight: 1.5 }}>{capability.description}</p>
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
        <button
          type="button"
          data-testid={`capability-details-open-${capability.capability_id}`}
          onClick={() => onOpen(capability)}
          aria-label={`View details for ${capability.name}`}
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
