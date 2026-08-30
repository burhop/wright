import type {
  EvidenceDetail,
  ProgramStatusBundle,
} from "../../services/program-status";

function Availability({ detail }: { detail: EvidenceDetail }) {
  if (detail.availability === "exact_github" && detail.exact_url) {
    return (
      <a href={detail.exact_url} target="_blank" rel="noreferrer">
        Open exact committed evidence
      </a>
    );
  }
  if (detail.availability === "checkout_available") {
    return (
      <span>
        Available in the exact local checkout at <code>{detail.path}</code>
      </span>
    );
  }
  return (
    <span>Identity only; raw content is not available from this runtime.</span>
  );
}

export function EvidenceDetails({ bundle }: { bundle: ProgramStatusBundle }) {
  const details = bundle.supplement.evidence_index;
  return (
    <section
      aria-labelledby="evidence-details-heading"
      data-testid="evidence-details"
    >
      <h2 id="evidence-details-heading">Evidence and recovery</h2>
      <p>
        Every exposed path and optional GitHub link is validated against the
        frozen exact-path contract. Readiness is never upgraded by this view.
      </p>
      {details.length === 0 ? (
        <p role="status">
          No bounded evidence details are available in this bundle.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "var(--space-sm)" }}>
          {details.map((detail) => (
            <details key={`${detail.id}-${detail.sha256}`}>
              <summary>
                {detail.label} · {detail.freshness}
              </summary>
              <p>{detail.summary}</p>
              <dl>
                <dt>Evidence ID</dt>
                <dd>
                  <code>{detail.id}</code>
                </dd>
                <dt>Path</dt>
                <dd>
                  <code>{detail.path}</code>
                </dd>
                <dt>SHA-256</dt>
                <dd>
                  <code>{detail.sha256}</code>
                </dd>
                <dt>Availability</dt>
                <dd>
                  <Availability detail={detail} />
                </dd>
                <dt>Recovery</dt>
                <dd>{detail.recovery ?? "No recovery action is recorded."}</dd>
              </dl>
            </details>
          ))}
        </div>
      )}
    </section>
  );
}
