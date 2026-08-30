import type { ProgramStatusBundle } from "../../services/program-status";

export function WorkProgress({
  work,
}: {
  work: ProgramStatusBundle["supplement"]["work"];
}) {
  return (
    <section
      aria-labelledby="work-progress-heading"
      data-testid="work-progress"
    >
      <h2 id="work-progress-heading">Work scope and completion</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "var(--space-md)",
        }}
      >
        <article
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: 12,
            padding: "var(--space-md)",
          }}
        >
          <h3>Registered program tasks</h3>
          <strong>
            {work.program_tasks.completed}/{work.program_tasks.total}
          </strong>
          <progress
            aria-label="Registered program task completion"
            value={work.program_tasks.completed}
            max={Math.max(work.program_tasks.total, 1)}
            style={{ width: "100%" }}
          />
          <p>
            This is only work already decomposed in{" "}
            {work.program_tasks.registered_sources.length} registered task
            graph(s).
          </p>
          <p>
            {work.program_tasks.undecomposed_roadmap_items.length} roadmap items
            remain outside this denominator.
          </p>
        </article>
        <article
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: 12,
            padding: "var(--space-md)",
          }}
        >
          <h3>{work.tasks.feature_id} active-feature tasks</h3>
          <strong>
            {work.tasks.completed}/{work.tasks.total}
          </strong>
          <progress
            aria-label={`${work.tasks.feature_id} task completion`}
            value={work.tasks.completed}
            max={Math.max(work.tasks.total, 1)}
            style={{ width: "100%" }}
          />
          <p>
            {work.tasks.remaining} tasks remain in this bounded feature. This is
            not overall product completion.
          </p>
        </article>
      </div>
    </section>
  );
}
