import { hostAdapter } from "./host-adapter";

export const PROGRAM_STATUS_SCHEMA_VERSION = "1.0.0" as const;

export interface EvidenceRef {
  id: string;
  path: string;
  sha256: string;
}

export interface EvidenceDetail extends EvidenceRef {
  label: string;
  summary: string;
  freshness: "current" | "stale" | "unavailable" | "unknown";
  recovery: string | null;
  availability: "checkout_available" | "exact_github" | "identity_only";
  exact_url: string | null;
}

export interface StatusAction {
  id: string;
  label: string;
  purpose: string;
  eligibility: "eligible" | "blocked" | "requires_approval" | "unavailable";
  authority_state:
    "authorized" | "not_authorized" | "not_required" | "stale" | "unavailable";
  requires_human_approval: boolean;
  blocker: string | null;
  evidence: EvidenceRef[];
}

export interface TaskCounts {
  completed: number;
  total: number;
  remaining: number;
}

export interface ProgramStatusObservation {
  commit: string;
  transition_id: string | null;
  parent_commit: string | null;
  observed_at: string;
  value: number;
  denominator: number | null;
  label: string;
  source_classification: string;
  change_reason: string | null;
  evidence: EvidenceRef[];
}

export interface ProgramStatusSeries {
  id: string;
  label: string;
  unit: string;
  counting_rule: string;
  source_classification: string;
  availability: "available" | "unavailable";
  feature_id: string | null;
  decision_use: string;
  current_limitation: string;
  next_action: StatusAction;
  latest_change: {
    commit: string;
    observed_at: string;
    from_value: number | null;
    to_value: number;
    reason: string;
  } | null;
  omitted_observations: number;
  unavailable_reason: string | null;
  observations: ProgramStatusObservation[];
}

export interface ProgramStatusBundle {
  schema_version: typeof PROGRAM_STATUS_SCHEMA_VERSION;
  bundle_id: string;
  generated_at: string;
  source: {
    commit: string;
    tree: string;
    program_tree: string;
    snapshot_path: string;
    snapshot_raw_sha256: string;
    raw_identity_verification: "publisher_git_blob_attested";
    raw_identity_evidence: EvidenceRef;
    dashboard_canonical_sha256: string;
    source_catalog_path: "specs/077-browser-program-status/contracts/program-status-source-catalog.json";
    source_catalog_sha256: string;
    validation_transition: string;
    validation_verdict: "passed";
  };
  dashboard: Readonly<Record<string, unknown>>;
  supplement: {
    history: ProgramStatusSeries[];
    customer_catalog: {
      proposed_total: number;
      source_path: string;
      source_digest: string;
      maturity_counts: Record<string, number>;
    };
    use_cases: {
      all: {
        total: number;
        not_started: number;
        in_progress: number;
        implemented: number;
        independently_verified: number;
        remaining: number;
      };
      process_100: {
        population_target: 100;
        defined: number;
        in_progress: number;
        implemented: number;
        tested: number;
        independently_verified: number;
        benchmark_qualified: number;
      };
      items: Array<Record<string, unknown>>;
    };
    test_history: {
      availability: "available" | "unavailable";
      unavailable_reason: string | null;
      checkpoints: Array<Record<string, unknown>>;
    };
    benchmark_context: {
      phase: string;
      hold_state: string;
      hold_reason: string | null;
      dependencies: Array<{
        id: string;
        label: string;
        status:
          | "satisfied"
          | "pending"
          | "blocked"
          | "not_authorized"
          | "unavailable";
        blocking: boolean;
        evidence: EvidenceRef[];
      }>;
      authorization_state: string;
      next_qualifying_action: StatusAction;
      evidence: EvidenceRef[];
    };
    work: {
      current_milestone: string;
      active_feature: string | null;
      program_tasks: TaskCounts & {
        registered_sources: string[];
        undecomposed_roadmap_items: string[];
      };
      tasks: TaskCounts & { feature_id: string };
      active_assignments: Array<Record<string, unknown>>;
      blockers: string[];
      current_next_action: StatusAction;
      lanes: Array<Record<string, unknown>>;
    };
    governance: Record<string, unknown>;
    evidence_index: EvidenceDetail[];
  };
}

export interface ProgramStatusPublisher {
  mode: "committed_watch" | "package_install" | "manual";
  state: "active" | "inactive" | "failed" | "unavailable";
  observed_commit: string | null;
  last_attempt_at: string | null;
  last_success_at: string | null;
  failure_code: string | null;
  recovery: string | null;
}

export interface ProgramStatusError {
  error_code: string;
  message: string;
  recovery_class: string;
  trace_id: string;
}

export interface ProgramStatusFetchResult {
  status: 200 | 304;
  etag: string | null;
  bundle: ProgramStatusBundle | null;
}

export class ProgramStatusDecodeError extends Error {
  readonly code: string;
  readonly path: string;

  constructor(code: string, path: string) {
    super(`${code} at ${path || "/"}`);
    this.code = code;
    this.path = path;
  }
}

export class ProgramStatusServiceError extends Error {
  readonly detail: ProgramStatusError;

  constructor(detail: ProgramStatusError) {
    super(detail.message);
    this.detail = detail;
  }
}

function record(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ProgramStatusDecodeError("EXPECTED_OBJECT", path);
  }
  return value as Record<string, unknown>;
}

function exact(
  value: Record<string, unknown>,
  keys: readonly string[],
  path: string,
): void {
  for (const key of keys) {
    if (!(key in value))
      throw new ProgramStatusDecodeError("MISSING_FIELD", `${path}/${key}`);
  }
  for (const key of Object.keys(value)) {
    if (!keys.includes(key))
      throw new ProgramStatusDecodeError("UNKNOWN_FIELD", `${path}/${key}`);
  }
}

function stringValue(value: unknown, path: string): string {
  if (typeof value !== "string")
    throw new ProgramStatusDecodeError("EXPECTED_STRING", path);
  return value;
}

function nullableString(value: unknown, path: string): string | null {
  return value === null ? null : stringValue(value, path);
}

function integer(value: unknown, path: string): number {
  if (!Number.isSafeInteger(value) || (value as number) < 0) {
    throw new ProgramStatusDecodeError("EXPECTED_NONNEGATIVE_INTEGER", path);
  }
  return value as number;
}

function booleanValue(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throw new ProgramStatusDecodeError("BOOLEAN_REQUIRED", path);
  }
  return value;
}

function hex(value: unknown, length: 40 | 64, path: string): string {
  const parsed = stringValue(value, path);
  if (!new RegExp(`^[0-9a-f]{${length}}$`).test(parsed)) {
    throw new ProgramStatusDecodeError("IDENTITY_FORMAT_INVALID", path);
  }
  return parsed;
}

function array(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value))
    throw new ProgramStatusDecodeError("EXPECTED_ARRAY", path);
  return value;
}

function evidence(value: unknown, path: string): EvidenceRef {
  const row = record(value, path);
  exact(row, ["id", "path", "sha256"], path);
  return {
    id: stringValue(row.id, `${path}/id`),
    path: stringValue(row.path, `${path}/path`),
    sha256: stringValue(row.sha256, `${path}/sha256`),
  };
}

