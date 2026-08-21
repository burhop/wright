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

    // App startup still reads setup status for the active theme, but setup
    // status no longer gates access to the dashboard or settings page.
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
            theme: "dark",
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

  test("loads and saves LLM, theme, and credential preferences", async ({
    page,
  }) => {
    await page.goto("/settings");

    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      "Global Settings",
    );
    await expect(page.getByTestId("settings-llm-provider")).toHaveValue(
      "hermes",
    );
    await expect(page.getByTestId("settings-theme")).toHaveValue("dark");

    await page.getByTestId("settings-llm-provider").selectOption("openai");
    await page.getByTestId("settings-theme").selectOption("light");
    await page.getByTestId("settings-api-key-openai").fill("sk-test-value");
    await page.getByTestId("settings-save-btn").click();

    await expect(page.getByTestId("settings-message-banner")).toContainText(
      "Global settings successfully updated!",
    );
    await expect
      .poll(() => savedSettings)
      .toMatchObject({
        llm_provider: "openai",
        theme: "light",
        api_keys: {
          OPENAI_API_KEY: "sk-test-value",
        },
      });
  });
});
