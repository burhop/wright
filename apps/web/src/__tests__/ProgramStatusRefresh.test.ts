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
    raw.supplement.test_history.selection_attestation = {
      source_path:
        "docs/programs/engineering-process-platform/test-run-ledger.json",
    };
    raw.supplement.benchmark_context.dependencies = [];
    raw.supplement.benchmark_context.evidence = [
      raw.supplement.work.current_next_action.evidence[0],
    ];
    raw.supplement.work.lease = { feature_id: "EPP-F01B" };
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

  it("uses the declared bounded fixed-point canonical number subset", () => {
    expect(
      canonicalProgramStatusJson([
        0, 1, 9007199254740991, 0.5, 0.125, 0.333333,
      ]),
    ).toBe("[0,1,9007199254740991,0.5,0.125,0.333333]");
    expect(() => canonicalProgramStatusJson(-0)).toThrow(
      "CANONICAL_NUMBER_INVALID",
    );
    expect(() => canonicalProgramStatusJson(0.0000001)).toThrow(
      "CANONICAL_NUMBER_INVALID",
    );
    expect(() => canonicalProgramStatusJson(9007199254740992)).toThrow(
      "CANONICAL_NUMBER_UNSAFE",
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
