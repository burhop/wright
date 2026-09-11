import { useEffect, useState } from "react";
import {
  fetchDevelopmentMetrics,
  projectTasks,
  cumulativeTaskSeries,
  taskStates,
  type Metrics,
} from "../../services/development-metrics";
import { PlotlyRenderer } from "../../services/surfaces/renderers/plotly-renderer";

const colors = [
  "#94a3b8",
  "#38bdf8",
  "#fbbf24",
  "#a78bfa",
  "#34d399",
  "#2dd4bf",
  "#fb7185",
  "#fb923c",
];
const labels = [
  "Defined / status unconfirmed",
  "Working",
  "Awaiting QA",
  "Implemented",
  "Verified",
  "Integrated",
  "Removed from scope",
  "Manual validation needed",
];
const windows = {
  "12 hours": 12,
  "24 hours": 24,
  "7 days": 168,
  "Full history": 0,
};

const chartNotes: Record<string, string> = {
  "Cumulative completed tasks":
    "Completed task counts accumulate across features, so each new batch starts from the preceding total. Colors mark when a new feature joins the running total. Reopened or removed completed tasks reduce the total; checkbox completion reports implementation, not QA approval. Dates are observation checkpoints.",
  "Observed checkbox completions":
    "Tasks seen changing from unchecked to checked, grouped by observation day (UTC). Tasks first encountered already checked are excluded because their completion date is unknown. Blank days have no recorded transition, not proof of no work. This measures reported implementation, not validated delivery.",
  "Implementation, testing, review and integration":
    "Recorded starts, finishes, failures and blockers show where execution is happening. Repeated failures in the same stage suggest a repair loop; activity without movement in the task chart calls for a closer look. An empty lane means no events were captured, not necessarily no work occurred.",
  "QA results over time":
    "Each point is one test attempt for the selected suite and environment. Use failures and skipped checks to judge whether the batch is converging toward acceptance. Reruns do not add coverage, and passing more tests does not establish that every requirement has been tested.",
  "Batch completion at latest observation":
    "Each feature's bar separates unfinished work from reported verification and integration. Check earlier batches for unresolved stages before starting another. Bar height reflects scope size, not percentage complete; removed tasks remain visible without counting as delivered.",
  "Model usage over time":
    "Five-minute totals show when the tracked sessions are consuming model tokens. Compare busy intervals with verified progress beside this chart to spot expensive retries or work that has yet to produce a checked result. Input includes cached tokens; these are usage counts, not cost or subscription-quota percentages.",
  "Verified and integrated work":
    "Verified work includes tasks that have subsequently been integrated, so moving a task forward does not look like lost progress. The gap between the lines shows checked work awaiting integration. Compare this trend with model usage to assess delivery; these are recorded task outcomes, not a release-readiness score.",
};

