import { beforeEach, describe, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("./host-adapter", () => ({
  hostAdapter: { mode: "browser", fetch: mocks.fetch },
}));
import { workspaceService } from "./workspace-service";
import { normalizeWorkflowInstructions } from "../prototypes/workflow-recovery/workflow-instructions";
const instructions = normalizeWorkflowInstructions({
  profile_id: "default",
  profile_version: "1",
  assets: [
    {
      id: "task",
      role: "workflow-task",
      version: "1",
      body: "Explicit instructions",
      body_digest: "a".repeat(64),
      origin: "packaged",
    },
  ],
  bindings: [{ role: "workflow-task", asset_ids: ["task"] }],
});
const document = {
  instructions,
  digest: "b".repeat(64),
  origin: "packaged",
  revision: "packaged-r1",
};
beforeEach(() => mocks.fetch.mockReset());
describe("instruction defaults server storage", () => {
  it("requests a protocol proposal for the exact draft without saving it", async () => {
    const upgraded = normalizeWorkflowInstructions({
      ...instructions,
      action_intent_contract: "wright.workflow-action-intent/1",
    });
    const proposal = {
      scope: "workflow",
      current_revision: null,
      current_digest: "a".repeat(64),
      proposed_digest: "b".repeat(64),
      instructions: upgraded,
      changes: [
        {
          path: "action_intent_contract",
          before: null,
          after: "wright.workflow-action-intent/1",
        },
      ],
      available: true,
    };
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify(proposal)));
    expect(
      await workspaceService.proposeWorkflowActionIntentUpgrade(instructions),
    ).toEqual(proposal);
    expect(mocks.fetch).toHaveBeenCalledOnce();
    expect(mocks.fetch.mock.calls[0]![0]).toMatch(/\/action-intent-upgrade$/);
    expect(JSON.parse(mocks.fetch.mock.calls[0]![1].body)).toEqual({
      instructions,
    });
  });
  it("rejects a proposal for the wrong scope without saving or retrying", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          scope: "defaults",
          current_revision: "r3",
          current_digest: "a".repeat(64),
          proposed_digest: "b".repeat(64),
          instructions,
          changes: [],
          available: false,
        }),
      ),
    );
    await expect(
      workspaceService.proposeWorkflowActionIntentUpgrade(instructions),
    ).rejects.toThrow(/invalid instruction upgrade proposal/);
    expect(mocks.fetch).toHaveBeenCalledOnce();
  });
  it("loads global and scoped workspace defaults without mutation", async () => {
    mocks.fetch.mockImplementation(
      async () => new Response(JSON.stringify(document)),
    );
    expect(await workspaceService.getWorkflowInstructionDefaults()).toEqual(
      document,
    );
    expect(mocks.fetch.mock.calls[0]![0]).toMatch(
      /\/api\/settings\/workflow-instructions$/,
    );
    expect(mocks.fetch.mock.calls[0]![1]).toEqual({ cache: "no-store" });
    await workspaceService.getWorkflowInstructionDefaults("workspace session");
    expect(mocks.fetch.mock.calls[1]![0]).toMatch(
      /instruction-defaults\?session_id=workspace\+session$/,
    );
  });
  it("writes normalized defaults with the expected revision", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({ ...document, origin: "global", revision: "r2" }),
      ),
    );
    await workspaceService.saveWorkflowInstructionDefaults(
      instructions,
      "packaged-r1",
    );
    const request = mocks.fetch.mock.calls[0]![1];
    expect(request.method).toBe("PUT");
    expect(JSON.parse(request.body)).toEqual({
      instructions,
      expected_revision: "packaged-r1",
    });
  });
  it("reports a conflict without retrying or replacing the edited collection", async () => {
    mocks.fetch.mockResolvedValue(new Response("{}", { status: 409 }));
    await expect(
      workspaceService.saveWorkflowInstructionDefaults(instructions, "stale"),
    ).rejects.toThrow(/Reload.*compare/i);
    expect(mocks.fetch).toHaveBeenCalledOnce();
  });
  it.each([
    { ...document, digest: "no" },
    { ...document, revision: "" },
    { ...document, origin: "invented" },
    {
      ...document,
      instructions: {
        ...instructions,
        bindings: [{ role: "workflow-task", asset_ids: ["missing"] }],
      },
    },
  ])("rejects malformed server collections", async (value) => {
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify(value)));
    await expect(
      workspaceService.getWorkflowInstructionDefaults(),
    ).rejects.toThrow();
  });
});
