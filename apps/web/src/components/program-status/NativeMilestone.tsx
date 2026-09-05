import type { CSSProperties } from "react";
import type { NativeMilestone as Milestone } from "./NativeMilestone.types";
import "./NativeMilestone.css";

const grid: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 260px), 1fr))",
  gap: "var(--space-md)",
};
const card: CSSProperties = {
  minWidth: 0,
  border: "1px solid var(--color-border)",
  borderRadius: 12,
  padding: "var(--space-md)",
  overflowWrap: "anywhere",
};
const stack: CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "var(--space-md)",
};
const muted: CSSProperties = { color: "var(--color-secondary)" };
const summaryStyle: CSSProperties = { cursor: "pointer", padding: "8px 0" };

function label(value: string): string {
  return value.replaceAll("_", " ");
}

function Status({ value }: { value: string }) {
  return <strong>{label(value)}</strong>;
}

function Commit({ value }: { value: string | null }) {
  return value ? (
    <code style={{ overflowWrap: "anywhere" }}>{value}</code>
  ) : (
    <span>Not recorded</span>
  );
}

function CheckLinks({ ids }: { ids: string[] }) {
  return ids.length ? (
    <span>
      {ids.map((id, index) => (
        <span key={id}>
          {index > 0 ? ", " : ""}
          <a href={`#native-check-${id}`}>{id}</a>
        </span>
      ))}
    </span>
  ) : (
    <span>None registered</span>
  );
}

function TaskCard({
  task,
  current = false,
}: {
  task: Milestone["tasks"][number];
  current?: boolean;
}) {
  return (
    <article
      style={card}
      data-testid={`native-${current ? "current-" : ""}task-${task.id}`}
    >
      <h3 style={{ margin: "0 0 8px" }}>
        {task.id} · {task.title}
      </h3>
      <p style={{ margin: "8px 0" }}>
        <Status value={task.activity} /> · Owner: {task.owner}
      </p>
      <dl style={{ margin: 0 }}>
        <dt>Implementation</dt>
        <dd>{task.implemented ? "Implemented" : "Remaining"}</dd>
        <dt>Verification</dt>
        <dd>{label(task.verification)}</dd>
        <dt>Dev integration</dt>
        <dd>
          {task.integration_required
            ? label(task.integration)
            : "Not applicable"}
        </dd>
      </dl>
      {task.blocker_ids.length > 0 && (
        <p>
          Blocked by:{" "}
          {task.blocker_ids.map((id, index) => (
            <span key={id}>
              {index > 0 ? ", " : ""}
              <a href={`#native-blocker-${id}`}>{id}</a>
            </span>
          ))}
        </p>
      )}
    </article>
  );
}

function QualityCheck({ check }: { check: Milestone["checks"][number] }) {
  return (
    <article id={`native-check-${check.id}`} style={card} tabIndex={-1}>
      <h3 style={{ marginTop: 0 }}>{check.label}</h3>
      <p>
        <Status value={check.status} /> · {label(check.kind)} ·{" "}
        {label(check.stage)}
      </p>
      {check.kind === "human_review" && (
        <p>Human validation requires recorded participant evidence.</p>
      )}
      <p>{check.summary || "No result summary recorded."}</p>
      <p>
        {check.coverage_current === true
          ? "Evidence covers the current declared source scope."
          : check.coverage_current === false
            ? "Evidence is stale: the covered source scope has changed."
            : "Current source coverage is not established."}
      </p>
      {check.counts && (
        <p data-testid={`native-check-counts-${check.id}`}>
          {check.counts.passed} passed · {check.counts.failed} failed ·{" "}
          {check.counts.skipped} skipped · {check.counts.not_run} not run (
          {check.counts.total} total)
        </p>
      )}
      {!check.evidence_id && <p>No evidence recorded.</p>}
      <details>
        <summary style={summaryStyle}>
          Evidence and coverage for {check.id}
        </summary>
        <dl>
          <dt>Tasks covered</dt>
          <dd>{check.task_ids.join(", ") || "None registered"}</dd>
          <dt>Tested commit</dt>
          <dd>
            <Commit value={check.tested_commit} />
          </dd>
          <dt>Observed</dt>
          <dd>
            {check.observed_at ? (
              <time dateTime={check.observed_at}>{check.observed_at}</time>
            ) : (
              "Not recorded"
            )}
          </dd>
          <dt>Evidence record</dt>
          <dd>{check.evidence_id ?? "Not recorded"}</dd>
        </dl>
        {check.artifact_urls.length ? (
          <ul>
            {check.artifact_urls.map((url, index) => (
              <li key={url}>
                <a href={url} target="_blank" rel="noreferrer">
                  {check.id} evidence artifact {index + 1} (opens in new tab)
                </a>
              </li>
            ))}
          </ul>
        ) : (
          <p>No linked artifacts available.</p>
        )}
      </details>
    </article>
  );
}

