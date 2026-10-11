import { expect, it, vi, afterEach } from "vitest";
import { hostAdapter } from "./host-adapter";
import { copyWorkspaceWorkflowSource } from "./workflow-source-copy";
afterEach(() => vi.restoreAllMocks());
const digest = "a".repeat(64);
const document = {
  workspace_id: "ws",
  path: "workflows/copy.workflow.wflow",
  storage_digest: digest,
  source: "exact saved instructions",
  metadata_authority: "wright_host",
  storage_revision: 1,
  definition_revision: 1,
};
it("posts only the selected saved subject and destination", async () => {
  const fetch = vi
    .spyOn(hostAdapter, "fetch")
    .mockResolvedValue(new Response(JSON.stringify(document)));
  await expect(
    copyWorkspaceWorkflowSource(
      "session",
      "workflows/original.workflow.wflow",
      document.path,
      digest,
    ),
  ).resolves.toEqual(document);
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({
    session_id: "session",
    source_path: "workflows/original.workflow.wflow",
    destination_path: document.path,
    expected_storage_digest: digest,
  });
});
it("does not retry an invalid subject or a storage conflict", async () => {
  const fetch = vi
    .spyOn(hostAdapter, "fetch")
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ ...document, storage_digest: "b".repeat(64) }),
      ),
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ detail: { message: "Saved source changed" } }),
        { status: 409 },
      ),
    );
  await expect(
    copyWorkspaceWorkflowSource("session", "original", document.path, digest),
  ).rejects.toThrow("invalid saved workflow copy");
  await expect(
    copyWorkspaceWorkflowSource("session", "original", document.path, digest),
  ).rejects.toThrow("Saved source changed");
  expect(fetch).toHaveBeenCalledTimes(2);
});
