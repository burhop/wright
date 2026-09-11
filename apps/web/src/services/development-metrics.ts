import { z } from "zod";
import { hostAdapter } from "./host-adapter";

const text = z.string().max(1000);
const count = z.number().int().nonnegative().max(1e12);
export const taskStates = [
  "queued",
  "working",
  "qa",
  "implemented",
  "verified",
  "integrated",
  "withdrawn",
  "manual_validation",
] as const;
const base = {
  id: text,
  at: z.iso.datetime({ offset: true }),
  feature: text,
  subject: text,
};
const schema = z.discriminatedUnion("kind", [
  z.object({
    ...base,
    kind: z.literal("snapshot"),
    data: z.object({
      tasks: z
        .array(z.object({ task: text, title: text, checked: z.boolean() }))
        .max(10000),
    }),
  }),
  z.object({
    ...base,
    kind: z.literal("task"),
    data: z.object({
      task: text,
      title: text,
      state: z.enum(taskStates),
      evidence: text,
      reason: text.optional(),
      action: text.optional(),
      owner: text.optional(),
    }),
  }),
  z.object({
    ...base,
    kind: z.literal("activity"),
    data: z.object({
      task: text,
      stage: z.enum(["implementation", "testing", "review", "integration"]),
      status: z.enum(["started", "completed", "failed", "blocked"]),
      summary: text,
    }),
  }),
  z.object({
    ...base,
    kind: z.literal("qa"),
    data: z.object({
      suite: text,
      environment: text,
      passed: count,
      failed: count,
      skipped: count,
      not_run: count.nullable(),
      evidence: text,
    }),
  }),
  z.object({
    ...base,
    kind: z.literal("usage"),
    data: z.object({
      session: text,
      task: text,
      input_tokens: count,
      output_tokens: count,
    }),
  }),
  z.object({
    ...base,
    kind: z.literal("heartbeat"),
    data: z.object({ status: z.enum(["active", "stopped", "failed"]) }),
  }),
]);
export const metricsSchema = z.object({
  schema_version: z.literal(1),
  events: z.array(schema).max(20000),
  truncated: z.boolean(),
  availability: z.enum(["available", "unavailable"]),
});
export type Metrics = z.infer<typeof metricsSchema>;
export type MetricEvent = Metrics["events"][number];
export type TaskState = (typeof taskStates)[number];

export async function fetchDevelopmentMetrics(
  signal?: AbortSignal,
): Promise<Metrics> {
  const response = await hostAdapter.fetch(
    `${hostAdapter.getApiBaseUrl()}/api/program-status/metrics`,
    { signal, cache: "no-store" },
  );
  if (!response.ok) throw new Error("Activity history unavailable");
  return metricsSchema.parse(await response.json());
}

export function projectTasks(events: MetricEvent[]) {
  const tasks = new Map<
    string,
    {
      feature: string;
      title: string;
      state: TaskState;
      reason?: string;
      action?: string;
      owner?: string;
    }
  >();
  const points: {
    at: string;
    feature: string;
    counts: Record<TaskState, number>;
    change: string;
    committed: boolean;
    completed: number;
    firstSeenChecked: number;
  }[] = [];
  const counts = (feature: string) => {
    const result = Object.fromEntries(taskStates.map((s) => [s, 0])) as Record<
      TaskState,
      number
    >;
    for (const task of tasks.values())
      if (task.feature === feature) result[task.state]++;
    return result;
  };
  for (const event of events) {
    let change = "";
    let completed = 0;
    let firstSeenChecked = 0;
    if (event.kind === "snapshot") {
      const keys = new Set(
        event.data.tasks.map((task) => `${event.feature}:${task.task}`),
      );
      for (const [key, task] of tasks)
        if (task.feature === event.feature && !keys.has(key)) {
          if (task.state !== "withdrawn") change += "Task removed from scope. ";
          task.state = "withdrawn";
        }
      for (const task of event.data.tasks) {
        const key = `${event.feature}:${task.task}`;
        const prior = tasks.get(key);
        if (task.checked) {
          if (
            !prior ||
            prior.title !== task.title ||
            prior.state === "withdrawn"
          )
            firstSeenChecked++;
          else if (["queued", "working", "qa"].includes(prior.state))
            completed++;
        }
        let state: TaskState = task.checked ? "implemented" : "queued";
        if (!prior) change += "Scope added. ";
        else if (prior.title === task.title && prior.state !== "withdrawn") {
          const wasChecked = ["implemented", "verified", "integrated"].includes(
            prior.state,
          );
          if (wasChecked === task.checked) state = prior.state;
          else if (!task.checked) change += "Task reopened. ";
        } else change += "Task scope revised. ";
        tasks.set(key, {
          ...(prior?.title === task.title && prior.state === state
            ? prior
            : {}),
          feature: event.feature,
          title: task.title,
          state,
        });
      }
    } else if (event.kind === "task") {
      const prior = tasks.get(`${event.feature}:${event.data.task}`);
      if (
        prior &&
        ["verified", "integrated"].includes(prior.state) &&
        !["verified", "integrated"].includes(event.data.state)
      )
        change = "Task reopened";
      tasks.set(`${event.feature}:${event.data.task}`, {
        feature: event.feature,
        title: event.data.title,
        state: event.data.state,
        reason: event.data.reason,
        action: event.data.action,
        owner: event.data.owner,
      });
    } else if (event.kind !== "heartbeat") continue;
    const features =
      event.kind === "heartbeat"
        ? [...new Set([...tasks.values()].map((t) => t.feature))]
        : [event.feature];
    for (const feature of features)
      points.push({
        at: event.at,
        feature,
        counts: counts(feature),
        change,
        committed: event.id.startsWith("git:"),
        completed,
        firstSeenChecked,
      });
  }
  return { points, tasks };
}

// One chronological total, colored by the most recently introduced feature.
// Earlier batches retain their contribution without overlapping separate totals.
export function cumulativeTaskSeries(
  points: ReturnType<typeof projectTasks>["points"],
  start: number,
  end: number,
) {
  const totals = new Map<string, number>();
  const series: { feature: string; x: string[]; y: number[] }[] = [];
  const groups = new Map<string, typeof points>();
  for (const point of points) {
    if (Date.parse(point.at) > end) continue;
    const group = groups.get(point.at) ?? [];
    group.push(point);
    groups.set(point.at, group);
  }
  let total = 0;
  let owner = "";
  let current: (typeof series)[number] | undefined;
  for (const [at, group] of [...groups].sort(
    ([a], [b]) => Date.parse(a) - Date.parse(b),
  )) {
    const previous = total;
    for (const point of group) {
      if (!totals.has(point.feature)) owner = point.feature;
      totals.set(
        point.feature,
        point.counts.implemented +
          point.counts.verified +
          point.counts.integrated,
      );
    }
    total = [...totals.values()].reduce((a, b) => a + b, 0);
    if (Date.parse(at) < start) continue;
    if (!current || current.feature !== owner) {
      // End the preceding segment at the handoff, then start at that same total.
      if (current) {
        current.x.push(at);
        current.y.push(previous);
      }
      current = { feature: owner, x: [at], y: [previous] };
      if (!series.length && Date.parse(at) > start && previous > 0) {
        current.x.unshift(new Date(start).toISOString());
        current.y.unshift(previous);
      }
      series.push(current);
    }
    current.x.push(at);
    current.y.push(total);
  }
  return series;
}
