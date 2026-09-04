import contract from "../../../../specs/077-browser-program-status/contracts/program-status-bundle.schema.json";
import type { NativeMilestone } from "../components/program-status/NativeMilestone.types";

type Row = Record<string, unknown>;
type Schema = {
  type?: string;
  const?: unknown;
  enum?: unknown[];
  oneOf?: Schema[];
  properties?: Record<string, Schema>;
  required?: string[];
  additionalProperties?: boolean;
  items?: Schema;
  minItems?: number;
  maxItems?: number;
  minLength?: number;
  maxLength?: number;
  minimum?: number;
  pattern?: string;
  format?: string;
};
const fail = (): never => {
  throw new Error("Invalid native milestone projection");
};
const rows = (v: unknown) => v as Row[];
const strings = (v: unknown) => v as string[];
const object = (v: unknown) => v as Row;
function canonical(v: unknown): string {
  if (Array.isArray(v)) return `[${v.map(canonical).join(",")}]`;
  if (v !== null && typeof v === "object")
    return `{${Object.keys(v)
      .sort()
      .map((k) => `${JSON.stringify(k)}:${canonical(object(v)[k])}`)
      .join(",")}}`;
  return JSON.stringify(v);
}
function shape(v: unknown, s: Schema): boolean {
  if (s.oneOf) return s.oneOf.filter((option) => shape(v, option)).length === 1;
  if ("const" in s && v !== s.const) return false;
  if (s.enum && !s.enum.includes(v)) return false;
  if (s.type === "null") return v === null;
  if (s.type === "boolean") return typeof v === "boolean";
  if (s.type === "integer")
    return (
      Number.isSafeInteger(v) &&
      (s.minimum === undefined || (v as number) >= s.minimum)
    );
  if (s.type === "string")
    return (
      typeof v === "string" &&
      (s.minLength === undefined || v.length >= s.minLength) &&
      (s.maxLength === undefined || v.length <= s.maxLength) &&
      (!s.pattern || new RegExp(s.pattern).test(v)) &&
      (!s.format ||
        (s.format === "date-time" &&
          /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$/.test(
            v,
          ) &&
          Number.isFinite(Date.parse(v))))
    );
  if (s.type === "array")
    return (
      Array.isArray(v) &&
      (s.minItems === undefined || v.length >= s.minItems) &&
      (s.maxItems === undefined || v.length <= s.maxItems) &&
      v.every((item) => !s.items || shape(item, s.items))
    );
  if (s.type === "object") {
    if (v === null || typeof v !== "object" || Array.isArray(v)) return false;
    const o = object(v),
      properties = s.properties ?? {};
    return (
      (s.required ?? []).every((k) => k in o) &&
      Object.keys(o).every((k) =>
        k in properties
          ? shape(o[k], properties[k])
          : s.additionalProperties !== false,
      )
    );
  }
  return s.enum !== undefined || "const" in s;
}
const unique = (v: Row[], key = "id") => {
  const result = new Map(v.map((r) => [String(r[key]), r]));
  if (result.size !== v.length) fail();
  return result;
};
const status = (values: string[]) =>
  values.length && values.every((v) => v === "passed")
    ? "passed"
    : ([
        "invalid",
        "failed",
        "stale",
        "blocked",
        "skipped",
        "not_run",
        "unavailable",
        "inconclusive",
        "not_tested",
      ].find((v) => values.includes(v)) ?? "not_tested");

