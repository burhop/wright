import { describe, expect, it, vi } from "vitest";
import {
  createNativeProcessClient,
  assertContract,
  ProcessClientError,
  type FollowUpdate,
  type ProcessFetch,
  type ProcessRef,
  type InputSnapshot,
  type InteractionSnapshot,
  type StartReceipt,
} from "@wright/process-client";

const digest = "a".repeat(64);
const process: ProcessRef = {
  workspace_id: "workspace",
  source_path: "workflows/part.wflow",
  source_digest: digest,
};
const input: InputSnapshot = {
  process,
  snapshot_id: "inputs-one",
  digest,
  created_at: "2026-09-30T12:00:00Z",
  bindings: [],
};
const snapshot = (
  run: string | null = null,
  state: InteractionSnapshot["state"] = "running",
): InteractionSnapshot => ({
  context: { process, run_id: run, generated_at: "2026-09-30T12:00:00Z" },
  state,
});
const receipt: StartReceipt = {
  process,
  request_id: "request-one",
  run_id: "run-one",
  input_snapshot_id: input.snapshot_id,
  input_digest: digest,
  payload_digest: digest,
  principal_id: "server-derived",
  created_at: input.created_at,
};
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), {
    status,
    headers: { "content-type": "application/json" },
  });
const fake = (implementation: ProcessFetch) => vi.fn(implementation);
const client = (fetch: ProcessFetch = fake(async () => json(snapshot()))) =>
  createNativeProcessClient({
    process,
    sessionId: "session",
    fetch,
    reconnectDelayMs: 0,
  });
const page = (sequence: number, following = true) => ({
  run_id: "run-one",
  cursor: `cursor-${sequence}`,
  events: [{ sequence, kind: "task_completed" }],
  following,
  has_more: false,
  state: following ? "running" : "completed",
});
const frame = (sequence: number, following = true) =>
  `id: cursor-${sequence}\nevent: progress\ndata: ${JSON.stringify(page(sequence, following))}\n\n`;
function stream(chunks: string[]) {
  const encoder = new TextEncoder();
  return new Response(
    new ReadableStream({
      start(controller) {
        for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
        controller.close();
      },
    }),
    { headers: { "content-type": "text/event-stream" } },
  );
}

describe("public process contract guards", () => {
  it("requires a discriminator in owning tagged input unions", () => {
    expect(() =>
      assertContract("InputSnapshot", {
        ...input,
        bindings: [{ input_id: "prompt", value: "hello" }],
      }),
    ).toThrow(ProcessClientError);
  });
  it("uses the owning shared shapes and optional defaults", () => {
    expect(assertContract("InteractionSnapshot", snapshot())).toEqual(
      snapshot(),
    );
    expect(assertContract("InputSnapshot", input)).toEqual(input);
    expect(assertContract("JsonValue", { value: [true, null, 12] })).toEqual({
      value: [true, null, 12],
    });
  });
  it.each([
    NaN,
    Infinity,
    undefined,
    new Date(),
    () => 1,
    { value: undefined },
    "\ud800",
  ])("rejects non-JSON values: %s", (value) => {
    expect(() => assertContract("JsonValue", value)).toThrow(
      ProcessClientError,
    );
  });
  it("rejects cycles, excessive depth, oversized inline values and accessors", () => {
    const cycle: Record<string, unknown> = {};
    cycle.child = cycle;
    let deep: unknown = null;
    for (let i = 0; i < 26; i++) deep = [deep];
    for (const value of [
      cycle,
      deep,
      "x".repeat(65536),
      {
        get value() {
          throw new Error("must not execute");
        },
      },
    ]) {
      expect(() => assertContract("JsonValue", value)).toThrow(
        ProcessClientError,
      );
    }
  });
  it.each([
    { ...snapshot(), state: "made_up" },
    { ...snapshot(), actor: "injected" },
    { ...input, digest: "bad" },
    {
      ...input,
      bindings: Array.from({ length: 257 }, () => ({
        kind: "value",
        input_id: "prompt",
        value: "hello",
      })),
    },
  ])("rejects incompatible closed/bounded contracts", (value) => {
    expect(() =>
      assertContract(
        "context" in value ? "InteractionSnapshot" : "InputSnapshot",
        value,
      ),
    ).toThrow(ProcessClientError);
  });
});

