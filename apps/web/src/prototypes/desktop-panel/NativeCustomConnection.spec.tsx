import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NativeCustomConnection } from "./NativeCustomConnection";
const workspace = {
  workspace_id: "a",
  session_id: "chat-a",
  workspace_name: "Alpha",
  available: true,
  reason: null,
};
const preview = {
  content: [],
  structuredContent: {
    workspace_id: "a",
    session_id: "chat-a",
    preview_token: "token",
    preview: {
      document_errors: [],
      expires_at: "2026-10-15T12:15:00Z",
      drafts: [
        {
          draft_id: "draft",
          draft_digest: "a".repeat(64),
          name: "Custom CAD",
          endpoint: "https://example.invalid/mcp",
          errors: [],
        },
      ],
    },
  },
};
afterEach(cleanup);
function fill(url = "https://example.invalid/mcp") {
  fireEvent.change(screen.getByLabelText("Connection name"), {
    target: { value: "Custom CAD" },
  });
  fireEvent.change(screen.getByLabelText("Public MCP endpoint"), {
    target: { value: url },
  });
  fireEvent.click(screen.getByRole("button", { name: "Preview connection" }));
}
it("previews without effects and forwards exact draft with publisher completion false by default", async () => {
  const plan = {
    plan_id: "saved",
    plan_digest: "b".repeat(64),
    capability_id: "import:custom",
    workspace_id: "a",
    requested_scope: "workspace",
    state: "blocked",
    blocking_reasons: [],
    effects: [],
  };
  const call = vi
    .fn()
    .mockResolvedValueOnce(preview)
    .mockResolvedValueOnce({
      content: [],
      structuredContent: { workspace_id: "a", session_id: "chat-a", plan },
    });
  const onPlan = vi.fn();
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={onPlan}
    />,
  );
  fill();
  await screen.findByRole("region", { name: "Custom connection preview" });
  expect(call).toHaveBeenCalledTimes(1);
  expect(onPlan).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Review custom setup" }));
  fireEvent.click(screen.getByRole("button", { name: "Review custom setup" }));
  await vi.waitFor(() => expect(onPlan).toHaveBeenCalledWith(plan));
  expect(call).toHaveBeenCalledTimes(2);
  expect(call).toHaveBeenLastCalledWith("wright_connection_import_plan", {
    workspace_id: "a",
    session_id: "chat-a",
    preview_token: "token",
    draft_id: "draft",
    draft_digest: "a".repeat(64),
    independently_completed_license: false,
  });
});
it("rejects credential-bearing endpoint before sending any host tool call", async () => {
  const call = vi.fn();
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fill("https://example.invalid/mcp?token=private");
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Nothing was sent",
  );
  expect(call).not.toHaveBeenCalled();
});
it("stops after uncertain plan creation and directs recovery through saved plans", async () => {
  const call = vi
    .fn()
    .mockResolvedValueOnce(preview)
    .mockRejectedValueOnce(Error("lost response"));
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fill();
  fireEvent.click(
    await screen.findByRole("button", { name: "Review custom setup" }),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Saved setup in this workspace",
  );
  expect(
    screen.getByRole("button", { name: "Review custom setup" }),
  ).toBeDisabled();
  expect(
    screen.getByRole("button", { name: "Preview connection" }),
  ).toBeDisabled();
  expect(call).toHaveBeenCalledTimes(2);
});

