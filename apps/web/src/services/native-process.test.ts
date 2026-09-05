import { beforeEach, expect, it, vi } from "vitest";
import { hostAdapter } from "./host-adapter";
import telemetry from "./telemetry";
import {
  nativeProcessApi,
  nativeRunApi,
  NativeProcessError,
} from "./native-process";
import { emptyDocument } from "../components/native-process/model";

vi.mock("./host-adapter", () => ({
  hostAdapter: { getApiBaseUrl: () => "http://127.0.0.1:8000", fetch: vi.fn() },
}));
vi.mock("./telemetry", () => ({ default: { startSpan: vi.fn() } }));
const span = { traceId: "abc123", end: vi.fn(), error: vi.fn() };
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(telemetry.startSpan).mockReturnValue(
    span as unknown as ReturnType<typeof telemetry.startSpan>,
  );
});
it("scopes and traces programmatic writes using the same canonical payload and CAS token", async () => {
  const document = emptyDocument();
  vi.mocked(hostAdapter.fetch).mockResolvedValue(
    new Response(
      JSON.stringify({ ...document, token: "saved-token", revision: 2 }),
      { status: 200 },
    ),
  );
  await nativeProcessApi.save(
    "session with spaces",
    Object.assign(document, {
      token: "dummy-response-only-token",
      revision: 1,
    }),
    "expected-token",
    "request-id",
  );
  const [url, request] = vi.mocked(hostAdapter.fetch).mock.calls[0];
  expect(String(url)).toContain("session_id=session+with+spaces");
  expect(request?.method).toBe("PUT");
  expect(request?.headers).toMatchObject({ "X-Trace-Id": "abc123" });
  expect(JSON.parse(request?.body as string)).toEqual({
    definition: document.definition,
    presentation: document.presentation,
    expected_token: "expected-token",
    request_id: "request-id",
  });
  expect(span.end).toHaveBeenCalledOnce();
});
it.each(["bindings", "contract", "examples", "runs", "check", "documents"])(
  "uses document resources for the valid process ID %s",
  async (id) => {
    const document = emptyDocument();
    document.definition.id = id;
    vi.mocked(hostAdapter.fetch).mockImplementation(
      async () => new Response(JSON.stringify({}), { status: 200 }),
    );
    await nativeProcessApi.get("session", id);
    await nativeProcessApi.save("session", document, "token", "save-request");
    await nativeRunApi.history("session", id, "next page");
    await nativeRunApi.start(
      "session",
      id,
      "token",
      "run-request",
      {},
      60,
      null,
    );
    const requests = vi
      .mocked(hostAdapter.fetch)
      .mock.calls.map(([url, init]) => ({
        path: new URL(String(url)).pathname,
        method: init?.method,
      }));
    const path = `/api/native-processes/documents/${id}`;
    expect(requests).toEqual([
      { path, method: "GET" },
      { path, method: "PUT" },
      { path: `${path}/runs`, method: "GET" },
      { path: `${path}/runs`, method: "POST" },
    ]);
    const historyUrl = new URL(
      String(vi.mocked(hostAdapter.fetch).mock.calls[2][0]),
    );
    expect(historyUrl.searchParams.get("cursor")).toBe("next page");
    expect(historyUrl.searchParams.get("session_id")).toBe("session");
  },
);
it("uses the canonical collection for create and paginated list", async () => {
  vi.mocked(hostAdapter.fetch).mockImplementation(
    async () => new Response(JSON.stringify({}), { status: 200 }),
  );
  await nativeProcessApi.create("session", emptyDocument(), "request-id");
  await nativeProcessApi.list("session");
  await nativeProcessApi.list("session", "next page");
  for (const [url] of vi.mocked(hostAdapter.fetch).mock.calls) {
    expect(new URL(String(url)).pathname).toBe(
      "/api/native-processes/documents",
    );
  }
  const listUrl = new URL(
    String(vi.mocked(hostAdapter.fetch).mock.calls[2][0]),
  );
  expect(listUrl.searchParams.get("cursor")).toBe("next page");
});
it("retains native conflict details and actionable findings", async () => {
  const detail = {
    code: "NATIVE_CONFLICT",
    message: "A newer version exists.",
    recovery: "Reload or save a copy.",
    trace_id: "trace-native",
    findings: [],
  };
  vi.mocked(hostAdapter.fetch).mockResolvedValue(
    new Response(JSON.stringify({ detail }), { status: 409 }),
  );
  const failure = await nativeProcessApi
    .create("session", emptyDocument(), "request-id")
    .catch((error) => error);
  expect(failure).toBeInstanceOf(NativeProcessError);
  expect(failure.detail).toEqual(detail);
  expect(span.error).toHaveBeenCalledOnce();
});
it("rejects an unreadable service response without pretending a document was saved", async () => {
  vi.mocked(hostAdapter.fetch).mockResolvedValue(
    new Response("not JSON", { status: 200 }),
  );
  await expect(nativeProcessApi.contract("session")).rejects.toThrow(
    /unreadable/,
  );
});
