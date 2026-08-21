import type {
  WindowsQualificationStatus,
  WindowsQualificationSummary as Summary,
} from "../../services/mcp-service";

const boundaryLabels = {
  source: "Source",
  package_or_registration: "MCP package or registration",
  startup: "Startup",
  protocol: "MCP protocol",
  host_or_backend: "Host app or backend",
  wright_setup: "Wright setup",
  gateway: "Wright gateway",
  cleanup: "Cleanup",
} as const;

const staleReasonLabels: Record<string, string> = {
  qualification_recipe_changed: "The qualification procedure changed",
  qualification_source_changed: "The MCP source changed",
  qualification_package_changed: "The MCP package changed",
  qualification_schema_changed: "The MCP tool definitions changed",
  qualification_machine_changed: "This computer changed",
  qualification_credential_binding_changed: "The account binding changed",
  qualification_evidence_expired: "The saved qualification expired",
};

function StatusRow({
  label,
  status,
}: {
  label: string;
  status: WindowsQualificationStatus;
}) {
  return (
    <div className="windows-qualification__item">
      <dt>{label}</dt>
      <dd data-result={status.result}>
        <span className="windows-qualification__indicator" aria-hidden="true" />
        <span>{status.label}</span>
      </dd>
    </div>
  );
}

export function WindowsQualificationSummary({ summary }: { summary: Summary }) {
  const observed = new Date(summary.observed_at);
  const observedLabel = Number.isNaN(observed.valueOf())
    ? summary.observed_at
    : new Intl.DateTimeFormat(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(observed);

  return (
    <section
      className="windows-qualification"
      aria-label="Windows qualification"
    >
      <header className="windows-qualification__header">
        <div>
          <div className="capability-dialog__section-label">
            Windows qualification
          </div>
          <h3 id="windows-qualification-title">
            {summary.current
              ? "Tested on this Windows setup"
              : "Windows test needs to be rerun"}
          </h3>
        </div>
        <time dateTime={summary.observed_at}>{observedLabel}</time>
      </header>

      {!summary.current ? (
        <div className="windows-qualification__stale" role="status">
          <strong>Recheck this Windows qualification</strong>
          <span>
            {summary.stale_reasons
              .map(
                (reason) =>
                  staleReasonLabels[reason] || "The saved evidence changed",
              )
              .join(". ")}
            .
          </span>
        </div>
      ) : null}

      {summary.claim ? (
        <p className="windows-qualification__claim">{summary.claim}</p>
      ) : null}

      <dl className="windows-qualification__grid">
        {(
          Object.keys(boundaryLabels) as Array<keyof typeof boundaryLabels>
        ).map((key) => (
          <StatusRow
            key={key}
            label={boundaryLabels[key]}
            status={summary[key]}
          />
        ))}
      </dl>

      <details className="windows-qualification__evidence">
        <summary data-testid="windows-qualification-evidence-toggle">
          Evidence reference
        </summary>
        <p>{summary.evidence_path}</p>
        <p>SHA-256 {summary.evidence_digest}</p>
      </details>
    </section>
  );
}