const commandArgs = ["-m", "existing_mcp", "a path with spaces"];
function commandPreview() {
  return {
    ...preview,
    structuredContent: {
      ...preview.structuredContent,
      preview: {
        ...preview.structuredContent.preview,
        drafts: [
          {
            draft_id: "draft",
            draft_digest: "a".repeat(64),
            name: "Custom CAD",
            transport: "stdio",
            command: "/usr/bin/python3",
            arguments: commandArgs,
            errors: [],
          },
        ],
      },
    },
  };
}
function fillCommand(argumentsText = JSON.stringify(commandArgs)) {
  fireEvent.change(screen.getByLabelText("Connection type"), {
    target: { value: "stdio" },
  });
  fireEvent.change(screen.getByLabelText("Connection name"), {
    target: { value: "Custom CAD" },
  });
  fireEvent.change(screen.getByLabelText("Executable on Wright host"), {
    target: { value: "/usr/bin/python3" },
  });
  fireEvent.change(screen.getByLabelText("Arguments (JSON array)"), {
    target: { value: argumentsText },
  });
  fireEvent.click(screen.getByRole("button", { name: "Preview connection" }));
}
it("previews literal GB10 command arguments without running or silently approving setup", async () => {
  const call = vi.fn().mockResolvedValue(commandPreview());
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fillCommand();
  await screen.findByRole("region", { name: "Custom connection preview" });
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_connection_command_preview",
    {
      request: {
        workspace_id: "a",
        session_id: "chat-a",
        name: "Custom CAD",
        command: "/usr/bin/python3",
        arguments: commandArgs,
      },
    },
  );
  expect(screen.getByText(/Commands run on the Wright/)).toHaveTextContent(
    "not on the Windows desktop",
  );
  expect(screen.getByRole("checkbox")).not.toBeChecked();
  fireEvent.change(screen.getByLabelText("Arguments (JSON array)"), {
    target: { value: "[]" },
  });
  expect(
    screen.queryByRole("region", { name: "Custom connection preview" }),
  ).not.toBeInTheDocument();
});
it.each(["not-json", "{}", "[42]", JSON.stringify(["x".repeat(4097)])])(
  "rejects malformed or oversized arguments before transport: %s",
  async (text) => {
    const call = vi.fn();
    render(
      <NativeCustomConnection
        workspace={workspace}
        call={call}
        disabled={false}
        onBusy={vi.fn()}
        onPlan={vi.fn()}
      />,
    );
    fillCommand(text);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nothing was sent",
    );
    expect(call).not.toHaveBeenCalled();
  },
);
it.each(["arguments", "workspace"])(
  "does not accept a preview for different %s",
  async (field) => {
    const value = commandPreview();
    if (field === "workspace") value.structuredContent.workspace_id = "other";
    else value.structuredContent.preview.drafts[0].arguments = ["changed"];
    const call = vi.fn().mockResolvedValue(value);
    render(
      <NativeCustomConnection
        workspace={workspace}
        call={call}
        disabled={false}
        onBusy={vi.fn()}
        onPlan={vi.fn()}
      />,
    );
    fillCommand();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No setup was applied",
    );
    expect(
      screen.queryByRole("button", { name: "Review custom setup" }),
    ).not.toBeInTheDocument();
  },
);

it("shows the existing normalizer's actionable diagnostics without enabling plan creation", async () => {
  const value = commandPreview();
  const call = vi.fn().mockResolvedValue({
    ...value,
    structuredContent: {
      ...value.structuredContent,
      preview: {
        ...value.structuredContent.preview,
        drafts: [
          {
            ...value.structuredContent.preview.drafts[0],
            command: null,
            errors: [
              {
                message:
                  "Shell expansion and control operators are not allowed.",
              },
            ],
          },
        ],
      },
    },
  });
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fillCommand();
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Shell expansion and control operators",
  );
  expect(
    screen.queryByRole("button", { name: "Review custom setup" }),
  ).not.toBeInTheDocument();
  expect(call).toHaveBeenCalledTimes(1);
});
it("ignores a saved-plan response after the connection panel unmounts", async () => {
  let finish!: (value: unknown) => void;
  const onPlan = vi.fn();
  const call = vi
    .fn()
    .mockResolvedValueOnce(commandPreview())
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
  const view = render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={onPlan}
    />,
  );
  fillCommand();
  fireEvent.click(
    await screen.findByRole("button", { name: "Review custom setup" }),
  );
  view.unmount();
  finish({
    structuredContent: {
      workspace_id: "a",
      session_id: "chat-a",
      plan: {
        workspace_id: "a",
        requested_scope: "workspace",
        capability_id: "import:draft",
      },
    },
  });
  await Promise.resolve();
  expect(onPlan).not.toHaveBeenCalled();
  expect(call).toHaveBeenCalledTimes(2);
});

