import { useEffect, useMemo, useState } from "react";
import {
  mcpService,
  type EngineeringMcpStatus,
  type EngineeringQualificationStatus,
} from "../../services/mcp-service";

const STATUS_LABELS: Record<EngineeringQualificationStatus, string> = {
  passing: "Passing",
  failing: "Failing",
  blocked: "Blocked",
  stale: "Stale",
  untested: "Untested",
};

const statusColor = (status: EngineeringQualificationStatus | string) => {
  if (status === "passing" || status === "passed") return "var(--color-success)";
  if (status === "failing" || status === "failed") return "var(--color-error)";
  if (status === "blocked" || status === "stale") return "var(--color-warning)";
  return "var(--color-text-muted)";
};

export function EngineeringMcpStatusDashboard({ refreshToken = 0 }: { refreshToken?: number }) {
  const [status, setStatus] = useState<EngineeringMcpStatus | null>(null);
  const [error, setError] = useState(false);
  const [query, setQuery] = useState("");
  const [qualification, setQualification] = useState<EngineeringQualificationStatus | "all">("all");

  useEffect(() => {
    let active = true;
    setError(false);
    mcpService
      .getEngineeringStatus()
      .then((value) => {
        if (active) setStatus(value);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, [refreshToken]);

  const records = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (status?.records || []).filter(
      (record) =>
        (qualification === "all" || record.qualification_status === qualification) &&
        (!needle ||
          [record.name, record.vendor, record.server_id, ...record.disciplines]
            .join(" ")
            .toLowerCase()
            .includes(needle)),
    );
  }, [qualification, query, status]);

  if (error) {
    return (
      <section role="alert" data-testid="engineering-mcp-status-error">
        Engineering MCP qualification status is unavailable. The server library remains usable.
      </section>
    );
  }
  if (!status) return <section role="status">Loading engineering MCP status…</section>;

  const targetWidth = Math.min(100, (status.target.curated / status.target.ideal) * 100);

  return (
    <section
      aria-labelledby="engineering-mcp-status-title"
      data-testid="engineering-mcp-status"
      style={{
        padding: "var(--space-xl)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-xl)",
        background: "var(--color-surface)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-lg)",
      }}
    >
      <div>
        <p style={{ margin: 0, color: "var(--color-text-muted)", fontWeight: 700 }}>QUALIFICATION EVIDENCE · {status.as_of}</p>
        <h1 id="engineering-mcp-status-title" style={{ margin: "var(--space-xs) 0" }}>Engineering MCP Status</h1>
        <p style={{ margin: 0, color: "var(--color-text-muted)" }}>
          Current scoped evidence for Wright’s engineering integration portfolio. Passing applies only to the recorded task, platform, and configuration.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "var(--space-sm)" }}>
        {(["curated", "follow_up", "removed"] as const).map((key) => (
          <div key={key} data-testid={`engineering-count-${key}`} style={{ padding: "var(--space-md)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)" }}>
            <strong style={{ display: "block", fontSize: "1.75rem" }}>{status.counts[key]}</strong>
            <span>{key === "follow_up" ? "Follow up" : key[0].toUpperCase() + key.slice(1)}</span>
          </div>
        ))}
      </div>

      <div data-testid="engineering-portfolio-target">
        <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-sm)", flexWrap: "wrap" }}>
          <strong>{status.target.curated} of {status.target.ideal} preferred integrations</strong>
          <span style={{ color: "var(--color-text-muted)" }}>Working range {status.target.minimum}–{status.target.maximum}</span>
        </div>
        <div aria-label={`${status.target.curated} of ${status.target.ideal} preferred integrations`} style={{ height: 10, marginTop: "var(--space-xs)", borderRadius: 999, background: "var(--color-neutral)", overflow: "hidden" }}>
          <div style={{ width: `${targetWidth}%`, height: "100%", background: "var(--color-secondary)" }} />
        </div>
      </div>

      <div aria-label="Qualification results" style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)" }}>
        {(Object.keys(STATUS_LABELS) as EngineeringQualificationStatus[]).map((key) => (
          <span key={key} data-testid={`engineering-status-${key}`} style={{ borderLeft: `4px solid ${statusColor(key)}`, padding: "var(--space-xs) var(--space-sm)", background: "var(--color-neutral)" }}>
            <strong>{status.qualification_counts[key]}</strong> {STATUS_LABELS[key]}
          </span>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "var(--space-md)" }}>
        {status.protocol_status.map((protocol) => (
          <article key={protocol.protocol} data-testid={`engineering-protocol-${protocol.protocol}`} style={{ padding: "var(--space-md)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)" }}>
            <h2 style={{ fontSize: "1rem", margin: 0 }}>{protocol.label}</h2>
            <p style={{ margin: "var(--space-xs) 0 0" }}>{protocol.passing} passing · {protocol.curated} curated · {protocol.known} known</p>
            {protocol.physical_operation_qualified === false ? (
              <p style={{ marginBottom: 0, color: "var(--color-text-muted)" }}>
                {protocol.protocol === "mhs"
                  ? "Research preview. Wright has not qualified physical operation."
                  : "Qualification required. Wright has not qualified physical operation."}
              </p>
            ) : null}
          </article>
        ))}
      </div>

      <div>
        <h2 style={{ fontSize: "1.1rem" }}>Tier 1 process-chain gates</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "var(--space-md)" }}>
          {status.chains.map((chain) => (
            <article key={chain.chain_id} data-testid={`engineering-chain-${chain.chain_id}`} style={{ padding: "var(--space-md)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-lg)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "var(--space-sm)" }}>
                <strong>{chain.name}</strong>
                <span style={{ color: statusColor(chain.status), fontWeight: 700 }}>{chain.status.toUpperCase()}</span>
              </div>
              <p>{chain.call_count} calls · {chain.handoffs_accepted} handoffs · {chain.artifact_checks} hash checks</p>
              <p style={{ color: "var(--color-text-muted)" }}>{chain.corrupt_handoffs_rejected} corrupt handoffs rejected · cleanup {chain.cleanup}</p>
              <a href={chain.evidence_href} target="_blank" rel="noreferrer">Open chain evidence</a>
            </article>
          ))}
        </div>
        <p style={{ color: "var(--color-text-muted)" }}>These use synthetic qualification fixtures and do not claim physical test results.</p>
      </div>

      <details data-testid="engineering-status-breakdowns">
        <summary>Results by discipline, protocol, transport, platform, and dependency</summary>
        {Object.entries(status.breakdowns).map(([dimension, rows]) => (
          <div key={dimension}>
            <h3 style={{ textTransform: "capitalize" }}>{dimension}</h3>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-xs)" }}>
              {rows.map((row) => <span key={row.key} style={{ padding: "var(--space-xs) var(--space-sm)", background: "var(--color-neutral)", borderRadius: "var(--radius-md)" }}>{row.key}: {row.passing}/{row.total} passing</span>)}
            </div>
          </div>
        ))}
      </details>

      <details data-testid="engineering-status-changes">
        <summary>Changes since {status.changes.previous_as_of || "the first run"} ({status.changes.count})</summary>
        <p>{Object.entries(status.changes.summary).map(([kind, count]) => `${kind}: ${count}`).join(" · ")}</p>
        {status.changes.items.length ? <ul>{status.changes.items.map((item) => <li key={item.server_id}>{item.server_id}: {item.change.replaceAll("_", " ")}{item.before && item.after ? ` (${item.before} → ${item.after})` : ""}</li>)}</ul> : <p>No recorded changes.</p>}
      </details>

      <details open data-testid="engineering-status-records">
        <summary>Server evidence ({records.length} shown)</summary>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-sm)", margin: "var(--space-md) 0" }}>
          <label>Search <input value={query} onChange={(event) => setQuery(event.target.value)} /></label>
          <label>Status <select value={qualification} onChange={(event) => setQualification(event.target.value as EngineeringQualificationStatus | "all")}><option value="all">All</option>{(Object.keys(STATUS_LABELS) as EngineeringQualificationStatus[]).map((key) => <option key={key} value={key}>{STATUS_LABELS[key]}</option>)}</select></label>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ minWidth: 1200, tableLayout: "fixed", width: "100%" }}>
            <colgroup>
              <col style={{ width: "16%" }} />
              <col style={{ width: "12%" }} />
              <col style={{ width: "23%" }} />
              <col style={{ width: "18%" }} />
              <col style={{ width: "14%" }} />
              <col style={{ width: "17%" }} />
            </colgroup>
            <thead><tr><th scope="col">Server</th><th scope="col">Status</th><th scope="col">Scope and mode</th><th scope="col">Platform and prerequisites</th><th scope="col">Evidence</th><th scope="col">Next action</th></tr></thead>
            <tbody>
              {records.map((record) => (
                <tr key={record.server_id}>
                  <th scope="row"><a href={record.source_url || undefined} target="_blank" rel="noreferrer">{record.name}</a><br /><small>{record.vendor} · {record.server_id}<br />{record.disposition}</small></th>
                  <td><strong style={{ color: statusColor(record.qualification_status) }}>{STATUS_LABELS[record.qualification_status]}</strong><br /><small>{record.latest_result}{record.failure ? ` · ${record.failure}` : ""}</small></td>
                  <td>{record.scope}<br /><small>{record.implementation_mode} · {record.protocol_family}/{record.transport}</small></td>
                  <td>{record.platforms.join(", ")}<br /><small>{record.prerequisites.join(", ") || "No recorded prerequisite"}<br />Credentials: {record.credentials.join(", ") || "none"}</small></td>
                  <td>{record.evidence_href ? <a href={record.evidence_href} target="_blank" rel="noreferrer">Open evidence</a> : "No evidence link"}<br /><small>{record.last_qualified_at ? `Qualified ${record.last_qualified_at}` : "No current qualification"}{record.evidence_age_days === null ? "" : ` · ${record.evidence_age_days} days old`}<br />{record.source_revision || "Revision not pinned in evidence"}</small></td>
                  <td>{record.next_action}<br /><small>{record.owner} · review {record.review_due || "unscheduled"}</small></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}
