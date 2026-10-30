import { afterEach, expect, it, vi } from "vitest";
import { hostAdapter } from "./host-adapter";
import {
  handleProfileRoles,
  handleToolRoles,
  printedHandleSetup,
  type HandleSetupProposal,
  type HandleSetupSelection,
} from "./printed-handle-setup";
import type { WorkspaceWorkflowSourceDocument } from "./workspace-service";

const document: WorkspaceWorkflowSourceDocument = {
  workspace_id: "workspace",
  path: "workflows/handle.workflow.wflow",
  source: "original",
  storage_revision: 1,
  definition_revision: 1,
  storage_digest: "a".repeat(64),
  metadata_authority: "wright_host",
  size_bytes: 8,
};
const proposal: HandleSetupProposal = {
  workspace_id: "workspace",
  workflow_id: "handle",
  path: document.path,
  expected_storage_revision: 1,
  expected_storage_digest: document.storage_digest,
  recipe: { id: "printed-handle-orca", version: "2", digest: "b".repeat(64) },
  proposal_id: "proposal",
  proposal_digest: "c".repeat(64),
  source: "prepared",
  source_digest: "d".repeat(64),
  dependencies: [],
  summary: {},
};
const options = {
  workspace_id: document.workspace_id,
  path: document.path,
  workflow_id: "handle",
  recipe: proposal.recipe,
  workspace_mount: "/workspace",
  tools: { construction: [], geometry: [], slicer: [], inspection: [] },
  profiles: {
    mode: "workspace_files",
    roles: ["machine", "process_original", "process_orca", "filament"],
  },
  requirements: ["Selected providers must share this workspace path."],
};
const selection: HandleSetupSelection = {
  workspace_mount: "/workspace",
  selected_orientation: "pads_down",
  tools: Object.fromEntries(
    handleToolRoles.map((role) => [
      role,
      {
        server_id: `${role}-server`,
        name: `${role}-server__${role === "construction" ? "execute_code" : "tool"}`,
        schema_digest: "c".repeat(64),
      },
    ]),
  ) as HandleSetupSelection["tools"],
  profiles: Object.fromEntries(
    handleProfileRoles.map((role) => [role, { path: `profiles/${role}.json` }]),
  ) as HandleSetupSelection["profiles"],
};
afterEach(() => vi.restoreAllMocks());

it("accepts only a proposal identity with the original source CAS preconditions", async () => {
  const accepted = {
    ...document,
    source: proposal.source,
    storage_digest: proposal.source_digest,
    storage_revision: 2,
    definition_revision: 2,
  };
  const fetch = vi
    .spyOn(hostAdapter, "fetch")
    .mockResolvedValue(new Response(JSON.stringify(accepted)));
  await expect(
    printedHandleSetup.accept("session", document, proposal),
  ).resolves.toEqual(accepted);
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({
    session_id: "session",
    path: document.path,
    expected_storage_revision: 1,
    expected_storage_digest: document.storage_digest,
    proposal_id: "proposal",
    proposal_digest: proposal.proposal_digest,
  });
});

it.each(["workspace_id", "path", "storage_digest", "source"])(
  "rejects an accepted response with a different %s",
  async (field) => {
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          ...document,
          source: proposal.source,
          storage_digest: proposal.source_digest,
          storage_revision: 2,
          definition_revision: 2,
          [field]: "different",
        }),
      ),
    );
    await expect(
      printedHandleSetup.accept("session", document, proposal),
    ).rejects.toThrow("acceptance response could not be matched");
  },
);

it("retains a normalized CAS refusal without retry or sending a replacement source", async () => {
  const fetch = vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        details: {
          message: "Saved source changed",
          correction: "Reopen before preparing another proposal.",
        },
      }),
      { status: 409 },
    ),
  );
  await expect(
    printedHandleSetup.accept("session", document, proposal),
  ).rejects.toThrow("Saved source changed Reopen");
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).not.toHaveProperty(
    "source",
  );
});

it("retains scoped options even when compatible tools are unavailable", async () => {
  vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
    new Response(JSON.stringify(options)),
  );
  await expect(
    printedHandleSetup.options("session", document),
  ).resolves.toEqual(options);
});

it("submits all four exact tool bindings without changing the source CAS contract", async () => {
  const fetch = vi
    .spyOn(hostAdapter, "fetch")
    .mockResolvedValue(new Response(JSON.stringify(proposal)));
  await expect(
    printedHandleSetup.propose("session", document, selection),
  ).resolves.toEqual(proposal);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(String(fetch.mock.calls[0][0])).toContain("/setup/proposals");
  expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({
    session_id: "session",
    path: document.path,
    expected_storage_revision: 1,
    expected_storage_digest: document.storage_digest,
    ...selection,
  });
});

it.each(["options", "proposal"])(
  "rejects an unsupported recipe version in %s without retry",
  async (operation) => {
    const value = operation === "options" ? options : proposal;
    const fetch = vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          ...value,
          recipe: { ...proposal.recipe, version: "1" },
        }),
      ),
    );
    await expect(
      operation === "options"
        ? printedHandleSetup.options("session", document)
        : printedHandleSetup.propose("session", document, selection),
    ).rejects.toThrow("requires printed-handle-orca version 2");
    expect(fetch).toHaveBeenCalledTimes(1);
  },
);

it("rejects a missing construction role instead of treating it as an optional provider", async () => {
  const legacyTools = {
    geometry: options.tools.geometry,
    slicer: options.tools.slicer,
    inspection: options.tools.inspection,
  };
  vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ ...options, tools: legacyTools })),
  );
  await expect(printedHandleSetup.options("session", document)).rejects.toThrow(
    "missing a required tool role: construction",
  );
});

it("rejects malformed construction schema identity before presenting choices", async () => {
  vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        ...options,
        tools: {
          ...options.tools,
          construction: [
            {
              ...selection.tools.construction,
              tool_name: "execute_code",
              schema_digest: "not-an-exact-schema-digest",
            },
          ],
        },
      }),
    ),
  );
  await expect(printedHandleSetup.options("session", document)).rejects.toThrow(
    "invalid or different workspace",
  );
});

it.each(["workspace_id", "path"])(
  "rejects setup options for another %s before presenting selectable capabilities",
  async (field) => {
    vi.spyOn(hostAdapter, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          ...options,
          [field]: "other",
        }),
      ),
    );
    await expect(
      printedHandleSetup.options("session", document),
    ).rejects.toThrow("invalid or different workspace");
  },
);
