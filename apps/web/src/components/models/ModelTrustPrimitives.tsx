import type {
  EngineeringModelVariant,
  EngineeringModelView,
} from "../../services/engineering-model-service";

const readinessLabels: Record<string, string> = {
  approved: "Approved",
  needs_review: "Needs review",
  gated_external_action: "External action required",
  incompatible: "Incompatible",
  deprecated: "Deprecated",
  withdrawn: "Withdrawn",
  blocked: "Blocked",
};

export function ModelReadinessBadge({ readiness }: { readiness: string }) {
  return (
    <span
      data-testid={`model-readiness-${readiness}`}
      style={{
        display: "inline-flex",
        padding: "var(--space-xs) var(--space-sm)",
        borderRadius: "var(--radius-lg)",
        border: "1px solid var(--color-border)",
        background: "var(--color-surface-subtle)",
        fontWeight: 700,
      }}
    >
      {readinessLabels[readiness] ?? readiness.replaceAll("_", " ")}
    </span>
  );
}

export function ModelEvidenceGrid({
  evidence,
}: {
  evidence: EngineeringModelView["evidence"];
}) {
  return (
    <dl
      data-testid="model-evidence-grid"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(8rem, 1fr))",
        gap: "var(--space-sm)",
        margin: 0,
      }}
    >
      {Object.entries(evidence).map(([facet, state]) => (
        <div key={facet}>
          <dt style={{ fontSize: "var(--font-size-sm)", opacity: 0.8 }}>
            {facet}
          </dt>
          <dd style={{ margin: 0, fontWeight: 700 }}>{state}</dd>
        </div>
      ))}
    </dl>
  );
}

function formatBytes(value: number | undefined): string {
  if (value === undefined) return "Not declared";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
}

export function ModelResourceSummary({
  variant,
}: {
  variant: EngineeringModelVariant;
}) {
  return (
    <dl style={{ margin: 0 }}>
      <div>
        <dt>Download</dt>
        <dd>{formatBytes(variant.resources?.download_bytes)}</dd>
      </div>
      <div>
        <dt>Installed</dt>
        <dd>{formatBytes(variant.resources?.installed_bytes)}</dd>
      </div>
      <div>
        <dt>RAM ceiling</dt>
        <dd>{formatBytes(variant.resources?.ram_bytes)}</dd>
      </div>
    </dl>
  );
}