const relativePathPattern =
  /^(?!.*(?:^|\/)\.{1,2}(?:\/|$))(?!.*\/\/)[A-Za-z0-9_-][A-Za-z0-9._-]*(?:\/[A-Za-z0-9_-][A-Za-z0-9._-]*)*$/;
const exactGitHubPattern =
  /^https:\/\/github\.com\/burhop\/wright\/blob\/[0-9a-f]{40}\/[A-Za-z0-9_-][A-Za-z0-9._-]*(?:\/[A-Za-z0-9_-][A-Za-z0-9._-]*)*$/;

function enumValue<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  const parsed = stringValue(value, path);
  if (!allowed.includes(parsed as T))
    throw new ProgramStatusDecodeError("ENUM_INVALID", path);
  return parsed as T;
}

function evidenceDetail(value: unknown, path: string): EvidenceDetail {
  const row = record(value, path);
  exact(
    row,
    [
      "id",
      "label",
      "path",
      "sha256",
      "summary",
      "freshness",
      "recovery",
      "availability",
      "exact_url",
    ],
    path,
  );
  const parsedPath = stringValue(row.path, `${path}/path`);
  if (!relativePathPattern.test(parsedPath))
    throw new ProgramStatusDecodeError("UNSAFE_EVIDENCE_PATH", `${path}/path`);
  const sha256 = stringValue(row.sha256, `${path}/sha256`);
  if (!/^[0-9a-f]{64}$/.test(sha256))
    throw new ProgramStatusDecodeError("DIGEST_INVALID", `${path}/sha256`);
  const availability = enumValue(
    row.availability,
    ["checkout_available", "exact_github", "identity_only"] as const,
    `${path}/availability`,
  );
  const exactUrl = nullableString(row.exact_url, `${path}/exact_url`);
  if (exactUrl !== null && !exactGitHubPattern.test(exactUrl))
    throw new ProgramStatusDecodeError(
      "UNSAFE_EVIDENCE_URL",
      `${path}/exact_url`,
    );
  if (availability === "exact_github" && exactUrl === null)
    throw new ProgramStatusDecodeError(
      "MISSING_EXACT_URL",
      `${path}/exact_url`,
    );
  return {
    id: stringValue(row.id, `${path}/id`),
    label: stringValue(row.label, `${path}/label`),
    path: parsedPath,
    sha256,
    summary: stringValue(row.summary, `${path}/summary`),
    freshness: enumValue(
      row.freshness,
      ["current", "stale", "unavailable", "unknown"] as const,
      `${path}/freshness`,
    ),
    recovery: nullableString(row.recovery, `${path}/recovery`),
    availability,
    exact_url: exactUrl,
  };
}

function action(value: unknown, path: string): StatusAction {
  const row = record(value, path);
  exact(
    row,
    [
      "id",
      "label",
      "purpose",
      "eligibility",
      "authority_state",
      "requires_human_approval",
      "blocker",
      "evidence",
    ],
    path,
  );
  if (typeof row.requires_human_approval !== "boolean") {
    throw new ProgramStatusDecodeError(
      "EXPECTED_BOOLEAN",
      `${path}/requires_human_approval`,
    );
  }
  return {
    id: stringValue(row.id, `${path}/id`),
    label: stringValue(row.label, `${path}/label`),
    purpose: stringValue(row.purpose, `${path}/purpose`),
    eligibility: enumValue(
      row.eligibility,
      ["eligible", "blocked", "requires_approval", "unavailable"] as const,
      `${path}/eligibility`,
    ),
    authority_state: enumValue(
      row.authority_state,
      [
        "authorized",
        "not_authorized",
        "not_required",
        "stale",
        "unavailable",
      ] as const,
      `${path}/authority_state`,
    ),
    requires_human_approval: row.requires_human_approval,
    blocker: nullableString(row.blocker, `${path}/blocker`),
    evidence: array(row.evidence, `${path}/evidence`).map((item, index) =>
      evidence(item, `${path}/evidence/${index}`),
    ),
  };
}

function counts(value: unknown, path: string): TaskCounts {
  const row = record(value, path);
  const result = {
    completed: integer(row.completed, `${path}/completed`),
    total: integer(row.total, `${path}/total`),
    remaining: integer(row.remaining, `${path}/remaining`),
  };
  if (result.completed + result.remaining !== result.total) {
    throw new ProgramStatusDecodeError("TASK_ARITHMETIC_INVALID", path);
  }
  return result;
}

