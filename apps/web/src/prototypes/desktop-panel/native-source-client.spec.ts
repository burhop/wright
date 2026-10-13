import { describe, expect, it, vi } from "vitest";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { initialLayout } from "../workflow-recovery/model";
import { NativeSourceClient, type NativeSourceCall } from "./native-source-client";
import { WorkspaceWorkflowSourceConflictError, type WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";

const scope = { workspaceId: "workspace", sessionId: "session", path: "workflows/test.workflow.wflow" };
const doc: WorkspaceWorkflowSourceDocument = {workspace_id: "workspace", path: scope.path, storage_revision: 7, storage_digest: "a".repeat(64), definition_revision: 2, metadata_authority: "wright_host", source: "accepted", size_bytes: 8, layout: initialLayout, layout_revision: 3};
const result = (value: object): CallToolResult => ({content: [], structuredContent: {...value}});
function fixture() {
  const call = vi.fn<NativeSourceCall>().mockResolvedValue(result(doc));
  const client = new NativeSourceClient(scope, call);
  return {client,call};
}

describe("native exact source client", () => {
  it("keeps the scope and forwards the accepted source and layout CAS", async () => {
    const {client,call} = fixture();await client.read();
    const saved = {...doc,source:"edited",storage_revision:8,storage_digest:"b".repeat(64),definition_revision:3,layout_revision:4,layout:{...initialLayout,semanticRevision:3,layoutRevision:4}};
    call.mockResolvedValueOnce(result({ok:true,document:saved}));
    expect(await client.save("edited",initialLayout)).toEqual(saved);
    expect(call.mock.calls[1]).toEqual(["wright_workflow_save",{workspace_id:"workspace",session_id:"session",path:scope.path,source:"edited",layout:initialLayout,expected_storage_revision:7,expected_storage_digest:doc.storage_digest,expected_layout_revision:3,semantic_change_validated:true}]);
  });
  it("rejects another workspace before accepting its source", async () => {
    const {client,call} = fixture();call.mockResolvedValue(result({...doc,workspace_id:"other"}));
    await expect(client.read()).rejects.toThrow("exact accepted");
    await expect(client.save("edited",initialLayout)).rejects.toThrow("Open the accepted");
    expect(call).toHaveBeenCalledTimes(1);
  });
  it("reports a stale CAS without silently rebasing the retained draft", async () => {
    const {client,call} = fixture();await client.read();
    call.mockResolvedValueOnce(result({...doc,storage_revision:8,storage_digest:"b".repeat(64),source:"another edit"}));await client.read();
    call.mockResolvedValueOnce(result({ok:false,error:{code:"WORKFLOW_SOURCE_CONFLICT",outcome_known:true}}));
    await expect(client.save("my draft",initialLayout)).rejects.toBeInstanceOf(WorkspaceWorkflowSourceConflictError);
    expect(call.mock.calls[2][1].expected_storage_revision).toBe(7);
  });
  it("blocks another write after an unknown outcome and does not retry", async () => {
    const {client,call} = fixture();await client.read();call.mockRejectedValueOnce(new Error("connection lost"));
    await expect(client.save("edited",initialLayout)).rejects.toThrow("connection lost");
    await expect(client.save("edited",initialLayout)).rejects.toThrow("outcome is still unknown");
    await client.read(); // Seeing the old state does not prove the write cannot finish later.
    await expect(client.save("edited",initialLayout)).rejects.toThrow("outcome is still unknown");
    expect(call.mock.calls.filter(x=>x[0]==="wright_workflow_save")).toHaveLength(1);
  });
  it("reconciles an unknown save only by observing the exact intended source/layout", async () => {
    const {client,call} = fixture();await client.read();call.mockRejectedValueOnce(new Error("connection lost"));
    await expect(client.save("edited",initialLayout)).rejects.toThrow();
    const confirmed = {...doc,source:"edited",storage_revision:8,storage_digest:"b".repeat(64),definition_revision:3,layout_revision:4,layout:{...initialLayout,semanticRevision:3,layoutRevision:4}};
    call.mockResolvedValueOnce(result(confirmed));await client.read();
    call.mockResolvedValueOnce(result({ok:true,document:{...confirmed,source:"next"}}));await client.save("next",initialLayout);
    expect(call.mock.calls.at(-1)?.[1].expected_storage_revision).toBe(8);
  });
  it("keeps mismatched success evidence uncertain instead of claiming the edit saved", async () => {
    const {client,call} = fixture();await client.read();call.mockResolvedValueOnce(result({ok:true,document:doc}));
    await expect(client.save("edited",initialLayout)).rejects.toThrow("intended source");
    await expect(client.save("edited",initialLayout)).rejects.toThrow("outcome is still unknown");
  });
  it("preserves denial as a known failure without automatic recovery or a grant", async () => {
    const {client,call} = fixture();await client.read();call.mockResolvedValueOnce(result({ok:false,error:{code:"PERMISSION_DENIED",outcome_known:true,message:"Permission denied"}}));
    await expect(client.save("edited",initialLayout)).rejects.toThrow("Permission denied");
    expect(call.mock.calls.filter(x=>x[0]==="wright_workflow_save")).toHaveLength(1);
  });
});
