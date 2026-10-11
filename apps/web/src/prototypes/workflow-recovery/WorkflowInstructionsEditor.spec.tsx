import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  WorkflowInstructionsEditor,
  WorkflowInstructionDefaultsCard,
  workflowInstructionPreview,
  updateInstructionDefaultsPreservingLayers,
} from "./WorkflowInstructionsEditor";
import {
  normalizeWorkflowInstructions,
  type WorkflowInstructionSet,
} from "./workflow-instructions";
import { workspaceService } from "../../services/workspace-service";

const collection = (body = "Preserve supplied dimensions.") =>
  normalizeWorkflowInstructions({
    profile_id: "design",
    profile_version: "1",
    assets: [
      {
        id: "task",
        role: "workflow-task",
        version: "1",
        body,
        body_digest: "a".repeat(64),
        origin: "packaged",
      },
    ],
    bindings: [{ role: "workflow-task", asset_ids: ["task"] }],
  });
const document = (revision = "r1", body?: string) => ({
  instructions: collection(body),
  digest: "b".repeat(64),
  origin: "global" as const,
  revision,
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("visible portable workflow instructions", () => {
  it("preserves and shows the saved action contract while editing guidance", async () => {
    const instructions = normalizeWorkflowInstructions({
      ...collection(),
      action_intent_contract: "wright.workflow-action-intent/1",
    });
    const onApply = vi.fn((_value: WorkflowInstructionSet) => true);
    render(
      <WorkflowInstructionsEditor
        instructions={instructions}
        onApply={onApply}
      />,
    );
    expect(
      screen.getByTestId("workflow-instructions-action-intent"),
    ).toHaveTextContent("wright.workflow-action-intent/1");
    fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
      target: { value: "Keep exact dimensions." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply workflow instructions" }),
    );
    await waitFor(() => expect(onApply).toHaveBeenCalledOnce());
    expect(onApply.mock.calls[0]![0].action_intent_contract).toBe(
      "wright.workflow-action-intent/1",
    );
  });

  it("shows a contract migration proposal without changing legacy instructions until reviewed apply", async () => {
    const instructions = collection();
    const upgraded = normalizeWorkflowInstructions({
      ...collection(),
      profile_version: "1.1.0",
      action_intent_contract: "wright.workflow-action-intent/1",
    });
    const onApply = vi.fn(
      (_value: WorkflowInstructionSet, _revision?: string) => true,
    );
    render(
      <WorkflowInstructionsEditor
        instructions={instructions}
        onApply={onApply}
        onLoadDefaults={async () => ({
          ...document("r2"),
          instructions: upgraded,
        })}
      />,
    );
    expect(
      screen.getByTestId("workflow-instructions-action-intent"),
    ).toHaveTextContent("Not declared");
    expect(instructions).not.toHaveProperty("action_intent_contract");
    fireEvent.click(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    );
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-instructions-action-intent-diff"),
      ).toHaveTextContent(
        "Not declared in this saved profile → wright.workflow-action-intent/1",
      ),
    );
    expect(onApply).not.toHaveBeenCalled();
    expect(
      screen.getByTestId("workflow-instructions-action-intent"),
    ).toHaveTextContent("Not declared");
    fireEvent.click(
      screen.getByRole("button", { name: "Apply reviewed instruction update" }),
    );
    await waitFor(() => expect(onApply).toHaveBeenCalledOnce());
    expect(onApply.mock.calls[0]![0].action_intent_contract).toBe(
      "wright.workflow-action-intent/1",
    );
    expect(onApply.mock.calls[0]![1]).toBe("r2");
  });

  it("does not fetch or apply installation defaults on open; legacy export explains its dependency", async () => {
    const onApply = vi.fn();
    const onLoadDefaults = vi.fn(async () => document());
    const onExport = vi.fn();
    render(
      <WorkflowInstructionsEditor
        onApply={onApply}
        onLoadDefaults={onLoadDefaults}
        onExport={onExport}
        exportReady
      />,
    );
    expect(onLoadDefaults).not.toHaveBeenCalled();
    expect(onApply).not.toHaveBeenCalled();
    expect(screen.getByText(/legacy workflow has no embedded/)).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Export saved workflow source" }),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", { name: "Make instructions explicit…" }),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Proposed instructions")).toBeTruthy(),
    );
    expect(onApply).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply reviewed instruction update" }),
    );
    await waitFor(() =>
      expect(onApply).toHaveBeenCalledWith(collection(), "r1"),
    );
  });

  it("saves explicit assumptions, protected requirements and scoped author guidance", async () => {
    const onApply = vi.fn((_value: WorkflowInstructionSet) => true);
    render(
      <WorkflowInstructionsEditor
        instructions={collection()}
        onApply={onApply}
      />,
    );
    fireEvent.change(screen.getByLabelText("Unspecified design choices"), {
      target: { value: "document_reasonable" },
    });
    fireEvent.change(screen.getByLabelText(/Protected requirements/), {
      target: { value: "thickness\nwidth\n" },
    });
    fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
      target: { value: "Document finish assumptions." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply workflow instructions" }),
    );
    await waitFor(() => expect(onApply).toHaveBeenCalledOnce());
    const saved = onApply.mock.calls[0]![0];
    expect(saved.policy).toEqual({
      assumption_policy: "document_reasonable",
      protected_requirements: ["thickness", "width"],
    });
    expect(saved.layers[0]).toMatchObject({
      origin: "workflow-author",
      mode: "append",
      text: "Document finish assumptions.",
      roles: ["workflow-task", "image-generation", "mcp-task"],
    });
    expect(screen.getByRole("status")).toHaveTextContent("Save the workflow");
  });

  it("rejects empty replace guidance without applying and can compare without crashing", async () => {
    const onApply = vi.fn();
    render(
      <WorkflowInstructionsEditor
        instructions={collection()}
        onApply={onApply}
        onLoadDefaults={async () => document()}
      />,
    );
    fireEvent.change(screen.getByLabelText("Guidance mode"), {
      target: { value: "replace" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply workflow instructions" }),
    );
    await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
    expect(onApply).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    );
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Resolve invalid instruction edits",
      ),
    );
  });

  it("rehashes edited body text and records its author origin before applying", async () => {
    const digest = vi.fn(async () => new Uint8Array(32).fill(15).buffer);
    vi.stubGlobal("crypto", { subtle: { digest } });
    const onApply = vi.fn((_value: WorkflowInstructionSet) => true);
    render(
      <WorkflowInstructionsEditor
        instructions={collection()}
        onApply={onApply}
      />,
    );
    fireEvent.change(screen.getByLabelText("task instruction body"), {
      target: { value: "Use explicit millimeters." },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Apply workflow instructions" }),
    );
    await waitFor(() => expect(onApply).toHaveBeenCalledOnce());
    expect(digest).toHaveBeenCalledWith(
      "SHA-256",
      new TextEncoder().encode("Use explicit millimeters."),
    );
    expect(onApply.mock.calls[0]![0].assets[0]).toMatchObject({
      body: "Use explicit millimeters.",
      body_digest: "0f".repeat(32),
      origin: "workflow-author",
    });
  });

  it("keeps read-only inspection available while disabling changes", () => {
    render(
      <WorkflowInstructionsEditor
        instructions={collection()}
        onApply={vi.fn()}
        onLoadDefaults={async () => document()}
        readOnly
      />,
    );
    expect(screen.getByLabelText("Unspecified design choices")).toBeDisabled();
    expect(
      screen.getByLabelText("Additional workflow guidance"),
    ).toBeDisabled();
    expect(screen.getByLabelText("task instruction body")).toBeDisabled();
    expect(screen.getByLabelText("Instruction role")).not.toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    ).toBeDisabled();
  });

  it("replaces default layers only, retaining author scopes and policy", () => {
    const current = normalizeWorkflowInstructions({
      ...collection(),
      policy: { assumption_policy: "document_reasonable" },
      layers: [
        { origin: "workspace-context", text: "Old workspace" },
        {
          origin: "workflow-author",
          text: "Author task",
          roles: ["workflow-task"],
        },
        {
          origin: "ui-author",
          text: "Interface author",
          roles: ["process-ui-author"],
        },
      ],
    });
    const defaults = normalizeWorkflowInstructions({
      ...collection("New task instructions"),
      layers: [{ origin: "workspace-context", text: "New workspace" }],
    });
    const updated = updateInstructionDefaultsPreservingLayers(
      current,
      defaults,
    );
    expect(updated.policy.assumption_policy).toBe("document_reasonable");
    expect(updated.layers.map((layer) => layer.text)).toEqual([
      "New workspace",
      "Author task",
      "Interface author",
    ]);
    expect(workflowInstructionPreview(updated, "workflow-task")?.text).toBe(
      "New task instructions\n\nNew workspace\n\nAuthor task",
    );
  });

  it("shows the proposed collection and preserves author edits until reviewed apply", async () => {
    const onApply = vi.fn((_value: WorkflowInstructionSet) => true);
    render(
      <WorkflowInstructionsEditor
        instructions={collection()}
        onApply={onApply}
        onLoadDefaults={async () => document("r2", "Latest defaults")}
      />,
    );
    fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
      target: { value: "My workflow guidance" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    );
    await waitFor(() =>
      expect(
        (screen.getByLabelText("Proposed instructions") as HTMLTextAreaElement)
          .value,
      ).toContain("Latest defaults"),
    );
    expect(
      (screen.getByLabelText("Proposed instructions") as HTMLTextAreaElement)
        .value,
    ).toContain("My workflow guidance");
    expect(onApply).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Cancel instruction update" }),
    );
    expect(screen.queryByLabelText("Proposed instructions")).toBeNull();
    expect(screen.getByLabelText("Additional workflow guidance")).toHaveValue(
      "My workflow guidance",
    );
    expect(onApply).not.toHaveBeenCalled();
  });
});

