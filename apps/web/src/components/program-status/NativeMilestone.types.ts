/** Validated current-work projection; historical readiness has its own contract. */
export interface NativeMilestone {
  id: string;
  title: string;
  feature_id: string;
  scope_revision: number;
  scope_history: Array<{
    revision: number;
    observed_at: string;
    added_task_ids: string[];
    removed_task_ids: string[];
    reason: string;
  }>;
  source_commit: string;
  observed_at: string;
  candidate_commit: string | null;
  language_authority: string;
  tasks: Array<{
    id: string;
    title: string;
    activity: "planned" | "active" | "blocked" | "verifying" | "idle";
    owner: string;
    implemented: boolean;
    verification: string;
    integration: string;
    integration_required: boolean;
    blocker_ids: string[];
  }>;
  counts: {
    implementation: { completed: number; total: number };
    verification: { completed: number; total: number };
    integration: { completed: number; total: number; not_applicable: number };
  };
  acceptance: Array<{
    id: string;
    title: string;
    task_ids: string[];
    check_ids: string[];
    status: string;
    missing_check_ids: string[];
  }>;
  checks: Array<{
    id: string;
    label: string;
    stage: string;
    kind: string;
    task_ids: string[];
    status: string;
    evidence_id: string | null;
    observed_at: string | null;
    tested_commit: string | null;
    coverage_current: boolean | null;
    counts: {
      total: number;
      passed: number;
      failed: number;
      skipped: number;
      not_run: number;
    } | null;
    summary: string;
    artifact_urls: string[];
  }>;
  blockers: Array<{
    id: string;
    summary: string;
    owner: string;
    required_action: string;
    task_ids: string[];
    check_ids: string[];
    observed_at: string;
  }>;
  next_task_ids: string[];
  examples: Array<{
    id: string;
    title: string;
    execution_mode: string;
    maturity: string;
    check_ids: string[];
    definition_path: string;
  }>;
  delivery: {
    branch: string;
    target_branch: string;
    baseline_commit: string;
    candidate_commit: string | null;
    pull_requests: Array<{
      url: string;
      head_commit: string;
      observed_at: string;
    }>;
    merged_commit: string | null;
    deployment_status: string;
    deployment_check_ids: string[];
  };
  readiness: {
    native_milestone: string;
    benchmark: string;
    commercial: string;
    release: string;
    rivet_migration: string;
    rivet_retirement: string;
  };
  capabilities: string[];
}
