import type { CapabilityView, EvidenceClass } from "../../services/mcp-service";

const evidenceLabels: Record<EvidenceClass, string> = {
  official_production: "Official",
  official_preview: "Publisher preview",
  verified_community: "Community source reviewed",
  community_candidate: "Community listing",
  user_reported_source_needed: "Source needed",
  api_wrapper_candidate: "API candidate",
  documentation_only: "Documentation only",
  blocked_validation: "Validation blocked",
  excluded_or_stale: "Excluded or stale",
};

export interface SetupStatusPresentation {
  label: string;
  color: string;
  summary: string;
}

export function getSetupStatus(
  capability: CapabilityView,
): SetupStatusPresentation {
  const evidence = capability.compatibility.reasons
    .map((reason) => `${reason.code} ${reason.source || ""} ${reason.message}`)
    .join(" ")
    .toLowerCase();

  if (capability.user_state.installed) {
    if (capability.local_validation?.state === "passed") {
      return {
        label: "Tested on this computer",
        color: "var(--color-success)",
        summary:
          "The MCP server is installed and its local protocol check passed.",
      };
    }
    return {
      label: "Installed · test needed",
      color: "var(--color-warning)",
      summary:
        "The MCP server is installed, but Wright has not recorded a successful local tool check yet.",
    };
  }

  if (
    /platform.*(unsupported|incompatible)|not supported|architecture.*unsupported/.test(
      evidence,
    )
  ) {
    return {
      label: "Not supported here",
      color: "var(--color-error)",
      summary:
        "The available evidence says this MCP server does not support this computer's platform.",
    };
  }
  if (
    /host_software|host software|required host|could not be confirmed/.test(
      evidence,
    )
  ) {
    return {
      label: "Host app needed",
      color: "var(--color-warning)",
      summary:
        "The MCP server can still be installed. Its engineering application must be installed or connected before the tools can run.",
    };
  }
  if (/credential|api key|sign.?in|account/.test(evidence)) {
    return {
      label: "Sign-in needed",
      color: "var(--color-warning)",
      summary:
        "The MCP server can be set up, but an account or credential is required before use.",
    };
  }
  if (/network|endpoint|remote/.test(evidence)) {
    return {
      label: "Connection check needed",
      color: "var(--color-warning)",
      summary:
        "This remote MCP server can be added after its endpoint and network access are confirmed.",
    };
  }
  if (capability.compatibility.status === "compatible") {
    return {
      label: "Ready to set up",
      color: "var(--color-success)",
      summary:
        "The known requirements match this computer. Installation and a local tool check are still separate steps.",
    };
  }
  if (capability.compatibility.status === "blocked") {
    return {
      label: "Setup blocked",
      color: "var(--color-error)",
      summary:
        "A stated requirement must be resolved before setup can continue.",
    };
  }
  if (capability.compatibility.status === "incompatible") {
    return {
      label: "Requirements missing",
      color: "var(--color-warning)",
      summary:
        "One or more requirements are missing. This does not necessarily prevent installing the MCP server package.",
    };
  }
  return {
    label: "Check required",
    color: "var(--color-warning)",
    summary:
      "Wright has not yet checked every requirement on this computer. This is not a failed installation.",
  };
}

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

export function CompatibilityBadge({
  capability,
}: {
  capability: CapabilityView;
}) {
  const presentation = getSetupStatus(capability);
  return (
    <span
      data-testid={`compatibility-badge-${capability.compatibility.status}`}
      title={presentation.summary}
      style={{ ...badgeStyle, color: presentation.color }}
    >
      {presentation.label}
    </span>
  );
}
