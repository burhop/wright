import { expect, test } from "@playwright/test";

function plan(backend: string, capabilityId = "fixture-mcp") {
  return {
    plan_id: `plan-${backend}`,
    plan_version: 1,
    state: "reviewable",
    capability_id: capabilityId,
    snapshot_id: "bundled-70",
    machine_observation_id: "machine-1",
    backend_kind: backend,
    requested_scope: "global_registered",
    source: {},
    requirements: {
      platform: ["windows_11_x64"],
      runtimes: [],
      license: {
        state: "known",
        reference: "MIT",
        independent_completion_required: false,
      },
      credentials: [],
      network: [],
      storage: [],
      host: backend === "host_bridge" ? ["Solid Edge"] : [],
    },
    effects: [
      {
        step_id: "effect-register",
        kind: "write_config",
        description: `Register the reviewed ${backend} configuration.`,
        reversible: true,
      },
    ],
    steps: [],
    validation_steps: [],
    rollback_steps: [],
    approval_gates: [],
    blocking_reasons: [],
    expires_at: "2026-08-12T12:30:00Z",
    plan_digest: "b".repeat(64),
  };
}

test.describe("Guided MCP onboarding", () => {
  test.beforeEach(async ({ page }) => {
    let importedBackend = "local_command";
    await page.route("**/api/auth/session/status", (route) =>
      route.fulfill({ json: { auth_required: false, authenticated: true } }),
    );
    await page.route("**/api/setup/status", (route) =>
      route.fulfill({
        json: { is_configured: true, active_agent: "hermes", theme: "dark" },
      }),
    );
    await page.route("**/api/mcp/catalog/state", (route) =>
      route.fulfill({
        json: {
          bundled_snapshot_id: "bundled-70",
          active_snapshot_id: "bundled-70",
          previous_snapshot_id: null,
          active_sequence: 1,
          active_channel: "bundled",
          active_generation: 1,
          updated_at: "2026-08-12T00:00:00Z",
          updated_by: "wright-bootstrap",
          configured_channels: [],
          diagnostic: null,
          history: [],
        },
      }),
    );
    await page.route("**/api/mcp/servers", (route) =>
      route.fulfill({ json: { servers: [] } }),
    );
    await page.route("**/api/mcp/tools", (route) =>
      route.fulfill({ json: { tools: [] } }),
    );
    await page.route("**/api/workspace/list", (route) =>
      route.fulfill({
        json: {
          workspaces: [
            {
              workspace_id: "workspace-a",
              session_id: "session-a",
              workspace_name: "Bracket project",
              local_path: "D:/workspace/a",
              git_remote_url: null,
              git_username: null,
              enabled_tools: [],
              updated_at: 1,
            },
            {
              workspace_id: "workspace-b",
              session_id: "session-b",
              workspace_name: "Pump project",
              local_path: "D:/workspace/b",
              git_remote_url: null,
              git_username: null,
              enabled_tools: [],
              updated_at: 1,
            },
          ],
        },
      }),
    );
    await page.route("**/api/mcp/capabilities**", (route) =>
      route.fulfill({
        json: {
          snapshot: {
            snapshot_id: "bundled-70",
            channel: "bundled",
            sequence: 1,
            offline: true,
            updated_at: "2026-08-12T00:00:00Z",
          },
          capabilities: [],
          next_cursor: null,
          total: 0,
        },
      }),
    );
    await page.route("**/api/mcp/imports/preview", async (route) => {
      const body = route.request().postDataJSON() as { configuration: string };
      importedBackend = body.configuration.includes("https://")
        ? "remote_endpoint"
        : "local_command";
      await route.fulfill({
        json: {
          preview_id: "import-1",
          detected_format: "plain_server",
          drafts: [
            {
              draft_id: "draft-1",
              name: "Fixture MCP",
              source_format: "plain_server",
              transport:
                importedBackend === "remote_endpoint"
                  ? "streamable_http"
                  : "stdio",
              command: importedBackend === "local_command" ? "python" : null,
              arguments:
                importedBackend === "local_command" ? ["server.py"] : [],
              endpoint:
                importedBackend === "remote_endpoint"
                  ? "https://example.invalid/mcp"
                  : null,
              environment_requirements: [],
              header_requirements: [],
              warnings: [],
              errors: [],
              redacted_preview: {},
              draft_digest: "a".repeat(64),
            },
          ],
          document_errors: [],
          created_at: "2026-08-12T12:00:00Z",
          expires_at: "2026-08-12T12:15:00Z",
          source_discarded: true,
        },
      });
    });
    await page.route("**/api/mcp/install-plans", async (route) => {
      const body = route.request().postDataJSON() as { capability_id?: string };
      const backend = body.capability_id
        ? body.capability_id.includes("solid-edge")
          ? "host_bridge"
          : body.capability_id.includes("nvidia-elements")
            ? "local_package"
            : "remote_endpoint"
        : importedBackend;
      importedBackend = backend;
      await route.fulfill({ json: plan(backend, body.capability_id) });
    });
    await page.route("**/api/mcp/install-plans/*/approve", async (route) => {
      await route.fulfill({
        json: { ...plan(importedBackend), state: "approved" },
      });
    });
    await page.route("**/api/mcp/install-plans/*/apply", async (route) => {
      await route.fulfill({
        json: {
          run_id: "run-1",
          plan_id: `plan-${importedBackend}`,
          plan_digest: "b".repeat(64),
          state: "completed",
          adapter_kind: importedBackend,
          adapter_version: "test",
          started_at: "2026-08-12T12:00:00Z",
          completed_at: "2026-08-12T12:00:01Z",
          effects: [],
          trace_id: "trace-1",
        },
      });
    });
    await page.route("**/api/mcp/servers/*/credentials", (route) =>
      route.fulfill({
        json: { server_id: "fixture-mcp", env_vars: [], configured: {} },
      }),
    );
    await page.route("**/api/mcp/servers/*/validation-runs", (route) =>
      route.fulfill({
        json: {
          evidence_id: "validation-1",
          capability_id: "fixture-mcp",
          server_id: "fixture-mcp",
          snapshot_id: "bundled-70",
          capability_digest: "c".repeat(64),
          observation_id: "machine-1",
          platform_key: "windows_11_x64",
          architecture: "amd64",
          server_revision: "1.0.0",
          credential_binding_digest: "d".repeat(64),
          state: "passed",
          protocol_steps: {
            initialize: "passed",
            "notifications/initialized": "passed",
            "tools/list": "passed",
          },
          schema_digest: "e".repeat(64),
          tool_count: 1,
          read_only_probe: {
            name: "health",
            argument_digest: "f".repeat(64),
            result_digest: "1".repeat(64),
            status: "passed",
            limitation: "Reads fixture status only",
          },
          observed_at: "2026-08-12T12:00:01Z",
          reason_codes: [],
          missing_requirements: [],
        },
      }),
    );
    await page.route("**/api/mcp/workspaces/*/capabilities/*/enable", (route) =>
      route.fulfill({
        json: {
          workspace_id: "workspace-a",
          capability_id: "fixture-mcp",
          server_id: "fixture-mcp",
          enabled: true,
          validation_evidence_id: "validation-1",
          invocation_approved: false,
          message:
            "Available in this workspace. Individual tool invocation remains separate.",
        },
      }),
    );
  });

  test("uses the keyboard for catalog review, credentials, and exact apply", async ({
    page,
  }) => {
    const installRequests: string[] = [];
    page.on("request", (request) => {
      if (/\/servers\/[^/]+\/install/.test(request.url()))
        installRequests.push(request.url());
    });
    await page.goto("/tool-registry");
    const add = page.getByRole("button", { name: "Add capability" });
    await add.focus();
    await page.keyboard.press("Enter");
    await page
      .getByLabel("Capability ID")
      .fill("onshape-labs-featurescript-mcp");
    await page.getByLabel(/independently completed/).check();
    await page.getByRole("button", { name: "Create read-only plan" }).click();
    await expect(page.getByText("Review exact plan")).toBeVisible();
    await page.getByRole("button", { name: "Continue to credentials" }).click();
    await expect(page.getByText("Credential boundary")).toBeVisible();
    await page
      .getByRole("button", { name: "Approve and apply exact plan" })
      .click();
    await expect(page.getByText("Choose one workspace")).toBeVisible();
    await expect(page.getByLabel("Workspace")).toHaveValue("workspace-a");
    await page
      .getByRole("button", { name: "Make available in this workspace" })
      .click();
    await expect(page.getByText("Onboarding completed")).toBeVisible();
    await expect(
      page.getByText(/Individual tool invocation remains separate/),
    ).toBeVisible();
    expect(installRequests).toEqual([]);
  });

  test("normalizes pasted, remote, local, and host sources without preflight effects", async ({
    page,
  }) => {
    for (const source of ["import", "remote", "local", "host"] as const) {
      await page.goto("/tool-registry");
      await page.getByRole("button", { name: "Add capability" }).click();
      await page.getByLabel("Source").selectOption(source);
      if (source === "import") {
        await page
          .getByLabel("MCP configuration JSON")
          .fill(
            '{"name":"safe","command":"python","args":["server.py"],"env":{"API_TOKEN":"secret-not-returned"}}',
          );
      } else if (source === "remote") {
        await page
          .getByLabel("HTTPS MCP endpoint")
          .fill("https://example.invalid/mcp");
      } else if (source === "local") {
        await page.getByLabel("Literal executable").fill("python");
        await page.getByLabel("Literal arguments").fill("server.py");
      } else {
        await page.getByLabel("Capability ID").fill("solid-edge-mcp");
      }
      await page.getByRole("button", { name: "Create read-only plan" }).click();
      await expect(page.getByText("Review exact plan")).toBeVisible();
      await expect(page.locator("body")).not.toContainText(
        "secret-not-returned",
      );
      await page.getByRole("button", { name: "Close onboarding" }).click();
    }
  });

  test("completes local-package, remote-endpoint, and host-bridge journeys", async ({
    page,
  }) => {
    const journeys = [
      {
        source: "catalog",
        capability: "nvidia-elements-mcp",
        backend: "local_package",
      },
      { source: "remote", backend: "remote_endpoint" },
      {
        source: "host",
        capability: "solid-edge-mcp",
        backend: "host_bridge",
      },
    ] as const;

    for (const journey of journeys) {
      await page.goto("/tool-registry");
      await page.getByRole("button", { name: "Add capability" }).click();
      await page.getByLabel("Source").selectOption(journey.source);
      if ("capability" in journey) {
        await page.getByLabel("Capability ID").fill(journey.capability);
        await page.getByLabel(/independently completed/).check();
      } else {
        await page
          .getByLabel("HTTPS MCP endpoint")
          .fill("https://example.invalid/mcp");
      }

      await page.getByRole("button", { name: "Create read-only plan" }).click();
      await expect(page.getByTestId("onboarding-plan-review")).toContainText(
        journey.backend,
      );
      await page
        .getByRole("button", { name: "Continue to credentials" })
        .click();
      await page
        .getByRole("button", { name: "Approve and apply exact plan" })
        .click();
      await expect(page.getByText("Choose one workspace")).toBeVisible();
      await expect(page.getByLabel("Workspace")).toHaveValue("workspace-a");
      await page
        .getByRole("button", { name: "Make available in this workspace" })
        .click();
      await expect(page.getByText("Onboarding completed")).toBeVisible();
      await expect(
        page.getByText(/Individual tool invocation remains separate/),
      ).toBeVisible();
      await page.getByRole("button", { name: "Done" }).click();
    }
  });

  test("shows a changed-plan conflict and returns to review", async ({
    page,
  }) => {
    await page.route("**/api/mcp/install-plans/*/approve", (route) =>
      route.fulfill({
        status: 409,
        json: {
          error_code: "install_plan_invalidated",
          message: "Catalog or machine evidence changed.",
          trace_id: "trace-changed",
          details: { recovery: "Create a fresh plan." },
        },
      }),
    );
    await page.goto("/tool-registry");
    await page.getByRole("button", { name: "Add capability" }).click();
    await page.getByLabel("Capability ID").fill("fixture-mcp");
    await page.getByRole("button", { name: "Create read-only plan" }).click();
    await page.getByRole("button", { name: "Continue to credentials" }).click();
    await page
      .getByRole("button", { name: "Approve and apply exact plan" })
      .click();
    await expect(page.getByRole("alert")).toContainText(
      "install_plan_invalidated",
    );
    await expect(page.getByText("Review exact plan")).toBeVisible();
  });
});

test.describe("Live local guided onboarding", () => {
  test("opens the real read-only source step without applying effects @live", async ({
    page,
  }) => {
    const effectRequests: string[] = [];
    page.on("request", (request) => {
      if (
        request.method() !== "GET" &&
        /\/(apply|install|activate|enable)$/.test(
          new URL(request.url()).pathname,
        )
      ) {
        effectRequests.push(request.url());
      }
    });
    await page.goto("/tool-registry");
    await page.getByRole("button", { name: "Add capability" }).click();
    const dialog = page.getByRole("dialog", {
      name: "Add an engineering capability",
    });
    await expect(dialog.getByLabel("Source")).toHaveValue("catalog");
    await expect(dialog.getByLabel("Capability ID")).toBeVisible();
    await expect(dialog).toContainText(
      "Nothing is installed, connected, or enabled during this step",
    );
    await dialog.getByRole("button", { name: "Close onboarding" }).click();
    expect(effectRequests).toEqual([]);
  });
});
