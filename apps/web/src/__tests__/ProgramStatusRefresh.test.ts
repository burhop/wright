import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "http://wright.local",
    fetch: vi.fn(),
  },
}));

import { hostAdapter } from "../services/host-adapter";
import {
  canonicalProgramStatusDigest,
  canonicalProgramStatusJson,
  decodeProgramStatusBundle,
  fetchProgramStatus,
  fetchProgramStatusPublisher,
  verifyProgramStatusIdentity,
  validateProgramStatusEvidenceRelations,
} from "../services/program-status";
import { makeProgramStatusBundle } from "./program-status-fixture";

const mockedFetch = vi.mocked(hostAdapter.fetch);

async function identityBoundBundle(): Promise<any> {
  const bundle = makeProgramStatusBundle() as any;
  bundle.source.dashboard_canonical_sha256 = await canonicalProgramStatusDigest(
    bundle.dashboard,
  );
  bundle.bundle_id = await canonicalProgramStatusDigest({
    source: bundle.source,
    dashboard: bundle.dashboard,
    supplement: bundle.supplement,
  });
  return bundle;
}

function addCanonicalTestRun(raw: any) {
  const reference = {
    id: "test:run-1:1",
    path: "test-results/program-status/run-1.json",
    sha256: "8".repeat(64),
  };
  raw.supplement.test_history.availability = "available";
  raw.supplement.test_history.unavailable_reason = null;
  raw.supplement.test_history.selection_attestation.selected_run_ids = [
    "run-1",
  ];
  raw.supplement.test_history.checkpoints = [
    {
      commit: "c".repeat(40),
      observed_at: "2026-08-29T03:00:00Z",
      counts: { total: 1, passed: 1, failed: 0, skipped: 0, not_run: 0 },
      pass_rate: 1,
      categories: {
        unit: { total: 1, passed: 1, failed: 0, skipped: 0, not_run: 0 },
        integration: null,
        e2e: null,
        benchmark: null,
      },
      suite_sources: [
        {
          suite_id: "suite-1",
          population_id: "population-1",
          run_id: "run-1",
          run_key:
            "7d0f2aaed54fd394524bacf7946adf2805b7adbf6f2ed291749d572b921c1266",
          attempt: 1,
          observed_at: "2026-08-29T03:00:00Z",
          terminal: true,
          aggregate_role: "component",
          category: "unit",
          test_case_ids: ["case-1"],
          test_case_set_sha256:
            "1e9c43b954b73005c6db72f0b0f674763dcb9d47f11696a8a70a31b2a78665f2",
          counts: { total: 1, passed: 1, failed: 0, skipped: 0, not_run: 0 },
          evidence: [reference],
        },
      ],
    },
  ];
  raw.supplement.evidence_index.push({
    ...reference,
    label: "Canonical unit run",
    summary: "Exact selected test result.",
    freshness: "current",
    recovery: null,
    availability: "identity_only",
    exact_url: null,
  });
}

