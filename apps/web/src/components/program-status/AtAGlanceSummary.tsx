import type { ProgramStatusBundle } from "../../services/program-status";

const cardStyle: React.CSSProperties = {
  border: "1px solid var(--color-border)",
  borderRadius: "12px",
  padding: "var(--space-md)",
  background: "var(--color-surface-subtle)",
  minWidth: 0,
};

function percent(completed: number, total: number): number {
  return total === 0 ? 0 : Math.round((completed / total) * 100);
}

export function AtAGlanceSummary({ bundle }: { bundle: ProgramStatusBundle }) {
  const {
    work,
    use_cases: useCases,
    customer_catalog: catalog,
    test_history: tests,
  } = bundle.supplement;
  const feature = work.tasks;
  const program = work.program_tasks;
  const process = useCases.process_100;
  const assignment = work.active_assignments[0];
  const assignmentTask =
    typeof assignment?.task_id === "string" ? assignment.task_id : null;
  const assignmentTitle =
    typeof assignment?.task_title === "string" ? assignment.task_title : null;
  const assignmentWhy =
    typeof assignment?.why_this_matters === "string"
      ? assignment.why_this_matters
      : null;
  const latestTests = tests.checkpoints.at(-1) as
    Record<string, unknown> | undefined;
  const latestCounts =
    latestTests &&
    typeof latestTests.counts === "object" &&
    latestTests.counts !== null
      ? (latestTests.counts as Record<string, unknown>)
      : null;
  const dashboard = bundle.dashboard as Record<string, unknown>;
  const releaseEligible = dashboard.release_eligible === true;
  const releaseApproval =
    typeof dashboard.release_approval === "string"
      ? dashboard.release_approval
      : "unavailable";
  const historicalAction =
    typeof dashboard.next_action === "object" && dashboard.next_action !== null
      ? (dashboard.next_action as Record<string, unknown>)
      : null;
  const historicalActionLabel =
    typeof dashboard.next_action === "string"
      ? dashboard.next_action
      : historicalAction && typeof historicalAction.action === "string"
        ? historicalAction.action
        : historicalAction && typeof historicalAction.label === "string"
          ? historicalAction.label
          : null;

  return (
    <section
      aria-labelledby="program-at-a-glance"
      data-testid="program-at-a-glance"
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: "var(--space-md)",
          alignItems: "baseline",
        }}
      >
        <div>
          <h2 id="program-at-a-glance" style={{ margin: 0 }}>
            At a glance
          </h2>
          <p
            style={{
              color: "var(--color-secondary)",
              margin: "4px 0 var(--space-md)",
            }}
          >
            Customer capability and delivery evidence—not governance activity
            alone.
          </p>
        </div>
        <code title={bundle.source.commit}>
          {bundle.source.commit.slice(0, 8)}
        </code>
      </div>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "var(--space-md)",
        }}
      >
        <article style={cardStyle} data-testid="program-work-summary">
          <h3 style={{ marginTop: 0 }}>How much work exists?</h3>
          <strong style={{ fontSize: "1.6rem" }}>
            {feature.completed}/{feature.total}
          </strong>
          <p>
            {feature.feature_id} tasks complete (
            {percent(feature.completed, feature.total)}
            %)
          </p>
          <progress
            aria-label={`${feature.feature_id} task completion`}
            value={feature.completed}
            max={Math.max(feature.total, 1)}
            style={{ width: "100%" }}
          />
          <small>
            Registered program work: {program.completed}/{program.total};{" "}
            {program.undecomposed_roadmap_items.length} roadmap items are not
            yet decomposed into tasks.
          </small>
        </article>

        <article style={cardStyle} data-testid="active-work-summary">
          <h3 style={{ marginTop: 0 }}>What is active now?</h3>
          {assignmentTask ? (
            <>
              <strong>
                {assignmentTask} · {assignmentTitle}
              </strong>
              <p>{assignmentWhy}</p>
            </>
          ) : (
            <>
              <strong>Committed assignment unavailable</strong>
              <p>
                No agent row is inferred from process activity. Current
                milestone: {work.current_milestone}
              </p>
            </>
          )}
        </article>

        <article style={cardStyle} data-testid="customer-capability-summary">
          <h3 style={{ marginTop: 0 }}>Customer capability</h3>
          <strong style={{ fontSize: "1.6rem" }}>
            {useCases.all.implemented}/{useCases.all.total}
          </strong>
          <p>
            Governed use cases implemented with customer-acceptance evidence;{" "}
            {useCases.all.independently_verified} independently verified.
          </p>
          <small>
            {catalog.proposed_total} proposed customer stories are a separate
            planning population and do not count as implemented.
          </small>
        </article>

        <article style={cardStyle} data-testid="process-benchmark-summary">
          <h3 style={{ marginTop: 0 }}>100-process journey</h3>
          <strong style={{ fontSize: "1.6rem" }}>
            {process.benchmark_qualified}/100 qualified
          </strong>
          <p>
            {process.defined} governed definitions · {process.implemented}{" "}
            implemented · {process.tested} tested
          </p>
          <progress
            aria-label="Governed benchmark qualification"
            value={process.benchmark_qualified}
            max={100}
            style={{ width: "100%" }}
          />
          <small>
            {bundle.supplement.benchmark_context.hold_reason ??
              "Qualification state is available in committed evidence."}
          </small>
        </article>

        <article style={cardStyle} data-testid="test-health-summary">
          <h3 style={{ marginTop: 0 }}>How are tests trending?</h3>
          {tests.availability === "available" && latestCounts ? (
            <>
              <strong>
                {String(latestCounts.passed ?? 0)} passed ·{" "}
                {String(latestCounts.failed ?? 0)} failed
              </strong>
              <p>Latest exact committed checkpoint.</p>
            </>
          ) : (
            <>
              <strong>History unavailable</strong>
              <p>
                {tests.unavailable_reason ??
                  "No canonical committed test ledger point is available."}
              </p>
            </>
          )}
        </article>

        <article style={cardStyle} data-testid="next-action-summary">
          <h3 style={{ marginTop: 0 }}>What changes next?</h3>
          <strong>{work.current_next_action.label}</strong>
          <p>
            {work.current_next_action.blocker ??
              "The committed authority evidence marks this action eligible."}
          </p>
          <small>
            Authority: {work.current_next_action.authority_state}; human
            approval:{" "}
            {work.current_next_action.requires_human_approval
              ? "required"
              : "not required"}
          </small>
          {historicalActionLabel ? (
            <details>
              <summary>Historical dashboard action</summary>
              <p>{historicalActionLabel}</p>
              <small>
                Snapshot context only. The current program-state action above
                takes precedence.
              </small>
            </details>
          ) : null}
        </article>

        <article style={cardStyle} data-testid="release-posture-summary">
          <h3 style={{ marginTop: 0 }}>Customer release posture</h3>
          <strong>
            {releaseEligible ? "Release eligible" : "Not release eligible"}
          </strong>
          <p>Approval: {releaseApproval}</p>
          <small>
            Release requires every independent readiness gate; feature task
            progress cannot compensate for a blocked area.
          </small>
        </article>
      </div>
    </section>
  );
}
