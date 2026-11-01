import { McpDeviceSignIn } from "./McpDeviceSignIn";
import { useState } from "react";
import { CapabilityApiError, mcpService, type CapabilityView, type CapabilityValidationEvidence } from "../../services/mcp-service";
import { CompatibilityBadge, EvidenceBadge } from "./CapabilityBadges";
import { capabilitySetupGuides } from "../../services/provider-setup-guides";
import { capabilityFacts } from "./CapabilityFacts";

export function CapabilityCard({
  capability,
  onOpen,
  onInstall,
  onConnectionChecked,
}: {
  capability: CapabilityView;
  onOpen: (capability: CapabilityView) => void;
  onInstall?: (capabilityId: string) => void;
  onConnectionChecked?: (evidence: CapabilityValidationEvidence) => void;
}) {
  const [checking, setChecking] = useState(false);
  const [connection, setConnection] = useState<CapabilityValidationEvidence | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const checkConnection = async () => {
    if (checking) return;
    setChecking(true);
    setConnection(null);
    setConnectionError(null);
    try {
      const evidence = await mcpService.runCapabilityValidation(
        capability.user_state.server_id || capability.capability_id,
      );
      setConnection(evidence);
      onConnectionChecked?.(evidence);
    } catch (error) {
      setConnectionError(error instanceof CapabilityApiError
        ? `${error.message}${error.recovery ? ` ${error.recovery}` : ""}`
        : "The connection result could not be retrieved. Inspect the server's current status before retrying.");
    } finally {
      setChecking(false);
    }
  };
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
      <McpDeviceSignIn serverId={capability.user_state.server_id || capability.capability_id} active={checking} />
      {(checking || connection || connectionError) && (
        <p role={connectionError ? "alert" : "status"} style={{ margin: 0 }}>
          {checking
            ? "Checking the connection. Complete sign-in in the browser if prompted."
            : connectionError || (connection?.state === "passed"
              ? `Connection checked: ${connection.tool_count ?? 0} tools discovered. Enable this server in your workspace to use it.`
              : `Connection check: ${connection?.state.replaceAll("_", " ")}. ${connection?.missing_requirements.join(" ") || "Review the server details and setup guide before retrying."}`)}
        </p>
      )}
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
        {capability.user_state.installed &&
          capability.protocol_family === "mcp" &&
          capability.available_actions.includes("manage_installation") && (
            <button type="button" disabled={checking} onClick={checkConnection}
              aria-label={`Check connection to ${capability.name}`}
              style={{ color: "var(--color-secondary)", padding: "8px 12px" }}>
              {checking ? "Checking connection…" : "Check connection"}
            </button>
          )}
        {onInstall &&
          !capability.user_state.installed &&
          capability.available_actions.includes("plan_onboarding") && (
            <button
              type="button"
              onClick={() => onInstall(capability.capability_id)}
              aria-label={`${capability.locality === "remote" ? "Connect" : "Install"} ${capability.name}`}
              style={{ color: "var(--color-secondary)", padding: "8px 12px" }}
            >
              {capability.locality === "remote" ? "Connect" : "Install"}
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
          {capabilitySetupGuides[capability.canonical_id]
            ? "View details and setup guide"
            : "View details"}
        </button>
      </div>
    </article>
  );
}
