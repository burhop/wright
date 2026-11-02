import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { PrintedHandleSetupDialog } from "./PrintedHandleSetupDialog";
import {
  handleProfileRoles,
  handleToolRoles,
  printedHandleSetup,
  type HandleSetupOptions,
  type HandleSetupProposal,
} from "../../services/printed-handle-setup";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import type { OpenWorkspaceToolSetup } from "../../services/workspace-tool-setup";

const document: WorkspaceWorkflowSourceDocument = {
  workspace_id: "workspace",
  path: "workflows/handle.workflow.wflow",
  storage_revision: 1,
  storage_digest: "a".repeat(64),
  definition_revision: 1,
  source: "saved original process",
  metadata_authority: "wright_host",
  size_bytes: 22,
};
const recipe = {
  id: "printed-handle-orca" as const,
  version: "2",
  digest: "b".repeat(64),
};
const options: HandleSetupOptions = {
  workspace_id: document.workspace_id,
  path: document.path,
  workflow_id: "workflow.handle",
  recipe,
  workspace_mount: "/workspace",
  profiles: { mode: "workspace_files", roles: [...handleProfileRoles] },
  requirements: ["FreeCAD, Blender and Orca must be qualified on this host."],
  tools: Object.fromEntries(
    handleToolRoles.map((role) => [
      role,
      [
        {
          server_id: `${role}-server`,
          name: `${role}__tool`,
          tool_name: `${role}_tool`,
          schema_digest: "c".repeat(64),
        },
      ],
    ]),
  ) as HandleSetupOptions["tools"],
};
const proposal: HandleSetupProposal = {
  workspace_id: document.workspace_id,
  workflow_id: options.workflow_id,
  path: document.path,
  expected_storage_revision: 1,
  expected_storage_digest: document.storage_digest,
  proposal_id: "proposal-1",
  proposal_digest: "d".repeat(64),
  recipe,
  source: "prepared exact source",
  source_digest: "e".repeat(64),
  dependencies: [
    {
      path: "inputs/frozen-process.json",
      sha256: "f".repeat(64),
      size_bytes: 84,
    },
  ],
  summary: {
    changes: ["Both orientations use exact profile copies."],
    qualification: "not established",
  },
};
const accepted = {
  ...document,
  source: proposal.source,
  storage_digest: proposal.source_digest,
  storage_revision: 2,
  definition_revision: 2,
};
const listFiles = vi.fn(async () =>
  handleProfileRoles.map((role) => ({
    name: `${role}.json`,
    path: `profiles/${role}.json`,
  })),
);
const onClose = vi.fn();
const onAccepted = vi.fn();
function view(saved = document, onConfigureTools?: OpenWorkspaceToolSetup) {
  return (
    <PrintedHandleSetupDialog
      document={saved}
      sessionId="session"
      onListFiles={listFiles}
      onClose={onClose}
      onAccepted={onAccepted}
      onConfigureTools={onConfigureTools}
    />
  );
}
async function fill() {
  await screen.findByTestId("handle-setup-tool-geometry");
  for (const role of handleProfileRoles)
    fireEvent.change(screen.getByTestId(`handle-setup-profile-${role}`), {
      target: { value: `profiles/${role}.json` },
    });
}
async function prepare() {
  await fill();
  fireEvent.click(screen.getByTestId("handle-setup-propose"));
  await screen.findByTestId("handle-setup-proposal");
}
beforeEach(() => {
  vi.spyOn(printedHandleSetup, "options").mockResolvedValue(
    structuredClone(options),
  );
  vi.spyOn(printedHandleSetup, "propose").mockResolvedValue(
    structuredClone(proposal),
  );
  vi.spyOn(printedHandleSetup, "accept").mockResolvedValue(accepted);
  onClose.mockReset();
  onAccepted.mockReset();
  listFiles.mockClear();
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

it("loads choices only, then requires proposal inspection and explicit acceptance without starting work", async () => {
  render(view());
  await fill();
  expect(printedHandleSetup.propose).not.toHaveBeenCalled();
  expect(printedHandleSetup.accept).not.toHaveBeenCalled();
  expect(screen.getByTestId("handle-setup-recipe")).toHaveTextContent(
    "printed-handle-orca · version 2",
  );
  expect(screen.getByText("Construction · FreeCAD")).toBeVisible();
  expect(screen.getByText("Repair and preview · Blender")).toBeVisible();
  expect(screen.getByTestId("handle-setup-mount")).toHaveAttribute("readonly");
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
  fireEvent.click(screen.getByTestId("handle-setup-propose"));
  await screen.findByTestId("handle-setup-proposal");
  expect(printedHandleSetup.propose).toHaveBeenCalledExactlyOnceWith(
    "session",
    document,
    {
      workspace_mount: "/workspace",
      selected_orientation: "pads_down",
      profiles: Object.fromEntries(
        handleProfileRoles.map((role) => [
          role,
          { path: `profiles/${role}.json` },
        ]),
      ),
      tools: Object.fromEntries(
        handleToolRoles.map((role) => [
          role,
          {
            server_id: `${role}-server`,
            name: `${role}__tool`,
            schema_digest: "c".repeat(64),
          },
        ]),
      ),
    },
  );
  expect(screen.getByTestId("handle-setup-proposal")).toHaveTextContent(
    "Native qualification, model access and current run readiness remain to be checked",
  );
  expect(screen.getByDisplayValue(document.source)).toHaveAttribute("readonly");
  expect(screen.getByDisplayValue(proposal.source)).toHaveAttribute("readonly");
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
  fireEvent.click(screen.getByTestId("handle-setup-reviewed"));
  fireEvent.click(screen.getByTestId("handle-setup-accept"));
  await waitFor(() =>
    expect(onAccepted).toHaveBeenCalledExactlyOnceWith(accepted),
  );
  expect(printedHandleSetup.accept).toHaveBeenCalledExactlyOnceWith(
    "session",
    document,
    proposal,
  );
});

it.each(["tool", "construction", "orientation", "profile"])(
  "invalidates the reviewed proposal when %s changes",
  async (field) => {
    render(view());
    await prepare();
    fireEvent.click(screen.getByTestId("handle-setup-reviewed"));
    const testId =
      field === "profile"
        ? "handle-setup-profile-machine"
        : field === "tool"
          ? "handle-setup-tool-geometry"
          : field === "construction"
            ? "handle-setup-tool-construction"
            : `handle-setup-${field}`;
    fireEvent.change(screen.getByTestId(testId), {
      target: {
        value: field === "orientation" ? "side" : "",
      },
    });
    expect(screen.queryByTestId("handle-setup-proposal")).toBeNull();
    expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
    expect(printedHandleSetup.accept).not.toHaveBeenCalled();
  },
);

it("returns from missing-tool configuration with exact scope and draft choices retained, refreshing actual options", async () => {
  let returnToSetup!: () => void;
  const configure = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        returnToSetup = resolve;
      }),
  );
  vi.mocked(printedHandleSetup.options).mockResolvedValueOnce({
    ...options,
    tools: { ...options.tools, construction: [] },
  });
  render(view(document, configure));
  await fill();
  fireEvent.change(screen.getByTestId("handle-setup-orientation"), {
    target: { value: "side" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Configure the CAD tool" }),
  );
  expect(configure).toHaveBeenCalledWith(
    expect.objectContaining({
      workspaceId: document.workspace_id,
      sessionId: "session",
      sourcePath: document.path,
      sourceDigest: document.storage_digest,
      requirements: options.requirements,
      guideText: expect.stringContaining("# FreeCAD MCP usage guide"),
    }),
  );
  expect(screen.getByTestId("printed-handle-setup-dialog")).not.toHaveAttribute(
    "open",
  );
  await act(async () => returnToSetup());
  await waitFor(() =>
    expect(printedHandleSetup.options).toHaveBeenCalledTimes(2),
  );
  await waitFor(() =>
    expect(screen.getByTestId("handle-setup-tool-construction")).toBeEnabled(),
  );
  expect(screen.getByTestId("printed-handle-setup-dialog")).toHaveAttribute(
    "open",
  );
  expect(screen.getByTestId("handle-setup-orientation")).toHaveValue("side");
  for (const role of handleProfileRoles)
    expect(screen.getByTestId(`handle-setup-profile-${role}`)).toHaveValue(
      `profiles/${role}.json`,
    );
  expect(screen.getByTestId("handle-setup-tool-geometry")).toHaveValue(
    "geometry__tool",
  );
  // A newly available tool is never silently selected on return.
  expect(screen.getByTestId("handle-setup-tool-construction")).toHaveValue("");
  expect(screen.getByTestId("handle-setup-propose")).toBeDisabled();
  fireEvent.change(screen.getByTestId("handle-setup-tool-construction"), {
    target: { value: "construction__tool" },
  });
  expect(screen.getByTestId("handle-setup-propose")).toBeEnabled();
  expect(printedHandleSetup.propose).not.toHaveBeenCalled();
  expect(printedHandleSetup.accept).not.toHaveBeenCalled();
});

it.each(["missing view", "failed opening"])(
  "retains useful help when configuration has a %s",
  async (failure) => {
    vi.mocked(printedHandleSetup.options).mockResolvedValue({
      ...options,
      tools: { ...options.tools, construction: [] },
    });
    const configure =
      failure === "missing view"
        ? undefined
        : vi
            .fn()
            .mockRejectedValue(
              new Error("Configuration unavailable; use provider help."),
            );
    render(view(document, configure));
    await fill();
    fireEvent.click(
      screen.getByRole("button", { name: "Configure the CAD tool" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/unavailable/);
    fireEvent.click(
      screen.getByText("Read provider setup guide (bundled copy)"),
    );
    expect(
      screen.getByRole("heading", { name: "FreeCAD MCP usage guide" }),
    ).toBeVisible();
    expect(screen.getByTestId("handle-setup-profile-machine")).toHaveValue(
      "profiles/machine.json",
    );
    expect(screen.getByTestId("handle-setup-propose")).toBeDisabled();
    expect(screen.getByTestId("printed-handle-setup-dialog")).toHaveAttribute(
      "open",
    );
  },
);

it("holds a failed return refresh, then retries without losing draft selections or restoring an old proposal", async () => {
  render(view());
  await prepare();
  fireEvent.click(screen.getByTestId("handle-setup-reviewed"));
  vi.mocked(printedHandleSetup.options).mockRejectedValueOnce(
    new Error("Current capabilities unavailable"),
  );
  fireEvent.click(screen.getByRole("button", { name: "Refresh choices" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Current capabilities unavailable",
  );
  expect(screen.queryByTestId("handle-setup-propose")).toBeNull();
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Refresh choices" }));
  await screen.findByTestId("handle-setup-propose");
  expect(screen.getByTestId("handle-setup-profile-machine")).toHaveValue(
    "profiles/machine.json",
  );
  expect(screen.queryByTestId("handle-setup-proposal")).toBeNull();
  expect(printedHandleSetup.accept).not.toHaveBeenCalled();
});

it("clears a removed capability and rejects preparation after refresh without losing profile choices", async () => {
  render(view());
  await fill();
  vi.mocked(printedHandleSetup.options).mockResolvedValue({
    ...options,
    tools: { ...options.tools, slicer: [] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Refresh choices" }));
  await screen.findByRole("button", { name: "Configure the slicing tool" });
  expect(screen.getByTestId("handle-setup-propose")).toBeDisabled();
  expect(screen.getByTestId("handle-setup-profile-machine")).toHaveValue(
    "profiles/machine.json",
  );
  expect(printedHandleSetup.propose).not.toHaveBeenCalled();
});

it("discards old setup selections and in-flight return when the exact source changes", async () => {
  let returnToSetup!: () => void;
  const configure = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        returnToSetup = resolve;
      }),
  );
  vi.mocked(printedHandleSetup.options).mockResolvedValueOnce({
    ...options,
    tools: { ...options.tools, construction: [] },
  });
  const rendered = render(view(document, configure));
  await fill();
  fireEvent.click(
    screen.getByRole("button", { name: "Configure the CAD tool" }),
  );
  rendered.rerender(view(accepted, configure));
  await screen.findByTestId("handle-setup-tool-construction");
  await act(async () => returnToSetup());
  expect(printedHandleSetup.options).toHaveBeenCalledTimes(2);
  expect(screen.getByTestId("handle-setup-profile-machine")).toHaveValue("");
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
});

it("reopens retained setup after a same-source document refresh while configuration is open", async () => {
  let returnToSetup!: () => void;
  const configure = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        returnToSetup = resolve;
      }),
  );
  vi.mocked(printedHandleSetup.options).mockResolvedValue({
    ...options,
    tools: { ...options.tools, construction: [] },
  });
  const rendered = render(view(document, configure));
  await fill();
  fireEvent.click(
    screen.getByRole("button", { name: "Configure the CAD tool" }),
  );
  rendered.rerender(view({ ...document, layout_revision: 2 }, configure));
  await waitFor(() =>
    expect(printedHandleSetup.options).toHaveBeenCalledTimes(2),
  );
  await act(async () => returnToSetup());
  expect(screen.getByTestId("printed-handle-setup-dialog")).toHaveAttribute(
    "open",
  );
  expect(screen.getByTestId("handle-setup-profile-machine")).toHaveValue(
    "profiles/machine.json",
  );
  expect(screen.getByTestId("handle-setup-propose")).toBeDisabled();
});

it.each(["construction", "slicer"])(
  "keeps a missing %s provider visible and prevents proposal creation",
  async (role) => {
    vi.mocked(printedHandleSetup.options).mockResolvedValue({
      ...options,
      tools: { ...options.tools, [role]: [] },
    });
    render(view());
    await fill();
    expect(screen.getByText(/No matching tool is available/)).toBeVisible();
    expect(screen.getByTestId("handle-setup-propose")).toBeDisabled();
    expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
    expect(printedHandleSetup.propose).not.toHaveBeenCalled();
  },
);

it("shows unsupported setup requirements without offering preparation or acceptance", async () => {
  vi.mocked(printedHandleSetup.options).mockRejectedValue(
    new Error("This setup recipe is unsupported. Check the Wright version."),
  );
  render(view());
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "setup recipe is unsupported",
  );
  expect(screen.queryByTestId("handle-setup-propose")).toBeNull();
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
  expect(printedHandleSetup.propose).not.toHaveBeenCalled();
  expect(printedHandleSetup.accept).not.toHaveBeenCalled();
});

it("holds source conflicts without retry, accepting or discarding the saved process", async () => {
  vi.mocked(printedHandleSetup.accept).mockRejectedValue(
    new Error("The saved source changed; reopen it."),
  );
  render(view());
  await prepare();
  fireEvent.click(screen.getByTestId("handle-setup-reviewed"));
  fireEvent.click(screen.getByTestId("handle-setup-accept"));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "saved source changed",
  );
  expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
  expect(screen.queryByTestId("handle-setup-proposal")).toBeNull();
  expect(printedHandleSetup.accept).toHaveBeenCalledTimes(1);
  expect(onAccepted).not.toHaveBeenCalled();
});

