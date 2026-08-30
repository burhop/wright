import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const capability = {
  capability_id: "onshape-labs-featurescript-mcp",
  canonical_id: "onshape-labs-featurescript-mcp",
  name: "Onshape Labs FeatureScript MCP",
  vendor: "Onshape / PTC",
  description: "Generate and refine FeatureScript from engineering intent.",
  domains: ["cad", "cloud-cad"],
  tags: ["onshape", "featurescript"],
  aliases: ["onshape-featurescript-mcp-official"],
  capability_summary: ["Generate FeatureScript", "Test and refine code"],
  evidence_class: "official_preview",
  transport: "streamable_http",
  locality: "remote",
  risk_level: "medium",
  installability_tier: "might_work",
  compatibility: {
    status: "uncertain",
    platform_key: "windows_11_x64",
    reasons: [
      {
        code: "network_access_unconfirmed",
        message: "Network access was not confirmed.",
        recovery: "Review and approve the endpoint during onboarding.",
        source: "machine.network_policy",
      },
    ],
  },
  source_records: [
    {
      url: "https://www.onshape.com/en/blog/featurescript-mcp-server-enables-text-code-cad",
      kind: "vendor_docs",
      primary: true,
      authority: "vendor",
      notes: "Official announcement.",
    },
  ],
  requirements: {
    host_software: [],
    credentials: [],
    license: "App Store subscription completed independently.",
    approval_gates: ["network_access_approval"],
  },
  validation_result: {
    status: "not_tested",
    message: "Wright has not contacted the endpoint.",
    missing_dependencies: [],
  },
  user_state: {
    installed: false,
    active: false,
    process_status: "inactive",
    explicit_disabled: false,
    credentials_configured: {},
    enabled_workspaces: [],
  },
  custom: false,
  available_actions: ["view_details", "observe", "plan_onboarding"],
  alternatives: ["jarvis-onshape-mcp"],
};

