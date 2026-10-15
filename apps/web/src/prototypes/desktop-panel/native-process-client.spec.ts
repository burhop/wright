import { describe, expect, it, vi } from "vitest";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type {
  InputSnapshot,
  InteractionResponse,
  InteractionSnapshot,
  StartReceipt,
} from "@wright/process-client";
import {
  createNativePanelProcessClient,
  type NativeProcessCall,
} from "./native-process-client";

const digest = "a".repeat(64);
const process = {
  workspace_id: "workspace",
  source_path: "workflows/test.wflow",
  source_digest: digest,
};
const input: InputSnapshot = {
  process,
  snapshot_id: "prepared",
  digest,
  created_at: "2026-10-12T12:00:00Z",
  bindings: [],
};
const snapshot = (runId = "saved-run"): InteractionSnapshot => ({
  context: { process, run_id: runId, generated_at: input.created_at },
  state: "running",
});
const receipt: StartReceipt = {
  process,
  request_id: "stable-start",
  run_id: "saved-run",
  input_snapshot_id: input.snapshot_id,
  input_digest: digest,
  payload_digest: digest,
  principal_id: "wright-owned",
  created_at: input.created_at,
};
const result = (value: object): CallToolResult => ({
  content: [],
  structuredContent: { ...value },
});
function setup() {
  const call = vi
    .fn<NativeProcessCall>()
    .mockResolvedValue(result({ ok: true, document: snapshot() }));
  const options = {
    process,
    sessionId: "session",
    workspaceName: "Prototype",
    call,
  };
  return { call, options, ...createNativePanelProcessClient(options) };
}