describe("native process client", () => {
  it("fixes host scope, uses host fetch, and reads without starting work", async () => {
    const fetch = fake(async () => json(snapshot()));
    await client(fetch).getSnapshot();
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain("/api/workspace/process-interfaces/interaction?");
    expect(
      new URL(url, "http://localhost").searchParams.get(
        "expected_storage_digest",
      ),
    ).toBe(digest);
    expect(init.method).toBe("GET");
    expect(init.cache).toBe("no-store");
  });
  it("copies host scope so later caller mutation cannot redirect it", async () => {
    const mutable = { ...process };
    const fetch = fake(async () => json(snapshot()));
    const scoped = createNativeProcessClient({
      process: mutable,
      sessionId: "session",
      fetch,
    });
    mutable.workspace_id = "other";
    mutable.source_path = "other.wflow";
    await scoped.getSnapshot();
    expect(fetch.mock.calls[0]?.[0]).toContain("path=workflows%2Fpart.wflow");
  });
  it("serializes only allowed fields, not caller actor/workspace authority", async () => {
    const fetch = fake(async () => json(input));
    await client(fetch).setInputs([
      { kind: "value", input_id: "prompt", value: "small part" },
    ]);
    const body = JSON.parse(
      (fetch.mock.calls[0] as unknown as [string, RequestInit])[1]
        .body as string,
    );
    expect(body).toEqual({
      session_id: "session",
      path: process.source_path,
      expected_storage_digest: digest,
      bindings: [{ kind: "value", input_id: "prompt", value: "small part" }],
    });
  });
  it("rejects injected binding fields before any mutation", async () => {
    const fetch = fake(async () => json(input));
    await expect(
      client(fetch).setInputs([
        { input_id: "prompt", value: "hello", actor: "admin" } as never,
      ]),
    ).rejects.toMatchObject({ reason: { code: "RESPONSE_INVALID" } });
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each(["workspace", "source_path", "source_digest"])(
    "rejects wrong reply scope: %s",
    async (field) => {
      const changed =
        field === "workspace"
          ? { ...process, workspace_id: "other" }
          : {
              ...process,
              [field]:
                field === "source_digest" ? "b".repeat(64) : "elsewhere.wflow",
            };
      await expect(
        client(
          fake(async () =>
            json({
              ...snapshot(),
              context: { ...snapshot().context, process: changed },
            }),
          ),
        ).getSnapshot(),
      ).rejects.toMatchObject({ reason: { code: "SCOPE_DENIED" } });
    },
  );
  it("rejects an attach response for another run", async () => {
    await expect(
      client(fake(async () => json(snapshot("other-run")))).attach("run-one"),
    ).rejects.toMatchObject({ reason: { code: "SCOPE_DENIED" } });
  });
  it("requires the exact input scope before start", async () => {
    const fetch = fake(async () => json(receipt));
    await expect(
      client(fetch).start(
        { ...input, process: { ...process, workspace_id: "other" } },
        "request-one",
      ),
    ).rejects.toMatchObject({ reason: { code: "SCOPE_DENIED" } });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("starts explicitly with a caller-retained stable request and input digest", async () => {
    const fetch = fake(async () => json(receipt, 202));
    expect(await client(fetch).start(input, "request-one")).toEqual(receipt);
    const body = JSON.parse(
      (fetch.mock.calls[0] as unknown as [string, RequestInit])[1]
        .body as string,
    );
    expect(body.request_id).toBe("request-one");
    expect(body.expected_input_digest).toBe(digest);
  });
  it.each(["request_id", "input_snapshot_id", "input_digest"])(
    "does not accept a mismatched start receipt: %s",
    async (field) => {
      const other = field === "input_digest" ? "b".repeat(64) : "other";
      await expect(
        client(
          fake(async () => json({ ...receipt, [field]: other }, 202)),
        ).start(input, "request-one"),
      ).rejects.toMatchObject({ uncertain: true, requestId: "request-one" });
    },
  );
  it("reports a lost start acknowledgement and never retries automatically", async () => {
    const fetch = fake(async () => {
      throw new TypeError("disconnected");
    });
    await expect(
      client(fetch).start(input, "request-one"),
    ).rejects.toMatchObject({
      reason: { code: "OUTCOME_UNKNOWN" },
      requestId: "request-one",
      uncertain: true,
    });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("preserves a structured backend reason and recovery instruction", async () => {
    const reason = {
      code: "OPTION_STALE",
      message: "Material choices changed.",
      correction: "Refresh options and prepare again.",
    };
    await expect(
      client(fake(async () => json({ detail: { reason } }, 409))).getSnapshot(),
    ).rejects.toMatchObject({ reason, httpStatus: 409 });
  });
  it("does not render arbitrary raw HTTP failures as user messages", async () => {
    await expect(
      client(
        fake(async () => new Response("secret debug payload", { status: 500 })),
      ).getSnapshot(),
    ).rejects.toMatchObject({ reason: { code: "CAPABILITY_UNAVAILABLE" } });
  });
  it("cancellation is explicit and represents a request, not confirmed stop", async () => {
    const fetch = fake(async () =>
      json({
        request_id: "cancel-one",
        run_id: "run-one",
        state: "cancellation_requested",
      }),
    );
    expect((await client(fetch).cancel("run-one", "cancel-one")).state).toBe(
      "cancellation_requested",
    );
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("pre-aborted submission never reaches the transport", async () => {
    const fetch = fake(async () => json(receipt));
    const abort = new AbortController();
    abort.abort();
    await expect(
      client(fetch).start(input, "request-one", { signal: abort.signal }),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("a disconnected cancellation cannot be reported as a confirmed stop", async () => {
    const fetch = fake(async () => {
      throw new TypeError("connection lost");
    });
    await expect(
      client(fetch).cancel("run-one", "cancel-one"),
    ).rejects.toMatchObject({
      requestId: "cancel-one",
      uncertain: true,
      reason: { code: "OUTCOME_UNKNOWN" },
    });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("checks readiness against the exact prepared input digest", async () => {
    const fetch = fake(async () =>
      json({
        process,
        assessment_id: "assessment",
        input_digest: "b".repeat(64),
        assessed_at: input.created_at,
        state: "ready",
      }),
    );
    await expect(client(fetch).checkReadiness(input)).rejects.toMatchObject({
      reason: { code: "SUBJECT_STALE" },
    });
  });
  it("passes only a validated exact navigation intent to the native host", async () => {
    const navigate = vi.fn(async () => undefined);
    const scoped = createNativeProcessClient({
      process,
      sessionId: "session",
      fetch: fake(async () => json(snapshot())),
      navigate,
    });
    await scoped.navigate({ kind: "block", block_id: "design" });
    expect(navigate).toHaveBeenCalledWith(process, {
      kind: "block",
      block_id: "design",
    });
    await expect(
      scoped.navigate({ kind: "block", url: "javascript:alert(1)" } as never),
    ).rejects.toBeInstanceOf(ProcessClientError);
    expect(navigate).toHaveBeenCalledTimes(1);
  });
  it("fails reserved capabilities explicitly without speculative calls", async () => {
    const fetch = fake(async () => json(snapshot()));
    const scoped = client(fetch);
    await expect(
      scoped.respond({
        checkpointId: "cp",
        subjectDigest: digest,
        value: {},
        requestId: "response",
      }),
    ).rejects.toMatchObject({ reason: { code: "CAPABILITY_UNAVAILABLE" } });
    await expect(
      scoped.getRepresentation({ artifact_ref: "part.stl", sha256: digest }),
    ).rejects.toMatchObject({ reason: { code: "RESPONSE_INVALID" } });
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("scoped input upload and representation reads", () => {
  const reference = {
    artifact_ref: `.wright/process-inputs/${digest}/one.txt`,
    sha256: digest,
    media_type: "text/plain",
  };
  const binary = (content = "data", headers: Record<string, string> = {}) =>
    new Response(content, {
      headers: {
        "content-type": "text/plain",
        "content-length": "4",
        "x-content-type-options": "nosniff",
        "x-wright-artifact-sha256": digest,
        ...headers,
      },
    });
  it("uploads only the declared input and host source fields without execution", async () => {
    const fetch = fake(async () => json(reference));
    await expect(
      client(fetch).uploadInput("brief", new File(["data"], "one.txt")),
    ).resolves.toEqual(reference);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = fetch.mock.calls[0];
    expect(url).toBe("/api/workspace/process-interfaces/inputs/upload");
    expect(init?.method).toBe("POST");
    expect(init?.headers).toEqual({ accept: "application/json" });
    const body = init?.body as FormData;
    expect([...body.keys()].sort()).toEqual([
      "expected_storage_digest",
      "file",
      "input_id",
      "path",
      "session_id",
    ]);
    expect(body.get("input_id")).toBe("brief");
    expect(body.get("expected_storage_digest")).toBe(digest);
    expect((body.get("file") as File).name).toBe("one.txt");
  });
  it.each(["../one.txt", ".hidden", "bad\nname.txt", "bad%name.txt"])(
    "rejects unsupported input names before a request: %s",
    async (name) => {
      const fetch = fake(async () => json(reference));
      await expect(
        client(fetch).uploadInput("brief", new File(["data"], name)),
      ).rejects.toMatchObject({ reason: { code: "RESPONSE_INVALID" } });
      expect(fetch).not.toHaveBeenCalled();
    },
  );
  it("rejects empty or oversized inputs and another source's upload receipt", async () => {
    const fetch = fake(async () =>
      json({
        ...reference,
        artifact_ref: `.wright/process-inputs/${"b".repeat(64)}/one.txt`,
      }),
    );
    const scoped = client(fetch);
    await expect(
      scoped.uploadInput("brief", new File([], "empty.txt")),
    ).rejects.toMatchObject({ reason: { code: "RESPONSE_INVALID" } });
    const oversized = new File(["x"], "large.txt");
    Object.defineProperty(oversized, "size", { value: 33_554_433 });
    await expect(scoped.uploadInput("brief", oversized)).rejects.toMatchObject({
      reason: { code: "RESPONSE_INVALID" },
    });
    expect(fetch).not.toHaveBeenCalled();
    await expect(
      scoped.uploadInput("brief", new File(["data"], "one.txt")),
    ).rejects.toMatchObject({ reason: { code: "SCOPE_DENIED" } });
  });
  it("reads through the exact run and preparation owner without a generic file route", async () => {
    const fetch = fake(async () => binary());
    const scoped = client(fetch);
    const blob = await scoped.getRepresentation(reference, {
      runId: "run-one",
    });
    expect(blob.type).toBe("text/plain");
    expect(blob.size).toBe(4);
    expect(fetch.mock.calls[0][0]).toBe(
      "/api/workspace/process-interfaces/representations/read",
    );
    expect(JSON.parse(fetch.mock.calls[0][1]!.body as string)).toEqual({
      session_id: "session",
      path: process.source_path,
      expected_storage_digest: digest,
      reference,
      run_id: "run-one",
    });
    await scoped.getRepresentation(reference, {
      inputSnapshotId: "inputs-one",
    });
    expect(
      JSON.parse(fetch.mock.calls[1][1]!.body as string).input_snapshot_id,
    ).toBe("inputs-one");
    await expect(scoped.getRepresentation(reference)).rejects.toMatchObject({
      reason: { code: "RESPONSE_INVALID" },
    });
    await expect(
      scoped.getRepresentation(reference, {
        runId: "run-one",
        inputSnapshotId: "inputs-one",
      }),
    ).rejects.toMatchObject({ reason: { code: "RESPONSE_INVALID" } });
    expect(fetch).toHaveBeenCalledTimes(2);
  });
  it.each<Record<string, string>>([
    { "x-wright-artifact-sha256": "b".repeat(64) },
    { "x-content-type-options": "" },
    { "content-length": "104857601" },
    { "content-length": "3" },
    { "content-length": "5" },
    { "content-length": "invalid" },
  ])(
    "rejects unverified, excessive or incomplete representations: %s",
    async (headers) => {
      const fetch = fake(async () => binary("data", headers));
      await expect(
        client(fetch).getRepresentation(reference, { runId: "run-one" }),
      ).rejects.toMatchObject({ reason: { code: "UI_INCOMPATIBLE" } });
      expect(fetch).toHaveBeenCalledTimes(1);
    },
  );
  it("keeps HTML inert and preserves abort and owning errors", async () => {
    const html = fake(async () =>
      binary("data", { "content-type": "text/html" }),
    );
    expect(
      (await client(html).getRepresentation(reference, { runId: "run-one" }))
        .type,
    ).toBe("application/octet-stream");
    const fetch = fake(async () => {
      throw new TypeError("connection lost");
    });
    await expect(
      client(fetch).getRepresentation(reference, { runId: "run-one" }),
    ).rejects.toMatchObject({ reason: { code: "CAPABILITY_UNAVAILABLE" } });
    const control = new AbortController();
    control.abort();
    await expect(
      client(fetch).getRepresentation(reference, {
        runId: "run-one",
        signal: control.signal,
      }),
    ).rejects.toMatchObject({ name: "AbortError" });
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});

describe("recorded event attachment and reconciliation", () => {
  it("parses chunk boundaries and CRLF, then reads the terminal snapshot without mutations", async () => {
    const content = frame(1, false).replaceAll("\n", "\r\n");
    const fetch = fake(async (url: RequestInfo | URL) =>
      String(url).includes("/events?")
        ? stream([content.slice(0, 17), content.slice(17)])
        : json(snapshot("run-one", "completed")),
    );
    const updates: FollowUpdate[] = [];
    for await (const update of client(fetch).follow({ runId: "run-one" }))
      updates.push(update);
    expect(updates.filter((v) => v.type === "progress")).toHaveLength(1);
    expect(updates.filter((v) => v.type === "snapshot").at(-1)).toMatchObject({
      snapshot: { state: "completed" },
    });
    for (const call of fetch.mock.calls)
      expect((call[1] as RequestInit)?.method).toBe("GET");
  });
  it("reconnects using the last recorded cursor and reconciles without restarting", async () => {
    let streams = 0;
    const fetch = fake(async (url: RequestInfo | URL) =>
      String(url).includes("/events?")
        ? stream([frame(++streams, streams === 1)])
        : json(snapshot("run-one", streams > 1 ? "completed" : "running")),
    );
    const updates: FollowUpdate[] = [];
    for await (const update of client(fetch).follow({ runId: "run-one" }))
      updates.push(update);
    expect(streams).toBe(2);
    expect(
      fetch.mock.calls.find((v) => String(v[0]).includes("cursor=cursor-1")),
    ).toBeDefined();
    expect(
      updates.some(
        (v) => v.type === "connection" && v.state === "reconnecting",
      ),
    ).toBe(true);
  });
  it("recovers a rejected cursor through a full snapshot and a fresh read attachment", async () => {
    let streams = 0;
    const reason = {
      code: "SUBJECT_STALE",
      message: "Cursor expired.",
      correction: "Reattach.",
    };
    const fetch = fake(async (url: RequestInfo | URL) =>
      String(url).includes("/events?")
        ? ++streams === 1
          ? json({ detail: { reason } }, 409)
          : stream([frame(1, false)])
        : json(snapshot("run-one")),
    );
    for await (const _ of client(fetch).follow({
      runId: "run-one",
      cursor: "expired",
    })) {
      /* consume */
    }
    const eventCalls = fetch.mock.calls.filter((v) =>
      String(v[0]).includes("/events?"),
    );
    expect(eventCalls[0]?.[0]).toContain("cursor=expired");
    expect(eventCalls[1]?.[0]).not.toContain("cursor=");
  });
  it("bounds repeated connection failures", async () => {
    const fetch = fake(async (url: RequestInfo | URL) => {
      if (String(url).includes("/events?")) throw new TypeError("offline");
      return json(snapshot("run-one"));
    });
    const consume = async () => {
      for await (const _ of client(fetch).follow({
        runId: "run-one",
        maxReconnects: 2,
      })) {
        /* consume */
      }
    };
    await expect(consume()).rejects.toMatchObject({
      reason: { code: "CAPABILITY_UNAVAILABLE" },
    });
    expect(
      fetch.mock.calls.filter((v) => String(v[0]).includes("/events?")),
    ).toHaveLength(3);
  });
  it("rejects wrong run events and oversized frames without mutation", async () => {
    for (const content of [
      frame(1, false).replace("run-one", "other-run"),
      `data: ${"x".repeat(66000)}\n\n`,
    ]) {
      const fetch = fake(async (url: RequestInfo | URL) =>
        String(url).includes("/events?")
          ? stream([content])
          : json(snapshot("run-one")),
      );
      const consume = async () => {
        for await (const _ of client(fetch).follow({ runId: "run-one" })) {
          /* consume */
        }
      };
      await expect(consume()).rejects.toBeInstanceOf(ProcessClientError);
      expect(
        fetch.mock.calls.filter((v) => String(v[0]).includes("/events?")),
      ).toHaveLength(1);
    }
  });
  it("closing an event observer releases it without cancelling the run", async () => {
    const cancelled = vi.fn();
    const fetch = fake(async (url: RequestInfo | URL) =>
      String(url).includes("/events?")
        ? new Response(
            new ReadableStream({
              start(c) {
                c.enqueue(new TextEncoder().encode(frame(1)));
              },
              cancel: cancelled,
            }),
            { headers: { "content-type": "text/event-stream" } },
          )
        : json(snapshot("run-one")),
    );
    for await (const update of client(fetch).follow({ runId: "run-one" }))
      if (update.type === "progress") break;
    expect(cancelled).toHaveBeenCalled();
    expect(fetch.mock.calls.some((v) => String(v[0]).includes("/cancel"))).toBe(
      false,
    );
  });
  it("an abort releases a pending reader without sending cancellation", async () => {
    const cancelled = vi.fn();
    const abort = new AbortController();
    const fetch = fake(async (url) =>
      String(url).includes("/events?")
        ? new Response(new ReadableStream({ cancel: cancelled }), {
            headers: { "content-type": "text/event-stream" },
          })
        : json(snapshot("run-one")),
    );
    const updates = client(fetch).follow({
      runId: "run-one",
      signal: abort.signal,
    });
    const iterator = updates[Symbol.asyncIterator]();
    await iterator.next();
    await iterator.next();
    const pending = iterator.next();
    abort.abort();
    expect((await pending).done).toBe(true);
    expect(cancelled).toHaveBeenCalled();
    expect(fetch.mock.calls.some((v) => String(v[0]).includes("/cancel"))).toBe(
      false,
    );
  });
  it("a server scope-reconciliation event stops reattachment and preserves the reason", async () => {
    const reason = {
      code: "SOURCE_CHANGED",
      message: "The accepted source changed.",
      correction: "Open its current revision.",
    };
    const fetch = fake(async (url) =>
      String(url).includes("/events?")
        ? stream([`event: reconciliation\ndata: ${JSON.stringify(reason)}\n\n`])
        : json(snapshot("run-one")),
    );
    const updates: FollowUpdate[] = [];
    const consume = async () => {
      for await (const update of client(fetch).follow({ runId: "run-one" }))
        updates.push(update);
    };
    await expect(consume()).rejects.toMatchObject({ reason });
    expect(updates).toContainEqual({ type: "reconciliation", reason });
    expect(
      fetch.mock.calls.filter((v) => String(v[0]).includes("/events?")),
    ).toHaveLength(1);
  });
  it("does not accept a partial final SSE frame after disconnection", async () => {
    const fetch = fake(async (url) =>
      String(url).includes("/events?")
        ? stream([frame(1, false).slice(0, -2)])
        : json(snapshot("run-one")),
    );
    const updates: FollowUpdate[] = [];
    const consume = async () => {
      for await (const update of client(fetch).follow({
        runId: "run-one",
        maxReconnects: 0,
      }))
        updates.push(update);
    };
    await expect(consume()).rejects.toBeInstanceOf(ProcessClientError);
    expect(updates.some((v) => v.type === "progress")).toBe(false);
  });
});
