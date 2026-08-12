import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test.beforeEach(async ({ page }) => {
    // Mock setup status
    await page.route("**/api/setup/status", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          is_configured: true,
          llm_api_url: "http://localhost:8000",
          active_agent: "hermes",
          theme: "dark",
        }),
      });
    });

    // Navigation is a mocked page-routing test. Keep Settings independent of
    // the optional live backend so a slow response cannot leave its loading
    // placeholder visible for the assertion below.
    await page.route("**/api/settings", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          llm_provider: "hermes",
          theme: "dark",
          api_keys: {},
        }),
      });
    });
  });

  test("should navigate to all sections successfully and persist URLs", async ({
    page,
  }) => {
    await page.goto("/");

    await expect(
      page.getByRole("link", { name: "Dashboard", exact: true }),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole("link", { name: /^Tool Registry/ }).click();
    await expect(page).toHaveURL("/tool-registry");
    await expect(page.getByTestId("page-tool-registry")).toBeVisible();

    await page.getByRole("link", { name: "Logs", exact: true }).click();
    await expect(page).toHaveURL("/logs");
    await expect(page.getByTestId("page-logs")).toBeVisible();

    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await expect(page).toHaveURL("/settings");
    await expect(page.getByTestId("page-settings")).toBeVisible();

    await page.goto("/invalid-url");
    await expect(page.getByTestId("page-not-found")).toBeVisible();

    await page.getByTestId("back-to-dashboard-btn").click();
    await expect(page).toHaveURL("/");
  });
});