function validateUseCaseInventory(
  useCases: Record<string, unknown>,
  all: ProgramStatusBundle["supplement"]["use_cases"]["all"],
  process: ProgramStatusBundle["supplement"]["use_cases"]["process_100"],
  dashboard: Record<string, unknown>,
): Array<Record<string, unknown>> {
  const rawItems = array(useCases.items, "/supplement/use_cases/items");
  const items = rawItems.map((value, itemIndex) => {
    const path = `/supplement/use_cases/items/${itemIndex}`;
    const item = record(value, path);
    exact(
      item,
      [
        "id",
        "title",
        "customer_outcome",
        "process_100_id",
        "definition_evidence",
        "progress_evidence",
        "acceptance_evidence",
        "test_evidence",
        "independent_verification_evidence",
        "benchmark_qualification_evidence",
      ],
      path,
    );
    stringValue(item.id, `${path}/id`);
    stringValue(item.title, `${path}/title`);
    stringValue(item.customer_outcome, `${path}/customer_outcome`);
    nullableString(item.process_100_id, `${path}/process_100_id`);
    for (const stageName of [
      "definition_evidence",
      "progress_evidence",
      "acceptance_evidence",
      "test_evidence",
      "independent_verification_evidence",
      "benchmark_qualification_evidence",
    ] as const) {
      array(item[stageName], `${path}/${stageName}`).forEach(
        (stageValue, stageIndex) => {
          const stagePath = `${path}/${stageName}/${stageIndex}`;
          const stage = record(stageValue, stagePath);
          exact(
            stage,
            [
              "evidence_class",
              "source_name",
              "subject_id",
              "verdict",
              "acceptance_subject_id",
              "evidence_author",
              "independent_verifier",
              "evidence",
            ],
            stagePath,
          );
          stringValue(stage.evidence_class, `${stagePath}/evidence_class`);
          stringValue(stage.source_name, `${stagePath}/source_name`);
          stringValue(stage.subject_id, `${stagePath}/subject_id`);
          stringValue(stage.verdict, `${stagePath}/verdict`);
          nullableString(
            stage.acceptance_subject_id,
            `${stagePath}/acceptance_subject_id`,
          );
          nullableString(stage.evidence_author, `${stagePath}/evidence_author`);
          nullableString(
            stage.independent_verifier,
            `${stagePath}/independent_verifier`,
          );
          evidence(stage.evidence, `${stagePath}/evidence`);
        },
      );
    }
    return item;
  });
  const ids = items.map((item) => item.id as string);
  if (new Set(ids).size !== ids.length || items.length !== all.total) {
    throw new ProgramStatusDecodeError(
      "USE_CASE_INVENTORY_INVALID",
      "/supplement/use_cases/items",
    );
  }
  const processIds = items
    .map((item) => item.process_100_id as string | null)
    .filter((value): value is string => value !== null);
  if (
    new Set(processIds).size !== processIds.length ||
    processIds.some(
      (value) => !/^EPP-PROC-(?:00[1-9]|0[1-9][0-9]|100)$/.test(value),
    )
  ) {
    throw new ProgramStatusDecodeError(
      "PROCESS_IDENTITY_INVALID",
      "/supplement/use_cases/items",
    );
  }
  const derivedAll = {
    total: items.length,
    not_started: 0,
    in_progress: 0,
    implemented: 0,
    independently_verified: 0,
    remaining: 0,
  };
  const derivedProcess = {
    population_target: 100 as const,
    defined: 0,
    in_progress: 0,
    implemented: 0,
    tested: 0,
    independently_verified: 0,
    benchmark_qualified: 0,
  };
  for (const item of items) {
    const acceptance = item.acceptance_evidence as Array<
      Record<string, unknown>
    >;
    const progress = item.progress_evidence as Array<Record<string, unknown>>;
    const verification = item.independent_verification_evidence as Array<
      Record<string, unknown>
    >;
    const qualification = item.benchmark_qualification_evidence as Array<
      Record<string, unknown>
    >;
    const testEvidence = item.test_evidence as Array<Record<string, unknown>>;
    const acceptanceIds = new Set(
      acceptance.map((stage) => stage.subject_id as string),
    );
    const identities = new Set<string>();
    for (const stageName of [
      "definition_evidence",
      "progress_evidence",
      "acceptance_evidence",
      "test_evidence",
      "independent_verification_evidence",
      "benchmark_qualification_evidence",
    ] as const) {
      for (const stage of item[stageName] as Array<Record<string, unknown>>) {
        const ref = stage.evidence as EvidenceRef;
        const identity = `${stage.source_name}\u0000${stage.subject_id}\u0000${ref.sha256}`;
        if (identities.has(identity)) {
          throw new ProgramStatusDecodeError(
            "USE_CASE_STAGE_REUSE_INVALID",
            "/supplement/use_cases/items",
          );
        }
        identities.add(identity);
      }
    }
    for (const stage of verification) {
      if (
        !acceptanceIds.has(stage.acceptance_subject_id as string) ||
        stage.evidence_author === stage.independent_verifier
      ) {
        throw new ProgramStatusDecodeError(
          "USE_CASE_VERIFICATION_INVALID",
          "/supplement/use_cases/items",
        );
      }
    }
    for (const stage of qualification) {
      if (
        stage.subject_id !== item.process_100_id ||
        !acceptanceIds.has(stage.acceptance_subject_id as string) ||
        stage.evidence_author === stage.independent_verifier ||
        verification.length === 0
      ) {
        throw new ProgramStatusDecodeError(
          "USE_CASE_QUALIFICATION_INVALID",
          "/supplement/use_cases/items",
        );
      }
    }
    const implemented = acceptance.length > 0;
    const verified = verification.length > 0;
    const inProgress = !implemented && progress.length > 0;
    derivedAll.implemented += Number(implemented);
    derivedAll.independently_verified += Number(verified);
    derivedAll.in_progress += Number(inProgress);
    derivedAll.not_started += Number(!implemented && !inProgress);
    if (item.process_100_id !== null) {
      derivedProcess.defined += Number(
        (item.definition_evidence as unknown[]).length > 0,
      );
      derivedProcess.in_progress += Number(inProgress);
      derivedProcess.implemented += Number(implemented);
      derivedProcess.tested += Number(
        testEvidence.some((stage) => stage.verdict === "passed"),
      );
      derivedProcess.independently_verified += Number(verified);
      derivedProcess.benchmark_qualified += Number(qualification.length > 0);
    }
  }
  derivedAll.remaining = derivedAll.total - derivedAll.implemented;
  if (JSON.stringify(derivedAll) !== JSON.stringify(all)) {
    throw new ProgramStatusDecodeError(
      "USE_CASE_ARITHMETIC_INVALID",
      "/supplement/use_cases/all",
    );
  }
  if (JSON.stringify(derivedProcess) !== JSON.stringify(process)) {
    throw new ProgramStatusDecodeError(
      "PROCESS_FUNNEL_INVALID",
      "/supplement/use_cases/process_100",
    );
  }
  const benchmarkSummary = record(
    dashboard.benchmark_summary,
    "/dashboard/benchmark_summary",
  );
  if (
    derivedProcess.benchmark_qualified !==
    integer(benchmarkSummary.counted, "/dashboard/benchmark_summary/counted")
  ) {
    throw new ProgramStatusDecodeError(
      "BENCHMARK_QUALIFICATION_INVALID",
      "/supplement/use_cases/process_100/benchmark_qualified",
    );
  }
  return items;
}