describe("native process bridge over the existing public client", () => {
  it("reads the exact retained run and rejects another run's snapshot", async () => {
    const { client, call } = setup();
    await client.attach("saved-run");
    expect(call.mock.calls[0].slice(0, 2)).toEqual([
      "wright_process_ui_read",
      {
        workspace_id: "workspace",
        session_id: "session",
        path: process.source_path,
        expected_storage_digest: digest,
        operation: "snapshot",
        run_id: "saved-run",
      },
    ]);
    call.mockResolvedValueOnce(
      result({ ok: true, document: snapshot("other-run") }),
    );
    await expect(client.attach("saved-run")).rejects.toMatchObject({
      reason: { code: "SCOPE_DENIED" },
    });
  });
  it("preserves an encoded identifier without changing its subject", async () => {
    const { client, call } = setup();
    call.mockResolvedValueOnce(
      result({ ok: true, document: snapshot("saved:run") }),
    );
    await client.attach("saved:run");
    expect(call.mock.calls[0][1].run_id).toBe("saved:run");
  });
  it("keeps the resolved session and transport when caller options change", async () => {
    const { client, call, options } = setup();
    const replacement = vi.fn<NativeProcessCall>();
    Object.assign(options, { sessionId: "other-session", call: replacement });
    await client.attach("saved-run");
    expect(call.mock.calls[0][1].session_id).toBe("session");
    expect(replacement).not.toHaveBeenCalled();
  });
  it("starts with the exact prepared subject and stable request identity", async () => {
    const { client, call } = setup();
    call.mockResolvedValueOnce(result({ ok: true, document: receipt }));
    expect(await client.start(input, "stable-start")).toEqual(receipt);
    expect(call.mock.calls[0][1]).toMatchObject({
      operation: "start",
      input_snapshot_id: "prepared",
      expected_input_digest: digest,
      request_id: "stable-start",
    });
    expect(call).toHaveBeenCalledTimes(1);
  });
  it("rejects a mismatched acknowledgement as uncertain without retrying", async () => {
    const { client, call } = setup();
    call.mockResolvedValueOnce(
      result({ ok: true, document: { ...receipt, request_id: "other-start" } }),
    );
    await expect(client.start(input, "stable-start")).rejects.toMatchObject({
      uncertain: true,
      requestId: "stable-start",
    });
    expect(call).toHaveBeenCalledTimes(1);
  });
  it("keeps owner denial distinct from an unknown write outcome", async () => {
    const { client, call } = setup();
    call.mockResolvedValueOnce(
      result({
        ok: false,
        http_status: 403,
        reason: {
          code: "SCOPE_DENIED",
          message: "Not permitted",
          correction: "Keep your draft",
        },
      }),
    );
    await expect(client.start(input, "stable-start")).rejects.toMatchObject({
      uncertain: false,
      reason: { code: "SCOPE_DENIED" },
    });
    call.mockResolvedValueOnce(
      result({
        ok: false,
        http_status: 503,
        reason: {
          code: "OUTCOME_UNKNOWN",
          message: "Not confirmed",
          correction: "Read the saved request",
        },
      }),
    );
    await expect(client.start(input, "stable-start")).rejects.toMatchObject({
      uncertain: true,
      requestId: "stable-start",
    });
    expect(call).toHaveBeenCalledTimes(2);
  });
  it("submits scalar declared input and validates its exact acknowledgement", async () => {
    const { client, call } = setup();
    const answer: InteractionResponse = {
      response_id: "answer",
      workspace_id: "workspace",
      run_id: "saved-run",
      checkpoint_id: "checkpoint",
      subject_digest: digest,
      schema_digest: digest,
      input_digest: digest,
      value: "selected",
      actor: "wright-owned",
      reason: "Declared input",
      request_id: "stable-answer",
      created_at: input.created_at,
      digest,
    };
    call.mockResolvedValueOnce(result({ ok: true, document: answer }));
    expect(
      await client.respond({
        checkpointId: "checkpoint",
        subjectDigest: digest,
        value: "selected",
        requestId: "stable-answer",
      }),
    ).toEqual(answer);
    expect(call.mock.calls[0][1]).toMatchObject({
      operation: "respond",
      checkpoint_id: "checkpoint",
      value: "selected",
      subject_digest: digest,
      request_id: "stable-answer",
    });
    expect(call.mock.calls[0][1]).not.toHaveProperty("decision");
  });
  it("submits an exact review decision without dispatching an action", async () => {
    const { client, call } = setup();
    call.mockResolvedValueOnce(
      result({
        ok: true,
        document: {
          ...snapshot(),
          interactions: [
            {
              checkpoint_id: "review:one",
              step_id: "review",
              kind: "action",
              subject_digest: digest,
              state: "responded",
              instructions: "Private fixture",
              decision: {
                decision: "changes_requested",
                actor: "server-owned",
                request_id: "stable-review",
                reason: "Missing measurement evidence",
                integration_test: false,
              },
            },
          ],
        },
      }),
    );
    await client.decide({
      checkpointId: "review:one",
      subjectDigest: digest,
      decision: "changes_requested",
      reason: "Missing measurement evidence",
      requestId: "stable-review",
    });
    expect(call).toHaveBeenCalledTimes(1);
    expect(call.mock.calls[0][0]).toBe("wright_process_ui_update");
    expect(call.mock.calls[0][1]).toMatchObject({
      operation: "decide",
      checkpoint_id: "review:one",
      subject_digest: digest,
      decision: "changes_requested",
      reason: "Missing measurement evidence",
      request_id: "stable-review",
      workspace_id: "workspace",
      expected_storage_digest: digest,
    });
    expect(call.mock.calls[0][1]).not.toHaveProperty("auto");
    expect(call.mock.calls[0][1]).not.toHaveProperty("actor");
  });
  it("keeps external dispatch unavailable", async () => {
    const { client, call } = setup();
    await expect(
      client.requestAction({
        actionId: "external",
        subjectDigest: digest,
        requestId: "action-request",
      }),
    ).rejects.toMatchObject({
      reason: { code: "CAPABILITY_UNAVAILABLE" },
      uncertain: false,
    });
    expect(call).not.toHaveBeenCalled();
  });
  it("closes a snapshot observer without cancelling or restarting its run", async () => {
    const { client, call } = setup();
    const control = new AbortController();
    const stream = client.follow({
      runId: "saved-run",
      signal: control.signal,
    });
    const follow = stream[Symbol.asyncIterator]();
    expect((await follow.next()).value?.type).toBe("connection");
    expect((await follow.next()).value?.type).toBe("snapshot");
    control.abort();
    expect((await follow.next()).done).toBe(true);
    expect(call).toHaveBeenCalledTimes(1);
    expect(call.mock.calls[0][0]).toBe("wright_process_ui_read");
  });
  it.each(["text/markdown", "image/png", "image/jpeg"])(
    "reads exact %s bytes through the read-only port",
    async (media) => {
      const { client, call } = setup();
      const bytes = "Recorded result";
      const hash = "c".repeat(64);
      call.mockResolvedValueOnce(
        result({
          ok: true,
          document: {
            bytes_base64: btoa(bytes),
            sha256: hash,
            media_type: media,
            size_bytes: bytes.length,
          },
        }),
      );
      const blob = await client.getRepresentation(
        { artifact_ref: "result.md", sha256: hash },
        { runId: "saved-run" },
      );
      expect(await blob.text()).toBe(bytes);
      expect(blob.type).toBe(media);
      expect(call.mock.calls[0][0]).toBe("wright_process_ui_read");
      expect(call.mock.calls[0][1]).toMatchObject({
        operation: "representation",
        run_id: "saved-run",
        reference: { artifact_ref: "result.md", sha256: hash },
      });
    },
  );
  it("rejects a truncated file instead of presenting its declared hash as proof", async () => {
    const { client, call } = setup();
    const hash = "c".repeat(64);
    call.mockResolvedValueOnce(
      result({
        ok: true,
        document: {
          bytes_base64: btoa("short"),
          sha256: hash,
          media_type: "text/markdown",
          size_bytes: 100,
        },
      }),
    );
    await expect(
      client.getRepresentation(
        { artifact_ref: "result.md", sha256: hash },
        { runId: "saved-run" },
      ),
    ).rejects.toMatchObject({ reason: { code: "CAPABILITY_UNAVAILABLE" } });
    expect(call).toHaveBeenCalledTimes(1);
  });
  it("does not silently substitute snapshot polling for an event cursor", async () => {
    const { client, call } = setup();
    const stream = client.follow({
      runId: "saved-run",
      cursor: "saved-cursor",
    });
    const follow = stream[Symbol.asyncIterator]();
    await expect(follow.next()).rejects.toMatchObject({
      reason: { code: "CAPABILITY_UNAVAILABLE" },
    });
    expect(call).not.toHaveBeenCalled();
  });
  it("shows a queued chat task for the exact run and never answers it", async () => {
    const { readReasoningStatus, call } = setup();
    call.mockResolvedValueOnce(
      result({
        ok: true,
        document: [
          {
            request: {
              workspace_id: "workspace",
              session_id: "session",
              run_id: "saved-run",
              schema_version: "wright.desktop-reasoning/1",
              binding: { adapter: "openai-desktop-harness" },
              kind: "response",
              request_id: "queued-task",
              created_at: input.created_at,
            },
          },
        ],
      }),
    );
    expect(
      await readReasoningStatus("saved-run", new AbortController().signal),
    ).toMatchObject({
      runId: "saved-run",
      requestId: "queued-task",
      label: "Waiting for desktop chat",
    });
    expect(call.mock.calls[0][1]).toMatchObject({
      operation: "reasoning",
      run_id: "saved-run",
    });
    expect(call.mock.calls[0][0]).toBe("wright_process_ui_read");
  });
});

it("routes explicit continuation once and preserves an uncertain owner outcome", async () => {
  const { client, call } = setup();
  call.mockResolvedValue(
    result({
      ok: false,
      http_status: 503,
      reason: {
        code: "OUTCOME_UNKNOWN",
        message: "Continuation acknowledgement lost",
        correction: "Inspect this same run before another action.",
      },
    }),
  );
  await expect(
    client.requestAction({
      actionId: "continue-checkpoint",
      subjectDigest: digest,
      requestId: "stable-continuation",
    }),
  ).rejects.toMatchObject({
    reason: { code: "OUTCOME_UNKNOWN" },
    uncertain: true,
  });
  expect(call).toHaveBeenCalledTimes(1);
  expect(call.mock.calls[0][1]).toMatchObject({
    operation: "continue",
    action_id: "continue-checkpoint",
    subject_digest: digest,
    request_id: "stable-continuation",
    workspace_id: "workspace",
    expected_storage_digest: digest,
  });
  expect(call.mock.calls[0][1]).not.toHaveProperty("decision");
  expect(call.mock.calls[0][1]).not.toHaveProperty("auto");
});