test.describe("Offline Capability Library", () => {
  test.beforeEach(async ({ page }) => {
    let catalogActivated = false;
    await page.route("**/api/auth/session/status", async (route) => {
      await route.fulfill({
        json: { auth_required: false, authenticated: true },
      });
    });
    await page.route("**/api/setup/status", async (route) => {
      await route.fulfill({
        json: { is_configured: true, active_agent: "hermes", theme: "dark" },
      });
    });
    await page.route("**/api/mcp/servers", async (route) =>
      route.fulfill({ json: { servers: [] } }),
    );
    await page.route("**/api/mcp/tools", async (route) =>
      route.fulfill({ json: { tools: [] } }),
    );
    await page.route("**/api/mcp/missing-capability-reports", async (route) => {
      const payload = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        json: {
          ...payload,
          report_id: "report-browser-1",
          reporter: "local-admin",
          created_at: "2026-08-12T15:00:00Z",
          updated_at: "2026-08-12T15:00:00Z",
          state: "submitted",
          matched_capability_id: null,
        },
      });
    });
    await page.route("**/api/mcp/catalog/state", async (route) => {
      await route.fulfill({
        json: {
          bundled_snapshot_id: "bundled-70",
          active_snapshot_id: catalogActivated ? "stable-71" : "bundled-70",
          previous_snapshot_id: catalogActivated ? "bundled-70" : null,
          active_sequence: catalogActivated ? 2 : 1,
          active_channel: catalogActivated ? "stable" : "bundled",
          active_generation: catalogActivated ? 2 : 1,
          updated_at: "2026-08-12T00:00:00Z",
          updated_by: "local-admin",
          configured_channels: ["stable"],
          diagnostic: null,
          history: [
            {
              activation_id: catalogActivated ? "activate-1" : "bootstrap-1",
              from_snapshot_id: catalogActivated ? "bundled-70" : null,
              to_snapshot_id: catalogActivated ? "stable-71" : "bundled-70",
              kind: catalogActivated ? "activate" : "bootstrap",
              actor: "local-admin",
              trace_id: "trace-catalog",
              occurred_at: 1,
              result: "succeeded",
              reason_code: null,
            },
          ],
        },
      });
    });
    await page.route("**/api/mcp/catalog/updates/preview", async (route) => {
      await route.fulfill({
        json: {
          preview_id: "preview-1",
          active_snapshot_id: "bundled-70",
          candidate_snapshot_id: "stable-71",
          candidate: {
            channel: "stable",
            sequence: 2,
            schema_version: 1,
            payload_sha256: "a".repeat(64),
            signer_key_id: "key-1",
            expires_at: "2026-08-19T00:00:00Z",
          },
          diff: {
            added: [{ id: "new-official-cad-mcp" }],
            removed: [],
            changed: [],
            summary: {
              added: 1,
              removed: 0,
              changed: 0,
              total_before: 70,
              total_after: 71,
            },
          },
          risk_summary: {
            new_executable_entries: 0,
            new_remote_entries: 1,
            high_or_safety_critical: 0,
            note: "Catalog activation changes metadata only; it cannot install or enable.",
          },
          actor: "local-admin",
          created_at: "2026-08-12T00:00:00Z",
          expires_at: "2026-08-12T00:10:00Z",
          state: "open",
          preview_digest: "b".repeat(64),
        },
      });
    });
    await page.route("**/api/mcp/catalog/updates/*/activate", async (route) => {
      catalogActivated = true;
      await route.fulfill({
        json: {
          state: {},
          reconciled: 71,
          preserved_user_state: true,
          preserved_counts: {},
        },
      });
    });
    await page.route("**/api/mcp/catalog/rollback", async (route) => {
      catalogActivated = false;
      await route.fulfill({
        json: {
          state: {},
          reconciled: 70,
          preserved_user_state: true,
          preserved_counts: {},
        },
      });
    });
    await page.route("**/api/mcp/capabilities**", async (route) => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith("/observe")) {
        await route.fulfill({
          json: {
            observation: {
              observation_id: "machine-1",
              observed_at: "2026-08-12T12:00:00Z",
              expires_at: "2026-08-12T12:15:00Z",
              platform_key: "windows_11_x64",
              os_name: "Windows",
              os_version: "11",
              architecture: "AMD64",
              distribution_mode: "native",
              runtimes: {},
              package_managers: {},
              network_policy: "unknown",
              host_observations: {},
              digest: "a".repeat(64),
            },
            compatibility: capability.compatibility,
          },
        });
        return;
      }
      const search = url.searchParams.get("search");
      await route.fulfill({
        json: {
          snapshot: {
            snapshot_id: catalogActivated ? "stable-71" : "bundled-70",
            channel: catalogActivated ? "stable" : "bundled",
            sequence: catalogActivated ? 2 : 1,
            offline: !catalogActivated,
            updated_at: "2026-08-12T00:00:00Z",
          },
          capabilities: search === "no result" ? [] : [capability],
          next_cursor: null,
          total: search === "no result" ? 0 : 70,
        },
      });
    });
  });

  test("discovers evidence and reasons without network-backed product calls", async ({
    page,
  }) => {
    const vendorRequests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("fs-mcp.labs.onshape.app"))
        vendorRequests.push(request.url());
    });

    await page.goto("/tool-registry");
    await expect(page.getByTestId("capability-offline-source")).toContainText(
      "complete bundled catalog",
    );
    await expect(
      page.getByTestId("evidence-badge-official_preview"),
    ).toContainText("Publisher preview");
    await expect(page.getByTestId("capability-primary-reason")).toContainText(
      "Network access was not confirmed",
    );
    expect(vendorRequests).toEqual([]);
  });

  test("supports keyboard detail review and read-only observation", async ({
    page,
  }) => {
    await page.goto("/tool-registry");
    const details = page.getByRole("button", {
      name: "View MCP server details for Onshape Labs FeatureScript MCP",
    });
    await details.focus();
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("App Store subscription");
    await expect(dialog).toContainText("Wright has not contacted the endpoint");
    await dialog.getByRole("button", { name: "Check this computer" }).click();
    await expect(dialog).toContainText("Network access was not confirmed");
  });

  test("activates and rolls back signed metadata without installing anything", async ({
    page,
  }) => {
    const installRequests: string[] = [];
    page.on("request", (request) => {
      if (/\/api\/mcp\/servers\/[^/]+\/install/.test(request.url())) {
        installRequests.push(request.url());
      }
    });
    await page.goto("/tool-registry");
    await page.getByRole("button", { name: "Check for updates" }).click();
    await expect(page.getByText("Verified signed update")).toBeVisible();
    await page.getByRole("button", { name: "Activate update" }).click();
    await expect(page.getByTestId("catalog-active-source")).toContainText(
      "stable",
    );
    await page.getByRole("button", { name: "Roll back" }).click();
    await expect(page.getByTestId("catalog-active-source")).toContainText(
      "bundled",
    );
    expect(installRequests).toEqual([]);
  });

  test("keeps URL-stable filters and renders an honest empty state", async ({
    page,
  }) => {
    await page.goto("/tool-registry");
    await page.getByLabel("Engineering domain").selectOption("cad");
    await page.getByLabel("Evidence class").selectOption("official_preview");
    await expect(page).toHaveURL(/domain=cad/);
    await expect(page).toHaveURL(/evidence_class=official_preview/);
    await page.getByLabel("Search MCP servers").fill("no result");
    await expect(page.getByTestId("capability-empty-state")).toBeVisible();
  });

  test("reports an empty-result need with structured context and no browser prompt", async ({
    page,
  }) => {
    const dialogs: string[] = [];
    const reports: Record<string, unknown>[] = [];
    page.on("dialog", async (dialog) => {
      dialogs.push(dialog.type());
      await dialog.dismiss();
    });
    page.on("request", (request) => {
      if (request.url().endsWith("/api/mcp/missing-capability-reports")) {
        reports.push(request.postDataJSON());
      }
    });

    await page.goto("/tool-registry");
    await page.getByLabel("Engineering domain").selectOption("cfd");
    await page.getByLabel("Search MCP servers").fill("no result");
    await expect(page.getByTestId("capability-empty-state")).toBeVisible();
    await page
      .getByRole("button", { name: "Report this missing MCP server" })
      .click();
    const form = page.getByRole("dialog", {
      name: "Report a missing MCP server",
    });
    await expect(
      form.getByTestId("missing-capability-search-context"),
    ).toContainText("no result · domain: cfd");
    await form.getByLabel("MCP server name").fill("Requested CFD MCP");
    await form
      .getByLabel("What engineering task should it perform?")
      .fill("Run a steady-state enclosure cooling study");
    await form.getByRole("button", { name: "Submit review request" }).click();
    await expect(form.getByRole("status")).toContainText("report-browser-1");
    expect(reports).toHaveLength(1);
    expect(reports[0]).toMatchObject({
      domains: ["cfd"],
      search_context: {
        query: "no result",
        filters: { domain: "cfd" },
      },
    });
    expect(dialogs).toEqual([]);
  });

  test("works at a narrow engineering-laptop layout with no critical a11y defects", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 760, height: 900 });
    await page.goto("/tool-registry");
    await expect(page.getByTestId("capability-results")).toBeVisible();
    const accessibility = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();
    expect(
      accessibility.violations.filter((violation) =>
        ["critical", "serious"].includes(violation.impact || ""),
      ),
    ).toEqual([]);
  });
});

test.describe("Live local Capability Library", () => {
  test("loads the actual local capability projection without vendor traffic @live", async ({
    page,
  }) => {
    test.setTimeout(90_000);
    const vendorRequests: string[] = [];
    page.on("request", (request) => {
      if (
        !new URL(request.url()).hostname.match(/^(localhost|127\.0\.0\.1)$/)
      ) {
        vendorRequests.push(request.url());
      }
    });
    const response = page.waitForResponse(
      (candidate) =>
        candidate.url().includes("/api/mcp/capabilities") &&
        candidate.request().method() === "GET",
      { timeout: 60_000 },
    );
    await page.goto("/tool-registry");
    expect((await response).status()).toBe(200);
    await expect(
      page.getByRole("heading", { name: "Engineering MCP Server Library" }),
    ).toBeVisible();
    await expect(page.getByLabel("MCP server filters")).toBeVisible();
    expect(vendorRequests).toEqual([]);
  });
});