export function NativeMilestone({
  milestone,
  benchmarkQualified,
}: {
  milestone: Milestone;
  benchmarkQualified: number;
}) {
  const currentTasks = milestone.tasks.filter((task) =>
    ["active", "blocked", "verifying"].includes(task.activity),
  );
  const stages = [
    {
      id: "implementation",
      title: "Implementation",
      detail: "Tasks implemented in the committed source.",
      ...milestone.counts.implementation,
    },
    {
      id: "verification",
      title: "Verification",
      detail: "Tasks with all required current checks passed.",
      ...milestone.counts.verification,
    },
    {
      id: "integration",
      title: "Dev integration",
      detail: `${milestone.counts.integration.not_applicable} tasks are exempt from integration.`,
      ...milestone.counts.integration,
    },
  ];
  const readiness = [
    ["Native milestone", milestone.readiness.native_milestone],
    ["Benchmark qualification", milestone.readiness.benchmark],
    ["Commercial readiness", milestone.readiness.commercial],
    ["Release readiness", milestone.readiness.release],
    ["Rivet migration", milestone.readiness.rivet_migration],
    ["Rivet retirement", milestone.readiness.rivet_retirement],
  ];

  return (
    <div
      className="native-milestone"
      data-testid="native-milestone"
      style={stack}
    >
      <section aria-labelledby="native-capabilities-heading" style={card}>
        <h2 id="native-capabilities-heading" style={{ marginTop: 0 }}>
          Available capabilities
        </h2>
        {milestone.capabilities.length ? (
          <ul>
            {milestone.capabilities.map((capability) => (
              <li key={capability}>{capability}</li>
            ))}
          </ul>
        ) : (
          <p>No native capabilities have delivery evidence yet.</p>
        )}
        <p style={muted}>{milestone.language_authority}</p>
        <p style={muted}>
          Autonomous AI authoring is future work. Rivet migration and retirement
          are tracked separately below.
        </p>
      </section>

      <section aria-labelledby="native-milestone-heading" style={stack}>
        <div>
          <p style={{ ...muted, margin: 0 }}>
            {milestone.id} · {milestone.feature_id} · Scope revision{" "}
            {milestone.scope_revision}
          </p>
          <h2 id="native-milestone-heading" style={{ margin: "4px 0" }}>
            {milestone.title}
          </h2>
          <p style={{ margin: "4px 0" }}>
            Milestone: <Status value={milestone.readiness.native_milestone} />
            {" · "}Updated{" "}
            <time dateTime={milestone.observed_at}>
              {milestone.observed_at}
            </time>
          </p>
        </div>
        <div style={grid}>
          {stages.map((stage) => (
            <article
              key={stage.id}
              style={card}
              data-testid={`native-progress-${stage.id}`}
            >
              <h3 style={{ marginTop: 0 }}>{stage.title}</h3>
              <strong style={{ fontSize: "1.8rem" }}>
                {stage.completed}/{stage.total}
              </strong>
              <p>{stage.detail}</p>
              <progress
                aria-label={`${stage.title} task progress`}
                value={stage.completed}
                max={Math.max(stage.total, 1)}
                style={{ width: "100%" }}
              />
            </article>
          ))}
        </div>
        <p style={{ ...muted, margin: 0 }}>
          Each stage has its own evidence and denominator. These counts do not
          represent overall product completion.
        </p>
        <details>
          <summary style={summaryStyle}>
            Scope changes and task denominator
          </summary>
          <ol>
            {milestone.scope_history.map((change) => (
              <li key={change.revision}>
                <strong>Revision {change.revision}</strong> ·{" "}
                <time dateTime={change.observed_at}>{change.observed_at}</time>
                <p>{change.reason}</p>
                <p>
                  Added: {change.added_task_ids.join(", ") || "None"}. Removed:{" "}
                  {change.removed_task_ids.join(", ") || "None"}.
                </p>
              </li>
            ))}
          </ol>
        </details>
      </section>

      <section aria-labelledby="native-acceptance-heading">
        <h2 id="native-acceptance-heading">
          Milestone acceptance and remaining work
        </h2>
        <div style={grid}>
          {milestone.acceptance.map((criterion) => (
            <article
              key={criterion.id}
              style={card}
              data-testid={`native-acceptance-${criterion.id}`}
            >
              <h3 style={{ marginTop: 0 }}>
                {criterion.id} · {criterion.title}
              </h3>
              <Status value={criterion.status} />
              {criterion.missing_check_ids.length > 0 && (
                <p>
                  Required checks remaining:{" "}
                  <CheckLinks ids={criterion.missing_check_ids} />
                </p>
              )}
              <details>
                <summary style={summaryStyle}>
                  Tasks and checks for {criterion.id}
                </summary>
                <p>Tasks: {criterion.task_ids.join(", ")}</p>
                <p>
                  Required checks: <CheckLinks ids={criterion.check_ids} />
                </p>
              </details>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="native-work-heading" style={stack}>
        <h2 id="native-work-heading" style={{ marginBottom: 0 }}>
          Current work and blockers
        </h2>
        {currentTasks.length ? (
          <div style={grid}>
            {currentTasks.map((task) => (
              <TaskCard key={task.id} task={task} current />
            ))}
          </div>
        ) : (
          <p>No active, blocked, or verifying task is recorded.</p>
        )}
        {milestone.blockers.length ? (
          <div style={grid}>
            {milestone.blockers.map((blocker) => (
              <article
                key={blocker.id}
                id={`native-blocker-${blocker.id}`}
                tabIndex={-1}
                style={card}
              >
                <h3 style={{ marginTop: 0 }}>
                  {blocker.id} · {blocker.summary}
                </h3>
                <p>Owner: {blocker.owner}</p>
                <p>Required action: {blocker.required_action}</p>
                <p>
                  Tasks: {blocker.task_ids.join(", ") || "None"}. Checks:{" "}
                  <CheckLinks ids={blocker.check_ids} />
                </p>
                <small>
                  Observed{" "}
                  <time dateTime={blocker.observed_at}>
                    {blocker.observed_at}
                  </time>
                </small>
              </article>
            ))}
          </div>
        ) : (
          <p>
            No explicit blockers recorded. Outstanding checks remain visible
            below.
          </p>
        )}
        <div>
          <h3>Next registered work</h3>
          {milestone.next_task_ids.length ? (
            <ol>
              {milestone.next_task_ids.map((id) => (
                <li key={id}>
                  {id} · {milestone.tasks.find((task) => task.id === id)?.title}
                </li>
              ))}
            </ol>
          ) : (
            <p>No next task recorded.</p>
          )}
        </div>
        <details>
          <summary style={summaryStyle}>
            All {milestone.tasks.length} milestone tasks
          </summary>
          <div style={grid}>
            {milestone.tasks.map((task) => (
              <TaskCard key={task.id} task={task} />
            ))}
          </div>
        </details>
      </section>

      <section aria-labelledby="native-quality-heading" style={stack}>
        <h2 id="native-quality-heading" style={{ marginBottom: 0 }}>
          Quality and candidate coverage
        </h2>
        <article style={card}>
          <p>
            Evidence age and coverage are separate. A recent report alone does
            not establish that the current candidate passed.
          </p>
          <dl>
            <dt>Current candidate</dt>
            <dd>
              <Commit value={milestone.candidate_commit} />
            </dd>
            <dt>Report source commit</dt>
            <dd>
              <Commit value={milestone.source_commit} />
            </dd>
          </dl>
        </article>
        {milestone.checks.length ? (
          <div style={grid}>
            {milestone.checks.map((check) => (
              <QualityCheck key={check.id} check={check} />
            ))}
          </div>
        ) : (
          <p>No verification or integration checks are registered.</p>
        )}
        <details>
          <summary style={summaryStyle}>
            Branch, PRs, merge and deployment
          </summary>
          <dl style={{ overflowWrap: "anywhere" }}>
            <dt>Branch → target</dt>
            <dd>
              {milestone.delivery.branch} → {milestone.delivery.target_branch}
            </dd>
            <dt>Baseline commit</dt>
            <dd>
              <Commit value={milestone.delivery.baseline_commit} />
            </dd>
            <dt>Delivery candidate commit</dt>
            <dd>
              <Commit value={milestone.delivery.candidate_commit} />
            </dd>
            <dt>Merged commit</dt>
            <dd>
              <Commit value={milestone.delivery.merged_commit} />
            </dd>
            <dt>Deployment verification</dt>
            <dd>{label(milestone.delivery.deployment_status)}</dd>
            <dt>Deployment checks</dt>
            <dd>
              <CheckLinks ids={milestone.delivery.deployment_check_ids} />
            </dd>
          </dl>
          {milestone.delivery.pull_requests.length ? (
            <ul>
              {milestone.delivery.pull_requests.map((pr) => (
                <li key={pr.url}>
                  <a href={pr.url} target="_blank" rel="noreferrer">
                    {pr.url} (opens in new tab)
                  </a>
                  <p>
                    Head: <Commit value={pr.head_commit} /> · Observed{" "}
                    <time dateTime={pr.observed_at}>{pr.observed_at}</time>
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <p>No pull request recorded.</p>
          )}
        </details>
      </section>

      <section aria-labelledby="native-examples-heading">
        <h2 id="native-examples-heading">Development examples</h2>
        <p>
          Execution evidence distinguishes fixtures, computed outputs and live
          MCP calls. Development examples do not confer benchmark qualification.
        </p>
        {milestone.examples.length ? (
          <div style={grid}>
            {milestone.examples.map((example) => (
              <article key={example.id} style={card}>
                <h3 style={{ marginTop: 0 }}>
                  {example.id} · {example.title}
                </h3>
                <p>
                  <Status value={example.maturity} /> ·{" "}
                  {label(example.execution_mode)}
                </p>
                <p>
                  Checks: <CheckLinks ids={example.check_ids} />
                </p>
                <details>
                  <summary style={summaryStyle}>Definition path</summary>
                  <code>{example.definition_path}</code>
                </details>
              </article>
            ))}
          </div>
        ) : (
          <p>No development examples registered.</p>
        )}
      </section>

      <section aria-labelledby="native-readiness-heading">
        <h2 id="native-readiness-heading">Separate readiness assessments</h2>
        <div style={grid}>
          {readiness.map(([title, status]) => (
            <article key={title} style={card}>
              <h3 style={{ marginTop: 0 }}>{title}</h3>
              <Status value={status} />
              {title === "Benchmark qualification" && (
                <p>{benchmarkQualified}/100 qualified</p>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
