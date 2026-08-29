const action = {
  id: "CONTINUE_IMPLEMENTATION",
  label: "Continue EPP-F01B implementation",
  purpose: "current_program_action",
  eligibility: "eligible",
  authority_state: "authorized",
  requires_human_approval: false,
  blocker: null,
  evidence: [
    {
      id: "TR-0072",
      path: "docs/programs/engineering-process-platform/evidence/transitions/TR-0072.json",
      sha256: "a".repeat(64),
    },
  ],
};

export function makeProgramStatusBundle(
  options: { evidence?: boolean } = {},
): unknown {
  const evidence = [
    {
      id: "dashboard",
      label: "Dashboard snapshot",
      path: "docs/programs/engineering-process-platform/dashboard.json",
      sha256: "f".repeat(64),
      summary: "Exact committed dashboard snapshot used by this bundle.",
      freshness: "current",
      recovery: null,
      availability: "exact_github",
      exact_url: `https://github.com/burhop/wright/blob/${"c".repeat(40)}/docs/programs/engineering-process-platform/dashboard.json`,
    },
    {
      id: "source-catalog",
      label: "Source catalog",
      path: "specs/077-browser-program-status/contracts/program-status-source-catalog.json",
      sha256: "2".repeat(64),
      summary: "Exact frozen source catalog.",
      freshness: "current",
      recovery: null,
      availability: "identity_only",
      exact_url: null,
    },
    {
      id: "TR-0072",
      label: "Implementation activation transition",
      path: "docs/programs/engineering-process-platform/evidence/transitions/TR-0072.json",
      sha256: "a".repeat(64),
      summary:
        "Exact transition authorizing the current local implementation lease.",
      freshness: "current",
      recovery: null,
      availability: options.evidence ? "exact_github" : "identity_only",
      exact_url: options.evidence
        ? `https://github.com/burhop/wright/blob/${"c".repeat(40)}/docs/programs/engineering-process-platform/evidence/transitions/TR-0072.json`
        : null,
    },
  ];
  return {
    schema_version: "1.0.0",
    bundle_id: "b".repeat(64),
    generated_at: "2026-08-29T02:02:46Z",
    source: {
      commit: "c".repeat(40),
      tree: "d".repeat(40),
      program_tree: "e".repeat(40),
      snapshot_path:
        "docs/programs/engineering-process-platform/dashboard.json",
      snapshot_raw_sha256: "f".repeat(64),
      raw_identity_verification: "publisher_git_blob_attested",
      raw_identity_evidence: {
        id: "dashboard",
        path: "docs/programs/engineering-process-platform/dashboard.json",
        sha256: "f".repeat(64),
      },
      dashboard_canonical_sha256: "1".repeat(64),
      source_catalog_path:
        "specs/077-browser-program-status/contracts/program-status-source-catalog.json",
      source_catalog_sha256: "2".repeat(64),
      validation_transition: "TR-0072",
      validation_verdict: "passed",
    },
    dashboard: {
      areas: {
        product_readiness: {
          status: "not_started",
          passed_gates: 0,
          required_gates: 11,
        },
      },
      release_eligible: false,
      release_approval: "not_requested",
      next_action: { action: "HISTORICAL_ONLY" },
      benchmark_summary: { counted: 0, target: 100 },
    },
    supplement: {
      history: [],
      customer_catalog: {
        proposed_total: 100,
        source_path:
          "docs/programs/engineering-process-platform/customer-process-user-stories.md",
        source_digest: "3".repeat(64),
        maturity_counts: { fully_defined: 5, ready_to_specify: 5 },
      },
      use_cases: {
        source_path:
          "docs/programs/engineering-process-platform/use-case-registry.json",
        source_digest: "4".repeat(64),
        all: {
          total: 0,
          not_started: 0,
          in_progress: 0,
          implemented: 0,
          independently_verified: 0,
          remaining: 0,
        },
        process_100: {
          population_target: 100,
          defined: 0,
          in_progress: 0,
          implemented: 0,
          tested: 0,
          independently_verified: 0,
          benchmark_qualified: 0,
        },
        items: [],
        graph_context: {
          meaning: "Governed use-case progress.",
          latest_change: null,
          current_limitation: "No governed use cases are registered yet.",
          next_action: { ...action, purpose: "metric_guidance" },
        },
      },
      test_history: {
        availability: "unavailable",
        counting_rule:
          "latest_terminal_attempt_per_commit_suite_id_population_id",
        pass_rate_rule: "passed_divided_by_passed_plus_failed_else_unavailable",
        identity_digest_rule:
          "wright_test_id_set_v1_lf_then_utf8_byte_lexicographic_unique_nfc_ids_length_colon_bytes_lf_sha256",
        run_key_rule:
          "wright_test_run_key_v1_lf_then_length_framed_nfc_utf8_commit_suite_population_attempt_sha256",
        runs_digest_rule:
          "wright_json_c14n_v1_nfc_sha256_complete_runs_array_in_stored_order",
        selection_attestation: {
          source_path:
            "docs/programs/engineering-process-platform/test-run-ledger.json",
          source_digest: "5".repeat(64),
          ledger_revision: 1,
          prior_ledger_runs_sha256: null,
          runs_sha256: "6".repeat(64),
          publisher_verified_append_only: true,
          selected_run_ids: [],
        },
        graph_context: {
          meaning: "Canonical test evidence.",
          latest_change: null,
          current_limitation: "No canonical committed test run exists yet.",
          next_action: { ...action, purpose: "metric_guidance" },
        },
        unavailable_reason: "No canonical committed test run exists yet.",
        checkpoints: [],
      },
      benchmark_context: {
        phase: "on_hold",
        hold_state: "on_hold",
        hold_reason: "Benchmark execution is not authorized.",
        dependencies: [],
        authorization_state: "not_authorized",
        next_qualifying_action: {
          ...action,
          purpose: "benchmark_qualifying_action",
          eligibility: "blocked",
          authority_state: "not_authorized",
          blocker: "Benchmark execution is not authorized.",
        },
        evidence: [
          {
            id: "dashboard",
            path: "docs/programs/engineering-process-platform/dashboard.json",
            sha256: "f".repeat(64),
          },
        ],
      },
      work: {
        current_milestone: "Browser program status",
        active_feature: "EPP-F01B",
        program_tasks: {
          completed: 80,
          total: 128,
          remaining: 48,
          registered_sources: ["specs/076-control-plane-validator/tasks.md"],
          undecomposed_roadmap_items: ["EPP-F02"],
        },
        tasks: {
          feature_id: "EPP-F01B",
          completed: 4,
          total: 48,
          remaining: 44,
        },
        active_assignments: [],
        blockers: [],
        lease: {
          branch: "codex/epp-continued-development-reconciled",
          dev_baseline: { commit: "9".repeat(40) },
        },
        current_next_action: action,
        lanes: [
          {
            kind: "integration",
            observed_at: "2026-08-28T02:02:46Z",
            events: [],
          },
          {
            kind: "continued_development",
            branch: "codex/epp-continued-development-reconciled",
            base_commit: "9".repeat(40),
          },
        ],
      },
      governance: {},
      evidence_index: evidence,
    },
  };
}