export function decodeProgramStatusBundle(value: unknown): ProgramStatusBundle {
  const root = record(value, "");
  exact(
    root,
    [
      "schema_version",
      "bundle_id",
      "generated_at",
      "source",
      "dashboard",
      "supplement",
    ],
    "",
  );
  if (root.schema_version !== PROGRAM_STATUS_SCHEMA_VERSION) {
    throw new ProgramStatusDecodeError(
      "UNSUPPORTED_VERSION",
      "/schema_version",
    );
  }
  const source = record(root.source, "/source");
  exact(
    source,
    [
      "commit",
      "tree",
      "program_tree",
      "snapshot_path",
      "snapshot_raw_sha256",
      "raw_identity_verification",
      "raw_identity_evidence",
      "dashboard_canonical_sha256",
      "source_catalog_path",
      "source_catalog_sha256",
      "validation_transition",
      "validation_verdict",
    ],
    "/source",
  );
  if (
    source.raw_identity_verification !== "publisher_git_blob_attested" ||
    source.validation_verdict !== "passed"
  ) {
    throw new ProgramStatusDecodeError(
      "IDENTITY_ATTESTATION_INVALID",
      "/source",
    );
  }
  const supplement = record(root.supplement, "/supplement");
  exact(
    supplement,
    [
      "history",
      "customer_catalog",
      "use_cases",
      "test_history",
      "benchmark_context",
      "work",
      "governance",
      "evidence_index",
    ],
    "/supplement",
  );
  const catalog = record(
    supplement.customer_catalog,
    "/supplement/customer_catalog",
  );
  const useCases = record(supplement.use_cases, "/supplement/use_cases");
  const allCases = record(useCases.all, "/supplement/use_cases/all");
  const processCases = record(
    useCases.process_100,
    "/supplement/use_cases/process_100",
  );
  const testHistory = record(
    supplement.test_history,
    "/supplement/test_history",
  );
  const benchmark = record(
    supplement.benchmark_context,
    "/supplement/benchmark_context",
  );
  const work = record(supplement.work, "/supplement/work");
  const programTaskRow = record(
    work.program_tasks,
    "/supplement/work/program_tasks",
  );
  const featureTaskRow = record(work.tasks, "/supplement/work/tasks");
  const programCounts = counts(
    programTaskRow,
    "/supplement/work/program_tasks",
  );
  const featureCounts = counts(featureTaskRow, "/supplement/work/tasks");
  const all = {
    total: integer(allCases.total, "/supplement/use_cases/all/total"),
    not_started: integer(
      allCases.not_started,
      "/supplement/use_cases/all/not_started",
    ),
    in_progress: integer(
      allCases.in_progress,
      "/supplement/use_cases/all/in_progress",
    ),
    implemented: integer(
      allCases.implemented,
      "/supplement/use_cases/all/implemented",
    ),
    independently_verified: integer(
      allCases.independently_verified,
      "/supplement/use_cases/all/independently_verified",
    ),
    remaining: integer(
      allCases.remaining,
      "/supplement/use_cases/all/remaining",
    ),
  };
  if (all.implemented + all.remaining !== all.total) {
    throw new ProgramStatusDecodeError(
      "USE_CASE_ARITHMETIC_INVALID",
      "/supplement/use_cases/all",
    );
  }
  const process100 = {
    population_target: integer(
      processCases.population_target,
      "/supplement/use_cases/process_100/population_target",
    ) as 100,
    defined: integer(
      processCases.defined,
      "/supplement/use_cases/process_100/defined",
    ),
    in_progress: integer(
      processCases.in_progress,
      "/supplement/use_cases/process_100/in_progress",
    ),
    implemented: integer(
      processCases.implemented,
      "/supplement/use_cases/process_100/implemented",
    ),
    tested: integer(
      processCases.tested,
      "/supplement/use_cases/process_100/tested",
    ),
    independently_verified: integer(
      processCases.independently_verified,
      "/supplement/use_cases/process_100/independently_verified",
    ),
    benchmark_qualified: integer(
      processCases.benchmark_qualified,
      "/supplement/use_cases/process_100/benchmark_qualified",
    ),
  };
  const useCaseItems = validateUseCaseInventory(
    useCases,
    all,
    process100,
    record(root.dashboard, "/dashboard"),
  );
  const proposedTotal = integer(
    catalog.proposed_total,
    "/supplement/customer_catalog/proposed_total",
  );
  if (proposedTotal !== 100)
    throw new ProgramStatusDecodeError(
      "CATALOG_TOTAL_INVALID",
      "/supplement/customer_catalog/proposed_total",
    );
  return {
    schema_version: PROGRAM_STATUS_SCHEMA_VERSION,
    bundle_id: hex(root.bundle_id, 64, "/bundle_id"),
    generated_at: stringValue(root.generated_at, "/generated_at"),
    source: {
      commit: hex(source.commit, 40, "/source/commit"),
      tree: hex(source.tree, 40, "/source/tree"),
      program_tree: hex(source.program_tree, 40, "/source/program_tree"),
      snapshot_path: stringValue(source.snapshot_path, "/source/snapshot_path"),
      snapshot_raw_sha256: hex(
        source.snapshot_raw_sha256,
        64,
        "/source/snapshot_raw_sha256",
      ),
      raw_identity_verification: "publisher_git_blob_attested",
      raw_identity_evidence: evidence(
        source.raw_identity_evidence,
        "/source/raw_identity_evidence",
      ),
      dashboard_canonical_sha256: hex(
        source.dashboard_canonical_sha256,
        64,
        "/source/dashboard_canonical_sha256",
      ),
      source_catalog_path: stringValue(
        source.source_catalog_path,
        "/source/source_catalog_path",
      ) as ProgramStatusBundle["source"]["source_catalog_path"],
      source_catalog_sha256: hex(
        source.source_catalog_sha256,
        64,
        "/source/source_catalog_sha256",
      ),
      validation_transition: stringValue(
        source.validation_transition,
        "/source/validation_transition",
      ),
      validation_verdict: "passed",
    },
    dashboard: record(root.dashboard, "/dashboard"),
    supplement: {
      history: array(
        supplement.history,
        "/supplement/history",
      ) as ProgramStatusSeries[],
      customer_catalog: {
        proposed_total: proposedTotal,
        source_path: stringValue(
          catalog.source_path,
          "/supplement/customer_catalog/source_path",
        ),
        source_digest: stringValue(
          catalog.source_digest,
          "/supplement/customer_catalog/source_digest",
        ),
        maturity_counts: record(
          catalog.maturity_counts,
          "/supplement/customer_catalog/maturity_counts",
        ) as Record<string, number>,
      },
      use_cases: {
        all,
        process_100: process100,
        items: useCaseItems,
      },
      test_history: {
        availability: stringValue(
          testHistory.availability,
          "/supplement/test_history/availability",
        ) as "available" | "unavailable",
        unavailable_reason: nullableString(
          testHistory.unavailable_reason,
          "/supplement/test_history/unavailable_reason",
        ),
        checkpoints: array(
          testHistory.checkpoints,
          "/supplement/test_history/checkpoints",
        ) as Array<Record<string, unknown>>,
      },
      benchmark_context: {
        phase: stringValue(
          benchmark.phase,
          "/supplement/benchmark_context/phase",
        ),
        hold_state: stringValue(
          benchmark.hold_state,
          "/supplement/benchmark_context/hold_state",
        ),
        hold_reason: nullableString(
          benchmark.hold_reason,
          "/supplement/benchmark_context/hold_reason",
        ),
        dependencies: array(
          benchmark.dependencies,
          "/supplement/benchmark_context/dependencies",
        ).map((item, index) => {
          const dependency = record(
            item,
            `/supplement/benchmark_context/dependencies/${index}`,
          );
          return {
            id: stringValue(
              dependency.id,
              `/supplement/benchmark_context/dependencies/${index}/id`,
            ),
            label: stringValue(
              dependency.label,
              `/supplement/benchmark_context/dependencies/${index}/label`,
            ),
            status: enumValue(
              dependency.status,
              [
                "satisfied",
                "pending",
                "blocked",
                "not_authorized",
                "unavailable",
              ] as const,
              `/supplement/benchmark_context/dependencies/${index}/status`,
            ),
            blocking: booleanValue(
              dependency.blocking,
              `/supplement/benchmark_context/dependencies/${index}/blocking`,
            ),
            evidence: array(
              dependency.evidence,
              `/supplement/benchmark_context/dependencies/${index}/evidence`,
            ).map((reference, evidenceIndex) =>
              evidence(
                reference,
                `/supplement/benchmark_context/dependencies/${index}/evidence/${evidenceIndex}`,
              ),
            ),
          };
        }),
        authorization_state: stringValue(
          benchmark.authorization_state,
          "/supplement/benchmark_context/authorization_state",
        ),
        next_qualifying_action: action(
          benchmark.next_qualifying_action,
          "/supplement/benchmark_context/next_qualifying_action",
        ),
        evidence: array(
          benchmark.evidence,
          "/supplement/benchmark_context/evidence",
        ).map((reference, index) =>
          evidence(
            reference,
            `/supplement/benchmark_context/evidence/${index}`,
          ),
        ),
      },
      work: {
        current_milestone: stringValue(
          work.current_milestone,
          "/supplement/work/current_milestone",
        ),
        active_feature:
          work.active_feature === null
            ? null
            : stringValue(
                work.active_feature,
                "/supplement/work/active_feature",
              ),
        program_tasks: {
          ...programCounts,
          registered_sources: array(
            programTaskRow.registered_sources,
            "/supplement/work/program_tasks/registered_sources",
          ).map((item, index) =>
            stringValue(
              item,
              `/supplement/work/program_tasks/registered_sources/${index}`,
            ),
          ),
          undecomposed_roadmap_items: array(
            programTaskRow.undecomposed_roadmap_items,
            "/supplement/work/program_tasks/undecomposed_roadmap_items",
          ).map((item, index) =>
            stringValue(
              item,
              `/supplement/work/program_tasks/undecomposed_roadmap_items/${index}`,
            ),
          ),
        },
        tasks: {
          ...featureCounts,
          feature_id: stringValue(
            featureTaskRow.feature_id,
            "/supplement/work/tasks/feature_id",
          ),
        },
        active_assignments: array(
          work.active_assignments,
          "/supplement/work/active_assignments",
        ) as Array<Record<string, unknown>>,
        blockers: array(work.blockers, "/supplement/work/blockers").map(
          (item, index) =>
            stringValue(item, `/supplement/work/blockers/${index}`),
        ),
        current_next_action: action(
          work.current_next_action,
          "/supplement/work/current_next_action",
        ),
        lanes: array(work.lanes, "/supplement/work/lanes") as Array<
          Record<string, unknown>
        >,
      },
      governance: record(supplement.governance, "/supplement/governance"),
      evidence_index: array(
        supplement.evidence_index,
        "/supplement/evidence_index",
      ).map((item, index) =>
        evidenceDetail(item, `/supplement/evidence_index/${index}`),
      ),
    },
  };
}

