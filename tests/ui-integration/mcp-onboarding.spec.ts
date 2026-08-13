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
          : "remote_endpoint"
        : importedBackend;
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
    await expect(page.getByText("Onboarding completed")).toBeVisible();
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
