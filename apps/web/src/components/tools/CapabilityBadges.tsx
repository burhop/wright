import type {
  CompatibilityStatus,
  EvidenceClass,
} from "../../services/mcp-service";

const evidenceLabels: Record<EvidenceClass, string> = {
  official_production: "Official",
  official_preview: "Official preview",
  verified_community: "Verified community",
  community_candidate: "Community candidate",
  user_reported_source_needed: "Source needed",
  api_wrapper_candidate: "API candidate",
  documentation_only: "Documentation only",
  blocked_validation: "Validation blocked",
  excluded_or_stale: "Excluded or stale",
};

const compatibilityLabels: Record<CompatibilityStatus, string> = {
  compatible: "Compatible",
  incompatible: "Incompatible",
  uncertain: "Compatibility uncertain",
  blocked: "Onboarding blocked",
};

const compatibilityColors: Record<CompatibilityStatus, string> = {
  compatible: "var(--color-success)",
  incompatible: "var(--color-error)",
  uncertain: "var(--color-warning)",
  blocked: "var(--color-error)",
};

const badgeStyle = {
  display: "inline-flex",
  alignItems: "center",
  borderRadius: "999px",
  padding: "3px 9px",
  fontSize: "0.72rem",
  fontWeight: 700,
  border: "1px solid currentColor",
} as const;

export function EvidenceBadge({ value }: { value: EvidenceClass }) {
  return (
    <span
      data-testid={`evidence-badge-${value}`}
      style={{ ...badgeStyle, color: "var(--color-secondary)" }}
    >
      {evidenceLabels[value]}
    </span>
  );
}

export function CompatibilityBadge({ value }: { value: CompatibilityStatus }) {
  return (
    <span
      data-testid={`compatibility-badge-${value}`}
      style={{ ...badgeStyle, color: compatibilityColors[value] }}
    >
      {compatibilityLabels[value]}
    </span>
  );
}
