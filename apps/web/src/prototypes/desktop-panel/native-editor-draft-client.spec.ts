import { expect, it, vi } from "vitest";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { act, renderHook } from "@testing-library/react";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import {
  NativeEditorDraftClient,
  type NativeEditorDraftCall,
  type EditorDraftRecord,
} from "./native-editor-draft-client";
import { useNativeEditorDrafts } from "./use-native-editor-drafts";
const accepted: WorkspaceWorkflowSourceDocument = {
  workspace_id: "alpha",
  path: "workflows/example.workflow.wflow",
  source: "accepted",
  storage_revision: 1,
  storage_digest: "a".repeat(64),
  definition_revision: 1,
  metadata_authority: "wright_host",
  size_bytes: 8,
};
const snapshot = {
  source: "invalid raw",
  applied_source: "diagram",
  layout: null,
  view: "code" as const,
};
const result = (value: Record<string, unknown>): CallToolResult => ({
  content: [],
  structuredContent: value,
});
function fixture() {
  let saved: EditorDraftRecord | undefined;
  let loseAck = false;
  const writes: Record<string, unknown>[] = [];
  const scope = {
    workspace_id: "alpha",
    session_id: "chat-alpha",
    path: accepted.path,
  };
  const call = vi.fn<NativeEditorDraftCall>(async (name, args) => {
    const request = args.request as Record<string, unknown>;
    if (name === "wright_editor_drafts_read") {
      if (request.draft_id) return result({ ...scope, draft: saved });
      return result({
        ...scope,
        drafts: saved
          ? [
              Object.fromEntries(
                Object.entries(saved).filter(
                  ([key]) =>
                    !["source", "applied_source", "layout"].includes(key),
                ),
              ),
            ]
          : [],
      });
    }
    writes.push(request);
    saved = {
      ...(request.snapshot as object),
      schema_version: "wright.workflow-editor-draft/1",
      path: accepted.path,
      draft_id: request.draft_id,
      request_id: request.request_id,
      draft_revision: writes.length,
      draft_digest: String(writes.length).repeat(64),
      updated_at: 123,
      base_matches_current: true,
      matches_accepted: false,
      accepted_checkpoint: false,
    } as EditorDraftRecord;
    if (loseAck) {
      loseAck = false;
      throw new Error("Lost acknowledgement");
    }
    return result({ ok: true, ...scope, draft: saved });
  });
  const client = new NativeEditorDraftClient(
    { workspaceId: "alpha", sessionId: "chat-alpha", path: accepted.path },
    call,
  );
  return {
    client,
    call,
    writes,
    lose: () => {
      loseAck = true;
    },
    saved: () => saved!,
  };
}
it("does not allocate an untouched draft; exact saves use its stream CAS", async () => {
  const f = fixture();
  await f.client.save(snapshot, accepted, false);
  expect(f.call).not.toHaveBeenCalled();
  await f.client.save(snapshot, accepted, true);
  await f.client.save({ ...snapshot, source: "next" }, accepted, true);
  expect(f.writes[1].draft_id).toBe(f.writes[0].draft_id);
  expect(f.writes[1].expected_draft_digest).toBe("1".repeat(64));
  expect(f.writes[1].request_id).not.toBe(f.writes[0].request_id);
});
it("a lost acknowledgement blocks another write until an exact explicit read, without replay", async () => {
  const f = fixture();
  f.lose();
  await expect(f.client.save(snapshot, accepted, true)).rejects.toThrow(
    "Lost acknowledgement",
  );
  await expect(f.client.save(snapshot, accepted, true)).rejects.toThrow(
    "no write was repeated",
  );
  expect(f.writes).toHaveLength(1);
  expect(await f.client.inspectPending()).toBe(true);
  expect(f.client.requiresRead).toBe(false);
  expect(f.writes).toHaveLength(1);
});
it("foreign or mismatched success stays uncertain and cannot accept a workflow", async () => {
  const f = fixture();
  f.call.mockResolvedValueOnce(
    result({
      ok: true,
      workspace_id: "foreign",
      session_id: "chat-alpha",
      path: accepted.path,
    }),
  );
  await expect(f.client.save(snapshot, accepted, true)).rejects.toThrow(
    "different workspace",
  );
  expect(f.client.requiresRead).toBe(true);
  expect(f.call).toHaveBeenCalledOnce();
});
it("known denial stops autosaves and requires an explicit separate stream", async () => {
  const f = fixture();
  f.call.mockResolvedValueOnce(
    result({ ok: false, error: { outcome_known: true } }),
  );
  await expect(f.client.save(snapshot, accepted, true)).rejects.toThrow(
    "not saved",
  );
  await expect(f.client.save(snapshot, accepted, true)).rejects.toThrow(
    "inspection",
  );
  f.client.startSeparateDraft();
  await f.client.save(snapshot, accepted, true);
  expect(f.writes[0].expected_draft_digest).toBeNull();
});
it("recovery requires an exact accepted base; clean checkpoints use the actual accepted source", async () => {
  const f = fixture();
  await f.client.save(snapshot, accepted, true);
  const record = await f.client.read(f.saved().draft_id);
  expect(() =>
    f.client.resume({ ...record, base_matches_current: false }, accepted),
  ).toThrow("older workflow");
  expect(() =>
    f.client.resume(record, { ...accepted, storage_digest: "b".repeat(64) }),
  ).toThrow("older workflow");
  f.client.resume(record, accepted);
  const current = {
    ...accepted,
    source: "new accepted",
    storage_revision: 2,
    storage_digest: "b".repeat(64),
  };
  await f.client.save(snapshot, current, false);
  expect(f.writes.at(-1)?.snapshot).toMatchObject({
    source: current.source,
    applied_source: current.source,
    base_storage_revision: 2,
    base_storage_digest: current.storage_digest,
  });
});
it("coalesces edits and reads an uncertain autosave without replaying its acknowledged content", async () => {
  vi.useFakeTimers();
  const f = fixture();
  const hook = renderHook(() => useNativeEditorDrafts(f.client, accepted));
  try {
    await act(async () => {});
    f.lose();
    act(() => hook.result.current.change(snapshot, true));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(f.writes).toHaveLength(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(f.writes).toHaveLength(1);
    await act(async () => {
      await hook.result.current.refresh();
    });
    expect(f.writes).toHaveLength(1);
    act(() => {
      hook.result.current.change({ ...snapshot, source: "intermediate" }, true);
      hook.result.current.change({ ...snapshot, source: "latest" }, true);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(f.writes).toHaveLength(2);
    expect(f.writes[1].snapshot).toMatchObject({ source: "latest" });
    const newer = {
      ...accepted,
      storage_digest: "b".repeat(64),
      storage_revision: 2,
    };
    act(() => hook.result.current.accepted(newer));
    act(() =>
      hook.result.current.change(
        { ...snapshot, source: "post-save edit" },
        true,
      ),
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(600);
    });
    expect(hook.result.current.rows[0]?.base_storage_digest).toBe(
      newer.storage_digest,
    );
  } finally {
    hook.unmount();
    vi.useRealTimers();
  }
});