/** Validate the frozen optional contract and independently recompute all credit. */
export function decodeNativeMilestone(
  value: unknown,
  sourceCommit: string,
): NativeMilestone {
  const schema = contract.$defs.work.properties.milestone as Schema;
  if (!shape(value, schema)) fail();
  const v = object(value),
    source = object(v.source_record);
  if (v.source_commit !== sourceCommit) fail();
  const tasks = unique(rows(source.tasks)),
    projectedTasks = unique(rows(v.tasks));
  const checks = unique(rows(source.checks)),
    evidence = unique(rows(source.evidence));
  const criteria = unique(rows(source.acceptance)),
    blockers = unique(rows(source.blockers));
  const examples = unique(rows(source.examples)),
    attestations = unique(rows(v.attestations), "evidence_id");
  const subset = (ids: unknown, map: Map<string, Row>) =>
    strings(ids).every((id) => map.has(id));
  if (
    tasks.size !== projectedTasks.size ||
    !subset([...tasks.keys()], projectedTasks) ||
    attestations.size !== evidence.size ||
    !subset([...evidence.keys()], attestations) ||
    !subset(source.next_task_ids, tasks)
  )
    fail();
  let population = new Set<string>();
  rows(source.scope_history).forEach((r, i) => {
    const added = strings(r.added_task_ids),
      removed = strings(r.removed_task_ids);
    if (
      r.revision !== i + 1 ||
      added.some((id) => population.has(id) || removed.includes(id)) ||
      removed.some((id) => !population.has(id))
    )
      fail();
    population = new Set(
      [...population].filter((id) => !removed.includes(id)).concat(added),
    );
  });
  if (
    rows(source.scope_history).length !== source.scope_revision ||
    population.size !== tasks.size ||
    !subset([...population], tasks)
  )
    fail();
  for (const r of tasks.values())
    if (
      !subset(r.blocker_ids, blockers) ||
      Boolean(r.integration_exemption) === r.integration_required
    )
      fail();
  for (const r of blockers.values())
    if (!subset(r.task_ids, tasks) || !subset(r.check_ids, checks)) fail();
  for (const r of checks.values()) if (!subset(r.task_ids, tasks)) fail();
  for (const r of criteria.values())
    if (!subset(r.task_ids, tasks) || !subset(r.required_check_ids, checks))
      fail();
  for (const r of examples.values()) if (!subset(r.check_ids, checks)) fail();
  const latest = new Map<string, Row>(),
    attempts = new Set<string>();
  for (const r of evidence.values()) {
    const key = `${r.check_id}:${r.attempt}`,
      counts = r.counts === null ? null : object(r.counts);
    if (!checks.has(String(r.check_id)) || attempts.has(key)) fail();
    attempts.add(key);
    if (
      counts &&
      ["passed", "failed", "skipped", "not_run"].reduce(
        (n, k) => n + Number(counts[k]),
        0,
      ) !== counts.total
    )
      fail();
    if (
      Number(latest.get(String(r.check_id))?.attempt ?? 0) < Number(r.attempt)
    )
      latest.set(String(r.check_id), r);
  }
  const projectedChecks = [...checks.values()].map((check) => {
    const r = latest.get(String(check.id));
    let result = "not_tested",
      current: boolean | null = null;
    if (r) {
      const proof = attestations.get(String(r.id))!,
        counts = r.counts === null ? null : object(r.counts);
      current = proof.tested_scope_sha256 === proof.current_scope_sha256;
      result = String(r.result);
      if (
        !proof.commit_tree_matches ||
        !proof.artifacts_match ||
        proof.tested_scope_sha256 !== r.scope_sha256
      )
        result = "invalid";
      else if (result === "passed") {
        if (
          !rows(r.artifacts).length ||
          (check.independent_required &&
            (r.verifier_id === null || r.verifier_id === r.author_id)) ||
          (check.kind === "human_review" &&
            r.verification_actor_kind !== "human")
        )
          result = "invalid";
        else if (!current) result = "stale";
        else if (
          (check.stage === "integration" || check.kind === "dev_deployment") &&
          !v.delivery_attested
        )
          result = "unavailable";
        else if (
          counts &&
          (!counts.total || counts.failed || counts.skipped || counts.not_run)
        )
          result = "inconclusive";
      }
    }
    return {
      id: check.id,
      label: check.label,
      stage: check.stage,
      kind: check.kind,
      task_ids: check.task_ids,
      status: result,
      evidence_id: r?.id ?? null,
      observed_at: r?.observed_at ?? null,
      tested_commit: r?.tested_commit ?? null,
      coverage_current: current,
      counts: r?.counts ?? null,
      summary:
        r?.summary ?? "No result has been recorded for this required check.",
      artifact_urls: r
        ? rows(r.artifacts).map(
            (a) =>
              `https://github.com/burhop/wright/blob/${a.commit}/${a.path}`,
          )
        : [],
    };
  });
  const byCheck = unique(projectedChecks);
  const expectedTasks = [...tasks.values()].map((task) => {
    const existing = projectedTasks.get(String(task.id))!;
    const stage = (s: string) => {
      const result = status(
        projectedChecks
          .filter(
            (c) =>
              c.stage === s && strings(c.task_ids).includes(String(task.id)),
          )
          .map((c) => c.status),
      );
      return result === "passed" && !existing.implemented
        ? "not_tested"
        : result;
    };
    return {
      id: task.id,
      title: existing.title,
      activity: task.activity,
      owner: task.owner,
      implemented: existing.implemented,
      verification: stage("verification"),
      integration: task.integration_required
        ? stage("integration")
        : "not_applicable",
      integration_required: task.integration_required,
      blocker_ids: task.blocker_ids,
    };
  });
  const expectedCriteria = [...criteria.values()].map((c) => {
    const ids = strings(c.required_check_ids),
      missing = ids.filter((id) => byCheck.get(id)!.status !== "passed");
    let result = status(ids.map((id) => String(byCheck.get(id)!.status)));
    if (
      result === "passed" &&
      !strings(c.task_ids).every((id) => projectedTasks.get(id)!.implemented)
    )
      result = "not_tested";
    return {
      id: c.id,
      title: c.title,
      task_ids: c.task_ids,
      check_ids: ids,
      status: result,
      missing_check_ids: missing,
    };
  });
  const delivery = object(source.delivery);
  if (!subset(delivery.deployment_check_ids, checks)) fail();
  const deployment = status(
    strings(delivery.deployment_check_ids).map((id) =>
      String(byCheck.get(id)!.status),
    ),
  );
  const expectedExamples = [...examples.values()].map((e) => {
    const relevant = strings(e.check_ids).map((id) => byCheck.get(id)!);
    let maturity =
      relevant.length && relevant.every((c) => c.status === "passed")
        ? "tested"
        : "planned";
    if (
      maturity === "tested" &&
      relevant.some((c) => checks.get(String(c.id))!.independent_required)
    )
      maturity = "independently_verified";
    return { ...e, maturity };
  });
  const total = tasks.size,
    integratedTotal = expectedTasks.filter(
      (t) => t.integration_required,
    ).length;
  const expected = {
    id: source.id,
    title: source.title,
    feature_id: source.feature_id,
    scope_revision: source.scope_revision,
    scope_history: source.scope_history,
    source_commit: sourceCommit,
    observed_at: v.observed_at,
    candidate_commit: delivery.candidate_commit ?? sourceCommit,
    language_authority: source.language_authority,
    capabilities: source.capabilities,
    tasks: expectedTasks,
    acceptance: expectedCriteria,
    checks: projectedChecks,
    counts: {
      implementation: {
        completed: expectedTasks.filter((t) => t.implemented).length,
        total,
      },
      verification: {
        completed: expectedTasks.filter((t) => t.verification === "passed")
          .length,
        total,
      },
      integration: {
        completed: expectedTasks.filter((t) => t.integration === "passed")
          .length,
        total: integratedTotal,
        not_applicable: total - integratedTotal,
      },
    },
    blockers: source.blockers,
    next_task_ids: source.next_task_ids,
    examples: expectedExamples,
    delivery: { ...delivery, deployment_status: deployment },
    readiness: {
      native_milestone:
        expectedCriteria.every((c) => c.status === "passed") &&
        deployment === "passed" &&
        expectedTasks.every(
          (t) =>
            t.implemented &&
            t.verification === "passed" &&
            ["passed", "not_applicable"].includes(t.integration),
        )
          ? "complete"
          : "in_progress",
      benchmark: "not_qualified",
      commercial: "not_assessed",
      release: "not_authorized",
      rivet_migration: "not_started",
      rivet_retirement: "not_started",
    },
    source_record: source,
    attestations: v.attestations,
    delivery_attested: v.delivery_attested,
  };
  if (canonical(expected) !== canonical(value)) fail();
  return value as NativeMilestone;
}
