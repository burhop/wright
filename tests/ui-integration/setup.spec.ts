import { expect, test } from "@playwright/test";

test.describe("Global Settings Flow", () => {
  let savedSettings: Record<string, unknown> | null;

  test.beforeEach(async ({ page }) => {
    savedSettings = null;

    await page.route("**/api/auth/session/status", async (route) => {
      await route.fulfill({
        json: { auth_required: false, authenticated: true },
      });
    });

    // Setup status can report an environment default. Saved appearance comes
    // from /api/settings and must survive a direct page load.
    await page.route("**/api/setup/status", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          is_configured: false,
          llm_api_url: null,
          active_agent: "hermes",
          theme: "dark",
        }),
      });
    });

    await page.route("**/api/settings", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            llm_provider: "hermes",
            theme: savedSettings?.theme ?? "dark",
            api_keys: {},
          }),
        });
        return;
      }

      savedSettings = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
    });
  });

  test("previews and persists appearance while Hermes manages credentials", async ({
    page,
  }) => {
    await page.goto("/settings");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Global Settings",
    );
    const theme = page.getByLabel("Interface Theme");
    await expect(theme).toBeEnabled();
    await expect(theme).toHaveValue("dark");
    await expect(page.getByText("API Keys & Secrets")).toHaveCount(0);
    await expect(page.getByTestId("settings-llm-provider")).toHaveCount(0);
    await expect(
      page.getByRole("link", { name: /Open Model Setup/ }),
    ).toHaveAttribute("href", "/setup/model");

    await theme.selectOption("light");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await expect(page.locator("body")).toHaveCSS(
      "background-color",
      "rgb(232, 237, 245)",
    );
    expect(savedSettings).toBeNull();
    await page.getByTestId("settings-save-btn").click();
    await expect(page.getByTestId("settings-message-banner")).toHaveText(
      "Preferences saved.",
    );
    expect(savedSettings).toEqual({
      llm_provider: "hermes",
      theme: "light",
      api_keys: {},
    });

    await page.reload();
    await expect(theme).toBeEnabled();
    await expect(theme).toHaveValue("light");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await page.goto("/");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
    await page.getByRole("link", { name: "Settings", exact: true }).click();
    await expect(theme).toBeEnabled();
    await theme.selectOption("dark");
    await expect(page.locator("body")).toHaveCSS(
      "background-color",
      "rgb(9, 13, 22)",
    );
    await page.getByTestId("settings-save-btn").click();
    await expect(page.getByTestId("settings-message-banner")).toHaveText(
      "Preferences saved.",
    );
    await page.reload();
    await expect(theme).toHaveValue("dark");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
  });
});