export function decodeProgramStatusPublisher(
  value: unknown,
): ProgramStatusPublisher {
  const row = record(value, "");
  exact(
    row,
    [
      "state",
      "mode",
      "observed_commit",
      "last_attempt_at",
      "last_success_at",
      "failure_code",
      "recovery",
    ],
    "",
  );
  return {
    state: enumValue(
      row.state,
      ["active", "inactive", "failed", "unavailable"] as const,
      "/state",
    ),
    mode: enumValue(
      row.mode,
      ["committed_watch", "package_install", "manual"] as const,
      "/mode",
    ),
    observed_commit: nullableString(row.observed_commit, "/observed_commit"),
    last_attempt_at: nullableString(row.last_attempt_at, "/last_attempt_at"),
    last_success_at: nullableString(row.last_success_at, "/last_success_at"),
    failure_code: nullableString(row.failure_code, "/failure_code"),
    recovery: nullableString(row.recovery, "/recovery"),
  };
}

function canonicalNumber(value: number): string {
  if (!Number.isFinite(value) || Object.is(value, -0)) {
    throw new ProgramStatusDecodeError("CANONICAL_NUMBER_INVALID", "");
  }
  if (Number.isInteger(value)) {
    if (!Number.isSafeInteger(value)) {
      throw new ProgramStatusDecodeError("CANONICAL_NUMBER_UNSAFE", "");
    }
    return String(value);
  }
  const magnitude = Math.abs(value);
  if (magnitude >= 1e-4 && magnitude < 1e16) return String(value);
  const scientific = value.toExponential();
  const match = /^(.*)e([+-])(\d+)$/.exec(scientific);
  if (!match)
    throw new ProgramStatusDecodeError("CANONICAL_NUMBER_INVALID", "");
  return `${match[1]}e${match[2]}${match[3].padStart(2, "0")}`;
}

export function canonicalProgramStatusJson(value: unknown): string {
  if (value === null) return "null";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") return canonicalNumber(value);
  if (Array.isArray(value)) {
    return `[${value.map(canonicalProgramStatusJson).join(",")}]`;
  }
  if (typeof value === "object") {
    const row = value as Record<string, unknown>;
    return `{${Object.keys(row)
      .sort()
      .map(
        (key) =>
          `${JSON.stringify(key)}:${canonicalProgramStatusJson(row[key])}`,
      )
      .join(",")}}`;
  }
  throw new ProgramStatusDecodeError("CANONICAL_VALUE_INVALID", "");
}

