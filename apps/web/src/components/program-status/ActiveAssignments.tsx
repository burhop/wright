import type { ProgramStatusBundle } from "../../services/program-status";

function text(row: Record<string, unknown>, key: string): string | null {
  return typeof row[key] === "string" ? row[key] : null;
}

export function ActiveAssignments({
  assignments,
}: {
  assignments: ProgramStatusBundle["supplement"]["work"]["active_assignments"];
}) {
  return (
    <section
      aria-labelledby="active-assignments-heading"
      data-testid="active-assignments"
    >
      <h2 id="active-assignments-heading">Active agent assignments</h2>
      {assignments.length === 0 ? (
        <p role="status">
          Unavailable: no committed assignment or lease evidence names an active
          agent task. Process activity is not used as a substitute.
        </p>
      ) : (
        <div style={{ display: "grid", gap: "var(--space-md)" }}>
          {assignments.map((assignment, index) => {
            const agent =
              text(assignment, "agent_id") ?? `unavailable-${index}`;
            return (
              <article
                key={agent}
                style={{
                  border: "1px solid var(--color-border)",
                  borderRadius: 12,
                  padding: "var(--space-md)",
                }}
              >
                <h3>{agent}</h3>
                <dl>
                  <dt>Exact task</dt>
                  <dd>
                    {text(assignment, "task_id") ?? "Unavailable"} ·{" "}
                    {text(assignment, "task_title") ?? "Unavailable"}
                  </dd>
                  <dt>State</dt>
                  <dd>{text(assignment, "task_state") ?? "Unavailable"}</dd>
                  <dt>Lane / branch</dt>
                  <dd>
                    {text(assignment, "lane") ?? "Unavailable"} ·{" "}
                    <code>{text(assignment, "branch") ?? "Unavailable"}</code>
                  </dd>
                  <dt>Why this matters</dt>
                  <dd>
                    {text(assignment, "why_this_matters") ?? "Unavailable"}
                  </dd>
                  <dt>Observed</dt>
                  <dd>
                    {text(assignment, "observed_at")
                      ? new Date(
                          text(assignment, "observed_at")!,
                        ).toLocaleString()
                      : "Unavailable"}
                  </dd>
                </dl>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
