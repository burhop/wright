import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { WorkflowToolDiscovery } from "../workflow-recovery/workflow-tool-discovery";
import { AuthoringCreateRail } from "../workflow-recovery/AuthoringControls";
import { createNativeToolDiscovery } from "./native-tool-discovery";
import type { HomeCall } from "./NativeHomePanel";

const tool = {
  name: "cad.inspect",
  server_id: "cad",
  server_name: "Study CAD",
  workspace_server: true,
  tool_name: "inspect",
  title: "Inspect CAD",
  description: "Inspect retained geometry",
  input_schema: { type: "object" },
  output_schema: null,
  schema_digest: "a".repeat(64),
};
const payload = {
  workspace_id: "workspace",
  session_id: "session",
  tools: [tool],
};
const fixture = () =>
  vi
    .fn<HomeCall>()
    .mockResolvedValue({ content: [], structuredContent: payload });
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it("uses native scope and keeps tool identity while presenting the server in the shared palette", async () => {
  const call = fixture();
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const onCreateServer = vi.fn();
  const openConnections = vi.fn();
  render(
    <WorkflowToolDiscovery.Provider
      value={{
        read: createNativeToolDiscovery("workspace", "session", call),
        sessionId: "session",
        openConnections,
      }}
    >
      <AuthoringCreateRail
        disabled={false}
        onCreate={vi.fn()}
        onCreateServer={onCreateServer}
      />
    </WorkflowToolDiscovery.Provider>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Add step" }));
  fireEvent.click(screen.getByRole("button", { name: "MCP servers" }));
  fireEvent.click(
    screen.getByRole("button", { name: "Add or enable a server" }),
  );
  expect(openConnections).toHaveBeenCalledTimes(1);
  expect(
    screen.queryByRole("link", { name: "Add or enable a server" }),
  ).toBeNull();
  fireEvent.click(
    await screen.findByTestId("workflow-recovery-create-server-cad"),
  );
  expect(onCreateServer).toHaveBeenCalledWith(
    expect.objectContaining({
      id: "cad",
      name: "Study CAD",
      tools: [
        expect.objectContaining({
          name: tool.name,
          schema_digest: tool.schema_digest,
        }),
      ],
    }),
  );
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_workflow_editor_tools", {
    request: { workspace_id: "workspace", session_id: "session" },
  });
  expect(fetch).not.toHaveBeenCalled();
});

it("rejects a different requested session before making a call", async () => {
  const call = fixture();
  await expect(
    createNativeToolDiscovery("workspace", "session", call)("other"),
  ).rejects.toThrow("unavailable");
  expect(call).not.toHaveBeenCalled();
});

it.each([
  { content: [], isError: true },
  { content: [], structuredContent: { ...payload, workspace_id: "other" } },
  { content: [], structuredContent: { ...payload, session_id: "other" } },
  {
    content: [],
    structuredContent: {
      ...payload,
      tools: [{ ...tool, schema_digest: "invalid" }],
    },
  },
])(
  "rejects unavailable or mismatched discovery without HTTP fallback",
  async (response) => {
    const call = vi.fn<HomeCall>().mockResolvedValue(response);
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    await expect(
      createNativeToolDiscovery("workspace", "session", call)("session"),
    ).rejects.toThrow();
    expect(call).toHaveBeenCalledTimes(1);
    expect(fetch).not.toHaveBeenCalled();
  },
);
