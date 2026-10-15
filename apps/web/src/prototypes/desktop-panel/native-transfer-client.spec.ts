import { expect, it, vi } from "vitest";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import {
  createNativeTransferClient,
  type NativeTransferCall,
} from "./native-transfer-client";

const bundle = {
  schema_version: "wright.workflow-bundle/1",
  source: "accepted",
  source_digest: "a".repeat(64),
};
const digest = "b".repeat(64);
const report = {
  bundle_digest: digest,
  can_import: true,
  can_run: false,
  diagnostics: [],
  external_dependencies: [],
  requirements: [],
};
const imported = {
  source: {
    workspace_id: "workspace",
    path: "workflows/import.workflow.wflow",
    source: bundle.source,
    storage_digest: bundle.source_digest,
  },
  imported_paths: [],
  inspection: report,
};
const response = (value: object): CallToolResult => ({
  content: [],
  structuredContent: { ...value },
});
const args = ["session", bundle, imported.source.path, digest] as const;
function setup() {
  const call = vi.fn<NativeTransferCall>();
  return {
    call,
    client: createNativeTransferClient("workspace", "session", call),
  };
}

it("lists reference files through a source-bound port and rejects foreign workspace lists", async () => {
  const { call, client } = setup();
  const files = [{ path: "inputs/brief.txt", name: "brief.txt" }];
  call
    .mockResolvedValueOnce(response({ workspace_id: "workspace", files }))
    .mockResolvedValueOnce(response({ workspace_id: "other", files }));
  expect(
    await client.listFiles("workflows/design.workflow.wflow", digest),
  ).toEqual(files);
  expect(call.mock.calls[0]).toEqual([
    "wright_workflow_transfer_assets",
    {
      request: {
        workspace_id: "workspace",
        session_id: "session",
        path: "workflows/design.workflow.wflow",
        expected_storage_digest: digest,
        kind: "references",
      },
    },
  ]);
  await expect(
    client.listFiles("workflows/design.workflow.wflow", digest),
  ).rejects.toThrow("invalid reference file list");
});

it("does not turn failed interface discovery into an empty success", async () => {
  const { call, client } = setup();
  call
    .mockResolvedValueOnce(response({ interfaces: [] }))
    .mockResolvedValueOnce({ isError: true, content: [] });
  expect(
    await client.listInterfaces("workflows/design.workflow.wflow", digest),
  ).toEqual([]);
  await expect(
    client.listInterfaces("workflows/design.workflow.wflow", digest),
  ).rejects.toThrow("did not confirm");
});

it("uses only the exact native ports and preserves inspected definition identity", async () => {
  const { call, client } = setup();
  call
    .mockResolvedValueOnce(
      response({ ok: true, bundle, bundle_digest: digest }),
    )
    .mockResolvedValueOnce(response(report))
    .mockResolvedValueOnce(response({ ok: true, document: imported }));
  expect(
    await client.export(
      "session",
      "workflows/original.workflow.wflow",
      bundle.source_digest,
      "source",
      [],
      [],
    ),
  ).toEqual({ bundle, bundle_digest: digest });
  expect(
    await client.inspect(
      ...(args.slice(0, 3) as [string, typeof bundle, string]),
    ),
  ).toEqual(report);
  expect(await client.import(...args)).toEqual(imported);
  expect(call.mock.calls.map(([name]) => name)).toEqual([
    "wright_workflow_export",
    "wright_workflow_import_inspect",
    "wright_workflow_import",
  ]);
  expect(call.mock.calls[2]![1]).toEqual({
    request: {
      workspace_id: "workspace",
      session_id: "session",
      bundle,
      destination_path: args[2],
      expected_bundle_digest: digest,
    },
  });
});

it("rejects cross-session input before calling any tool", async () => {
  const { call, client } = setup();
  await expect(client.import("other", bundle, args[2], digest)).rejects.toThrow(
    "another session",
  );
  expect(call).not.toHaveBeenCalled();
});

it.each(["lost", "malformed", "other-source", "other-workspace", "ready"])(
  "keeps %s import uncertain and blocks duplicate submission",
  async (fault) => {
    const { call, client } = setup();
    if (fault === "lost")
      call.mockRejectedValueOnce(new Error("connection lost"));
    else {
      const document = structuredClone(imported);
      if (fault === "other-source") document.source.source = "different";
      if (fault === "other-workspace") document.source.workspace_id = "other";
      if (fault === "ready") document.inspection.can_run = true;
      call.mockResolvedValueOnce(
        response({ ok: true, document: fault === "malformed" ? {} : document }),
      );
    }
    await expect(client.import(...args)).rejects.toThrow();
    await expect(client.import(...args)).rejects.toThrow(
      "no import was repeated",
    );
    expect(call).toHaveBeenCalledTimes(1);
  },
);

it("allows an explicit corrected submission after a known pre-dispatch rejection", async () => {
  const { call, client } = setup();
  call
    .mockResolvedValueOnce(
      response({
        ok: false,
        error: {
          outcome_known: true,
          message: "Bundle changed before submission",
        },
      }),
    )
    .mockResolvedValueOnce(response({ ok: true, document: imported }));
  await expect(client.import(...args)).rejects.toThrow("before submission");
  expect(await client.import(...args)).toEqual(imported);
  expect(call).toHaveBeenCalledTimes(2);
});

it("keeps an unknown owner response blocked while allowing read-only inspection", async () => {
  const { call, client } = setup();
  call
    .mockResolvedValueOnce(
      response({
        ok: false,
        error: { outcome_known: false, message: "Inspect destination" },
      }),
    )
    .mockResolvedValueOnce(response({ ...report, can_import: false }));
  await expect(client.import(...args)).rejects.toThrow("Inspect destination");
  expect((await client.inspect("session", bundle, args[2])).can_import).toBe(
    false,
  );
  await expect(client.import(...args)).rejects.toThrow(
    "no import was repeated",
  );
  expect(call).toHaveBeenCalledTimes(2);
});