describe("server-backed instruction defaults", () => {
  it("reviews a protocol upgrade of the edited global draft and saves only on explicit apply with its original CAS revision", async () => {
    vi.spyOn(
      workspaceService,
      "getWorkflowInstructionDefaults",
    ).mockResolvedValue(document("r4"));
    const propose = vi
      .spyOn(workspaceService, "proposeWorkflowActionIntentUpgrade")
      .mockImplementation(async (current) => ({
        scope: "workflow",
        current_revision: null,
        current_digest: "a".repeat(64),
        proposed_digest: "b".repeat(64),
        instructions: normalizeWorkflowInstructions({
          ...current!,
          action_intent_contract: "wright.workflow-action-intent/1",
        }),
        changes: [
          {
            path: "action_intent_contract",
            before: null,
            after: "wright.workflow-action-intent/1",
          },
        ],
        available: true,
      }));
    const save = vi
      .spyOn(workspaceService, "saveWorkflowInstructionDefaults")
      .mockImplementation(async (current) => ({
        ...document("r5"),
        instructions: current,
      }));
    render(<WorkflowInstructionDefaultsCard />);
    fireEvent.click(
      screen.getByRole("button", { name: "Load instruction defaults" }),
    );
    await screen.findByLabelText("Additional workflow guidance");
    fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
      target: { value: "Keep my global customization." },
    });
    fireEvent.click(
      screen.getByRole("button", {
        name: "Review instruction compatibility upgrade…",
      }),
    );
    await screen.findByTestId("workflow-instructions-action-intent-diff");
    expect(propose.mock.calls[0]![0]?.layers[0].text).toBe(
      "Keep my global customization.",
    );
    expect(save).not.toHaveBeenCalled();
    expect(
      (screen.getByLabelText("Proposed instructions") as HTMLTextAreaElement)
        .value,
    ).toContain("Keep my global customization.");
    fireEvent.click(
      screen.getByRole("button", { name: "Apply reviewed instruction update" }),
    );
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![0].action_intent_contract).toBe(
      "wright.workflow-action-intent/1",
    );
    expect(save.mock.calls[0]![1]).toBe("r4");
  });
  it("loads explicitly and saves with its original revision even after cancelling a refresh", async () => {
    const load = vi
      .spyOn(workspaceService, "getWorkflowInstructionDefaults")
      .mockResolvedValueOnce(document("r1"))
      .mockResolvedValueOnce(document("r2", "Other browser edit"));
    const save = vi
      .spyOn(workspaceService, "saveWorkflowInstructionDefaults")
      .mockRejectedValue(
        new Error("Defaults changed. Reload and compare before retrying."),
      );
    render(<WorkflowInstructionDefaultsCard />);
    expect(load).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Load instruction defaults" }),
    );
    await screen.findByLabelText("Additional workflow guidance");
    fireEvent.change(screen.getByLabelText("Additional workflow guidance"), {
      target: { value: "Local draft" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    );
    await screen.findByLabelText("Proposed instructions");
    fireEvent.click(
      screen.getByRole("button", { name: "Cancel instruction update" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Save instruction defaults" }),
    );
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![1]).toBe("r1");
    expect(screen.getByRole("alert")).toHaveTextContent("Defaults changed");
    expect(screen.getByLabelText("Additional workflow guidance")).toHaveValue(
      "Local draft",
    );
  });

  it("uses the newly reviewed revision only when applying the displayed update", async () => {
    vi.spyOn(workspaceService, "getWorkflowInstructionDefaults")
      .mockResolvedValueOnce(document("r1"))
      .mockResolvedValueOnce(document("r2", "Latest defaults"));
    const save = vi
      .spyOn(workspaceService, "saveWorkflowInstructionDefaults")
      .mockResolvedValue(document("r3", "Latest defaults"));
    render(<WorkflowInstructionDefaultsCard />);
    fireEvent.click(
      screen.getByRole("button", { name: "Load instruction defaults" }),
    );
    await screen.findByLabelText("Additional workflow guidance");
    fireEvent.click(
      screen.getByRole("button", { name: "Update from current defaults…" }),
    );
    await screen.findByLabelText("Proposed instructions");
    expect(save).not.toHaveBeenCalled();
    fireEvent.click(
      screen.getByRole("button", { name: "Apply reviewed instruction update" }),
    );
    await waitFor(() => expect(save).toHaveBeenCalledOnce());
    expect(save.mock.calls[0]![1]).toBe("r2");
    expect(save.mock.calls[0]![0].assets[0].body).toBe("Latest defaults");
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        "Instruction defaults saved",
      ),
    );
  });
});
