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
      authorization_state: string;
      next_qualifying_action: StatusAction;
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
  /^https:\/\/github\.com\/[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\/[A-Za-z0-9](?:[A-Za-z0-9._-]{0,98}[A-Za-z0-9_-])?\/blob\/[0-9a-f]{40}\/[A-Za-z0-9_-][A-Za-z0-9._-]*(?:\/[A-Za-z0-9_-][A-Za-z0-9._-]*)*$/;

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
        process_100: {
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
        },
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
        authorization_state: stringValue(
          benchmark.authorization_state,
          "/supplement/benchmark_context/authorization_state",
        ),
        next_qualifying_action: action(
          benchmark.next_qualifying_action,
          "/supplement/benchmark_context/next_qualifying_action",
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
  const token = String(value);
  if (/[eE]/.test(token) || !/^-?(?:0|[1-9][0-9]*)\.[0-9]{1,6}$/.test(token)) {
    throw new ProgramStatusDecodeError("CANONICAL_NUMBER_INVALID", "");
  }
  const scaled = Number(token.replace(".", ""));
  if (!Number.isSafeInteger(scaled)) {
    throw new ProgramStatusDecodeError("CANONICAL_NUMBER_UNSAFE", "");
  }
  return token;
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

function sameEvidence(left: EvidenceRef, right: EvidenceDetail): boolean {
  return (
    left.id === right.id &&
    left.path === right.path &&
    left.sha256 === right.sha256
  );
}

function evidenceReferences(value: unknown): EvidenceRef[] {
  const references: EvidenceRef[] = [];
  const visit = (item: unknown, key = "") => {
    if (key === "evidence_index") return;
    if (Array.isArray(item)) {
      item.forEach((candidate) => visit(candidate));
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
      references.push(evidence(row, `/${key || "evidence"}`));
      return;
    }
    for (const [childKey, child] of Object.entries(item)) {
      visit(child, childKey);
    }
  };
  visit(value);
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
  if (new Set(details.map((detail) => detail.id)).size !== details.length) {
    throw new ProgramStatusDecodeError(
      "EVIDENCE_INDEX_DUPLICATE",
      "/supplement/evidence_index",
    );
  }
  const references = [
    evidence(source.raw_identity_evidence, "/source/raw_identity_evidence"),
    ...evidenceReferences(supplement),
  ];
  for (const reference of references) {
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
