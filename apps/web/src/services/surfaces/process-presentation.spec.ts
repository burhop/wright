import { describe, expect, it, vi } from "vitest";
import {
  assertPresentationContext,
  createPresentationProcessClient,
  type ProcessPresentationContext,
  type InputSnapshot,
  type StartReceipt,
  type ProcessFetch,
} from "@wright/process-client";

const process = {
  workspace_id: "workspace",
  source_path: "workflows/job.wflow",
  source_digest: "a".repeat(64),
};
const context: ProcessPresentationContext = {
  schema_version: "wright.process-presentation/1",
  process,
  session_id: "session-one",
  ui_id: "ui-" + "a".repeat(32),
  revision_id: "revision-" + "b".repeat(32),
  run_id: null,
  read_only: true,
  capabilities: ["process.read", "process.results", "process.navigate"],
  presentation_id: "presentation-one",
  generation: 1,
};
const input: InputSnapshot = {
  process,
  snapshot_id: "inputs-one",
  digest: "c".repeat(64),
  created_at: "2026-10-01T12:00:00Z",
  bindings: [],
};
const receipt: StartReceipt = {
  process,
  request_id: "request-one",
  run_id: "run-one",
  input_snapshot_id: input.snapshot_id,
  input_digest: input.digest,
  payload_digest: "d".repeat(64),
  principal_id: "user",
  created_at: input.created_at,
};
const json = (value: unknown) =>
  new Response(JSON.stringify(value), {
    headers: { "content-type": "application/json" },
  });
const snapshot = (run: string | null = null) => ({
  context: { process, run_id: run, generated_at: input.created_at },
  state: "running",
});

describe("isolated process presentation transport", () => {
  it.each([
    { schema_version: "future" },
    { read_only: "false" },
    { generation: 0 },
    { ui_id: "chosen-ui" },
    { revision_id: "chosen-revision" },
    { run_id: undefined },
    { capabilities: ["process.read", "process.invokeTool"] },
    { capabilities: ["process.read", "process.read"] },
    { capabilities: ["process.results"] },
    { capabilities: ["process.read", "process.start"] },
    { native_token: "forbidden" },
  ])("rejects malformed/widened context %j", (changes) => {
    expect(() =>
      assertPresentationContext({ ...context, ...changes }),
    ).toThrow();
  });

  it("clones and freezes exact context without trusting later mutations", () => {
    const raw = {
      ...context,
      process: { ...process },
      capabilities: [...context.capabilities],
    };
    const checked = assertPresentationContext(raw);
    raw.process.workspace_id = "other";
    raw.capabilities.push("process.start");
    expect(checked.process.workspace_id).toBe("workspace");
    expect(checked.capabilities).not.toContain("process.start");
    expect(Object.isFrozen(checked.process)).toBe(true);
  });

  it("reads only the reserved same-origin transport with no native credential", async () => {
    const fetch = vi.fn<ProcessFetch>(async () => json(snapshot()));
    const client = createPresentationProcessClient(context, { fetch });
    await client.getSnapshot();
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url.startsWith("/__wright/process/interaction?")).toBe(true);
    expect(
      new URL(url, "https://preview.example.test").searchParams.get(
        "session_id",
      ),
    ).toBe(context.session_id);
    expect(init.credentials).toBe("same-origin");
    expect(init.mode).toBe("same-origin");
    expect(init.redirect).toBe("error");
    expect(new Headers(init.headers).has("Authorization")).toBe(false);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("rejects all preview mutations before fetching", async () => {
    const fetch = vi.fn<ProcessFetch>(async () => json(snapshot()));
    const client = createPresentationProcessClient(context, { fetch });
    const operations = [
      () => client.setInputs([]),
      () => client.uploadInput("brief", new File(["ref"], "ref.png")),
      () => client.start(input, "request-one"),
      () =>
        client.respond({
          checkpointId: "input-one",
          subjectDigest: process.source_digest,
          value: "answer",
          requestId: "answer-one",
        }),
      () =>
        client.decide({
          checkpointId: "review-one",
          subjectDigest: process.source_digest,
          decision: "approved",
          reason: "review",
          requestId: "decision-one",
        }),
      () =>
        client.requestAction({
          actionId: "continue-one",
          subjectDigest: process.source_digest,
          requestId: "action-one",
        }),
      () => client.cancel("run-one", "cancel-one"),
    ];
    for (const operation of operations)
      await expect(operation()).rejects.toThrow("not authorized");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("binds snapshot/attach/follow/cancel to the exact current run", async () => {
    const fetch = vi.fn<ProcessFetch>(async () => json(snapshot("run-one")));
    const client = createPresentationProcessClient(
      { ...context, run_id: "run-one" },
      { fetch },
    );
    await client.getSnapshot();
    expect(String(fetch.mock.calls[0][0])).toContain("/runs/run-one?");
    await expect(client.getSnapshot({ runId: "other-run" })).rejects.toThrow(
      "not authorized",
    );
    await expect(client.attach("other-run")).rejects.toThrow("not authorized");
    await expect(
      client.follow({ runId: "other-run" })[Symbol.asyncIterator]().next(),
    ).rejects.toThrow("not authorized");
    await expect(
      client.navigate({ kind: "run", run_id: "other-run" }),
    ).rejects.toThrow("not authorized");
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("notifies native host from a verified receipt without broadening the current binding", async () => {
    const fetch = vi.fn<ProcessFetch>(async () => json(receipt));
    const onRunStarted = vi.fn();
    const client = createPresentationProcessClient(
      {
        ...context,
        read_only: false,
        capabilities: ["process.read", "process.start"],
      },
      { fetch, onRunStarted },
    );
    expect(fetch).not.toHaveBeenCalled();
    expect(await client.start(input, receipt.request_id)).toEqual(receipt);
    expect(onRunStarted).toHaveBeenCalledWith(receipt);
    await expect(client.attach(receipt.run_id)).rejects.toThrow(
      "not authorized",
    );
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("does not change known accepted outcome when host navigation fails", async () => {
    const client = createPresentationProcessClient(
      {
        ...context,
        read_only: false,
        capabilities: ["process.read", "process.start"],
      },
      {
        fetch: async () => json(receipt),
        onRunStarted: () => {
          throw new Error("host lost");
        },
      },
    );
    expect(await client.start(input, receipt.request_id)).toEqual(receipt);
  });

  it("does not notify host from a mismatched or uncertain start reply", async () => {
    const onRunStarted = vi.fn();
    const client = createPresentationProcessClient(
      {
        ...context,
        read_only: false,
        capabilities: ["process.read", "process.start"],
      },
      {
        fetch: async () => json({ ...receipt, request_id: "wrong-request" }),
        onRunStarted,
      },
    );
    await expect(client.start(input, receipt.request_id)).rejects.toMatchObject(
      { uncertain: true, requestId: receipt.request_id },
    );
    expect(onRunStarted).not.toHaveBeenCalled();
  });

  it("requires fresh native binding for preparation controls on an attached run", async () => {
    const fetch = vi.fn<ProcessFetch>(async () => json(snapshot("run-one")));
    const client = createPresentationProcessClient(
      {
        ...context,
        read_only: false,
        run_id: "run-one",
        capabilities: ["process.read", "process.inputs", "process.start"],
      },
      { fetch },
    );
    await expect(client.setInputs([])).rejects.toThrow("not authorized");
    await expect(client.start(input, "request-one")).rejects.toThrow(
      "not authorized",
    );
    expect(fetch).not.toHaveBeenCalled();
  });
});