it("ignores an in-flight proposal after the accepted source context changes", async () => {
  let finish!: (value: HandleSetupProposal) => void;
  vi.mocked(printedHandleSetup.propose).mockReturnValue(
    new Promise((resolve) => {
      finish = resolve;
    }),
  );
  const rendered = render(view());
  await fill();
  fireEvent.click(screen.getByTestId("handle-setup-propose"));
  rendered.rerender(view(accepted));
  await waitFor(() =>
    expect(printedHandleSetup.options).toHaveBeenCalledTimes(2),
  );
  await act(async () => finish(proposal));
  expect(screen.queryByTestId("handle-setup-proposal")).toBeNull();
  expect(printedHandleSetup.accept).not.toHaveBeenCalled();
  expect(onAccepted).not.toHaveBeenCalled();
});

it.each(["workflow_id", "id", "version", "digest"])(
  "rejects a proposal with another recipe or workflow %s without offering acceptance",
  async (field) => {
    const changed = structuredClone(proposal);
    if (field === "workflow_id") changed.workflow_id = "other";
    else Object.assign(changed.recipe, { [field]: "other" });
    vi.mocked(printedHandleSetup.propose).mockResolvedValue(changed);
    render(view());
    await fill();
    fireEvent.click(screen.getByTestId("handle-setup-propose"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "recipe or workflow changed",
    );
    expect(screen.getByTestId("handle-setup-accept")).toBeDisabled();
    expect(printedHandleSetup.accept).not.toHaveBeenCalled();
  },
);
