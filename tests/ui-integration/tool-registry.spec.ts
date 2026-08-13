import { expect, test } from "@playwright/test";

test.describe("Capability Library navigation", () => {
  test("shows the capability-first registry shell @smoke", async ({ page }) => {
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
    await page.route("**/api/mcp/capabilities**", async (route) =>
      route.fulfill({
        json: {
          snapshot: {
            snapshot_id: "bundled",
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

    await page.goto("/tool-registry");
    await expect(
      page.getByRole("heading", { name: "Engineering Capability Library" }),
    ).toBeVisible();
    await expect(page.getByLabel("Capability filters")).toBeVisible();
    await expect(page.getByTestId("capability-empty-state")).toBeVisible();
  });
});