describe("program status conditional refresh transport", () => {
  beforeEach(() => mockedFetch.mockReset());

  it("sends the prior exact identity and accepts a bodyless 304", async () => {
    mockedFetch.mockResolvedValue(
      new Response(null, { status: 304, headers: { etag: '"bundle-1"' } }),
    );
    const result = await fetchProgramStatus('"bundle-1"');
    expect(result).toEqual({ status: 304, etag: '"bundle-1"', bundle: null });
    expect(mockedFetch).toHaveBeenCalledWith(
      "http://wright.local/api/program-status",
      expect.objectContaining({
        headers: { "If-None-Match": '"bundle-1"' },
        cache: "no-cache",
      }),
    );
  });

  it("decodes a changed bundle as one complete 200 response", async () => {
    const bundle = await identityBoundBundle();
    mockedFetch.mockResolvedValue(
      new Response(JSON.stringify(bundle), {
        status: 200,
        headers: { "content-type": "application/json", etag: '"bundle-2"' },
      }),
    );
    const result = await fetchProgramStatus('"bundle-1"');
    expect(result.status).toBe(200);
    expect(result.etag).toBe('"bundle-2"');
    expect(result.bundle?.supplement.customer_catalog.proposed_total).toBe(100);
  });

  it("independently rejects dashboard and bundle identity drift", async () => {
    const dashboardDrift = await identityBoundBundle();
    dashboardDrift.dashboard.release_eligible = true;
    await expect(verifyProgramStatusIdentity(dashboardDrift)).rejects.toThrow(
      "DASHBOARD_IDENTITY_MISMATCH",
    );

    const supplementDrift = await identityBoundBundle();
    supplementDrift.supplement.customer_catalog.proposed_total = 99;
    await expect(verifyProgramStatusIdentity(supplementDrift)).rejects.toThrow(
      "BUNDLE_IDENTITY_MISMATCH",
    );
  });

  it("verifies the complete raw supplement before projecting UI fields", async () => {
    const raw = makeProgramStatusBundle() as any;
    raw.supplement.use_cases.source_path =
      "docs/programs/engineering-process-platform/use-case-registry.json";
    raw.supplement.use_cases.source_digest = "4".repeat(64);
    raw.supplement.use_cases.items = [];
    raw.supplement.use_cases.graph_context = { meaning: "raw-only" };
    raw.supplement.test_history.counting_rule =
      "latest_terminal_attempt_per_commit_suite_id_population_id";
    raw.supplement.test_history.selection_attestation.source_path =
      "docs/programs/engineering-process-platform/test-run-ledger.json";
    raw.supplement.benchmark_context.dependencies = [];
    raw.supplement.benchmark_context.evidence = [
      raw.supplement.work.current_next_action.evidence[0],
    ];
    raw.supplement.work.lease.feature_id = "EPP-F01B";
    raw.supplement.work.checkpoints = [];
    raw.source.dashboard_canonical_sha256 = await canonicalProgramStatusDigest(
      raw.dashboard,
    );
    raw.bundle_id = await canonicalProgramStatusDigest({
      source: raw.source,
      dashboard: raw.dashboard,
      supplement: raw.supplement,
    });
    mockedFetch.mockResolvedValue(
      new Response(JSON.stringify(raw), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );

    await expect(fetchProgramStatus()).resolves.toMatchObject({ status: 200 });
  });

  it("requires each emitted evidence reference to resolve exactly once", () => {
    const missing = makeProgramStatusBundle() as any;
    missing.supplement.evidence_index =
      missing.supplement.evidence_index.filter(
        (detail: any) => detail.id !== "TR-0072",
      );
    expect(() => validateProgramStatusEvidenceRelations(missing)).toThrow(
      "EVIDENCE_REFERENCE_UNRESOLVED",
    );

    const duplicate = makeProgramStatusBundle() as any;
    duplicate.supplement.evidence_index.push({
      ...duplicate.supplement.evidence_index[0],
    });
    expect(() => validateProgramStatusEvidenceRelations(duplicate)).toThrow(
      "EVIDENCE_INDEX_DUPLICATE",
    );
  });

  it("binds raw snapshot, source catalog, history, and delivery-lane identities", () => {
    const rawIdentity = makeProgramStatusBundle() as any;
    rawIdentity.source.raw_identity_evidence.sha256 = "9".repeat(64);
    expect(() => validateProgramStatusEvidenceRelations(rawIdentity)).toThrow(
      "RAW_IDENTITY_EVIDENCE_MISMATCH",
    );

    const catalog = makeProgramStatusBundle() as any;
    catalog.source.source_catalog_sha256 = "9".repeat(64);
    expect(() => validateProgramStatusEvidenceRelations(catalog)).toThrow(
      "SOURCE_CATALOG_EVIDENCE_MISMATCH",
    );

    const lane = makeProgramStatusBundle() as any;
    lane.supplement.work.lanes[1].branch = "wrong-branch";
    expect(() => validateProgramStatusEvidenceRelations(lane)).toThrow(
      "DELIVERY_LANE_RELATION_INVALID",
    );

    const sharedBranch = makeProgramStatusBundle() as any;
    sharedBranch.supplement.work.lanes[0].branch =
      sharedBranch.supplement.work.lanes[1].branch;
    expect(() => validateProgramStatusEvidenceRelations(sharedBranch)).toThrow(
      "DELIVERY_LANE_RELATION_INVALID",
    );

    const history = makeProgramStatusBundle() as any;
    history.supplement.history = [
      {
        id: "feature_tasks",
        availability: "unavailable",
        latest_change: null,
        observations: [{ commit: "c".repeat(40) }],
      },
    ];
    expect(() => validateProgramStatusEvidenceRelations(history)).toThrow(
      "HISTORY_AVAILABILITY_MISMATCH",
    );

    const denominator = makeProgramStatusBundle() as any;
    denominator.supplement.history = [
      {
        id: "feature_tasks",
        availability: "available",
        observations: [
          {
            commit: "c".repeat(40),
            observed_at: "2026-08-29T00:00:00Z",
            value: 1,
            denominator: 1,
          },
        ],
        latest_change: {
          commit: "c".repeat(40),
          observed_at: "2026-08-29T00:00:00Z",
          from_value: null,
          to_value: 1,
        },
      },
    ];
    denominator.supplement.history[0].observations[0].value = 2;
    denominator.supplement.history[0].observations[0].denominator = 1;
    expect(() => validateProgramStatusEvidenceRelations(denominator)).toThrow(
      "HISTORY_DENOMINATOR_INVALID",
    );
  });

  it("binds checkpoint time to the latest selected test source", () => {
    const raw = makeProgramStatusBundle() as any;
    addCanonicalTestRun(raw);
    raw.supplement.test_history.checkpoints[0].observed_at =
      "2026-08-29T00:00:00Z";
    expect(() => validateProgramStatusEvidenceRelations(raw)).toThrow(
      "TEST_CHECKPOINT_TIME_INVALID",
    );
  });

  it("admits test-results evidence only for selected test suite sources", () => {
    const raw = makeProgramStatusBundle() as any;
    addCanonicalTestRun(raw);
    const reference = {
      id: "test:unit-attempt-1:1",
      path: "test-results/program-status/unit.json",
      sha256: "8".repeat(64),
    };
    expect(() => validateProgramStatusEvidenceRelations(raw)).not.toThrow();

    const orphan = makeProgramStatusBundle() as any;
    orphan.supplement.evidence_index.push({
      ...reference,
      label: "Orphan test run",
      summary: "Not selected by test history.",
      freshness: "current",
      recovery: null,
      availability: "identity_only",
      exact_url: null,
    });
    expect(() => validateProgramStatusEvidenceRelations(orphan)).toThrow(
      "TEST_RESULT_EVIDENCE_UNBOUND",
    );

    const wrongContext = makeProgramStatusBundle() as any;
    wrongContext.supplement.work.current_next_action = {
      ...wrongContext.supplement.work.current_next_action,
      evidence: [reference],
    };
    wrongContext.supplement.evidence_index.push({
      ...reference,
      label: "Wrong-context test result",
      summary: "A test-result path cannot support a non-test action.",
      freshness: "current",
      recovery: null,
      availability: "identity_only",
      exact_url: null,
    });
    expect(() => validateProgramStatusEvidenceRelations(wrongContext)).toThrow(
      "TEST_RESULT_EVIDENCE_CONTEXT_INVALID",
    );
  });

  it("resolves evidence nested inside a non-empty governed use-case stage", () => {
    const raw = makeProgramStatusBundle() as any;
    const reference = raw.supplement.work.current_next_action.evidence[0];
    raw.supplement.use_cases.items = [
      {
        id: "EPP-UC-001",
        title: "Inspect status",
        customer_outcome: "A customer can inspect evidence-backed status.",
        process_100_id: null,
        definition_evidence: [
          {
            evidence_class: "definition",
            source_name: "roadmap",
            subject_id: "EPP-F01B",
            verdict: "not_applicable",
            acceptance_subject_id: null,
            evidence_author: null,
            independent_verifier: null,
            evidence: reference,
          },
        ],
        progress_evidence: [],
        acceptance_evidence: [],
        test_evidence: [],
        independent_verification_evidence: [],
        benchmark_qualification_evidence: [],
      },
    ];
    expect(() => validateProgramStatusEvidenceRelations(raw)).not.toThrow();

    raw.supplement.use_cases.items[0].definition_evidence[0].evidence = {
      ...reference,
      sha256: "9".repeat(64),
    };
    expect(() => validateProgramStatusEvidenceRelations(raw)).toThrow(
      "EVIDENCE_REFERENCE_UNRESOLVED",
    );
  });

  it("recomputes a non-empty use-case funnel and rejects non-independent evidence", () => {
    const raw = makeProgramStatusBundle() as any;
    const acceptanceRef = {
      id: "use-case-acceptance",
      path: "docs/programs/engineering-process-platform/gate-evidence.json",
      sha256: "6".repeat(64),
    };
    const verificationRef = {
      id: "use-case-verification",
      path: "docs/programs/engineering-process-platform/evidence/verification/EPP-F01-V9.json",
      sha256: "7".repeat(64),
    };
    raw.supplement.use_cases.items = [
      {
        id: "EPP-UC-001",
        title: "Inspect status",
        customer_outcome: "A customer can inspect evidence-backed status.",
        process_100_id: "EPP-PROC-001",
        definition_evidence: [],
        progress_evidence: [],
        acceptance_evidence: [
          {
            evidence_class: "customer_acceptance",
            source_name: "gate_evidence",
            subject_id: "ACC-001",
            verdict: "passed",
            acceptance_subject_id: null,
            evidence_author: "customer-reviewer",
            independent_verifier: null,
            evidence: acceptanceRef,
          },
        ],
        test_evidence: [],
        independent_verification_evidence: [
          {
            evidence_class: "independent_verification",
            source_name: "verification_evidence",
            subject_id: "VER-001",
            verdict: "passed",
            acceptance_subject_id: "ACC-001",
            evidence_author: "implementation-agent",
            independent_verifier: "independent-reviewer",
            evidence: verificationRef,
          },
        ],
        benchmark_qualification_evidence: [],
      },
    ];
    raw.supplement.use_cases.all = {
      total: 1,
      not_started: 0,
      in_progress: 0,
      implemented: 1,
      independently_verified: 1,
      remaining: 0,
    };
    raw.supplement.use_cases.process_100 = {
      population_target: 100,
      defined: 0,
      in_progress: 0,
      implemented: 1,
      tested: 0,
      independently_verified: 1,
      benchmark_qualified: 0,
    };
    expect(() => decodeProgramStatusBundle(raw)).not.toThrow();

    raw.supplement.use_cases.items[0].independent_verification_evidence[0].independent_verifier =
      "implementation-agent";
    expect(() => decodeProgramStatusBundle(raw)).toThrow(
      "USE_CASE_VERIFICATION_INVALID",
    );
  });

  it("uses Python-compatible shortest canonical numbers", () => {
    expect(
      canonicalProgramStatusJson([
        0,
        1,
        9007199254740991,
        0.5,
        2 / 3,
        0.00001,
        0.0000001,
      ]),
    ).toBe("[0,1,9007199254740991,0.5,0.6666666666666666,1e-05,1e-07]");
    expect(() => canonicalProgramStatusJson(-0)).toThrow(
      "CANONICAL_NUMBER_INVALID",
    );
    expect(() => canonicalProgramStatusJson(9007199254740992)).toThrow(
      "CANONICAL_NUMBER_UNSAFE",
    );
  });

  it("recomputes canonical test-case and run-key digests in the browser", async () => {
    const raw = makeProgramStatusBundle() as any;
    addCanonicalTestRun(raw);
    raw.source.dashboard_canonical_sha256 = await canonicalProgramStatusDigest(
      raw.dashboard,
    );
    raw.bundle_id = await canonicalProgramStatusDigest({
      source: raw.source,
      dashboard: raw.dashboard,
      supplement: raw.supplement,
    });
    await expect(verifyProgramStatusIdentity(raw)).resolves.toBeUndefined();

    raw.supplement.test_history.checkpoints[0].suite_sources[0].test_case_set_sha256 =
      "9".repeat(64);
    await expect(verifyProgramStatusIdentity(raw)).rejects.toThrow(
      "TEST_CASE_SET_IDENTITY_MISMATCH",
    );
  });

  it("keeps typed failure recovery bounded", async () => {
    mockedFetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          error_code: "PROGRAM_STATUS_INVALID",
          message: "Program status is unavailable.",
          recovery_class: "republish_exact_committed_subject",
          trace_id: "trace-1",
        }),
        { status: 503, headers: { "content-type": "application/json" } },
      ),
    );
    await expect(fetchProgramStatus()).rejects.toMatchObject({
      detail: {
        error_code: "PROGRAM_STATUS_INVALID",
        recovery_class: "republish_exact_committed_subject",
      },
    });
  });

  it("reads publisher health separately with no-store semantics", async () => {
    mockedFetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          state: "active",
          mode: "committed_watch",
          observed_commit: "a".repeat(40),
          last_attempt_at: "2026-08-29T03:10:00Z",
          last_success_at: "2026-08-29T03:10:00Z",
          failure_code: null,
          recovery: null,
        }),
        { status: 200, headers: { "content-type": "application/json" } },
      ),
    );
    expect((await fetchProgramStatusPublisher()).state).toBe("active");
    expect(mockedFetch).toHaveBeenCalledWith(
      "http://wright.local/api/program-status/publisher",
      expect.objectContaining({ cache: "no-store" }),
    );
  });
});