export async function canonicalProgramStatusDigest(
  value: unknown,
): Promise<string> {
  const raw = new TextEncoder().encode(canonicalProgramStatusJson(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", raw);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

async function framedProgramStatusDigest(
  prefix: string,
  values: string[],
): Promise<string> {
  const encoder = new TextEncoder();
  const chunks: Uint8Array[] = [encoder.encode(`${prefix}\n`)];
  for (const value of values) {
    if (value.includes("\0") || value.normalize("NFC") !== value) {
      throw new ProgramStatusDecodeError("TEST_IDENTITY_INPUT_INVALID", "");
    }
    const encoded = encoder.encode(value);
    chunks.push(
      encoder.encode(`${encoded.length}:`),
      encoded,
      encoder.encode("\n"),
    );
  }
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const framed = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    framed.set(chunk, offset);
    offset += chunk.length;
  }
  const digest = await globalThis.crypto.subtle.digest("SHA-256", framed);
  return Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
}

function utf8Compare(left: string, right: string): number {
  const encoder = new TextEncoder();
  const leftBytes = encoder.encode(left);
  const rightBytes = encoder.encode(right);
  for (
    let index = 0;
    index < Math.min(leftBytes.length, rightBytes.length);
    index += 1
  ) {
    if (leftBytes[index] !== rightBytes[index])
      return leftBytes[index] - rightBytes[index];
  }
  return leftBytes.length - rightBytes.length;
}

async function verifyTestHistoryDigests(
  supplement: Record<string, unknown>,
): Promise<void> {
  const testHistory = record(
    supplement.test_history,
    "/supplement/test_history",
  );
  for (const [checkpointIndex, checkpointValue] of array(
    testHistory.checkpoints,
    "/supplement/test_history/checkpoints",
  ).entries()) {
    const checkpointPath = `/supplement/test_history/checkpoints/${checkpointIndex}`;
    const checkpoint = record(checkpointValue, checkpointPath);
    for (const [sourceIndex, sourceValue] of array(
      checkpoint.suite_sources,
      `${checkpointPath}/suite_sources`,
    ).entries()) {
      const sourcePath = `${checkpointPath}/suite_sources/${sourceIndex}`;
      const suite = record(sourceValue, sourcePath);
      const cases = array(
        suite.test_case_ids,
        `${sourcePath}/test_case_ids`,
      ).map((item, index) =>
        stringValue(item, `${sourcePath}/test_case_ids/${index}`),
      );
      if (new Set(cases).size !== cases.length) {
        throw new ProgramStatusDecodeError(
          "TEST_CASE_ID_DUPLICATE",
          `${sourcePath}/test_case_ids`,
        );
      }
      const caseDigest = await framedProgramStatusDigest(
        "wright-test-id-set-v1",
        [...cases].sort(utf8Compare),
      );
      if (
        caseDigest !==
        hex(
          suite.test_case_set_sha256,
          64,
          `${sourcePath}/test_case_set_sha256`,
        )
      ) {
        throw new ProgramStatusDecodeError(
          "TEST_CASE_SET_IDENTITY_MISMATCH",
          `${sourcePath}/test_case_set_sha256`,
        );
      }
      const runDigest = await framedProgramStatusDigest(
        "wright-test-run-key-v1",
        [
          hex(checkpoint.commit, 40, `${checkpointPath}/commit`),
          stringValue(suite.suite_id, `${sourcePath}/suite_id`),
          stringValue(suite.population_id, `${sourcePath}/population_id`),
          String(integer(suite.attempt, `${sourcePath}/attempt`)),
        ],
      );
      if (runDigest !== hex(suite.run_key, 64, `${sourcePath}/run_key`)) {
        throw new ProgramStatusDecodeError(
          "TEST_RUN_KEY_MISMATCH",
          `${sourcePath}/run_key`,
        );
      }
    }
  }
}

function sameEvidence(left: EvidenceRef, right: EvidenceDetail): boolean {
  return (
    left.id === right.id &&
    left.path === right.path &&
    left.sha256 === right.sha256
  );
}

type LocatedEvidence = {
  reference: EvidenceRef;
  path: Array<string | number>;
};

function evidenceReferences(
  value: unknown,
  rootPath: Array<string | number> = [],
): LocatedEvidence[] {
  const references: LocatedEvidence[] = [];
  const visit = (item: unknown, path: Array<string | number>) => {
    const key = path.at(-1);
    if (key === "evidence_index") return;
    if (Array.isArray(item)) {
      item.forEach((candidate, index) => visit(candidate, [...path, index]));
      return;
    }
    if (typeof item !== "object" || item === null) return;
    const row = item as Record<string, unknown>;
    const keys = Object.keys(row).sort();
    if (
      keys.length === 3 &&
      keys[0] === "id" &&
      keys[1] === "path" &&
      keys[2] === "sha256"
    ) {
      references.push({
        reference: evidence(row, `/${path.join("/") || "evidence"}`),
        path,
      });
      return;
    }
    for (const [childKey, child] of Object.entries(item)) {
      visit(child, [...path, childKey]);
    }
  };
  visit(value, rootPath);
  return references;
}

export function validateProgramStatusEvidenceRelations(value: unknown): void {
  const root = record(value, "");
  const source = record(root.source, "/source");
  const supplement = record(root.supplement, "/supplement");
  const details = array(
    supplement.evidence_index,
    "/supplement/evidence_index",
  ).map((item, index) =>
    evidenceDetail(item, `/supplement/evidence_index/${index}`),
  );
  const sourceCommit = hex(source.commit, 40, "/source/commit");
  const rawIdentity = evidence(
    source.raw_identity_evidence,
    "/source/raw_identity_evidence",
  );
  if (
    rawIdentity.path !==
      stringValue(source.snapshot_path, "/source/snapshot_path") ||
    rawIdentity.sha256 !==
      hex(source.snapshot_raw_sha256, 64, "/source/snapshot_raw_sha256")
  ) {
    throw new ProgramStatusDecodeError(
      "RAW_IDENTITY_EVIDENCE_MISMATCH",
      "/source/raw_identity_evidence",
    );
  }
  const catalogPath = stringValue(
    source.source_catalog_path,
    "/source/source_catalog_path",
  );
  const catalogDigest = hex(
    source.source_catalog_sha256,
    64,
    "/source/source_catalog_sha256",
  );
  if (
    !details.some(
      (detail) =>
        detail.path === catalogPath && detail.sha256 === catalogDigest,
    )
  ) {
    throw new ProgramStatusDecodeError(
      "SOURCE_CATALOG_EVIDENCE_MISMATCH",
      "/source/source_catalog_sha256",
    );
  }
  for (const detail of details) {
    if (
      detail.exact_url !== null &&
      detail.exact_url !==
        `https://github.com/burhop/wright/blob/${sourceCommit}/${detail.path}`
    ) {
      throw new ProgramStatusDecodeError(
        "EVIDENCE_URL_IDENTITY_MISMATCH",
        `/supplement/evidence_index/${detail.id}/exact_url`,
      );
    }
  }
  if (new Set(details.map((detail) => detail.id)).size !== details.length) {
    throw new ProgramStatusDecodeError(
      "EVIDENCE_INDEX_DUPLICATE",
      "/supplement/evidence_index",
    );
  }

  const historyIds = new Set<string>();
  for (const [seriesIndex, item] of array(
    supplement.history,
    "/supplement/history",
  ).entries()) {
    const path = `/supplement/history/${seriesIndex}`;
    const series = record(item, path);
    const id = stringValue(series.id, `${path}/id`);
    if (historyIds.has(id)) {
      throw new ProgramStatusDecodeError("HISTORY_ID_DUPLICATE", `${path}/id`);
    }
    historyIds.add(id);
    const availability = enumValue(
      series.availability,
      ["available", "unavailable"] as const,
      `${path}/availability`,
    );
    const observations = array(series.observations, `${path}/observations`);
    if (
      (availability === "available" && observations.length === 0) ||
      (availability === "unavailable" && observations.length !== 0)
    ) {
      throw new ProgramStatusDecodeError(
        "HISTORY_AVAILABILITY_MISMATCH",
        `${path}/observations`,
      );
    }
    const commits = new Set<string>();
    let priorTime = "";
    let priorValue: number | null = null;
    let latest: Record<string, unknown> | null = null;
    for (const [observationIndex, observationValue] of observations.entries()) {
      const observationPath = `${path}/observations/${observationIndex}`;
      const observation = record(observationValue, observationPath);
      const commit = hex(observation.commit, 40, `${observationPath}/commit`);
      const observedAt = stringValue(
        observation.observed_at,
        `${observationPath}/observed_at`,
      );
      const valueNumber = integer(
        observation.value,
        `${observationPath}/value`,
      );
      const denominatorValue = integer(
        observation.denominator,
        `${observationPath}/denominator`,
      );
      if (valueNumber < 0 || valueNumber > denominatorValue) {
        throw new ProgramStatusDecodeError(
          "HISTORY_DENOMINATOR_INVALID",
          observationPath,
        );
      }
      if (commits.has(commit) || observedAt < priorTime) {
        throw new ProgramStatusDecodeError(
          "HISTORY_ORDER_INVALID",
          observationPath,
        );
      }
      commits.add(commit);
      priorTime = observedAt;
      priorValue =
        latest === null ? null : integer(latest.value, `${path}/latest/value`);
      latest = { ...observation, value: valueNumber };
    }
    if (availability === "available") {
      const change = record(series.latest_change, `${path}/latest_change`);
      if (
        latest === null ||
        change.commit !== latest.commit ||
        change.observed_at !== latest.observed_at ||
        integer(change.to_value, `${path}/latest_change/to_value`) !==
          latest.value ||
        change.from_value !== priorValue
      ) {
        throw new ProgramStatusDecodeError(
          "HISTORY_LATEST_CHANGE_MISMATCH",
          `${path}/latest_change`,
        );
      }
    } else if (series.latest_change !== null) {
      throw new ProgramStatusDecodeError(
        "HISTORY_LATEST_CHANGE_MISMATCH",
        `${path}/latest_change`,
      );
    }
  }

  const testHistory = record(
    supplement.test_history,
    "/supplement/test_history",
  );
  const selection = record(
    testHistory.selection_attestation,
    "/supplement/test_history/selection_attestation",
  );
  const selectedRunIds = array(
    selection.selected_run_ids,
    "/supplement/test_history/selection_attestation/selected_run_ids",
  ).map((item, index) =>
    stringValue(
      item,
      `/supplement/test_history/selection_attestation/selected_run_ids/${index}`,
    ),
  );
  const projectedRunIds: string[] = [];
  const runKeys = new Set<string>();
  const checkpointCommits = new Set<string>();
  let checkpointTime = "";
  for (const [checkpointIndex, checkpointValue] of array(
    testHistory.checkpoints,
    "/supplement/test_history/checkpoints",
  ).entries()) {
    const checkpointPath = `/supplement/test_history/checkpoints/${checkpointIndex}`;
    const checkpoint = record(checkpointValue, checkpointPath);
    const checkpointCommit = hex(
      checkpoint.commit,
      40,
      `${checkpointPath}/commit`,
    );
    if (checkpointCommits.has(checkpointCommit)) {
      throw new ProgramStatusDecodeError(
        "TEST_CHECKPOINT_COMMIT_DUPLICATE",
        `${checkpointPath}/commit`,
      );
    }
    checkpointCommits.add(checkpointCommit);
    const observedAt = stringValue(
      checkpoint.observed_at,
      `${checkpointPath}/observed_at`,
    );
    if (observedAt < checkpointTime) {
      throw new ProgramStatusDecodeError(
        "TEST_HISTORY_ORDER_INVALID",
        checkpointPath,
      );
    }
    checkpointTime = observedAt;
    const aggregate = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      not_run: 0,
    };
    const categoryAggregates = new Map<
      string,
      {
        total: number;
        passed: number;
        failed: number;
        skipped: number;
        not_run: number;
      }
    >();
    const seenCases = new Set<string>();
    const sourceTimes: string[] = [];
    for (const [sourceIndex, sourceValue] of array(
      checkpoint.suite_sources,
      `${checkpointPath}/suite_sources`,
    ).entries()) {
      const sourcePath = `${checkpointPath}/suite_sources/${sourceIndex}`;
      const suite = record(sourceValue, sourcePath);
      if (suite.terminal !== true) {
        throw new ProgramStatusDecodeError(
          "TEST_RUN_NOT_TERMINAL",
          `${sourcePath}/terminal`,
        );
      }
      const runId = stringValue(suite.run_id, `${sourcePath}/run_id`);
      sourceTimes.push(
        stringValue(suite.observed_at, `${sourcePath}/observed_at`),
      );
      const runKey = hex(suite.run_key, 64, `${sourcePath}/run_key`);
      if (runKeys.has(runKey)) {
        throw new ProgramStatusDecodeError(
          "TEST_RUN_KEY_DUPLICATE",
          `${sourcePath}/run_key`,
        );
      }
      runKeys.add(runKey);
      projectedRunIds.push(runId);
      const cases = array(
        suite.test_case_ids,
        `${sourcePath}/test_case_ids`,
      ).map((item, index) =>
        stringValue(item, `${sourcePath}/test_case_ids/${index}`),
      );
      const countRow = record(suite.counts, `${sourcePath}/counts`);
      const sourceCounts = {
        total: integer(countRow.total, `${sourcePath}/counts/total`),
        passed: integer(countRow.passed, `${sourcePath}/counts/passed`),
        failed: integer(countRow.failed, `${sourcePath}/counts/failed`),
      };
      const skipped = integer(countRow.skipped, `${sourcePath}/counts/skipped`);
      const notRun = integer(countRow.not_run, `${sourcePath}/counts/not_run`);
      if (
        sourceCounts.total !== cases.length ||
        sourceCounts.total !==
          sourceCounts.passed + sourceCounts.failed + skipped + notRun
      ) {
        throw new ProgramStatusDecodeError(
          "TEST_RUN_COUNTS_INVALID",
          `${sourcePath}/counts`,
        );
      }
      if (suite.aggregate_role === "component") {
        const category = enumValue(
          suite.category,
          ["unit", "integration", "e2e", "benchmark"] as const,
          `${sourcePath}/category`,
        );
        for (const testCase of cases) {
          if (seenCases.has(testCase)) {
            throw new ProgramStatusDecodeError(
              "TEST_COMPONENT_OVERLAP",
              `${sourcePath}/test_case_ids`,
            );
          }
          seenCases.add(testCase);
        }
        aggregate.total += sourceCounts.total;
        aggregate.passed += integer(
          countRow.passed,
          `${sourcePath}/counts/passed`,
        );
        aggregate.failed += integer(
          countRow.failed,
          `${sourcePath}/counts/failed`,
        );
        aggregate.skipped += skipped;
        aggregate.not_run += notRun;
        const categoryCounts = categoryAggregates.get(category) ?? {
          total: 0,
          passed: 0,
          failed: 0,
          skipped: 0,
          not_run: 0,
        };
        categoryCounts.total += sourceCounts.total;
        categoryCounts.passed += sourceCounts.passed;
        categoryCounts.failed += sourceCounts.failed;
        categoryCounts.skipped += skipped;
        categoryCounts.not_run += notRun;
        categoryAggregates.set(category, categoryCounts);
      } else if (suite.aggregate_role !== "summary_only") {
        throw new ProgramStatusDecodeError(
          "TEST_AGGREGATE_ROLE_INVALID",
          `${sourcePath}/aggregate_role`,
        );
      }
    }
    const checkpointCounts = record(
      checkpoint.counts,
      `${checkpointPath}/counts`,
    );
    if (sourceTimes.length && observedAt !== [...sourceTimes].sort().at(-1)) {
      throw new ProgramStatusDecodeError(
        "TEST_CHECKPOINT_TIME_INVALID",
        `${checkpointPath}/observed_at`,
      );
    }
    for (const name of [
      "total",
      "passed",
      "failed",
      "skipped",
      "not_run",
    ] as const) {
      if (
        integer(checkpointCounts[name], `${checkpointPath}/counts/${name}`) !==
        aggregate[name]
      ) {
        throw new ProgramStatusDecodeError(
          "TEST_CHECKPOINT_COUNTS_INVALID",
          `${checkpointPath}/counts/${name}`,
        );
      }
    }
    const denominator = aggregate.passed + aggregate.failed;
    const expectedPassRate = denominator
      ? aggregate.passed / denominator
      : null;
    if (checkpoint.pass_rate !== expectedPassRate) {
      throw new ProgramStatusDecodeError(
        "TEST_PASS_RATE_INVALID",
        `${checkpointPath}/pass_rate`,
      );
    }
    const categories = record(
      checkpoint.categories,
      `${checkpointPath}/categories`,
    );
    for (const name of ["unit", "integration", "e2e", "benchmark"] as const) {
      const expected = categoryAggregates.get(name);
      if (!expected && categories[name] !== null) {
        throw new ProgramStatusDecodeError(
          "TEST_CATEGORY_COUNTS_INVALID",
          `${checkpointPath}/categories/${name}`,
        );
      }
      if (expected) {
        const actual = record(
          categories[name],
          `${checkpointPath}/categories/${name}`,
        );
        for (const countName of [
          "total",
          "passed",
          "failed",
          "skipped",
          "not_run",
        ] as const) {
          if (
            integer(
              actual[countName],
              `${checkpointPath}/categories/${name}/${countName}`,
            ) !== expected[countName]
          ) {
            throw new ProgramStatusDecodeError(
              "TEST_CATEGORY_COUNTS_INVALID",
              `${checkpointPath}/categories/${name}/${countName}`,
            );
          }
        }
      }
    }
  }
  if (
    selectedRunIds.length !== projectedRunIds.length ||
    [...selectedRunIds]
      .sort()
      .some((id, index) => id !== [...projectedRunIds].sort()[index])
  ) {
    throw new ProgramStatusDecodeError(
      "TEST_SELECTION_ATTESTATION_MISMATCH",
      "/supplement/test_history/selection_attestation/selected_run_ids",
    );
  }

  const work = record(supplement.work, "/supplement/work");
  const benchmark = record(
    supplement.benchmark_context,
    "/supplement/benchmark_context",
  );
  const dependencyIds = new Set<string>();
  for (const [index, dependencyValue] of array(
    benchmark.dependencies,
    "/supplement/benchmark_context/dependencies",
  ).entries()) {
    const dependencyPath = `/supplement/benchmark_context/dependencies/${index}`;
    const dependency = record(dependencyValue, dependencyPath);
    const id = stringValue(dependency.id, `${dependencyPath}/id`);
    const status = stringValue(dependency.status, `${dependencyPath}/status`);
    if (
      dependencyIds.has(id) ||
      dependency.blocking !== (status !== "satisfied")
    ) {
      throw new ProgramStatusDecodeError(
        "BENCHMARK_DEPENDENCY_RELATION_INVALID",
        dependencyPath,
      );
    }
    dependencyIds.add(id);
  }
  const lease = record(work.lease, "/supplement/work/lease");
  const lanes = array(work.lanes, "/supplement/work/lanes").map((item, index) =>
    record(item, `/supplement/work/lanes/${index}`),
  );
  const integration = lanes.find((lane) => lane.kind === "integration");
  const development = lanes.find(
    (lane) => lane.kind === "continued_development",
  );
  if (
    lanes.length !== 2 ||
    !integration ||
    !development ||
    integration.branch === development.branch ||
    development.branch !== lease.branch ||
    development.base_commit !==
      record(lease.dev_baseline, "/supplement/work/lease/dev_baseline").commit
  ) {
    throw new ProgramStatusDecodeError(
      "DELIVERY_LANE_RELATION_INVALID",
      "/supplement/work/lanes",
    );
  }
  const events = array(
    integration.events,
    "/supplement/work/lanes/integration/events",
  );
  if (events.length) {
    const lastEvent = record(
      events.at(-1),
      "/supplement/work/lanes/integration/events/last",
    );
    if (lastEvent.observed_at !== integration.observed_at) {
      throw new ProgramStatusDecodeError(
        "DELIVERY_LANE_RELATION_INVALID",
        "/supplement/work/lanes/integration/observed_at",
      );
    }
  }
  const references: LocatedEvidence[] = [
    {
      reference: evidence(
        source.raw_identity_evidence,
        "/source/raw_identity_evidence",
      ),
      path: ["source", "raw_identity_evidence"],
    },
    ...evidenceReferences(supplement, ["supplement"]),
  ];
  const isSelectedTestEvidence = (path: Array<string | number>) =>
    path.length === 8 &&
    path[0] === "supplement" &&
    path[1] === "test_history" &&
    path[2] === "checkpoints" &&
    typeof path[3] === "number" &&
    path[4] === "suite_sources" &&
    typeof path[5] === "number" &&
    path[6] === "evidence" &&
    typeof path[7] === "number";
  const evidenceKey = (item: EvidenceRef) =>
    `${item.id}\u0000${item.path}\u0000${item.sha256}`;
  const selectedTestResultKeys = new Set(
    references
      .filter(
        ({ reference, path }) =>
          reference.path.startsWith("test-results/") &&
          isSelectedTestEvidence(path),
      )
      .map(({ reference }) => evidenceKey(reference)),
  );
  const indexedTestResultKeys = new Set(
    details
      .filter((detail) => detail.path.startsWith("test-results/"))
      .map((detail) => evidenceKey(detail)),
  );
  for (const { reference, path } of references) {
    if (
      reference.path.startsWith("test-results/") &&
      !isSelectedTestEvidence(path)
    ) {
      throw new ProgramStatusDecodeError(
        "TEST_RESULT_EVIDENCE_CONTEXT_INVALID",
        `/${path.join("/")}`,
      );
    }
  }
  if (
    indexedTestResultKeys.size !== selectedTestResultKeys.size ||
    [...indexedTestResultKeys].some((key) => !selectedTestResultKeys.has(key))
  ) {
    throw new ProgramStatusDecodeError(
      "TEST_RESULT_EVIDENCE_UNBOUND",
      "/supplement/evidence_index",
    );
  }
  for (const { reference } of references) {
    const matches = details.filter((detail) => sameEvidence(reference, detail));
    if (matches.length !== 1) {
      throw new ProgramStatusDecodeError(
        "EVIDENCE_REFERENCE_UNRESOLVED",
        `/supplement/evidence_index/${reference.id}`,
      );
    }
  }
}

export async function verifyProgramStatusIdentity(
  value: unknown,
): Promise<void> {
  const root = record(value, "");
  const source = record(root.source, "/source");
  const dashboard = record(root.dashboard, "/dashboard");
  const supplement = record(root.supplement, "/supplement");
  validateProgramStatusEvidenceRelations(root);
  await verifyTestHistoryDigests(supplement);
  if (
    (await canonicalProgramStatusDigest(dashboard)) !==
    hex(
      source.dashboard_canonical_sha256,
      64,
      "/source/dashboard_canonical_sha256",
    )
  ) {
    throw new ProgramStatusDecodeError(
      "DASHBOARD_IDENTITY_MISMATCH",
      "/source/dashboard_canonical_sha256",
    );
  }
  const expected = await canonicalProgramStatusDigest({
    source,
    dashboard,
    supplement,
  });
  if (expected !== hex(root.bundle_id, 64, "/bundle_id")) {
    throw new ProgramStatusDecodeError(
      "BUNDLE_IDENTITY_MISMATCH",
      "/bundle_id",
    );
  }
}

async function typedError(response: Response): Promise<ProgramStatusError> {
  try {
    const row = record(await response.json(), "");
    return {
      error_code: stringValue(row.error_code, "/error_code"),
      message: stringValue(row.message, "/message"),
      recovery_class: stringValue(row.recovery_class, "/recovery_class"),
      trace_id: stringValue(row.trace_id, "/trace_id"),
    };
  } catch {
    return {
      error_code: "PROGRAM_STATUS_READ_FAILED",
      message: "Program status could not be read.",
      recovery_class: "inspect_local_runtime",
      trace_id: "unavailable",
    };
  }
}

export async function fetchProgramStatus(
  etag?: string,
  signal?: AbortSignal,
): Promise<ProgramStatusFetchResult> {
  const headers: Record<string, string> = {};
  if (etag) headers["If-None-Match"] = etag;
  const response = await hostAdapter.fetch(
    `${hostAdapter.getApiBaseUrl()}/api/program-status`,
    { headers, signal, cache: "no-cache" },
  );
  if (response.status === 304)
    return { status: 304, etag: response.headers.get("etag"), bundle: null };
  if (!response.ok)
    throw new ProgramStatusServiceError(await typedError(response));
  const raw = await response.json();
  await verifyProgramStatusIdentity(raw);
  const bundle = decodeProgramStatusBundle(raw);
  return {
    status: 200,
    etag: response.headers.get("etag"),
    bundle,
  };
}

export async function fetchProgramStatusPublisher(
  signal?: AbortSignal,
): Promise<ProgramStatusPublisher> {
  const response = await hostAdapter.fetch(
    `${hostAdapter.getApiBaseUrl()}/api/program-status/publisher`,
    { signal, cache: "no-store" },
  );
  if (!response.ok)
    throw new ProgramStatusServiceError(await typedError(response));
  return decodeProgramStatusPublisher(await response.json());
}
