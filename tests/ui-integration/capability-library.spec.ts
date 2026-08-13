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
            snapshot_id: "bundled-70",
            channel: "bundled",
            sequence: 1,
            offline: true,
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
    ).toContainText("Official preview");
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
      name: "View details for Onshape Labs FeatureScript MCP",
    });
    await details.focus();
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog");
    await expect(dialog).toContainText("App Store subscription");
    await expect(dialog).toContainText("Wright has not contacted the endpoint");
    await dialog
      .getByRole("button", { name: "Check this machine again" })
      .click();
    await expect(dialog).toContainText("Network access was not confirmed");
  });

  test("keeps URL-stable filters and renders an honest empty state", async ({
    page,
  }) => {
    await page.goto("/tool-registry");
    await page.getByLabel("Engineering domain").selectOption("cad");
    await page.getByLabel("Evidence class").selectOption("official_preview");
    await expect(page).toHaveURL(/domain=cad/);
    await expect(page).toHaveURL(/evidence_class=official_preview/);
    await page.getByLabel("Search capabilities").fill("no result");
    await expect(page.getByTestId("capability-empty-state")).toBeVisible();
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
