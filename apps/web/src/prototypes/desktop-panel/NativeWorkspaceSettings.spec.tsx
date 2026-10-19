import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { NativeWorkspaceSettings } from "./NativeWorkspaceSettings";
import {
  NativeSettingsClient,
  type WorkspaceSettings,
} from "./native-settings-client";
import type { HomeCall } from "./NativeHomePanel";

const workspace = {
  workspace_id: "alpha",
  session_id: "desktop-alpha",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const initial: WorkspaceSettings = {
  workspace_id: "alpha",
  revision: "a".repeat(64),
  workspace_prompt: "old context",
  git_remote_url: null,
  git_username: "public-user",
  git_large_file_threshold: 10485760,
  remote_hidden: true,
};
function fixture() {
  let saved = { ...initial };
  const call = vi.fn<HomeCall>(async (name, args) => {
    if (name === "wright_workspace_settings_save") {
      const request = args.request as { changes: object };
      saved = { ...saved, ...request.changes, revision: "b".repeat(64) };
    }
    return {
      content: [],
      structuredContent: {
        ok: true,
        workspace_id: "alpha",
        session_id: "desktop-alpha",
        settings: saved,
      },
    };
  });
  return {
    call,
    current: () => saved,
    replace: (value: WorkspaceSettings) => {
      saved = value;
    },
  };
}

it("saves only changed nonsecret fields and never copies workspace metadata into a request", async () => {
  const f = fixture();
  const dirty = vi.fn();
  render(
    <NativeWorkspaceSettings
      workspace={workspace}
      call={f.call}
      onDirty={dirty}
    />,
  );
  const field = await screen.findByLabelText("Default workflow context");
  expect(field).toHaveValue("old context");
  expect(f.call.mock.calls[0]).toEqual([
    "wright_workspace_settings_read",
    { request: { workspace_id: "alpha", session_id: "desktop-alpha" } },
  ]);
  fireEvent.change(field, { target: { value: "new context" } });
  fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
  await screen.findByText(
    "Settings saved. Workflow context applies to newly created workflows.",
  );
  const request = f.call.mock.calls.find(
    ([name]) => name === "wright_workspace_settings_save",
  )?.[1].request;
  expect(request).toEqual({
    workspace_id: "alpha",
    session_id: "desktop-alpha",
    expected_revision: initial.revision,
    changes: { workspace_prompt: "new context" },
  });
  expect(f.current().remote_hidden).toBe(true);
  expect(dirty).toHaveBeenLastCalledWith(false);
});

it("keeps an uncertain settings save locked until explicit read finds the intended values, without replay", async () => {
  const f = fixture();
  const dirty = vi.fn();
  const owner = f.call.getMockImplementation()!;
  f.call.mockImplementation(async (name, args) => {
    const result = await owner(name, args);
    if (name === "wright_workspace_settings_save")
      throw new Error("Lost acknowledgement");
    return result;
  });
  render(
    <NativeWorkspaceSettings
      workspace={workspace}
      call={f.call}
      onDirty={dirty}
    />,
  );
  const field = await screen.findByLabelText("Default workflow context");
  fireEvent.change(field, { target: { value: "saved despite lost reply" } });
  fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
  await screen.findByText("Lost acknowledgement");
  expect(field).toBeDisabled();
  expect(screen.getByRole("button", { name: "Save settings" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Read saved settings" }));
  await screen.findByText(
    "Saved settings match your requested values. No write was repeated.",
  );
  expect(field).toHaveValue("saved despite lost reply");
  expect(field).toBeEnabled();
  expect(
    f.call.mock.calls.filter(
      ([name]) => name === "wright_workspace_settings_save",
    ),
  ).toHaveLength(1);
  expect(dirty).toHaveBeenLastCalledWith(false);
});

it("reads a known conflict without discarding local edits; rebasing requires an explicit choice", async () => {
  const f = fixture();
  render(
    <NativeWorkspaceSettings
      workspace={workspace}
      call={f.call}
      onDirty={vi.fn()}
    />,
  );
  const field = await screen.findByLabelText("Default workflow context");
  fireEvent.change(field, { target: { value: "my edit" } });
  f.call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: false,
      error: { outcome_known: true, message: "Settings changed" },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
  await screen.findByText("Settings changed");
  f.replace({
    ...initial,
    workspace_prompt: "another editor",
    git_username: "new-user",
    revision: "c".repeat(64),
  });
  fireEvent.click(screen.getByRole("button", { name: "Read saved settings" }));
  await screen.findByText("another editor");
  expect(field).toHaveValue("my edit");
  expect(screen.getByRole("button", { name: "Save settings" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Keep my edit" }));
  fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
  await screen.findByText(
    "Settings saved. Workflow context applies to newly created workflows.",
  );
  expect(f.call.mock.calls.at(-1)?.[1].request).toMatchObject({
    expected_revision: "c".repeat(64),
    changes: { workspace_prompt: "my edit" },
  });
  expect(f.current().git_username).toBe("new-user");
});

it("refuses credential-bearing remote input before calling the transport", async () => {
  const f = fixture();
  render(
    <NativeWorkspaceSettings
      workspace={workspace}
      call={f.call}
      onDirty={vi.fn()}
    />,
  );
  await screen.findByLabelText("Default workflow context");
  fireEvent.click(screen.getByText("Git settings"));
  fireEvent.change(screen.getByLabelText("Git remote URL"), {
    target: { value: "https://user:private@host/repo" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Save settings" }));
  await screen.findByText(
    "Use HTTPS or SSH without passwords, tokens, query or fragment.",
  );
  expect(
    f.call.mock.calls.filter(
      ([name]) => name === "wright_workspace_settings_save",
    ),
  ).toHaveLength(0);
  expect(screen.queryByLabelText(/token|password/i)).not.toBeInTheDocument();
});

it("keeps a mismatched success uncertain and rejects a foreign settings record", async () => {
  const f = fixture();
  const client = new NativeSettingsClient(workspace, f.call);
  await client.read();
  f.call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: true,
      workspace_id: "alpha",
      session_id: "desktop-alpha",
      settings: initial,
    },
  });
  await expect(client.save({ workspace_prompt: "intended" })).rejects.toThrow(
    "not confirmed",
  );
  await expect(client.save({ workspace_prompt: "intended" })).rejects.toThrow(
    "no save was repeated",
  );
  f.call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      workspace_id: "foreign",
      session_id: "desktop-alpha",
      settings: initial,
    },
  });
  await expect(client.read()).rejects.toThrow("different workspace");
  expect(client.requiresRead).toBe(true);
});

it("an initial read failure can be retried without allocating a write", async () => {
  const f = fixture();
  f.call.mockRejectedValueOnce(new Error("unavailable"));
  render(
    <NativeWorkspaceSettings
      workspace={workspace}
      call={f.call}
      onDirty={vi.fn()}
    />,
  );
  await screen.findByText(
    "Settings could not be read. Try Read saved settings.",
  );
  fireEvent.click(screen.getByRole("button", { name: "Read saved settings" }));
  await waitFor(() =>
    expect(screen.getByLabelText("Default workflow context")).toHaveValue(
      "old context",
    ),
  );
  expect(
    f.call.mock.calls.every(
      ([name]) => name === "wright_workspace_settings_read",
    ),
  ).toBe(true);
});