export function DevelopmentMetrics() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [failed, setFailed] = useState(false);
  const [now, setNow] = useState(Date.now());
  const [windowLabel, setWindowLabel] =
    useState<keyof typeof windows>("12 hours");
  const [feature, setFeature] = useState("all");
  const [suite, setSuite] = useState("");
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    const poll = async () => {
      try {
        const result = await fetchDevelopmentMetrics(controller.signal);
        if (active) {
          setMetrics(result);
          setFailed(false);
        }
      } catch {
        if (active) setFailed(true);
      } finally {
        if (active) {
          setNow(Date.now());
          timer = setTimeout(poll, 15000);
        }
      }
    };
    void poll();
    return () => {
      active = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, []);

  const events = metrics?.events ?? [];
  const hours = windows[windowLabel];
  const start = hours
    ? now - hours * 3600000
    : Math.min(now - 3600000, ...events.map((e) => Date.parse(e.at)));
  const range = [new Date(start).toISOString(), new Date(now).toISOString()];
  const selected = events.filter(
    (e) => feature === "all" || e.feature === feature || e.kind === "heartbeat",
  );
  const visible = selected.filter(
    (e) => Date.parse(e.at) >= start && Date.parse(e.at) <= now,
  );
  const projection = projectTasks(selected);
  const features = [
    ...new Set(
      events
        .filter((e) => ["snapshot", "task"].includes(e.kind))
        .map((e) => e.feature),
    ),
  ];
  const heartbeat = events.filter((e) => e.kind === "heartbeat").at(-1);
  const fresh =
    heartbeat?.kind === "heartbeat" &&
    heartbeat.data.status === "active" &&
    now - Date.parse(heartbeat.at) < 90000 &&
    !failed;
  // Break task curves whenever collector observations stop; never bridge a blind interval.
  const grouped = new Map<string, typeof projection.points>();
  for (const point of projection.points) {
    const group = grouped.get(point.at) ?? [];
    group.push(point);
    grouped.set(point.at, group);
  }
  const pointTimes = [...grouped.keys()].sort();
  const x: (string | null)[] = [];
  const y = taskStates.map(() => [] as (number | null)[]);
  const hover: string[] = [];
  const last = new Map<string, (typeof projection.points)[number]>();
  let priorTime = 0;
  let priorCommitted = false;
  for (const at of pointTimes) {
    const current = grouped.get(at)!;
    current.forEach((p) => last.set(p.feature, p));
    const ms = Date.parse(at);
    if (ms < start || ms > now) continue;
    const committed = current.every((p) => p.committed);
    if (priorTime && ms - priorTime > 90000 && !(committed && priorCommitted)) {
      x.push(null);
      y.forEach((series) => series.push(null));
      hover.push("Observation gap");
    }
    x.push(at);
    taskStates.forEach((state, i) =>
      y[i].push([...last.values()].reduce((n, p) => n + p.counts[state], 0)),
    );
    hover.push(
      (committed ? "Committed checkpoint. " : "Live observation. ") +
        current
          .map((p) => p.change)
          .filter(Boolean)
          .join(" ") || "Observed task population",
    );
    priorTime = ms;
    priorCommitted = committed;
  }
  const qa = visible.filter((e) => e.kind === "qa");
  const suiteKey = (e: (typeof qa)[number]) =>
    `${e.feature} / ${e.data.suite} / ${e.data.environment}`;
  const suites = [...new Set(qa.map(suiteKey))];
  const activeSuite = suites.includes(suite) ? suite : suites[0];
  const qaPoints = qa.filter((e) => suiteKey(e) === activeSuite);
  const activity = visible.filter((e) => e.kind === "activity");
  const usage = visible.filter((e) => e.kind === "usage");
  const usageBins = new Map<number, { input: number; output: number }>();
  for (const event of usage) {
    const bucket = Math.floor(Date.parse(event.at) / 300000) * 300000;
    const totals = usageBins.get(bucket) ?? { input: 0, output: 0 };
    totals.input += event.data.input_tokens;
    totals.output += event.data.output_tokens;
    usageBins.set(bucket, totals);
  }
  const bins = [...usageBins.entries()].sort(([a], [b]) => a - b);
  const taskTraces = cumulativeTaskSeries(projection.points, start, now).map(
    (series, i) => ({
      x: series.x,
      y: series.y,
      type: "scatter",
      mode: "lines+markers",
      name: series.feature,
      line: { shape: "hv", color: colors[i % colors.length] },
      hovertemplate:
        "%{x}<br>%{y} completed tasks across selected features<extra>%{fullData.name}</extra>",
    }),
  );
  const completedValues = taskTraces.flatMap((trace) => trace.y);
  const completedMin = completedValues.length
    ? Math.min(...completedValues)
    : 0;
  const completedMax = completedValues.length
    ? Math.max(...completedValues)
    : 0;
  const completedRange = [
    hours ? completedMin : 0,
    completedMax +
      Math.max(1, (completedMax - (hours ? completedMin : 0)) * 0.08),
  ];
  const observed = projection.points.filter(
    (p) => Date.parse(p.at) >= start && Date.parse(p.at) <= now,
  );
  const completionDays = new Map<string, number>();
  for (const p of observed) {
    if (p.completed) {
      const day = p.at.slice(0, 10);
      completionDays.set(day, (completionDays.get(day) ?? 0) + p.completed);
    }
  }
  const firstSeenChecked = observed.reduce((n, p) => n + p.firstSeenChecked, 0);
  const hasVerification = selected.some(
    (e) =>
      e.kind === "task" &&
      ["verified", "integrated"].includes(e.data.state) &&
      Date.parse(e.at) <= now,
  );
  const chart = (
    title: string,
    traces: unknown[],
    unit: string,
    available: boolean,
    timeAxis = true,
    emptyMessage = "No observations in this period",
  ) => (
    <article
      style={{
        minWidth: 0,
        border: "1px solid var(--color-border)",
        borderRadius: 12,
        padding: 12,
      }}
    >
      <h3>{title}</h3>
      {available ? (
        <PlotlyRenderer
          representation={{
            mediaType: "application/vnd.plotly.v1+json",
            encoding: "json",
            data: {
              data: traces,
              layout: {
                height: 370,
                autosize: true,
                margin: {
                  l: 65,
                  r: 18,
                  t: 10,
                  b: traces.length > 6 ? 125 : 85,
                },
                paper_bgcolor: "rgba(0,0,0,0)",
                plot_bgcolor: "rgba(0,0,0,0)",
                font: { color: "#94a3b8" },
                xaxis: timeAxis
                  ? { type: "date", range, tickangle: 0, nticks: 4 }
                  : { title: { text: "Feature" } },
                yaxis: {
                  title: { text: unit },
                  rangemode: "tozero",
                  ...(title === "Cumulative completed tasks"
                    ? {
                        range: completedRange,
                        rangemode: "normal",
                        tickformat: ",d",
                        ...(completedRange[1] - completedRange[0] <= 10
                          ? { dtick: 1 }
                          : {}),
                      }
                    : {}),
                  automargin: true,
                },
                legend: {
                  orientation: "h",
                  y: -0.3,
                  entrywidth: 0.5,
                  entrywidthmode: "fraction",
                  font: { size: 11 },
                },
                barmode: "stack",
              },
            },
          }}
          description={title}
          fallback={
            <p>
              Chart unavailable. Recorded observations remain available below.
            </p>
          }
        />
      ) : (
        <div
          role="status"
          style={{
            minHeight: 70,
            padding: 16,
            display: "grid",
            placeItems: "center",
            border: "1px dashed var(--color-border)",
          }}
        >
          {emptyMessage}
        </div>
      )}
      <p
        data-testid="chart-purpose"
        style={{
          marginTop: 12,
          paddingTop: 12,
          borderTop: "1px solid var(--color-border)",
          color: "var(--color-secondary)",
          fontSize: ".9rem",
          lineHeight: 1.6,
        }}
      >
        {chartNotes[title]}
        {title === "Cumulative completed tasks" && hours > 0
          ? " The vertical axis is zoomed to this period's totals; any decrease below the starting total remains visible."
          : ""}
      </p>
    </article>
  );

  return (
    <section
      aria-labelledby="development-metrics-title"
      data-testid="development-metrics"
    >
      <h2 id="development-metrics-title">Development progress over time</h2>
      <div
        style={{
          display: "flex",
          gap: 16,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <label>
          Period{" "}
          <select
            value={windowLabel}
            onChange={(e) =>
              setWindowLabel(e.target.value as keyof typeof windows)
            }
          >
            {Object.keys(windows).map((w) => (
              <option key={w}>{w}</option>
            ))}
          </select>
        </label>
        <label>
          Feature{" "}
          <select value={feature} onChange={(e) => setFeature(e.target.value)}>
            <option value="all">All registered work</option>
            {features.map((f) => (
              <option key={f}>{f}</option>
            ))}
          </select>
        </label>
        <span role="status">
          {fresh
            ? "Collector active"
            : "Observation gap — collector unavailable or stopped"}
          {failed && metrics ? " · showing last received history" : ""}
        </span>
      </div>
      <p>
        Local observations · checkbox completion means implemented ·
        verification requires an evidence reference.
      </p>
      <p style={{ color: "var(--color-secondary)", fontSize: ".9rem" }}>
        {projection.points.some((p) => p.committed)
          ? `Task history includes Git checkpoints from ${new Date(projection.points.find((p) => p.committed)!.at).toLocaleDateString()}. Checkpoints show recorded state; completion times between them are unknown.`
          : "No committed task history loaded yet. Live task tracking begins with the first collected snapshot."}
      </p>
      <aside
        aria-label="Completion requirements"
        style={{
          padding: 16,
          border: "1px solid var(--color-border)",
          borderRadius: 12,
        }}
      >
        <h3>From defined to complete</h3>
        <div
          style={{
            display: "flex",
            gap: 8,
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          {[
            "Defined",
            "Working",
            "Implemented",
            "Awaiting QA / manual validation",
            "Verified",
            "Integrated into dev/main",
            "Complete",
          ].map((stage, i) => (
            <span
              key={stage}
              style={{
                padding: 8,
                border: "1px solid var(--color-border)",
                borderRadius: 6,
              }}
            >
              {i > 0 ? "→ " : ""}
              {stage}
            </span>
          ))}
        </div>
        <p>
          Complete requires implementation, passing required tests and
          validation for the delivered code, and confirmed integration into dev
          or main. A checked task or a merge alone is insufficient.
        </p>
        <p>
          Coverage: checkbox history is tracked for all registered features. QA,
          review and branch evidence are not yet fully reconciled into these
          metrics; feature completion remains unconfirmed. Undefined activity is
          shown as “Defined / status unconfirmed”, not “Not started”.
        </p>
      </aside>
      <details open>
        <summary>Unresolved work — reason and next action</summary>
        <div
          style={{
            display: "grid",
            gridTemplateColumns:
              "repeat(auto-fit, minmax(min(100%, 320px), 1fr))",
            gap: 12,
          }}
        >
          {[...projection.tasks.entries()]
            .filter(([, task]) =>
              ["queued", "working", "qa", "manual_validation"].includes(
                task.state,
              ),
            )
            .map(([id, task]) => (
              <article
                key={id}
                style={{
                  padding: 12,
                  border: "1px solid var(--color-border)",
                  borderRadius: 8,
                }}
              >
                <strong>
                  {id} · {labels[taskStates.indexOf(task.state)]}
                </strong>
                <p>
                  {task.reason ||
                    "The task is unchecked; its activity and reason for remaining open have not been recorded."}
                </p>
                <p>
                  <strong>Next action:</strong>{" "}
                  {task.action ||
                    "Coordinator: inspect the task and its evidence, then record its actual state, owner and remaining acceptance step."}
                </p>
                <small>Owner: {task.owner || "Coordinator to assign"}</small>
              </article>
            ))}
        </div>
      </details>
      {metrics?.truncated && (
        <p role="alert">
          Earlier history is outside the 20,000-event display limit; totals may
          be incomplete.
        </p>
      )}
      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fit, minmax(min(100%, 550px), 1fr))",
          gap: 16,
        }}
      >
        {chart(
          "Cumulative completed tasks",
          taskTraces,
          "Completed tasks",
          x.length > 0,
        )}
        <div>
          {chart(
            "Observed checkbox completions",
            [
              {
                x: [...completionDays.keys()].map((d) => `${d}T00:00:00Z`),
                y: [...completionDays.values()],
                type: "bar",
                name: "Unchecked to checked",
                marker: { color: "#34d399" },
                width: 3600000,
                hovertemplate:
                  "%{x|%Y-%m-%d}<br>%{y} observed completions<extra></extra>",
              },
            ],
            "Tasks per day (UTC)",
            completionDays.size > 0,
            true,
            "No unchecked-to-checked transitions recorded in this period.",
          )}
          <p>
            {firstSeenChecked} tasks first appeared already checked in this
            period; excluded from completion counts.
          </p>
        </div>
        {chart(
          "Implementation, testing, review and integration",
          [
            {
              x: activity.map((e) => e.at),
              y: activity.map((e) => e.data.stage),
              type: "scatter",
              mode: "markers",
              marker: {
                size: 12,
                color: activity.map((e) =>
                  e.data.status === "failed"
                    ? "#fb7185"
                    : e.data.status === "completed"
                      ? "#34d399"
                      : "#38bdf8",
                ),
                symbol: activity.map((e) =>
                  e.data.status === "failed"
                    ? "x"
                    : e.data.status === "completed"
                      ? "diamond"
                      : "circle",
                ),
              },
              text: activity.map(
                (e) =>
                  `${e.feature} ${e.data.task}: ${e.data.status} — ${e.data.summary}`,
              ),
              hovertemplate: "%{x}<br>%{text}<extra></extra>",
              name: "Activity events",
            },
          ],
          "Stage",
          activity.length >= 3 &&
            new Set(activity.map((e) => e.data.stage)).size > 1,
          true,
          `Activity tracking incomplete: ${activity.length} events recorded across ${new Set(activity.map((e) => e.data.stage)).size} stages in this period. There is not enough coverage to show a development timeline.`,
        )}
        <div>
          <label>
            QA suite{" "}
            <select
              value={activeSuite ?? ""}
              onChange={(e) => setSuite(e.target.value)}
            >
              {suites.length ? (
                suites.map((s) => <option key={s}>{s}</option>)
              ) : (
                <option value="">Unavailable</option>
              )}
            </select>
          </label>
          {chart(
            "QA results over time",
            (["passed", "failed", "skipped", "not_run"] as const).map(
              (key, i) => ({
                x: qaPoints.map((e) => e.at),
                y: qaPoints.map((e) => e.data[key]),
                type: "scatter",
                mode: "markers",
                name: key.replace("_", " "),
                marker: {
                  color: ["#34d399", "#fb7185", "#fbbf24", "#94a3b8"][i],
                  size: 9,
                  symbol: ["circle", "x", "diamond", "square"][i],
                },
                text: qaPoints.map((e) => `${e.subject}: ${e.data.evidence}`),
                hovertemplate:
                  "%{x}<br>%{y}<br>%{text}<extra>%{fullData.name}</extra>",
              }),
            ),
            "Test cases per run",
            qaPoints.length > 0,
          )}
        </div>
        {chart(
          "Batch completion at latest observation",
          taskStates.map((state, i) => ({
            x: [...last.keys()],
            y: [...last.values()].map((p) => p.counts[state]),
            type: "bar",
            name: labels[i],
            marker: { color: colors[i] },
          })),
          "Tasks",
          last.size > 0,
          false,
        )}
        {chart(
          "Model usage over time",
          (["input", "output"] as const).map((kind) => ({
            x: bins.map(([time]) =>
              new Date(Math.max(start, time)).toISOString(),
            ),
            y: bins.map(([, totals]) => totals[kind]),
            type: "bar",
            name: kind === "input" ? "Input (includes cache)" : "Output",
            hovertemplate:
              "%{x}<br>%{y} tokens / 5-minute bucket<extra>%{fullData.name}</extra>",
          })),
          "Tokens per 5 minutes",
          usage.length > 0,
        )}
        {chart(
          "Verified and integrated work",
          taskStates.slice(4, 6).map((state, i) => ({
            x,
            y:
              i === 0
                ? y[4].map((value, index) =>
                    value === null ? null : value + (y[5][index] ?? 0),
                  )
                : y[5],
            type: "scatter",
            mode: "lines+markers",
            connectgaps: false,
            name: state,
            line: { shape: "hv", color: colors[i + 4] },
          })),
          "Tasks",
          hasVerification && x.length > 0,
          true,
          "Verification and integration are not being recorded for these tasks. Delivery progress is unknown.",
        )}
      </div>
      <details>
        <summary>Observation evidence and scope changes</summary>
        <p>
          QA points are individual attempts for one suite and environment, never
          added across reruns. Token values are reported deltas; absent usage is
          unknown. Historical task snapshots use commit times; live activity
          begins when collection is enabled.
        </p>
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Feature</th>
              <th>Observation</th>
              <th>Subject</th>
            </tr>
          </thead>
          <tbody>
            {visible
              .filter((e) => e.kind !== "heartbeat")
              .slice(-100)
              .map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.at).toLocaleString()}</td>
                  <td>{e.feature}</td>
                  <td>
                    {e.kind}
                    {e.kind === "task"
                      ? `: ${e.data.task} ${e.data.state} ${e.data.evidence}`
                      : e.kind === "qa"
                        ? `: ${e.data.suite} ${e.data.evidence}`
                        : ""}
                  </td>
                  <td>{e.subject}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}