it("imports environment names locally and sends only explicitly selected public values", async () => {
  const data = {
    ...preview,
    structuredContent: {
      ...preview.structuredContent,
      preview: {
        ...preview.structuredContent.preview,
        drafts: [
          {
            draft_id: "local",
            draft_digest: "a".repeat(64),
            name: "Design",
            transport: "stdio",
            command: "uvx",
            arguments: ["example-mcp==1.2.3"],
            errors: [],
            env_vars: [{ name: "API_KEY" }],
            launch_env: { RUN_MODE: "read-only" },
          },
        ],
      },
    },
  };
  const call = vi.fn().mockResolvedValue(data);
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByText("Add a custom MCP"));
  const file = new File(["synthetic"], "config.json", {
    type: "application/json",
  });
  Object.defineProperty(file, "text", {
    value: async () =>
      JSON.stringify({
        mcpServers: {
          Design: {
            command: "uvx",
            args: ["example-mcp==1.2.3"],
            env: {
              API_KEY: "placeholder-private-value",
              RUN_MODE: "read-only",
            },
          },
        },
      }),
  });
  fireEvent.change(screen.getByLabelText("Import MCP configuration (JSON)"), {
    target: { files: [file] },
  });
  const include = await screen.findByLabelText(/Include RUN_MODE as public/);
  expect(include).not.toBeChecked();
  expect(call).not.toHaveBeenCalled();
  expect(document.body.textContent).not.toContain("placeholder-private-value");
  fireEvent.click(include);
  fireEvent.click(screen.getByRole("button", { name: "Preview connection" }));
  await screen.findByRole("region", { name: "Custom connection preview" });
  expect(call).toHaveBeenCalledOnce();
  expect(call).toHaveBeenCalledWith("wright_connection_configuration_preview", {
    request: {
      workspace_id: "a",
      session_id: "chat-a",
      name: "Design",
      command: "uvx",
      arguments: ["example-mcp==1.2.3"],
      environment_fields: ["API_KEY", "RUN_MODE"],
      public_environment: { RUN_MODE: "read-only" },
    },
  });
  expect(JSON.stringify(call.mock.calls)).not.toContain(
    "placeholder-private-value",
  );
});

it("opens a replacement with a required fresh name and no write on initialization", async () => {
  const initial = {
    name: "",
    type: "stdio" as const,
    command: "uvx",
    arguments: ["example-mcp==1.0.0"],
    url: "",
    environmentFields: ["API_KEY", "RUN_MODE"],
    publicCandidates: { RUN_MODE: "read-only" },
  };
  const call = vi.fn();
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
      initialConfiguration={initial}
    />,
  );
  expect(screen.getByLabelText("Executable on Wright host")).toHaveValue("uvx");
  expect(screen.getByLabelText("Connection name")).toHaveValue("");
  expect(
    screen.getByRole("button", { name: "Preview connection" }),
  ).toBeDisabled();
  expect(screen.getByLabelText(/Include RUN_MODE as public/)).not.toBeChecked();
  expect(call).not.toHaveBeenCalled();
});

it("imports HTTPS header names while withholding their complete private values", async () => {
  const call = vi
    .fn()
    .mockResolvedValue({
      content: [],
      structuredContent: {
        ...preview.structuredContent,
        preview: {
          ...preview.structuredContent.preview,
          drafts: [
            {
              draft_id: "remote",
              draft_digest: "a".repeat(64),
              name: "Remote",
              endpoint: "https://provider.example/mcp",
              errors: [],
              env_vars: [{ name: "Authorization", target: "http_header" }],
            },
          ],
        },
      },
    });
  render(
    <NativeCustomConnection
      workspace={workspace}
      call={call}
      disabled={false}
      onBusy={vi.fn()}
      onPlan={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByText("Add a custom MCP"));
  const file = new File(["synthetic"], "remote.json", {
    type: "application/json",
  });
  Object.defineProperty(file, "text", {
    value: async () =>
      JSON.stringify({
        name: "Remote",
        url: "https://provider.example/mcp",
        headers: { Authorization: "Bearer placeholder-private" },
      }),
  });
  fireEvent.change(screen.getByLabelText("Import MCP configuration (JSON)"), {
    target: { files: [file] },
  });
  await screen.findByText(/Private HTTP headers after setup/);
  fireEvent.click(screen.getByRole("button", { name: "Preview connection" }));
  await screen.findByRole("region", { name: "Custom connection preview" });
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_connection_configuration_preview",
    {
      request: {
        workspace_id: "a",
        session_id: "chat-a",
        name: "Remote",
        url: "https://provider.example/mcp",
        header_fields: ["Authorization"],
      },
    },
  );
  expect(JSON.stringify(call.mock.calls)).not.toContain("placeholder-private");
});
