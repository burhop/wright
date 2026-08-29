import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "http://wright.local",
    fetch: vi.fn(),
  },
}));

import { hostAdapter } from "../services/host-adapter";
import {
  fetchProgramStatus,
  fetchProgramStatusPublisher,
} from "../services/program-status";
import { makeProgramStatusBundle } from "./program-status-fixture";

const mockedFetch = vi.mocked(hostAdapter.fetch);

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
    mockedFetch.mockResolvedValue(
      new Response(JSON.stringify(makeProgramStatusBundle()), {
        status: 200,
        headers: { "content-type": "application/json", etag: '"bundle-2"' },
      }),
    );
    const result = await fetchProgramStatus('"bundle-1"');
    expect(result.status).toBe(200);
    expect(result.etag).toBe('"bundle-2"');
    expect(result.bundle?.supplement.customer_catalog.proposed_total).toBe(100);
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
